"""The gold-tier suite: the gallery-wide expectation suite every gold-tier data source proves.

This module builds the suite's collection-time parameterization -- the (case, data source) product
that turns the declarative case table in `gold_expectation_case_table.py` into parametrized test
items --
and the measurement switch that lets a candidate data source be run against the suite before it has
declared gold-tier membership.

Every case is parameterized through `data_sources_for_tier_case(SupportTier.GOLD, case.key)` and
through nothing else, so a member's declared `tier_case_exclusions` entry for a case takes effect no
matter which case asks, exactly as the curated-tier suite does in `test_curated_backend_suite.py`. A
case parameterized directly over a raw membership list would silently ignore that exclusion.

The product is built inside `pytest_generate_tests`, at collection time, rather than once at
import: the registry state that matters is the run's, not the import's, so a data source that
registers after this module is first imported is still picked up the next time collection runs.

An empty product is legal and is not an error: an unclaimed tier and a case every member has
excluded are both states this suite must be able to report, not states it crashes on. The existing
`parameterize_batch_for_data_sources` decorator raises on an empty data-source list; the builder
here deliberately does not.

The test functions that consume the generated parameters -- one per fixture shape, asserting what
a case proves -- are `test_standard_case`, `test_extra_table_case`, and `test_comparison_case`,
below. Each receives the batch (or comparison batch) the harness's own fixtures build from the
generated `TestConfig`, and the `GoldCase` carried alongside it, and asserts the three things a
case proves: the passing configuration succeeds, the failing configuration fails with a message
that says the case is not discriminating (never merely that the expectation failed), and neither
validation raised.
"""

from __future__ import annotations

import inspect
import sys
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    Optional,
    Sequence,
    cast,
)

import pytest

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    from great_expectations.datasource.fluent.interfaces import Batch

import great_expectations.expectations as gxe
from tests.integration.conftest import MultiSourceBatch
from tests.integration.conftest import TestConfig as _TestConfig
from tests.integration.data_sources_and_expectations.gold_expectation_case_table import (
    GOLD_CASES,
)
from tests.integration.data_sources_and_expectations.gold_expectation_cases import (
    EXTRA_TABLE_SELF_REFERENCE,
    GOLD_EXTRA_TABLE_DATA,
    GOLD_EXTRA_TABLE_NAME,
    GOLD_FIXTURE_DATA,
    CaseFixtureShape,
    GoldCase,
)
from tests.integration.test_utils.data_source_config import (
    CiLaneRef,
    DataSourceProvisioning,
    DataSourceTestConfig,
    SupportTier,
    data_sources_for_tier_case,
)
from tests.integration.test_utils.data_source_config.backend_spec import SqlBackendSpec
from tests.integration.test_utils.data_source_config.registry import (
    isolated_registry,
    iter_data_source_configs,
    register_sql_config,
)
from tests.integration.test_utils.execution_engine_kind import ExecutionEngineKind

# The pytest option that turns on measurement mode. Declared once here and read by name from
# `metafunc.config` rather than re-declared, so the option string used to register it
# (`tests/conftest.py`) and the string used to read it can never drift apart.
GOLD_MEASUREMENT_OPTION = "--gold-measurement"

# Which fixture shape each case-consuming test function in this module asserts. A later unit of
# work adds the functions themselves; this mapping is the contract they join by name. A function
# not listed here requests no gold parameterization at all, whatever fixtures it declares.
_SHAPE_BY_TEST_FUNCTION_NAME: Dict[str, CaseFixtureShape] = {
    "test_standard_case": CaseFixtureShape.STANDARD,
    "test_extra_table_case": CaseFixtureShape.EXTRA_TABLE,
    "test_comparison_case": CaseFixtureShape.COMPARISON,
}

# The two fixture names a case-consuming test function must request together for this module to
# parametrize it: the harness's own indirect batch-setup fixture, and the gold case itself.
_BATCH_SETUP_FIXTURE_NAME = "_batch_setup_for_datasource"
_GOLD_CASE_FIXTURE_NAME = "gold_case"


def _candidate_data_sources(
    case: GoldCase, *, measurement_mode: bool
) -> List[DataSourceTestConfig]:
    """The data sources offered to `case`, before the engine filter.

    Normal operation resolves through the tier-case accessor and through nothing else, so a
    member's declared exclusion for `case.key` takes effect. Measurement mode substitutes every
    registered data source that has a config class, unfiltered by tier and by exclusion, because a
    candidate has declared no membership and so has made no claim to be filtered against. A
    data source with no recorded execution engine is still offered here -- `_engine_applies`, run
    unconditionally over every candidate this function returns, already drops it, in both modes;
    filtering it out a second time here would duplicate that check rather than add one, since
    `GoldCase.engines` is never empty and never contains `None`, so `_engine_applies` can never
    see a case an engineless candidate would otherwise slip past.
    """
    if measurement_mode:
        return [
            cast("DataSourceTestConfig", config_class())
            for config_class in iter_data_source_configs()
        ]
    return data_sources_for_tier_case(SupportTier.GOLD, case.key)


