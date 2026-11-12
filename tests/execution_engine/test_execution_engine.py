from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Tuple
from unittest.mock import patch

import pandas as pd
import pytest

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.metric_function_types import (
    MetricPartialFunctionTypeSuffixes,
    SummarizationMetricNameSuffixes,
)
from great_expectations.execution_engine import ExecutionEngine, PandasExecutionEngine
from great_expectations.execution_engine.execution_engine import (
    InvalidConditionError,
    MetricComputationConfiguration,
    _column_comparison_error_context,
)
from great_expectations.expectations.legacy_row_conditions import (
    RowCondition,
    RowConditionParserType,
)
from great_expectations.expectations.row_conditions import (
    AndCondition,
    Column,
    ColumnComparisonCondition,
    ComparisonCondition,
    OrCondition,
    PassThroughCondition,
)

# Testing ordinary process of adding column row condition
from great_expectations.validator.metric_configuration import (
    MetricConfiguration,
    MetricConfigurationID,
)
from tests.expectations.test_util import get_table_columns_metric

if TYPE_CHECKING:
    from great_expectations.core.batch import BatchData, BatchMarkers
    from great_expectations.expectations.row_conditions import NullityCondition
    from great_expectations.validator.computed_metric import MetricValue


@pytest.fixture
def test_execution_engine():
    """
    This fixture is for mocking the abstract ExecutionEngine class to test method functionality.
    Instead of using it's child classes in tests, which could override the parent methods,
    we create a subclass that implements abstract methods (raising exceptions if used)
    and use that fixture in tests.
    """

    class TestExecutionEngine(ExecutionEngine):
        def get_batch_data_and_markers(self, batch_spec) -> Tuple[BatchData, BatchMarkers]:  # type: ignore[explicit-override] # FIXME
            raise NotImplementedError

        @override
        def _comparison_condition_to_filter_clause(self, condition: ComparisonCondition) -> str:
            raise NotImplementedError

        @override
        def _nullity_condition_to_filter_clause(self, condition: NullityCondition) -> str:
            raise NotImplementedError

        @override
        def _and_condition_to_filter_clause(self, condition: AndCondition) -> str:
            raise NotImplementedError

        @override
        def _or_condition_to_filter_clause(self, condition: OrCondition) -> str:
            raise NotImplementedError

    return TestExecutionEngine()


@pytest.mark.unit
def test_add_column_row_condition_filter_null_row_condition_not_present(
    test_execution_engine,
):
    e = test_execution_engine

    # Checking that adding a simple column row condition is functional
    # default of add_column_row_condition is to apply filter_null=True
    domain_kwargs: dict = {}
    new_domain_kwargs = e.add_column_row_condition(domain_kwargs, "a")
    assert new_domain_kwargs == {
        "filter_conditions": [
            RowCondition(condition='col("a").notnull()', condition_type=RowConditionParserType.GE)
        ]
    }

    # Ensuring that this also works when formatted differently
    # default of add_column_row_condition is to apply filter_null=True
    new_domain_kwargs = e.add_column_row_condition({"column": "a"})
    assert new_domain_kwargs == {
        "column": "a",
        "filter_conditions": [
            RowCondition(condition='col("a").notnull()', condition_type=RowConditionParserType.GE)
        ],
    }


@pytest.mark.unit
def test_add_column_row_condition_filter_null_false_row_condition_not_present(
    test_execution_engine,
):
    e = test_execution_engine

    # Identity case
    # default of add_column_row_condition is to apply filter_null=True
    domain_kwargs: dict = {}
    new_domain_kwargs = e.add_column_row_condition(domain_kwargs, "a", filter_null=False)
    assert new_domain_kwargs == domain_kwargs


@pytest.mark.unit
def test_add_column_row_condition_filter_null_false_row_condition_present(
    test_execution_engine,
):
    e = test_execution_engine

    # Identity case
    # default of add_column_row_condition is to apply filter_null=True
    domain_kwargs: dict = {"row_condition": "some_condition"}
    new_domain_kwargs = e.add_column_row_condition(domain_kwargs, "a", filter_null=False)
    assert new_domain_kwargs == domain_kwargs