def _engine_applies(config: DataSourceTestConfig, case: GoldCase) -> bool:
    """Whether `config`'s execution engine survives `case`'s engine restriction.

    A data source with no recorded execution engine never applies to any case: it names a storage
    target rather than something a single engine reads a batch from. `None` -- what an unrecorded
    engine reads as -- is never a member of `case.engines` (it is always `GoldCase`'s full default
    set or a proper, non-empty subset of `ExecutionEngineKind`, per `GoldCase.__post_init__`), so
    membership alone already excludes an engineless candidate without a separate `is None` guard.
    Neither drop is treated as an exclusion -- `tier_case_exclusions` is the one mechanism that
    means that, and this filter never consults it and never writes to it.
    """
    engine: Optional[ExecutionEngineKind] = config.DATA_SOURCE_SPEC.execution_engine
    return engine in case.engines


def _test_config_for(case: GoldCase, config: DataSourceTestConfig) -> _TestConfig:
    """The `_TestConfig` the existing indirect `_batch_setup_for_datasource` fixture consumes, built
    from `case`'s fixture shape and the shared fixture data `gold_expectation_cases` publishes.

    The `COMPARISON` shape uses the same data source, and the same shared frame, for both the base
    and the comparison side: `gold_expectation_cases` publishes one shared frame, and a case needing
    a comparison source needing different data from the base declares its own frame there when one
    is added, the same way `EXTRA_TABLE` cases share `GOLD_EXTRA_TABLE_DATA` rather than each
    inventing a second table.
    """
    if case.fixture_shape is CaseFixtureShape.STANDARD:
        return _TestConfig(data_source_config=config, data=GOLD_FIXTURE_DATA, extra_data={})
    if case.fixture_shape is CaseFixtureShape.EXTRA_TABLE:
        return _TestConfig(
            data_source_config=config,
            data=GOLD_FIXTURE_DATA,
            extra_data={GOLD_EXTRA_TABLE_NAME: GOLD_EXTRA_TABLE_DATA},
        )
    if case.fixture_shape is CaseFixtureShape.COMPARISON:
        return _TestConfig(
            data_source_config=config,
            data=GOLD_FIXTURE_DATA,
            extra_data={},
            secondary_source_config=config,
            secondary_data=GOLD_FIXTURE_DATA,
        )
    raise ValueError(
        f"Unhandled gold case fixture shape: {case.fixture_shape!r}"
    )  # pragma: no cover


def build_gold_case_params(
    cases: Sequence[GoldCase], *, measurement_mode: bool
) -> List[ParameterSet]:
    """The suite's collection-time (case, data source) product, as a flat list of `pytest.param`.

    For each case, in table order, resolves candidate data sources (through the accessor in normal
    operation, or through the measurement substitution), drops any pair whose data source's
    execution engine is outside the case's restriction or unrecorded, and emits one `pytest.param`
    per surviving pair. Each param's id names both the data source and the case key
    (`<data source test id>-<case key>`); each param's marks are the data source's own mark plus the
    suite marker (`pytest.mark.gold`).

    Legal to return an empty list -- an unclaimed tier or a fully excluded case are both reportable
    states, not errors -- and this never raises for either reason. `pytest.mark.parametrize` (via
    `metafunc.parametrize`) tolerates an empty parameter list on its own: it collects the test as a
    single item automatically skipped for an empty parameter set, rather than raising, which is what
    lets an empty tier and an empty case both survive collection.
    """
    params: List[ParameterSet] = []
    for case in cases:
        candidates = _candidate_data_sources(case, measurement_mode=measurement_mode)
        for config in candidates:
            if not _engine_applies(config, case):
                continue
            params.append(
                pytest.param(
                    _test_config_for(case, config),
                    case,
                    id=f"{config.test_id}-{case.key}",
                    marks=[config.pytest_mark, pytest.mark.gold],
                )
            )
    return params