@pytest.mark.unit
def test_add_column_row_condition_filter_null_row_condition_present(
    test_execution_engine,
):
    e = test_execution_engine

    # Ensuring that we don't override if a row condition is present
    # default of add_column_row_condition is to apply filter_null=True
    domain_kwargs: dict = {"column": "a", "row_condition": "some_row_condition"}
    new_domain_kwargs = e.add_column_row_condition(domain_kwargs, filter_null=True)
    assert new_domain_kwargs == {
        "column": "a",
        "row_condition": "some_row_condition",
        "filter_conditions": [
            RowCondition(condition='col("a").notnull()', condition_type=RowConditionParserType.GE)
        ],
    }

    # Ensuring that we don't override if a row condition is present,
    # default of add_column_row_condition is to apply filter_null=True
    domain_kwargs: dict = {"column": "a", "row_condition": "some_row_condition"}
    new_domain_kwargs = e.add_column_row_condition(domain_kwargs)
    assert new_domain_kwargs == {
        "column": "a",
        "row_condition": "some_row_condition",
        "filter_conditions": [
            RowCondition(condition='col("a").notnull()', condition_type=RowConditionParserType.GE)
        ],
    }


@pytest.mark.unit
def test_add_column_row_condition_filter_null_row_condition_none(test_execution_engine):
    e = test_execution_engine

    # Ensuring that everything still works if a row condition of None given
    # default of add_column_row_condition is to apply filter_null=True
    domain_kwargs: dict = {"column": "a", "row_condition": None}
    new_domain_kwargs = e.add_column_row_condition(domain_kwargs)
    assert new_domain_kwargs == {
        "column": "a",
        "row_condition": None,
        "filter_conditions": [
            RowCondition(condition='col("a").notnull()', condition_type=RowConditionParserType.GE)
        ],
    }


# Edge cases
@pytest.mark.unit
def test_add_column_row_condition_with_unsupported_filter_nan_true(
    test_execution_engine,
):
    e = test_execution_engine

    # Ensuring that an attempt to filter nans within base class yields an error
    with pytest.raises(gx_exceptions.GreatExpectationsError) as error:
        _ = e.add_column_row_condition({}, "a", filter_nan=True)
    assert (
        "Base ExecutionEngine does not support adding nan condition filters" in error.value.message
    )


@pytest.mark.unit
def test_add_column_row_condition_with_unsupported_no_column_provided(
    test_execution_engine,
):
    e = test_execution_engine

    # Testing that error raised when column not given
    with pytest.raises(AssertionError):
        _ = e.add_column_row_condition({})