def _empty_product_placeholder() -> ParameterSet:
    """The single collected item substituted for a truly empty (case, data source) product.

    `metafunc.parametrize` with an empty `argvalues` list already collects one automatically
    skipped item on its own -- that mechanism is what lets an empty tier and a fully excluded case
    survive collection at all (see `build_gold_case_params`'s docstring) -- but pytest's own
    synthetic item carries none of this repo's required markers, which the marker-coverage check
    (`tests/conftest.py::_verify_marker_coverage`) treats as an uncovered test. This placeholder
    supplies that marker explicitly, plus an explicit (rather than pytest's generic) skip reason.

    Its `_batch_setup_for_datasource` and `gold_case` values are never touched: a `pytest.mark.skip`
    on a parametrized item's marks makes pytest skip the item during test *setup*, before any
    fixture (including an indirect one) runs -- verified directly against this repo's fixture, not
    assumed from pytest's docs.
    """
    return pytest.param(
        None,
        None,
        id="no-data-source",
        marks=[
            pytest.mark.project,
            pytest.mark.skip(
                reason="no data source offered this shape's cases anything to validate"
            ),
        ],
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Build the (case, data source) product for this module's case-shape test functions.

    Runs at collection time, once per matching test function, so the registry state it reads is the
    run's registry state rather than whatever the registry held when this module was first
    imported. A function this module has not declared a shape for, or that does not request both
    `_batch_setup_for_datasource` and `gold_case`, is left untouched.
    """
    shape = _SHAPE_BY_TEST_FUNCTION_NAME.get(metafunc.function.__name__)
    if shape is None:
        return
    if _BATCH_SETUP_FIXTURE_NAME not in metafunc.fixturenames:
        return
    if _GOLD_CASE_FIXTURE_NAME not in metafunc.fixturenames:
        return

    measurement_mode = bool(metafunc.config.getoption(GOLD_MEASUREMENT_OPTION))
    cases = [case for case in GOLD_CASES if case.fixture_shape is shape]
    params = build_gold_case_params(cases, measurement_mode=measurement_mode)
    metafunc.parametrize(
        [_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME],
        params or [_empty_product_placeholder()],
        indirect=[_BATCH_SETUP_FIXTURE_NAME],
    )


if TYPE_CHECKING:
    from great_expectations.core.expectation_validation_result import (
        ExpectationValidationResult as _ExpectationValidationResult,
    )


def _raised_exception(exception_info: Mapping[str, object]) -> bool:
    """Whether `exception_info` records a raised exception, in either shape
    `ExpectationValidationResult.exception_info` takes.

    The documented, ordinary shape is flat: `{"raised_exception": bool, ...}`. But when metric
    *resolution* itself fails -- for instance, a column that does not exist in the batch -- GX
    instead reports a dict keyed by metric-configuration-id, each value itself the same flat
    shape. `exception_info.get("raised_exception")` alone silently reads `None` (falsy) for that
    second shape, which would let a case whose configuration crashed pass this suite's "neither
    validation raised" assertion instead of failing it.
    """
    direct = exception_info.get("raised_exception")
    if isinstance(direct, bool):
        return direct
    return any(
        isinstance(value, Mapping) and bool(value.get("raised_exception"))
        for value in exception_info.values()
    )


def _assert_case_proves_its_expectation(
    case: GoldCase,
    *,
    validate_passing: Callable[[], _ExpectationValidationResult],
    validate_failing: Callable[[], _ExpectationValidationResult],
) -> None:
    """Assert the three verdicts every gold case proves, per case-shape test function below.

    `validate_passing` and `validate_failing` run `case.passing`/`case.failing` against this
    test's batch and return the result. Taking callables rather than results keeps this helper
    identical across shapes despite each shape resolving and validating its case differently.
    """
    passing_result = validate_passing()
    assert not _raised_exception(passing_result.exception_info), (
        f"gold case {case.key!r}: the passing configuration raised during "
        f"validation instead of evaluating cleanly: {passing_result.exception_info}"
    )
    assert passing_result.success, (
        f"gold case {case.key!r}: the configuration declared as `passing` reported failure. "
        f"result={passing_result}"
    )

    failing_result = validate_failing()
    assert not _raised_exception(failing_result.exception_info), (
        f"gold case {case.key!r}: the failing configuration raised during validation instead of "
        f"evaluating to false: {failing_result.exception_info}"
    )
    assert not failing_result.success, (
        f"gold case {case.key!r} is not discriminating: its `failing` configuration reported "
        "success against the shared fixture data, so this case cannot distinguish a working "
        "implementation of the expectation from a broken one. This is not an ordinary expectation "
        "failure -- fix the case's `failing` configuration or fixture data. "
        f"result={failing_result}"
    )


def test_standard_case(
    batch_for_datasource: Batch,
    gold_case: GoldCase,
) -> None:
    """Assert what a `STANDARD`-shape gold case proves, against the shared fixture alone."""
    _assert_case_proves_its_expectation(
        gold_case,
        validate_passing=lambda: batch_for_datasource.validate(gold_case.passing),
        validate_failing=lambda: batch_for_datasource.validate(gold_case.failing),
    )


def test_extra_table_case(
    batch_for_datasource: Batch,
    _batch_setup_for_datasource: object,
    extra_table_names_for_datasource: Mapping[str, str],
    gold_case: GoldCase,
) -> None:
    """Assert what an `EXTRA_TABLE`-shape gold case proves, resolving each configuration's
    placeholder table reference (`EXTRA_TABLE_SELF_REFERENCE`, or the shared extra table's
    logical name) to the physical table name this test's own batch setup created."""
    from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup

    assert isinstance(_batch_setup_for_datasource, SQLBatchTestSetup)
    primary_table_name = _batch_setup_for_datasource.table_name

    def _resolve(
        expectation: gxe.Expectation,
    ) -> gxe.ExpectTableRowCountToEqualOtherTable:
        assert isinstance(expectation, gxe.ExpectTableRowCountToEqualOtherTable)
        placeholder = expectation.other_table_name
        assert isinstance(placeholder, str), (
            f"gold case {gold_case.key!r}: expected a placeholder `other_table_name` string, "
            f"got {placeholder!r}"
        )
        other_table_name = (
            primary_table_name
            if placeholder == EXTRA_TABLE_SELF_REFERENCE
            else extra_table_names_for_datasource[placeholder]
        )
        resolved = expectation.copy(update={"other_table_name": other_table_name})
        assert isinstance(resolved, gxe.ExpectTableRowCountToEqualOtherTable)
        return resolved

    _assert_case_proves_its_expectation(
        gold_case,
        validate_passing=lambda: batch_for_datasource.validate(_resolve(gold_case.passing)),
        validate_failing=lambda: batch_for_datasource.validate(_resolve(gold_case.failing)),
    )


def test_comparison_case(
    multi_source_batch: MultiSourceBatch,
    gold_case: GoldCase,
) -> None:
    """Assert what a `COMPARISON`-shape gold case proves, resolving each configuration's
    placeholder comparison-source reference to the comparison batch this test's own multi-source
    setup created."""

    def _resolve(
        expectation: gxe.Expectation,
    ) -> gxe.ExpectQueryResultsToMatchComparison:
        assert isinstance(expectation, gxe.ExpectQueryResultsToMatchComparison)
        comparison_query = expectation.comparison_query
        assert isinstance(comparison_query, str), (
            f"gold case {gold_case.key!r}: expected a placeholder `comparison_query` string, "
            f"got {comparison_query!r}"
        )
        resolved_query = comparison_query.replace(
            "{source_table}", multi_source_batch.comparison_table_name
        )
        resolved = expectation.copy(
            update={
                "comparison_data_source_name": multi_source_batch.comparison_data_source_name,
                "comparison_query": resolved_query,
            }
        )
        assert isinstance(resolved, gxe.ExpectQueryResultsToMatchComparison)
        return resolved

    _assert_case_proves_its_expectation(
        gold_case,
        validate_passing=lambda: multi_source_batch.base_batch.validate(
            _resolve(gold_case.passing)
        ),
        validate_failing=lambda: multi_source_batch.base_batch.validate(
            _resolve(gold_case.failing)
        ),
    )


@pytest.mark.project
def test_shape_dispatch_names_a_real_function_for_every_key_and_vice_versa() -> None:
    """`_SHAPE_BY_TEST_FUNCTION_NAME` is a bijection with the case-consuming functions in this
    module: every key names a real function here, and every case-consuming function here (one
    named `test_*_case`, taking the `gold_case` fixture) has a key. Without this guard, renaming
    a consumer function silently drops its shape from collection -- `pytest_generate_tests` would
    just never dispatch to it, yielding zero collected cases for that shape with a green suite."""
    module_globals = sys.modules[__name__].__dict__
    for function_name in _SHAPE_BY_TEST_FUNCTION_NAME:
        candidate = module_globals.get(function_name)
        assert callable(candidate), (
            f"_SHAPE_BY_TEST_FUNCTION_NAME names {function_name!r}, but this module defines no "
            "such function."
        )

    case_consuming_names = {
        name
        for name, value in module_globals.items()
        if callable(value)
        and getattr(value, "__module__", None) == __name__
        and _GOLD_CASE_FIXTURE_NAME in inspect.signature(value).parameters
    }
    assert case_consuming_names == set(_SHAPE_BY_TEST_FUNCTION_NAME), (
        "A function in this module requests the `gold_case` fixture but has no entry in "
        "_SHAPE_BY_TEST_FUNCTION_NAME, or vice versa. "
        f"dispatch={sorted(_SHAPE_BY_TEST_FUNCTION_NAME)} "
        f"consumers={sorted(case_consuming_names)}"
    )


# --------------------------------------------------------------------------------------------
# Coverage for the collection-time builder
# --------------------------------------------------------------------------------------------
#
# GOLD_CASES holds one seed case per fixture shape today; later work fills out the rest of the
# gallery. No real data source declares SupportTier.GOLD yet, so the product is empty in normal
# mode. That state is exercised directly below rather than worked around: an unclaimed tier, and
# a table holding no case of a given shape, are exactly the states the builder has to survive.
# Every other behavior -- exclusion honored, engine restriction applied, engineless data source
# dropped, measurement substitution -- is proven against throwaway cases and
# throwaway registrations, per the module docstring, so none of it waits on a later unit of work
# filling in real cases or real gold-tier members.


def _make_throwaway_case(
    key: str, *, engines: Optional[FrozenSet[ExecutionEngineKind]] = None
) -> GoldCase:
    expectation = gxe.ExpectColumnValuesToNotBeNull(column="increasing_key")
    kwargs: dict[str, object] = {"key": key, "passing": expectation, "failing": expectation}
    if engines is not None:
        kwargs["engines"] = engines
        kwargs["engine_restriction_reason"] = "throwaway restriction for a builder test"
    return GoldCase(**kwargs)  # type: ignore[arg-type]


def _make_gold_backend_spec(**overrides: object) -> SqlBackendSpec:
    defaults: dict[str, object] = dict(
        label="throwaway-gold-backend",
        public_name="Throwaway Gold Backend",
        marker="throwaway_gold_backend",
        provisioning=DataSourceProvisioning.LOCAL_FILE,
        ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="throwaway_gold_backend"),
        uses_schema=False,
        tiers=frozenset({SupportTier.GOLD, SupportTier.CANONICAL_EXPECTATIONS}),
        execution_engine=ExecutionEngineKind.SQL,
    )
    defaults.update(overrides)
    return SqlBackendSpec(**defaults)  # type: ignore[arg-type]


def _make_config_class(name: str, spec: SqlBackendSpec) -> type:
    """A minimal, instantiable `DataSourceTestConfig` subclass carrying `spec`, so a throwaway
    registration behaves like a real config for every property `build_gold_case_params` reads
    (`.label`, `.pytest_mark`, `.test_id`, `.data_source_spec`) -- not just the raw class
    attribute the registry itself reads.
    """

    def _create_batch_setup(self, *args: object, **kwargs: object) -> object:
        raise NotImplementedError("this throwaway config is never used to create a real batch")

    return type(
        name,
        (DataSourceTestConfig,),
        {"DATA_SOURCE_SPEC": spec, "create_batch_setup": _create_batch_setup},
    )


def _param_test_config(param: ParameterSet) -> _TestConfig:
    """The `_TestConfig` half of `param.values`, narrowed by an `isinstance` assertion.

    `ParameterSet.values` types each element as `object | NotSetType`, so a direct attribute
    access on `param.values[0]` is unchecked -- mypy cannot see through it. Narrowing here, once,
    keeps every call site's assertion about what a param actually carries genuinely checked rather
    than silently `Any`.
    """
    test_config, _gold_case = param.values
    assert isinstance(test_config, _TestConfig)
    return test_config


def _param_gold_case(param: ParameterSet) -> GoldCase:
    """The `GoldCase` half of `param.values`, narrowed the same way as `_param_test_config`."""
    _test_config, gold_case = param.values
    assert isinstance(gold_case, GoldCase)
    return gold_case