@pytest.mark.unit
def test_resolve_metrics_with_aggregates_and_column_map():
    # Testing resolve metric function for a variety of cases - test from test_core used
    df = pd.DataFrame({"a": [1, 2, 3, None]})
    engine = PandasExecutionEngine(batch_data_dict={"my_id": df})

    metrics: Dict[MetricConfigurationID, MetricValue] = {}

    table_columns_metric: MetricConfiguration
    results: Dict[MetricConfigurationID, MetricValue]

    table_columns_metric, results = get_table_columns_metric(execution_engine=engine)

    metrics.update(results)

    mean = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    mean.metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    stdev = MetricConfiguration(
        metric_name="column.standard_deviation",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    stdev.metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    desired_metrics = (mean, stdev)
    results = engine.resolve_metrics(metrics_to_resolve=desired_metrics, metrics=metrics)
    metrics.update(results)

    desired_map_metric = MetricConfiguration(
        metric_name=f"column_values.z_score.{MetricPartialFunctionTypeSuffixes.MAP.value}",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_map_metric.metric_dependencies = {
        "column.standard_deviation": stdev,
        "column.mean": mean,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(metrics_to_resolve=(desired_map_metric,), metrics=metrics)
    metrics.update(results)

    desired_threshold_condition_metric = MetricConfiguration(
        metric_name=f"column_values.z_score.under_threshold.{MetricPartialFunctionTypeSuffixes.CONDITION.value}",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    desired_threshold_condition_metric.metric_dependencies = {
        f"column_values.z_score.{MetricPartialFunctionTypeSuffixes.MAP.value}": desired_map_metric,
        "table.columns": table_columns_metric,
    }
    results = engine.resolve_metrics(
        metrics_to_resolve=(desired_threshold_condition_metric,), metrics=metrics
    )
    metrics.update(results)
    assert list(results[desired_threshold_condition_metric.id][0]) == [
        False,
        False,
        False,
    ]

    desired_metric = MetricConfiguration(
        metric_name=f"column_values.z_score.under_threshold.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"double_sided": True, "threshold": 2},
    )
    desired_metric.metric_dependencies = {
        "unexpected_condition": desired_threshold_condition_metric,
    }
    results = engine.resolve_metrics(metrics_to_resolve=(desired_metric,), metrics=metrics)
    metrics.update(results)
    assert results[desired_metric.id] == 0


@pytest.mark.unit
def test_resolve_metrics_with_extraneous_value_key():
    df = pd.DataFrame({"a": [1, 2, 3, None]})
    engine = PandasExecutionEngine(batch_data_dict={"my_id": df})

    metrics: Dict[MetricConfigurationID, MetricValue] = {}

    table_columns_metric: MetricConfiguration
    results: Dict[MetricConfigurationID, MetricValue]

    table_columns_metric, results = get_table_columns_metric(execution_engine=engine)

    metrics.update(results)

    mean = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    mean.metric_dependencies = {
        "table.columns": table_columns_metric,
    }
    # Ensuring that an unused value key will not mess up computation
    stdev = MetricConfiguration(
        metric_name="column.standard_deviation",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={"value_set": [1, 2, 3, 4, 5]},
    )
    stdev.metric_dependencies = {
        "table.columns": table_columns_metric,
    }

    desired_metrics = (mean, stdev)
    results = engine.resolve_metrics(metrics_to_resolve=desired_metrics, metrics=metrics)
    metrics.update(results)

    # Ensuring extraneous value key did not change computation
    assert (
        metrics[
            MetricConfigurationID(
                "column.standard_deviation", "column=a", "value_set=[1, 2, 3, 4, 5]"
            )
        ]
        == 1.0
    )


# Testing that metric resolution also works with metric partial function
@pytest.mark.unit
def test_resolve_metrics_with_incomplete_metric_input():
    engine = PandasExecutionEngine()

    mean = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    stdev = MetricConfiguration(
        metric_name="column.standard_deviation",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )

    desired_metric = MetricConfiguration(
        metric_name=f"column_values.z_score.{MetricPartialFunctionTypeSuffixes.MAP.value}",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    desired_metric.metric_dependencies = {
        "column.standard_deviation": stdev,
        "column.mean": mean,
    }

    # Ensuring that incomplete metrics given raises a GreatExpectationsError
    with pytest.raises(gx_exceptions.GreatExpectationsError):
        engine.resolve_metrics(metrics_to_resolve=(desired_metric,), metrics={})


@pytest.mark.unit
def test_bundle_failure_falls_back_to_individual_metric_computation(
    test_execution_engine,
):
    """When a bulk metric query fails, each metric should be computed individually.

    Metrics that succeed individually should be returned; only metrics that also
    fail individually should appear in the MetricResolutionError.failed_metrics.
    This ensures one bad metric cannot poison unrelated metrics in the same bundle.
    """
    engine = test_execution_engine

    metric_a = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs=None,
    )
    metric_b = MetricConfiguration(
        metric_name="column.mean",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs=None,
    )

    config_a = MetricComputationConfiguration(
        metric_configuration=metric_a,
        metric_fn=lambda: None,  # unused — resolve_metric_bundle is mocked
        metric_provider_kwargs={},
    )
    config_b = MetricComputationConfiguration(
        metric_configuration=metric_b,
        metric_fn=lambda: None,  # unused — resolve_metric_bundle is mocked
        metric_provider_kwargs={},
    )

    individual_error = Exception("column b is not numeric")

    call_count = 0

    def mock_resolve_bundle(metric_fn_bundle):
        nonlocal call_count
        call_count += 1
        configs = list(metric_fn_bundle)
        if call_count == 1:
            # First call is the bulk query — fail to trigger fallback
            raise RuntimeError("bulk query failed")
        # Individual fallback calls: succeed for metric_a, fail for metric_b
        assert len(configs) == 1
        if configs[0].metric_configuration == metric_a:
            return {metric_a.id: 2.0}
        raise individual_error

    with patch.object(engine, "resolve_metric_bundle", side_effect=mock_resolve_bundle):
        with pytest.raises(gx_exceptions.MetricResolutionError) as exc_info:
            engine._process_direct_and_bundled_metric_computation_configurations(
                metric_fn_direct_configurations=[],
                metric_fn_bundle_configurations=[config_a, config_b],
            )

    err = exc_info.value
    # Only metric_b should be reported as failed
    assert list(err.failed_metrics) == [metric_b]
    # resolve_metric_bundle was called once for the bulk attempt and once per metric
    assert call_count == 3


@pytest.mark.unit
def test_condition_to_filter_clause_routes_column_comparison_to_dedicated_method(
    test_execution_engine,
):
    """A column comparison reaches its own rendering method, not the literal comparison one."""
    sentinel = "rendered column comparison"
    seen: list[ColumnComparisonCondition] = []

    class ColumnComparisonEngine(type(test_execution_engine)):
        @override
        def _column_comparison_condition_to_filter_clause(
            self, condition: ColumnComparisonCondition
        ) -> str:
            seen.append(condition)
            return sentinel

        @override
        def _comparison_condition_to_filter_clause(self, condition: ComparisonCondition) -> str:
            raise AssertionError("a column comparison must not be rendered as a literal comparison")

    engine = ColumnComparisonEngine()
    condition = Column("a") < Column("b")
    assert isinstance(condition, ColumnComparisonCondition)

    assert engine.condition_to_filter_clause(condition) == sentinel
    assert seen == [condition]


@pytest.mark.unit
def test_condition_to_filter_clause_routes_literal_comparison_unchanged(test_execution_engine):
    """A literal comparison still reaches the literal rendering method, and only that one."""
    sentinel = "rendered literal comparison"

    class LiteralComparisonEngine(type(test_execution_engine)):
        @override
        def _comparison_condition_to_filter_clause(self, condition: ComparisonCondition) -> str:
            return sentinel

        @override
        def _column_comparison_condition_to_filter_clause(
            self, condition: ColumnComparisonCondition
        ) -> str:
            raise AssertionError("a literal comparison must not be rendered as a column comparison")

    engine = LiteralComparisonEngine()
    condition = Column("a") < 1
    assert isinstance(condition, ComparisonCondition)

    assert engine.condition_to_filter_clause(condition) == sentinel


@pytest.mark.unit
def test_column_comparison_default_rendering_raises_invalid_condition_error(
    test_execution_engine,
):
    """An engine that does not render column comparisons rejects them rather than guessing."""
    condition = Column("a") != Column("b")

    with pytest.raises(InvalidConditionError) as exc_info:
        test_execution_engine.condition_to_filter_clause(condition)

    assert str(type(condition)) in str(exc_info.value)
    with pytest.raises(InvalidConditionError):
        test_execution_engine._column_comparison_condition_to_filter_clause(condition)


@pytest.mark.unit
def test_column_comparison_default_rendering_does_not_change_other_condition_handling(
    test_execution_engine,
):
    """The safe default is specific to column comparisons; other unsupported types still raise."""
    condition = PassThroughCondition(pass_through_filter="a < b")

    with pytest.raises(InvalidConditionError):
        test_execution_engine.condition_to_filter_clause(condition)


@pytest.mark.unit
def test_engine_without_column_comparison_support_still_instantiates():
    """The column comparison hook is a concrete default, so existing subclasses are unaffected."""
    assert "_column_comparison_condition_to_filter_clause" not in (
        ExecutionEngine.__abstractmethods__
    )

    class LegacyEngine(ExecutionEngine):
        # Implements only the pre-existing abstract methods.
        def get_batch_data_and_markers(self, batch_spec) -> Tuple[BatchData, BatchMarkers]:  # type: ignore[explicit-override] # FIXME
            raise NotImplementedError

        @override
        def _comparison_condition_to_filter_clause(self, condition: ComparisonCondition) -> str:
            raise NotImplementedError

        @override
        def _nullity_condition_to_filter_clause(self, condition: NullityCondition) -> str:
            raise NotImplementedError

        @override
        def _and_condition_to_filter_clause(self, condition: AndCondition) -> str:
            raise NotImplementedError

        @override
        def _or_condition_to_filter_clause(self, condition: OrCondition) -> str:
            raise NotImplementedError

    LegacyEngine()


_COLUMN_COMPARISON_FAILURE_NOTE = (
    "If the error concerns one of these columns, check that both columns exist and that the "
    "backend can compare their values."
)


def _failed_metric(**domain_kwargs) -> MetricConfiguration:
    return MetricConfiguration(
        metric_name="table.row_count",
        metric_domain_kwargs=domain_kwargs,
        metric_value_kwargs=None,
    )


def _context_sentence(comparisons: str) -> str:
    return f" Row condition column comparisons: {comparisons}. {_COLUMN_COMPARISON_FAILURE_NOTE}"


@pytest.mark.unit
@pytest.mark.parametrize("as_dict", [False, True], ids=["condition_object", "serialized_dict"])
def test_column_comparison_error_context_names_a_standalone_comparison(as_dict: bool):
    """The sentence names both columns, whether the domain holds the object or its dict form."""
    condition = Column("end_date") > Column("start_date")
    row_condition = condition.dict() if as_dict else condition

    context = _column_comparison_error_context([_failed_metric(row_condition=row_condition)])

    assert context == _context_sentence("end_date > start_date")


@pytest.mark.unit
@pytest.mark.parametrize("as_dict", [False, True], ids=["condition_object", "serialized_dict"])
@pytest.mark.parametrize(
    "build_condition",
    [
        pytest.param(
            lambda comparison: AndCondition(conditions=[Column("x") > 1, comparison]),
            id="and",
        ),
        pytest.param(
            lambda comparison: OrCondition(conditions=[comparison, Column("x").is_null()]),
            id="or",
        ),
        pytest.param(
            lambda comparison: AndCondition(
                conditions=[
                    Column("x") > 1,
                    OrCondition(conditions=[Column("y").is_null(), comparison]),
                ]
            ),
            id="or_inside_and",
        ),
    ],
)
def test_column_comparison_error_context_finds_a_comparison_nested_in_a_group(
    build_condition, as_dict: bool
):
    """Only the column comparison is named; literal siblings in the group are not."""
    condition = build_condition(Column("end_date") > Column("start_date"))
    row_condition = condition.dict() if as_dict else condition

    context = _column_comparison_error_context([_failed_metric(row_condition=row_condition)])

    assert context == _context_sentence("end_date > start_date")


@pytest.mark.unit
def test_column_comparison_error_context_lists_distinct_comparisons_in_written_order():
    """Several comparisons in one tree are listed in the order they were written."""
    condition = AndCondition(
        conditions=[
            Column("c") < Column("d"),
            OrCondition(conditions=[Column("a") != Column("b"), Column("x") > 1]),
            Column("e") >= Column("f"),
        ]
    )

    context = _column_comparison_error_context([_failed_metric(row_condition=condition)])

    assert context == _context_sentence("c < d, a != b, e >= f")


@pytest.mark.unit
def test_column_comparison_error_context_deduplicates_within_a_tree_keeping_first_seen_order():
    condition = AndCondition(
        conditions=[
            Column("a") < Column("b"),
            Column("c") < Column("d"),
            Column("a") < Column("b"),
            OrCondition(conditions=[Column("c") < Column("d"), Column("e") < Column("f")]),
        ]
    )

    context = _column_comparison_error_context([_failed_metric(row_condition=condition)])

    assert context == _context_sentence("a < b, c < d, e < f")


@pytest.mark.unit
def test_column_comparison_error_context_deduplicates_across_metrics_keeping_first_seen_order():
    first = _failed_metric(row_condition=(Column("a") < Column("b")).dict())
    second = _failed_metric(
        row_condition=AndCondition(
            conditions=[Column("c") < Column("d"), Column("a") < Column("b")]
        )
    )
    third = _failed_metric(row_condition=Column("e") < Column("f"))
    fourth = _failed_metric(row_condition=(Column("c") < Column("d")).dict())

    context = _column_comparison_error_context([first, second, third, fourth])

    assert context == _context_sentence("a < b, c < d, e < f")


@pytest.mark.unit
def test_column_comparison_error_context_keeps_comparisons_that_differ_in_operator_or_order():
    """De-duplication is by display form: `a < b`, `a > b` and `b > a` are three comparisons."""
    condition = AndCondition(
        conditions=[
            Column("a") < Column("b"),
            Column("a") > Column("b"),
            Column("b") > Column("a"),
        ]
    )

    context = _column_comparison_error_context([_failed_metric(row_condition=condition)])

    assert context == _context_sentence("a < b, a > b, b > a")


@pytest.mark.unit
def test_column_comparison_error_context_accepts_any_iterable_of_failed_metrics():
    metric = _failed_metric(row_condition=Column("a") < Column("b"))

    context = _column_comparison_error_context(m for m in (metric,))

    assert context == _context_sentence("a < b")


@pytest.mark.unit
@pytest.mark.parametrize(
    "domain_kwargs",
    [
        pytest.param({"row_condition": Column("x") > 1}, id="literal_comparison"),
        pytest.param({"row_condition": (Column("x") > 1).dict()}, id="literal_comparison_dict"),
        pytest.param({"row_condition": Column("x").is_null()}, id="nullity"),
        pytest.param(
            {
                "row_condition": AndCondition(
                    conditions=[
                        Column("x") > 1,
                        OrCondition(conditions=[Column("y").is_null(), Column("z") <= 3]),
                    ]
                ).dict()
            },
            id="literal_only_group_dict",
        ),
        pytest.param(
            {"row_condition": PassThroughCondition(pass_through_filter="a < b")},
            id="pass_through",
        ),
        pytest.param(
            {"row_condition": 'col("a") < col("b")', "condition_parser": "great_expectations"},
            id="legacy_string_that_reads_like_a_comparison",
        ),
        pytest.param({"row_condition": "a < b", "condition_parser": "pandas"}, id="pandas_string"),
        pytest.param({"row_condition": None}, id="row_condition_none"),
        pytest.param({"column": "a"}, id="row_condition_absent"),
        pytest.param({}, id="empty_domain_kwargs"),
    ],
)
def test_column_comparison_error_context_is_empty_without_a_column_comparison(domain_kwargs):
    """No column comparison means no context, so the original message is left untouched."""
    assert _column_comparison_error_context([_failed_metric(**domain_kwargs)]) == ""


@pytest.mark.unit
def test_column_comparison_error_context_is_empty_for_no_failed_metrics():
    assert _column_comparison_error_context([]) == ""


@pytest.mark.unit
@pytest.mark.parametrize(
    "row_condition",
    [
        pytest.param({"type": "no_such_condition"}, id="unknown_type"),
        pytest.param({"column": "a"}, id="no_type"),
        pytest.param({"type": "column_comparison"}, id="column_comparison_missing_fields"),
        pytest.param(
            {
                "type": "column_comparison",
                "column": {"name": "a"},
                "operator": "IN",
                "other_column": {"name": "b"},
            },
            id="column_comparison_unsupported_operator",
        ),
        pytest.param(
            {"type": "and", "conditions": [{"type": "column_comparison", "column": {"name": "a"}}]},
            id="group_with_malformed_child",
        ),
        pytest.param(12345, id="not_a_condition_or_string"),
        pytest.param(["a < b"], id="list"),
    ],
)
def test_column_comparison_error_context_is_empty_for_a_malformed_row_condition(row_condition):
    """A row condition that cannot be deserialized yields no context and does not raise."""
    assert _column_comparison_error_context([_failed_metric(row_condition=row_condition)]) == ""


@pytest.mark.unit
def test_column_comparison_error_context_ignores_a_malformed_metric_but_keeps_the_others():
    malformed = _failed_metric(row_condition={"type": "column_comparison", "column": {"name": "a"}})
    valid = _failed_metric(row_condition=(Column("a") < Column("b")).dict())

    context = _column_comparison_error_context([malformed, valid, malformed])

    assert context == _context_sentence("a < b")


@pytest.mark.unit
@pytest.mark.parametrize(
    "failed_metrics",
    [
        pytest.param(None, id="none"),
        pytest.param(42, id="not_iterable"),
        pytest.param([object()], id="not_a_metric"),
        pytest.param([None], id="none_metric"),
    ],
)
def test_column_comparison_error_context_never_raises(failed_metrics):
    """The context is appended while another error is being raised and must not replace it."""
    assert _column_comparison_error_context(failed_metrics) == ""


def _failing_direct_configuration(
    metric: MetricConfiguration, error: Exception
) -> MetricComputationConfiguration:
    def metric_fn(**kwargs):
        raise error

    return MetricComputationConfiguration(
        metric_configuration=metric,
        metric_fn=metric_fn,
        metric_provider_kwargs={},
    )


def _bundled_configuration(metric: MetricConfiguration) -> MetricComputationConfiguration:
    return MetricComputationConfiguration(
        metric_configuration=metric,
        metric_fn=lambda: None,  # unused: resolve_metric_bundle is patched
        metric_provider_kwargs={},
    )


def _resolve_bundled_metrics_failing_individually(
    engine: ExecutionEngine,
    outcomes: list[tuple[MetricConfiguration, Exception | None]],
) -> gx_exceptions.MetricResolutionError:
    """Run the bundled path with a bulk failure, then one retry per metric, in the order given.

    An outcome of None means that metric's individual retry succeeds; an exception means it fails
    with that exception. Returns the MetricResolutionError the engine raises.
    """
    configurations = [_bundled_configuration(metric) for metric, _ in outcomes]
    bulk_attempted = False

    def resolve_bundle(metric_fn_bundle):
        nonlocal bulk_attempted
        configs = list(metric_fn_bundle)
        if not bulk_attempted:
            bulk_attempted = True
            raise RuntimeError("bulk query failed")
        assert len(configs) == 1
        (metric_configuration,) = (c.metric_configuration for c in configs)
        for metric, error in outcomes:
            if metric is metric_configuration:
                if error is not None:
                    raise error
                return {metric.id: 1.0}
        raise AssertionError("unexpected metric in the individual retry")  # pragma: no cover

    with patch.object(engine, "resolve_metric_bundle", side_effect=resolve_bundle):
        with pytest.raises(gx_exceptions.MetricResolutionError) as exc_info:
            engine._process_direct_and_bundled_metric_computation_configurations(
                metric_fn_direct_configurations=[],
                metric_fn_bundle_configurations=configurations,
            )
    return exc_info.value


_ROW_CONDITIONS_WITHOUT_A_COLUMN_COMPARISON = [
    pytest.param(None, id="absent"),
    pytest.param(Column("a") > 1, id="literal_comparison"),
    pytest.param((Column("a") > 1).dict(), id="literal_comparison_dict"),
    pytest.param(Column("a").is_not_null(), id="nullity"),
    pytest.param(PassThroughCondition(pass_through_filter="a > 1"), id="pass_through"),
    pytest.param(AndCondition(conditions=[Column("a") > 1, Column("b") < 2]), id="literal_group"),
]


def _domain_kwargs_with(row_condition) -> dict:
    return {"row_condition": row_condition} if row_condition is not None else {}


@pytest.mark.unit
@pytest.mark.parametrize("as_dict", [False, True], ids=["condition_object", "serialized_dict"])
def test_direct_metric_failure_appends_the_column_comparison_context(
    test_execution_engine, as_dict: bool
):
    """A direct metric that raises keeps the backend's message first, then names the comparison."""
    condition = Column("end_date") > Column("start_date")
    metric = _failed_metric(row_condition=condition.dict() if as_dict else condition)
    backend_error = RuntimeError("cannot compare timestamp with text")

    with pytest.raises(gx_exceptions.MetricResolutionError) as exc_info:
        test_execution_engine._process_direct_and_bundled_metric_computation_configurations(
            metric_fn_direct_configurations=[_failing_direct_configuration(metric, backend_error)],
            metric_fn_bundle_configurations=[],
        )

    err = exc_info.value
    assert str(err) == "cannot compare timestamp with text" + _context_sentence(
        "end_date > start_date"
    )
    assert err.message == str(err)
    assert err.__cause__ is backend_error
    assert list(err.failed_metrics) == [metric]


@pytest.mark.unit
def test_direct_metric_failure_context_names_a_comparison_nested_in_a_group(
    test_execution_engine,
):
    condition = AndCondition(conditions=[Column("a") > 1, Column("b") <= Column("c")])
    metric = _failed_metric(row_condition=condition)

    with pytest.raises(gx_exceptions.MetricResolutionError) as exc_info:
        test_execution_engine._process_direct_and_bundled_metric_computation_configurations(
            metric_fn_direct_configurations=[
                _failing_direct_configuration(metric, RuntimeError("no such column: c"))
            ],
            metric_fn_bundle_configurations=[],
        )

    assert str(exc_info.value) == "no such column: c" + _context_sentence("b <= c")


@pytest.mark.unit
@pytest.mark.parametrize("row_condition", _ROW_CONDITIONS_WITHOUT_A_COLUMN_COMPARISON)
def test_direct_metric_failure_message_is_unchanged_without_a_column_comparison(
    test_execution_engine, row_condition
):
    """With no column comparison involved the message is exactly the original exception's."""
    metric = _failed_metric(**_domain_kwargs_with(row_condition))
    backend_error = RuntimeError("column a does not exist")

    with pytest.raises(gx_exceptions.MetricResolutionError) as exc_info:
        test_execution_engine._process_direct_and_bundled_metric_computation_configurations(
            metric_fn_direct_configurations=[_failing_direct_configuration(metric, backend_error)],
            metric_fn_bundle_configurations=[],
        )

    err = exc_info.value
    assert str(err) == str(backend_error)
    assert err.message == str(backend_error)
    assert list(err.failed_metrics) == [metric]


@pytest.mark.unit
@pytest.mark.parametrize("as_dict", [False, True], ids=["condition_object", "serialized_dict"])
def test_bundled_metric_failure_appends_the_column_comparison_context(
    test_execution_engine, as_dict: bool
):
    """A bundled metric that also fails on its own gets the backend's message, then the context."""
    condition = Column("end_date") > Column("start_date")
    failing = _failed_metric(row_condition=condition.dict() if as_dict else condition)
    unrelated = _failed_metric(column="other")
    backend_error = RuntimeError("cannot compare timestamp with text")

    err = _resolve_bundled_metrics_failing_individually(
        test_execution_engine, [(unrelated, None), (failing, backend_error)]
    )

    assert str(err) == "cannot compare timestamp with text" + _context_sentence(
        "end_date > start_date"
    )
    assert err.message == str(err)
    assert err.__cause__ is backend_error
    assert list(err.failed_metrics) == [failing]


@pytest.mark.unit
@pytest.mark.parametrize("row_condition", _ROW_CONDITIONS_WITHOUT_A_COLUMN_COMPARISON)
def test_bundled_metric_failure_message_is_unchanged_without_a_column_comparison(
    test_execution_engine, row_condition
):
    """With no column comparison involved the message is exactly the original exception's."""
    failing = _failed_metric(**_domain_kwargs_with(row_condition))
    backend_error = RuntimeError("column a does not exist")

    err = _resolve_bundled_metrics_failing_individually(
        test_execution_engine, [(failing, backend_error)]
    )

    assert str(err) == str(backend_error)
    assert err.message == str(backend_error)
    assert list(err.failed_metrics) == [failing]


@pytest.mark.unit
def test_bundled_metric_failure_context_is_not_taken_from_a_different_failed_metric(
    test_execution_engine,
):
    """The context follows the metric whose exception is shown, not every failed metric.

    Two bundled metrics fail on their own. The one with a column comparison fails first; the
    last exception, which gives the message, comes from a metric with no column comparison. The
    comparison belongs to a different failure than the message, so no context is appended.
    """
    with_comparison = _failed_metric(row_condition=Column("end_date") > Column("start_date"))
    without_comparison = _failed_metric(row_condition=Column("a") > 1)
    first_error = RuntimeError("cannot compare timestamp with text")
    last_error = RuntimeError("column a does not exist")

    err = _resolve_bundled_metrics_failing_individually(
        test_execution_engine,
        [(with_comparison, first_error), (without_comparison, last_error)],
    )

    assert str(err) == "column a does not exist"
    assert err.__cause__ is last_error
    # Every metric that failed is still reported.
    assert list(err.failed_metrics) == [with_comparison, without_comparison]


@pytest.mark.unit
def test_bundled_metric_failure_context_follows_the_metric_whose_exception_is_shown(
    test_execution_engine,
):
    """When the shown exception comes from the metric with the comparison, the context names it."""
    without_comparison = _failed_metric(row_condition=Column("a") > 1)
    with_comparison = _failed_metric(row_condition=Column("end_date") > Column("start_date"))
    first_error = RuntimeError("column a does not exist")
    last_error = RuntimeError("cannot compare timestamp with text")

    err = _resolve_bundled_metrics_failing_individually(
        test_execution_engine,
        [(without_comparison, first_error), (with_comparison, last_error)],
    )

    assert str(err) == "cannot compare timestamp with text" + _context_sentence(
        "end_date > start_date"
    )
    assert list(err.failed_metrics) == [without_comparison, with_comparison]


@pytest.mark.unit
def test_bundled_metric_failure_context_names_only_the_shown_metrics_comparisons(
    test_execution_engine,
):
    """Two failed metrics each have a comparison: only the shown exception's metric is named."""
    first = _failed_metric(row_condition=Column("end_date") > Column("start_date"))
    last = _failed_metric(row_condition=Column("high") >= Column("low"))

    err = _resolve_bundled_metrics_failing_individually(
        test_execution_engine,
        [(first, RuntimeError("first failure")), (last, RuntimeError("last failure"))],
    )

    assert str(err) == "last failure" + _context_sentence("high >= low")
    assert "end_date" not in str(err)
    assert list(err.failed_metrics) == [first, last]