class TestBuildGoldCaseParams:
    """Direct coverage of `build_gold_case_params`, the pure function `pytest_generate_tests`
    delegates to. Asserted against the returned `pytest.param` objects themselves -- their ids,
    their marks, and which `_TestConfig`/`GoldCase` pair they carry -- never by reaching a data
    source, since none of these tests set up a batch.

    Marked `project` here, on the class, rather than on the module: the generated case-shape
    tests a later unit of work adds to this module carry their own marks (a data source's own
    mark plus `gold`) through `build_gold_case_params` itself, and a module-level mark would give
    each of those a second required marker alongside its own.
    """

    pytestmark = pytest.mark.project

    def test_empty_case_list_returns_no_params(self) -> None:
        assert build_gold_case_params([], measurement_mode=False) == []

    def test_unclaimed_tier_returns_no_params_without_raising(self) -> None:
        # No real data source declares SupportTier.GOLD today; this is the "tier unclaimed" state
        # the suite must report rather than crash on.
        case = _make_throwaway_case("unclaimed_tier_case")
        assert build_gold_case_params([case], measurement_mode=False) == []

    def test_normal_mode_resolves_through_the_tier_case_accessor_and_honors_exclusion(self) -> None:
        case_key = "exclusion_honoring_case"
        excluded_spec = _make_gold_backend_spec(
            label="excluded-backend",
            public_name="Excluded Backend",
            marker="sqlite",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="sqlite"),
            tier_case_exclusions={SupportTier.GOLD: {case_key: "throwaway exclusion for a test"}},
        )
        included_spec = _make_gold_backend_spec(
            label="included-backend",
            public_name="Included Backend",
            marker="postgresql",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="postgresql"),
        )
        with isolated_registry():
            register_sql_config(_make_config_class("ExcludedBackend", excluded_spec))
            register_sql_config(_make_config_class("IncludedBackend", included_spec))

            case = _make_throwaway_case(case_key)
            params = build_gold_case_params([case], measurement_mode=False)

            expected_configs = data_sources_for_tier_case(SupportTier.GOLD, case_key)

        assert [config.label for config in expected_configs] == ["included-backend"]
        assert len(params) == 1
        [param] = params
        test_config, gold_case = param.values
        assert isinstance(test_config, _TestConfig)
        assert test_config.data_source_config.label == "included-backend"
        assert gold_case is case
        assert param.id == f"included-backend-{case_key}"
        assert {mark.name for mark in param.marks} == {"postgresql", "gold"}

    def test_engine_restriction_drops_a_pair_without_treating_it_as_an_exclusion(self) -> None:
        case_key = "engine_restricted_case"
        sql_spec = _make_gold_backend_spec(
            label="sql-backend",
            public_name="SQL Backend",
            marker="mysql",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="mysql"),
            execution_engine=ExecutionEngineKind.SQL,
        )
        pandas_spec = _make_gold_backend_spec(
            label="pandas-backend",
            public_name="Pandas Backend",
            marker="filesystem",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="filesystem"),
            execution_engine=ExecutionEngineKind.PANDAS,
        )
        with isolated_registry():
            register_sql_config(_make_config_class("SqlBackend", sql_spec))
            register_sql_config(_make_config_class("PandasBackend", pandas_spec))

            case = _make_throwaway_case(case_key, engines=frozenset({ExecutionEngineKind.SQL}))
            params = build_gold_case_params([case], measurement_mode=False)

        assert len(params) == 1
        [param] = params
        assert _param_test_config(param).data_source_config.label == "sql-backend"
        # Dropping the pandas backend must not be recorded on it as a `tier_case_exclusions`
        # entry -- nothing in this test declared one, so the registry's own record of that
        # backend must still show none.
        assert pandas_spec.tier_case_exclusions == {}

    def test_data_source_with_no_recorded_engine_is_dropped(self) -> None:
        # A positive control (an engine-bearing, config-bound backend) sits alongside the
        # engineless one so this test is a set difference, not an emptiness check: `params == []`
        # alone cannot distinguish "the engineless backend was dropped for its missing engine"
        # from "everything was dropped for any reason at all."
        case_key = "no_engine_case"
        engineless_spec = _make_gold_backend_spec(
            label="engineless-backend",
            public_name="Engineless Backend",
            marker="trino",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="trino"),
            execution_engine=None,
        )
        engine_bearing_spec = _make_gold_backend_spec(
            label="engine-bearing-backend",
            public_name="Engine Bearing Backend",
            marker="postgresql",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="postgresql"),
            execution_engine=ExecutionEngineKind.SQL,
        )
        with isolated_registry():
            register_sql_config(_make_config_class("EngineLessBackend", engineless_spec))
            register_sql_config(_make_config_class("EngineBearingBackend", engine_bearing_spec))

            case = _make_throwaway_case(case_key)
            params = build_gold_case_params([case], measurement_mode=False)

        labels = {_param_test_config(param).data_source_config.label for param in params}
        assert labels == {"engine-bearing-backend"}

    def test_measurement_mode_emits_one_param_per_registered_candidate_with_config_and_engine(
        self,
    ) -> None:
        # A positive control (an engine-bearing, config-bound backend) and a negative control (an
        # engineless one) are registered together, and the expected labels are stated literally
        # rather than by re-running the production predicate over `iter_data_source_configs()` --
        # doing that would move both sides of the assertion together and let a broken filter
        # survive undetected.
        case_key = "measurement_mode_case"
        engine_bearing_spec = _make_gold_backend_spec(
            label="measurement-engine-bearing-backend",
            public_name="Measurement Engine Bearing Backend",
            marker="postgresql",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="postgresql"),
            execution_engine=ExecutionEngineKind.SQL,
        )
        engineless_spec = _make_gold_backend_spec(
            label="measurement-engineless-backend",
            public_name="Measurement Engineless Backend",
            marker="trino",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="trino"),
            execution_engine=None,
        )
        with isolated_registry():
            register_sql_config(
                _make_config_class("MeasurementEngineBearingBackend", engine_bearing_spec)
            )
            register_sql_config(_make_config_class("MeasurementEnginelessBackend", engineless_spec))

            case = _make_throwaway_case(case_key)
            params = build_gold_case_params([case], measurement_mode=True)

            labels = {_param_test_config(param).data_source_config.label for param in params}
            ids = {param.id for param in params}

        assert labels == {"measurement-engine-bearing-backend"}
        assert ids == {f"measurement-engine-bearing-backend-{case_key}"}
        for param in params:
            assert pytest.mark.gold in param.marks

    def test_measurement_mode_ignores_a_declared_exclusion(self) -> None:
        # A candidate in measurement mode has declared no membership at all, so it has nothing
        # for `tier_case_exclusions` to take effect against -- unlike normal mode, an exclusion
        # declared for this case must not remove the backend from measurement mode's result.
        case_key = "measurement_ignores_exclusion_case"
        excluded_spec = _make_gold_backend_spec(
            label="measurement-excluded-backend",
            public_name="Measurement Excluded Backend",
            marker="oracle",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="oracle"),
            tier_case_exclusions={SupportTier.GOLD: {case_key: "throwaway exclusion for a test"}},
        )
        with isolated_registry():
            register_sql_config(_make_config_class("MeasurementExcludedBackend", excluded_spec))

            case = _make_throwaway_case(case_key)
            params = build_gold_case_params([case], measurement_mode=True)

            labels = {_param_test_config(param).data_source_config.label for param in params}

        assert "measurement-excluded-backend" in labels

    def test_a_case_declaring_empty_engines_shape_is_rejected_at_construction(self) -> None:
        with pytest.raises(ValueError, match="empty engine set"):
            _make_throwaway_case("empty_engines_case", engines=frozenset())


# --------------------------------------------------------------------------------------------
# Coverage for `pytest_generate_tests` itself
# --------------------------------------------------------------------------------------------
#
# `pytest_generate_tests` is a collection-time hook: pytest calls it with a real `Metafunc`, which
# nothing here constructs. A stub carrying exactly the four members the hook reads --
# `function.__name__`, `fixturenames`, `config.getoption`, and a recording `parametrize` -- is
# enough to drive it directly and pin all four behaviors the hook itself is responsible for: the
# `_SHAPE_BY_TEST_FUNCTION_NAME` name dispatch, both `fixturenames` gates, the
# `--gold-measurement` option read reaching `build_gold_case_params`, and `indirect=` being passed
# as intended. `build_gold_case_params` itself is not re-verified here -- that is
# `TestBuildGoldCaseParams`'s job -- so these cases use throwaway registrations only large enough
# to tell the hook's own wiring apart from a no-op.


class _RecordedParametrizeCall:
    def __init__(
        self,
        argnames: object,
        argvalues: object,
        *,
        indirect: object,
    ) -> None:
        self.argnames = argnames
        self.argvalues = list(cast("List[ParameterSet]", argvalues))
        self.indirect = indirect


class _StubMetafunc:
    """A minimal stand-in for `pytest.Metafunc`, carrying only what `pytest_generate_tests` reads
    and a recording `parametrize` in place of pytest's collection-time one."""

    def __init__(
        self,
        *,
        function_name: str,
        fixturenames: Sequence[str],
        measurement_mode: bool,
    ) -> None:
        self.function = type("StubFunction", (), {"__name__": function_name})()
        self.fixturenames = list(fixturenames)
        self.config = type(
            "StubConfig",
            (),
            {
                "getoption": lambda self, name: measurement_mode
                if name == GOLD_MEASUREMENT_OPTION
                else None
            },  # FIXME CoP
        )()
        self.calls: List[_RecordedParametrizeCall] = []

    def parametrize(
        self,
        argnames: object,
        argvalues: object,
        *,
        indirect: object = False,
    ) -> None:
        self.calls.append(_RecordedParametrizeCall(argnames, argvalues, indirect=indirect))


class TestPytestGenerateTests:
    """Direct coverage of the `pytest_generate_tests` hook, via `_StubMetafunc`."""

    pytestmark = pytest.mark.project

    def test_empty_product_is_collected_as_one_marked_skipped_placeholder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # No case of this shape, no registration at all -- guarantees an empty product without
        # depending on the real registry's current state.
        monkeypatch.setattr(sys.modules[__name__], "GOLD_CASES", ())
        metafunc = _StubMetafunc(
            function_name="test_standard_case",
            fixturenames=[_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME],
            measurement_mode=False,
        )
        pytest_generate_tests(cast("pytest.Metafunc", metafunc))

        [call] = metafunc.calls
        # A real, non-empty parametrize call -- not the empty list `build_gold_case_params` itself
        # would legally return -- is what makes marker-coverage see a required marker on this
        # otherwise-collected-but-empty test (see `_empty_product_placeholder`'s docstring).
        assert len(call.argvalues) == 1
        [param] = call.argvalues
        assert param.values == (None, None)
        assert {mark.name for mark in param.marks} == {"project", "skip"}

    def test_unrecognized_function_name_is_left_untouched(self) -> None:
        metafunc = _StubMetafunc(
            function_name="test_not_a_gold_shape_function",
            fixturenames=[_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME],
            measurement_mode=False,
        )
        pytest_generate_tests(cast("pytest.Metafunc", metafunc))
        assert metafunc.calls == []

    def test_recognized_name_missing_batch_setup_fixture_is_left_untouched(self) -> None:
        metafunc = _StubMetafunc(
            function_name="test_standard_case",
            fixturenames=[_GOLD_CASE_FIXTURE_NAME],
            measurement_mode=False,
        )
        pytest_generate_tests(cast("pytest.Metafunc", metafunc))
        assert metafunc.calls == []

    def test_recognized_name_missing_gold_case_fixture_is_left_untouched(self) -> None:
        metafunc = _StubMetafunc(
            function_name="test_standard_case",
            fixturenames=[_BATCH_SETUP_FIXTURE_NAME],
            measurement_mode=False,
        )
        pytest_generate_tests(cast("pytest.Metafunc", metafunc))
        assert metafunc.calls == []

    def test_recognized_name_with_both_fixtures_dispatches_by_shape_and_reads_the_option(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Two throwaway cases of different shapes: only the STANDARD one may reach the builder for
        # `test_standard_case`, which pins the `_SHAPE_BY_TEST_FUNCTION_NAME` dispatch itself, not
        # just "some case reached the builder."
        standard_case = _make_throwaway_case("generate_tests_standard_case")
        extra_table_case = GoldCase(
            key="generate_tests_extra_table_case",
            passing=standard_case.passing,
            failing=standard_case.failing,
            fixture_shape=CaseFixtureShape.EXTRA_TABLE,
        )
        # Patched on the live module object (via `sys.modules[__name__]`), not by dotted string
        # path: this directory has no `__init__.py`, so pytest collects this file under its bare
        # module name while the dotted path resolves (via PEP 420 namespace packages) to a
        # *second*, independently-imported module object -- patching that one leaves the globals
        # `pytest_generate_tests` actually reads untouched.
        monkeypatch.setattr(sys.modules[__name__], "GOLD_CASES", (standard_case, extra_table_case))

        spec = _make_gold_backend_spec(
            label="generate-tests-backend",
            public_name="Generate Tests Backend",
            marker="postgresql",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="postgresql"),
        )
        with isolated_registry():
            register_sql_config(_make_config_class("GenerateTestsBackend", spec))

            metafunc = _StubMetafunc(
                function_name="test_standard_case",
                fixturenames=[_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME],
                measurement_mode=False,
            )
            pytest_generate_tests(cast("pytest.Metafunc", metafunc))

            expected_params = build_gold_case_params([standard_case], measurement_mode=False)

        assert len(metafunc.calls) == 1
        [call] = metafunc.calls
        assert call.argnames == [_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME]
        assert call.indirect == [_BATCH_SETUP_FIXTURE_NAME]
        assert {param.id for param in call.argvalues} == {param.id for param in expected_params}
        # The EXTRA_TABLE case must not have contributed a param to a STANDARD-shape function.
        assert all(_param_gold_case(param).key != extra_table_case.key for param in call.argvalues)

    def test_measurement_option_reaches_the_builder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        case = _make_throwaway_case("generate_tests_measurement_case")
        monkeypatch.setattr(sys.modules[__name__], "GOLD_CASES", (case,))

        excluded_spec = _make_gold_backend_spec(
            label="generate-tests-measurement-backend",
            public_name="Generate Tests Measurement Backend",
            marker="postgresql",
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="postgresql"),
            tier_case_exclusions={SupportTier.GOLD: {case.key: "throwaway exclusion for a test"}},
        )
        with isolated_registry():
            register_sql_config(
                _make_config_class("GenerateTestsMeasurementBackend", excluded_spec)
            )

            normal_metafunc = _StubMetafunc(
                function_name="test_standard_case",
                fixturenames=[_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME],
                measurement_mode=False,
            )
            pytest_generate_tests(cast("pytest.Metafunc", normal_metafunc))

            measurement_metafunc = _StubMetafunc(
                function_name="test_standard_case",
                fixturenames=[_BATCH_SETUP_FIXTURE_NAME, _GOLD_CASE_FIXTURE_NAME],
                measurement_mode=True,
            )
            pytest_generate_tests(cast("pytest.Metafunc", measurement_metafunc))

        # Normal mode resolves through the tier-case accessor, so a declared exclusion for this
        # backend/case pair drops it; measurement mode ignores that exclusion entirely. The two
        # calls' argvalues differing is the evidence that `metafunc.config.getoption` actually
        # reached `build_gold_case_params` rather than the option being read and then ignored.
        [normal_call] = normal_metafunc.calls
        [measurement_call] = measurement_metafunc.calls
        # An empty product is substituted with the single marked placeholder param -- see
        # `_empty_product_placeholder` -- rather than an empty list, so this asserts that
        # substitution rather than emptiness.
        assert len(normal_call.argvalues) == 1
        [normal_param] = normal_call.argvalues
        assert normal_param.values == (None, None)
        assert {mark.name for mark in normal_param.marks} == {"project", "skip"}
        assert len(measurement_call.argvalues) == 1
        [param] = measurement_call.argvalues
        assert (
            _param_test_config(param).data_source_config.label
            == "generate-tests-measurement-backend"
        )
