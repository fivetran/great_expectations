"""Extension-point behavior tests for the shared SQL batch-setup layer.

Every declaration below is a throwaway, never decorated with `register_sql_config`, so none of it
joins the registry that the derived data-source lists and completeness checks walk. The schema
items these declarations contribute are plain SQLAlchemy constructs with no dialect package
involved, so the whole module runs against a file-backed SQLite database and needs no server.
"""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar, List, Mapping, Optional, Sequence, Type, Union, cast

import pandas as pd
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import registry as sa_dialect_registry
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite

import great_expectations as gx
from great_expectations.compatibility.typing_extensions import override
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import iter_data_source_specs
from tests.integration.test_utils.data_source_config import sql as sql_module
from tests.integration.test_utils.data_source_config.backend_spec import (
    SqlBackendSpec,
    TransactionMode,
)
from tests.integration.test_utils.data_source_config.data_source_spec import (
    CiLaneRef,
    DataSourceProvisioning,
)
from tests.integration.test_utils.data_source_config.generic_sql import (
    GenericSQLBatchTestSetup,
    GenericSQLDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup
from tests.integration.test_utils.data_source_config.sql_config import SqlDatasourceTestConfig

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    from great_expectations.compatibility.sqlalchemy import TypeEngine
    from great_expectations.data_context import AbstractDataContext
    from great_expectations.datasource.fluent.sql_datasource import TableAsset
    from tests.integration.conftest import TestConfig
    from tests.integration.sql_session_manager import SessionSQLEngineManager
    from tests.integration.test_utils.data_source_config.base import BatchTestSetup

pytestmark = pytest.mark.sqlite


_BASE_SPEC = SqlBackendSpec(
    label="throwaway-table-schema-items",
    public_name="SQLite",
    marker="sqlite",
    provisioning=DataSourceProvisioning.LOCAL_FILE,
    ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="sqlite"),
    uses_schema=False,
)
"""A minimal, well-formed declaration reused as the base for every throwaway declaration below.
Never registered, so its label never has to be globally unique the way a real backend's does -
only unique enough to keep this module's own throwaway configs distinguishable from each other."""


class _ThrowawayDatasourceTestConfig(SqlDatasourceTestConfig):
    """A file-backed declaration used only to drive the tests in this module."""

    DATA_SOURCE_SPEC: ClassVar[SqlBackendSpec] = _BASE_SPEC

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)
        return _ThrowawayBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


class _ThrowawayBatchTestSetup(SQLBatchTestSetup[_ThrowawayDatasourceTestConfig]):
    """Mirrors `SqliteBatchTestSetup` exactly - a file-backed setup - so these tests exercise the
    real table-construction path rather than a stand-in for it.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        config: _ThrowawayDatasourceTestConfig,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        base_dir: pathlib.Path,
        table_name: Optional[str] = None,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> None:
        self._base_dir = base_dir
        super().__init__(
            config=config,
            data=data,
            extra_data=extra_data,
            table_name=table_name,
            engine_manager=engine_manager,
            context=context,
        )

    @override
    def build_connection_string(self, schema: str | None = None) -> str:
        return f"sqlite:///{self.db_file_path}"

    @property
    def db_file_path(self) -> pathlib.Path:
        return self._base_dir / "database.db"

    @override
    def make_asset(self) -> TableAsset:
        return self.context.data_sources.add_sqlite(
            name=self._random_resource_name(),
            connection_string=self.build_connection_string(),
        ).add_table_asset(name=self._random_resource_name(), table_name=self.table_name)


_DATA = pd.DataFrame({"col_a": [1, 2, 3]})
_EXTRA_DATA = {"extra_table": pd.DataFrame({"col_b": [4, 5, 6]})}


def _extra_table(batch_setup: _ThrowawayBatchTestSetup) -> sa.Table:
    [table_data] = batch_setup.extra_table_data.values()
    return table_data.table


class TestTableSchemaItemFactoryAttachesToEveryTable:
    def test_identifiable_item_appears_on_both_the_primary_and_extra_table(
        self, tmp_path: pathlib.Path
    ) -> None:
        constraint_name = "chk_throwaway_marker"

        def factory() -> Sequence[sa.CheckConstraint]:
            return (sa.CheckConstraint("1=1", name=constraint_name),)

        config = _ThrowawayDatasourceTestConfig(
            backend_spec_override=dataclasses.replace(_BASE_SPEC, table_schema_items=factory)
        )
        batch_setup = _ThrowawayBatchTestSetup(
            data=_DATA,
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            main_names = {c.name for c in batch_setup.main_table_data.table.constraints}
            extra_names = {c.name for c in _extra_table(batch_setup).constraints}

            assert constraint_name in main_names
            assert constraint_name in extra_names
        finally:
            batch_setup.teardown()

    def test_no_factory_contributes_nothing_and_table_creation_still_succeeds(
        self, tmp_path: pathlib.Path
    ) -> None:
        # `table_schema_items` defaults to `None` on `_BASE_SPEC`, so this exercises the
        # behavior-preserving default the hook must fall back to.
        config = _ThrowawayDatasourceTestConfig()
        batch_setup = _ThrowawayBatchTestSetup(
            data=_DATA,
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            # Only the implicit primary-key constraint is present; nothing extra was contributed.
            assert {c.name for c in batch_setup.main_table_data.table.constraints} == {None}
        finally:
            batch_setup.teardown()


class TestTableSchemaItemFactoryIsCalledOncePerTableWithFreshItems:
    def test_factory_call_count_matches_table_count_and_items_are_not_shared(
        self, tmp_path: pathlib.Path
    ) -> None:
        constructed_items: List[sa.CheckConstraint] = []

        def factory() -> Sequence[sa.CheckConstraint]:
            item = sa.CheckConstraint("1=1", name=f"chk_throwaway_{len(constructed_items)}")
            constructed_items.append(item)
            return (item,)

        config = _ThrowawayDatasourceTestConfig(
            backend_spec_override=dataclasses.replace(_BASE_SPEC, table_schema_items=factory)
        )
        batch_setup = _ThrowawayBatchTestSetup(
            data=_DATA,
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            # One primary table plus one extra table: the factory must run exactly twice, not
            # once for the whole setup and not once per call site that happens to touch a table.
            assert len(constructed_items) == 2

            main_item = next(
                c
                for c in batch_setup.main_table_data.table.constraints
                if isinstance(c, sa.CheckConstraint)
            )
            extra_item = next(
                c
                for c in _extra_table(batch_setup).constraints
                if isinstance(c, sa.CheckConstraint)
            )

            # Each table received the exact object the factory built for it, in call order...
            assert main_item is constructed_items[0]
            assert extra_item is constructed_items[1]
            # ...and, the crux of this test: the two tables do not share one instance. A design
            # that built the items once and reused them across tables would still make both
            # tables "carry an item" (the previous test would pass) but would fail here, because
            # a dialect construct binds to the first table it is attached to and reusing it
            # corrupts every subsequent table.
            assert main_item is not extra_item
        finally:
            batch_setup.teardown()


class TestSchemaNameConflictsWithNoSchemaDeclarationRaises:
    def test_explicit_schema_name_against_a_no_schema_declaration_raises(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _ThrowawayDatasourceTestConfig(schema_name="some_schema")
        batch_setup = _ThrowawayBatchTestSetup(
            data=_DATA,
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        with pytest.raises(ValueError) as excinfo:
            _ = batch_setup.schema

        assert (
            str(excinfo.value)
            == "Schema name provided but use_schema is False for this datasource type."
        )


def _rendered(sql_type: Union[Type[TypeEngine], TypeEngine], dialect: sa.engine.Dialect) -> str:
    """The DDL fragment one dialect emits for one declared type."""
    instance = sql_type() if isinstance(sql_type, type) else sql_type
    return str(instance.compile(dialect=dialect))


def _sql_backend_specs() -> List[SqlBackendSpec]:
    """Every registered SQL backend's declaration, in label order.

    Read from the registry rather than named here, so a backend added later is one this module
    accounts for without an edit to this module -- and is not silently skipped by it.
    """
    return [spec for spec in iter_data_source_specs() if isinstance(spec, SqlBackendSpec)]


def _backend_params() -> List[ParameterSet]:
    """One parameter per registered SQL backend, carrying that backend's own pytest marker.

    The marker is what puts a backend's case in the lane that installs its dialect. This module
    carries a module-level `sqlite` marker, which covers the dialects SQLAlchemy ships with, but
    seven of these backends have a third-party dialect that only its own lane installs -- and no
    lane selects a module by a marker it does not carry. Without the per-backend marker those
    seven would be skipped in every lane, leaving their recorded rows checked nowhere.
    """
    return [
        pytest.param(
            spec,
            # No marker declared means no lane of its own selects this backend, so its case runs
            # only where this module's own marker does.
            marks=[getattr(pytest.mark, spec.marker)] if spec.marker else [],
            id=spec.label,
        )
        for spec in _sql_backend_specs()
    ]


class TestSharedDefaultTypesSayWhatTheyMean:
    """A default type that leaves its width unstated lets each server pick one.

    That failure does not announce itself: the DDL is valid everywhere, so nothing errors --
    the server simply stores something other than what the fixture declared, and an assertion
    about a value ends up asserting about a different value.
    """

    def test_a_running_setup_resolves_what_the_declaration_resolves(
        self, tmp_path: pathlib.Path
    ) -> None:
        """This module reads the type map from the declaration rather than from a live setup,
        which says something about the tables the harness builds only while a setup reads the
        same map. A setup that resolved its columns some other way would leave every check below
        true of a map nothing uses.
        """
        setup = _ThrowawayBatchTestSetup(
            data=pd.DataFrame({"col_int": [1]}),
            config=_ThrowawayDatasourceTestConfig(),
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        assert setup.inferrable_types_lookup == sql_module.inferrable_types_for(_BASE_SPEC)

    def test_the_float_default_states_its_own_width(self) -> None:
        """A float type that names no width is the shape that silently loses data.

        Two spellings do it. An unqualified decimal is read by several dialects as scale zero, so
        every fractional value in a fixture frame is rounded to an integer on write. A float with
        no precision is read by at least one dialect as its 4-byte type, so a Python float -- a
        double -- is stored at half the width it was declared at. Both produce valid DDL and no
        error. A type that names its own width (a double, a float carrying a precision, or a
        decimal carrying an explicit scale) leaves the server nothing to decide.
        """
        default_float = sql_module.inferrable_types_for(_BASE_SPEC)[float]
        instance = default_float() if isinstance(default_float, type) else default_float

        assert isinstance(instance, sa.Numeric), (
            f"the shared default for `float` is {instance!r}, which is not a numeric type at all"
        )
        states_its_own_width = (
            # `Double` names 8 bytes in the type name itself, so it needs no precision.
            isinstance(instance, sa.Double)
            or (isinstance(instance, sa.Float) and instance.precision is not None)
            or (not isinstance(instance, sa.Float) and instance.scale is not None)
        )

        assert states_its_own_width, (
            f"the shared default for `float` is {instance!r}, which names no width: the server "
            "picks one, and a fixture value that does not fit the one it picks is rounded or "
            "narrowed on write, with valid DDL and no error"
        )


class TestEveryBackendResolvesTheColumnTypesRecordedHere:
    """What each registered backend's fixture columns actually become, written down.

    A shared default is a per-dialect decision even though it is written once, and a backend's own
    override is the other half of that decision. What a table ends up holding is the two together,
    so that is what this records: one row per registered SQL backend, resolved from its
    declaration and compiled against its dialect.

    Recording the shared defaults alone would leave the half a reader most needs to see. An
    override can change, or be dropped, and move nothing in this file -- which is how a backend
    whose datetime column had been pinned to a sub-second type could come to be created as a
    second-resolution one with no line here disagreeing.

    This does not know which renderings are right; no local check can, since a type name means
    whatever the server says it means, and only a run against one settles that. What it does is
    make the renderings visible: editing a shared default or a backend override changes this table
    in the same diff, so the per-backend consequences are read at review time rather than
    discovered a continuous-integration run later. A dialect absent from the environment is
    skipped, since each lane installs only its own.

    `float` and `datetime` only, because those two are where a dialect's reading of a type name
    has actually diverged from what the harness meant. `pd.Timestamp` carries no row of its own:
    it is asserted to render as `datetime` does, since a backend overriding one and not the other
    is a defect rather than a fact worth recording.
    """

    _RESOLVED: ClassVar[Mapping[str, Mapping[str, str]]] = {
        "big-query": {"dialect": "bigquery", "float": "FLOAT64", "datetime": "DATETIME"},
        "clickhouse": {
            "dialect": "clickhouse",
            "float": "Nullable(Float64)",
            "datetime": "Nullable(DateTime64(3))",
        },
        "databricks": {"dialect": "databricks", "float": "DOUBLE", "datetime": "TIMESTAMP_NTZ"},
        "mssql": {"dialect": "mssql", "float": "FLOAT(53)", "datetime": "DATETIME"},
        "mysql": {"dialect": "mysql", "float": "FLOAT(53)", "datetime": "DATETIME"},
        "oracle": {"dialect": "oracle", "float": "DECIMAL(38, 10)", "datetime": "TIMESTAMP"},
        "postgresql": {
            "dialect": "postgresql",
            "float": "FLOAT(53)",
            "datetime": "TIMESTAMP WITHOUT TIME ZONE",
        },
        "redshift": {
            "dialect": "redshift",
            "float": "FLOAT(53)",
            "datetime": "TIMESTAMP WITHOUT TIME ZONE",
        },
        "singlestore": {"dialect": "singlestoredb", "float": "DOUBLE", "datetime": "DATETIME"},
        # Lowercase as this dialect emits it; the server reads type names case-insensitively.
        "snowflake": {"dialect": "snowflake", "float": "FLOAT", "datetime": "datetime"},
        "sqlite": {"dialect": "sqlite", "float": "FLOAT", "datetime": "DATETIME"},
        "trino": {"dialect": "trino", "float": "DOUBLE", "datetime": "TIMESTAMP"},
    }
    """Keyed by the backend's own declared label; `dialect` names the SQLAlchemy dialect it
    connects through, which is spelled differently from the label for two of them."""

    def test_every_registered_sql_backend_has_a_row(self) -> None:
        """A backend with no row is one whose columns nobody wrote down."""
        assert {spec.label for spec in _sql_backend_specs()} == set(self._RESOLVED), (
            "a SQL backend is registered that this table does not account for (or the reverse); "
            "add its row, resolved from its declaration, in the change that adds the backend"
        )

    @pytest.mark.parametrize("spec", _backend_params())
    def test_the_recorded_types_are_what_this_backend_resolves(self, spec: SqlBackendSpec) -> None:
        recorded = self._RESOLVED.get(spec.label)
        assert recorded is not None, (
            f"{spec.label} has no row here; test_every_registered_sql_backend_has_a_row says why"
        )

        try:
            dialect = sa_dialect_registry.load(recorded["dialect"])()
        except sa.exc.NoSuchModuleError:
            # Only this: a dialect absent from the lane is the expected case, and skipping says
            # so out loud. Any other failure means an installed dialect is broken, which must not
            # read here as though the backend simply were not present.
            pytest.skip(f"the {recorded['dialect']} dialect is not installed in this lane")

        resolved = sql_module.inferrable_types_for(spec)
        for name, python_type in (("float", float), ("datetime", datetime)):
            assert _rendered(resolved[python_type], dialect) == recorded[name], (
                f"{spec.label} resolves `{name}` to a different type than recorded here; "
                "confirm the new rendering is a type that server has, and that it holds a "
                "declared value without narrowing it, then update this table in the same change"
            )

        assert _rendered(resolved[pd.Timestamp], dialect) == recorded["datetime"], (
            f"{spec.label} resolves a pandas timestamp to a different type than a plain "
            "datetime; the two describe the same fixture column and a backend overriding one "
            "without the other stores the same value two ways"
        )


class TestColumnTypeOverridesMergeOverSharedDefault:
    def test_overridden_type_applies_only_to_the_declared_python_type(
        self, tmp_path: pathlib.Path
    ) -> None:
        # A length distinct from the one any real backend declares, so a pass here can only be
        # explained by this declaration's own override actually being read - not by coincidental
        # agreement with, say, MySQL's or Databricks' `VARCHAR(255)`.
        config = _ThrowawayDatasourceTestConfig(
            backend_spec_override=dataclasses.replace(
                _BASE_SPEC, column_type_overrides={str: sa.VARCHAR(42)}
            )
        )
        batch_setup = _ThrowawayBatchTestSetup(
            data=pd.DataFrame({"col_str": ["a", "b"], "col_int": [1, 2]}),
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            columns = {c.name: c.type for c in batch_setup.main_table_data.table.columns}

            # The Python type named in the override receives the declared type...
            str_column_type = columns["col_str"]
            assert isinstance(str_column_type, sa.VARCHAR)
            assert str_column_type.length == 42

            # ...while every other Python type still receives the shared default, unaffected by
            # the override declared for a different type.
            assert isinstance(columns["col_int"], sa.INTEGER)
        finally:
            batch_setup.teardown()


def _count_insert_statements(
    monkeypatch: pytest.MonkeyPatch,
) -> List[sa.Insert]:
    """Patch `sa.Connection.execute` to record every `Insert` statement issued through it, and
    return the list that accumulates them.

    Patching at the connection-class level, rather than stubbing `_safe_bulk_insert` or its
    caller, observes the actual number of statements sent to the database - the chunking
    arithmetic's real, external effect - rather than merely the arguments the caller passed in.
    Non-insert statements (schema DDL, table creation) also flow through this same method during
    `setup()`, so the filter on `isinstance(statement, sa.Insert)` is what isolates the count to
    inserts specifically.
    """
    insert_calls: List[sa.Insert] = []
    original_execute = sa.Connection.execute

    def counting_execute(
        self: sa.Connection, statement: sa.Executable, *args: object, **kwargs: object
    ) -> object:
        if isinstance(statement, sa.Insert):
            insert_calls.append(statement)
        return original_execute(self, statement, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(sa.Connection, "execute", counting_execute)
    return insert_calls


class TestDeclaredInsertParameterLimitDrivesChunking:
    """The shared insert path reads its chunking limit from `self.backend_spec.insert_parameter_
    limit` rather than from any property of the live connection. A declaration that carries a
    limit must split a known-width insert into the exact chunk count the limit's own arithmetic
    predicts; a declaration that carries none must issue the whole insert as a single statement.
    Both tests use a single-table declaration (no extra data) so every recorded `Insert` belongs
    to the one table under test, and count actual statements rather than merely asserting that
    some parameter value was forwarded - a caller that forwarded the right number but the
    chunking helper ignored it would still pass a "value was passed" assertion but must fail
    this one.
    """

    def test_declared_limit_splits_a_known_width_insert_into_the_expected_statement_count(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        insert_calls = _count_insert_statements(monkeypatch)

        # Two columns, limit of 5 -> max_rows = 5 // 2 = 2 rows per statement. Seven rows then
        # split as [2, 2, 2, 1]: ceil(7 / 2) = 4 statements, an exact figure derived from the
        # declared limit and the data's own shape rather than an observed count taken on faith.
        data = pd.DataFrame({"col_a": range(7), "col_b": range(7)})
        config = _ThrowawayDatasourceTestConfig(
            backend_spec_override=dataclasses.replace(_BASE_SPEC, insert_parameter_limit=5)
        )
        batch_setup = _ThrowawayBatchTestSetup(
            data=data,
            config=config,
            base_dir=tmp_path,
            extra_data={},
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            assert len(insert_calls) == 4
        finally:
            batch_setup.teardown()

    def test_declaration_with_no_limit_issues_a_single_statement(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        insert_calls = _count_insert_statements(monkeypatch)

        # Same data shape as the positive case above - the only thing that differs is the
        # declaration, which is `_BASE_SPEC` unmodified: `insert_parameter_limit` defaults to
        # `None`.
        data = pd.DataFrame({"col_a": range(7), "col_b": range(7)})
        config = _ThrowawayDatasourceTestConfig()
        batch_setup = _ThrowawayBatchTestSetup(
            data=data,
            config=config,
            base_dir=tmp_path,
            extra_data={},
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            assert len(insert_calls) == 1
        finally:
            batch_setup.teardown()


_CACHE_REGRESSION_SETUP_CALLS: List[None] = []
_CACHE_REGRESSION_TEARDOWN_CALLS: List[None] = []
_CACHE_REGRESSION_SETUP_IDENTITY: List[BatchTestSetup] = []

_CACHE_REGRESSION_SPEC = dataclasses.replace(_BASE_SPEC, label="throwaway-cache-regression")

_CACHE_REGRESSION_DATA = pd.DataFrame({"col_a": [1, 2, 3]})


class _CountingBatchTestSetup(_ThrowawayBatchTestSetup):
    """Records every `setup`/`teardown` call so the session-scoped batch-setup cache can be
    pinned by a counting oracle rather than by "the fixtures were not edited" - a regression here
    costs session time, not a red test, so only a counter catches it.
    """

    @override
    def setup(self) -> None:
        _CACHE_REGRESSION_SETUP_CALLS.append(None)
        super().setup()

    @override
    def teardown(self) -> None:
        _CACHE_REGRESSION_TEARDOWN_CALLS.append(None)
        super().teardown()


class _CacheRegressionDatasourceTestConfig(_ThrowawayDatasourceTestConfig):
    DATA_SOURCE_SPEC: ClassVar[SqlBackendSpec] = _CACHE_REGRESSION_SPEC

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)
        return _CountingBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


_CACHE_REGRESSION_CONFIG = _CacheRegressionDatasourceTestConfig()


def _cache_regression_entry(
    _cached_test_configs: dict[TestConfig, BatchTestSetup],
) -> tuple[TestConfig, BatchTestSetup]:
    """Return the `(cache_key, cached_setup)` pair `_batch_setup_for_datasource` filed the
    throwaway cache-regression declaration under. Shared by both tests below so each does its own
    independent lookup rather than one passing state to the other directly - the point is to
    observe what the shared cache actually holds, not to hand off a reference.
    """
    [cache_key] = [
        test_config
        for test_config in _cached_test_configs
        if test_config.data_source_config == _CACHE_REGRESSION_CONFIG
        and test_config.data.equals(_CACHE_REGRESSION_DATA)
    ]
    return cache_key, _cached_test_configs[cache_key]


class TestSessionCacheSharesOneBatchSetupAcrossEqualConfigs:
    """Regression coverage for the session-scoped batch-setup cache. The two tests below must run
    in the order they are declared: the first establishes the cached setup, the second observes
    that reusing the same declaration and the same data does not set it up a second time. Both are
    decorated with `parameterize_batch_for_data_sources` over the identical throwaway config and
    data, which is exactly what the session-scoped cache keys on.
    """

    @parameterize_batch_for_data_sources(
        data_source_configs=[_CACHE_REGRESSION_CONFIG], data=_CACHE_REGRESSION_DATA
    )
    def test_a_first_use_sets_up_the_batch_once(
        self,
        batch_for_datasource: object,
        _cached_test_configs: dict[TestConfig, BatchTestSetup],
    ) -> None:
        assert batch_for_datasource is not None
        assert len(_CACHE_REGRESSION_SETUP_CALLS) == 1

        # Record which object the cache holds after this test's own use, so test_b has something
        # concrete to check identity against instead of only re-deriving a call count that would
        # hold either way.
        _, cached_setup = _cache_regression_entry(_cached_test_configs)
        _CACHE_REGRESSION_SETUP_IDENTITY.append(cached_setup)

    @parameterize_batch_for_data_sources(
        data_source_configs=[_CACHE_REGRESSION_CONFIG], data=_CACHE_REGRESSION_DATA
    )
    def test_b_second_use_of_the_same_config_and_data_reuses_the_cached_setup(
        self,
        batch_for_datasource: object,
        _cached_test_configs: dict[TestConfig, BatchTestSetup],
    ) -> None:
        assert batch_for_datasource is not None

        # This is only non-vacuous because test_a is the sole writer to
        # `_CACHE_REGRESSION_SETUP_IDENTITY`: if this test runs alone, the list is empty and this
        # fails outright, rather than the call-count checks below, which would still hold either
        # way (this test's own fixture invocation would be the one and only setup call).
        assert len(_CACHE_REGRESSION_SETUP_IDENTITY) == 1
        cache_key, cached_setup = _cache_regression_entry(_cached_test_configs)
        assert cached_setup is _CACHE_REGRESSION_SETUP_IDENTITY[0]

        # Still exactly one: this test's request for the same declaration and the same data
        # reused the cached BatchTestSetup instead of constructing and setting up a second one.
        assert len(_CACHE_REGRESSION_SETUP_CALLS) == 1
        assert len(_CACHE_REGRESSION_TEARDOWN_CALLS) == 0

        # Tear down deterministically inside the test rather than waiting for the session-scoped
        # cleanup fixture's finalizer, which only fires once the entire pytest session ends, and
        # remove the cached entry so that finalizer does not tear it down a second time when it
        # eventually runs.
        _cached_test_configs.pop(cache_key)
        cached_setup.teardown()

        assert len(_CACHE_REGRESSION_SETUP_CALLS) == 1
        assert len(_CACHE_REGRESSION_TEARDOWN_CALLS) == 1


class _RecordingConnection:
    """A stand-in for `sa.Connection` that records whether `commit()` is invoked, without
    touching a real database. The commit decision under test only ever calls `.commit()` on
    its argument, so a double exposing just that one method is enough to observe it."""

    def __init__(self) -> None:
        self.commit_calls = 0

    def commit(self) -> None:
        self.commit_calls += 1


class TestTransactionModeControlsCommit:
    """`setup()` and `teardown()` both call `self._safe_commit(conn)` once, at the same
    relative position, and nothing else sits between that call and the connection. Calling
    `_safe_commit` directly, once per site, exercises exactly what each site does without
    depending on a live database honoring an auto-commit declaration - sqlite, the file-backed
    dialect the throwaway declarations in this module use, does not persist uncommitted rows past
    the connection that issued them (schema DDL survives regardless), so a round trip asserting
    data visibility would fail for a reason unrelated to the decision itself.
    """

    def test_autocommit_declaration_causes_no_commit_call_in_setup_or_teardown(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _ThrowawayDatasourceTestConfig(
            backend_spec_override=dataclasses.replace(
                _BASE_SPEC, transaction_mode=TransactionMode.AUTOCOMMIT
            )
        )
        batch_setup = _ThrowawayBatchTestSetup(
            data=_DATA,
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )
        conn = _RecordingConnection()
        sa_conn = cast("sa.Connection", conn)

        batch_setup._safe_commit(sa_conn)  # what setup() does at its own call site
        batch_setup._safe_commit(sa_conn)  # what teardown() does at its own call site

        assert conn.commit_calls == 0

    def test_explicit_commit_declaration_causes_exactly_one_commit_call_per_call_site(
        self, tmp_path: pathlib.Path
    ) -> None:
        config = _ThrowawayDatasourceTestConfig()  # default declaration: explicit commit
        batch_setup = _ThrowawayBatchTestSetup(
            data=_DATA,
            config=config,
            base_dir=tmp_path,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )
        conn = _RecordingConnection()
        sa_conn = cast("sa.Connection", conn)

        batch_setup._safe_commit(sa_conn)  # what setup() does at its own call site
        assert conn.commit_calls == 1

        batch_setup._safe_commit(sa_conn)  # what teardown() does at its own call site
        assert conn.commit_calls == 2


class TestGenericSqlEscapeHatchRoutesToTheSameCommitDecision:
    """`TestTransactionModeControlsCommit` above proves `_safe_commit` honors
    `self.backend_spec.transaction_mode`. It does not prove that the generic-SQL escape hatch's
    two routes to autocommit - the `GX_TEST_GENERIC_SQL_AUTOCOMMIT` environment variable and the
    `autocommit=True` field - actually reach that property. Both routes resolve through
    `GenericSQLBatchTestSetup.backend_spec`, but by different mechanisms: the environment
    variable is applied by that override itself, while the field has already been folded into
    the config's own declaration at construction, so the override passes it through untouched.
    The environment route is therefore the one that pins the override; a base class
    that instead read `self.config.backend_spec` directly would skip that override, silently
    reintroducing a commit call, and every existing test in both changed test modules would still
    pass. Only a real `GenericSQLBatchTestSetup` against a real backend spec, driven through
    `_safe_commit`, distinguishes the two.
    """

    def test_environment_variable_route_causes_no_commit_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GX_TEST_GENERIC_SQL_AUTOCOMMIT", "1")
        config = GenericSQLDatasourceTestConfig(connection_string="sqlite:///:memory:")
        batch_setup = GenericSQLBatchTestSetup(
            data=_DATA,
            config=config,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )
        conn = _RecordingConnection()
        sa_conn = cast("sa.Connection", conn)

        batch_setup._safe_commit(sa_conn)  # what setup() does at its own call site
        batch_setup._safe_commit(sa_conn)  # what teardown() does at its own call site

        assert conn.commit_calls == 0

    def test_autocommit_field_route_causes_no_commit_call(self) -> None:
        config = GenericSQLDatasourceTestConfig(
            connection_string="sqlite:///:memory:", autocommit=True
        )
        batch_setup = GenericSQLBatchTestSetup(
            data=_DATA,
            config=config,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )
        conn = _RecordingConnection()
        sa_conn = cast("sa.Connection", conn)

        batch_setup._safe_commit(sa_conn)  # what setup() does at its own call site
        batch_setup._safe_commit(sa_conn)  # what teardown() does at its own call site

        assert conn.commit_calls == 0

    def test_neither_route_set_causes_exactly_one_commit_call_per_call_site(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Clear the variable rather than assuming it is unset: exporting it is the escape
        # hatch's own documented usage, so a developer running that way would otherwise turn
        # this negative control red for a reason that has nothing to do with what it asserts.
        monkeypatch.delenv("GX_TEST_GENERIC_SQL_AUTOCOMMIT", raising=False)
        config = GenericSQLDatasourceTestConfig(connection_string="sqlite:///:memory:")
        batch_setup = GenericSQLBatchTestSetup(
            data=_DATA,
            config=config,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )
        conn = _RecordingConnection()
        sa_conn = cast("sa.Connection", conn)

        batch_setup._safe_commit(sa_conn)  # what setup() does at its own call site
        assert conn.commit_calls == 1

        batch_setup._safe_commit(sa_conn)  # what teardown() does at its own call site
        assert conn.commit_calls == 2


class TestSharedSetupModuleHasNoImportTimeEnvironmentRead:
    """Guards the shared setup module's import-time behavior: no environment variable is read
    and no module-level mutable dialect state is built when the module is imported.

    The primary test below is behavioral: it checks that the dialect enumeration's member map is
    unchanged after import with the former driver-registration environment variable set. It runs
    in a subprocess rather than via
    `importlib.reload`: reload would leave every already-imported dependent module (the nine SQL
    batch-setup subclasses, in particular, each of which captured its own reference to the
    pre-reload class object at its own import time) holding a stale reference, whereas a fresh
    interpreter has no prior import to go stale.

    The second test is a source-level assertion kept as a mechanical backstop: it fails fast and
    with a precise pointer if the deleted names are ever reintroduced, which the behavioral test
    alone would not localize as clearly.
    """

    def test_dialect_enumeration_unchanged_after_import_with_former_driver_env_var_set(
        self,
    ) -> None:
        script = (
            "import json\n"
            "from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect\n"
            "import tests.integration.test_utils.data_source_config.sql  # noqa: F401\n"
            "print(json.dumps(sorted(GXSqlDialect._value2member_map_)))\n"
        )
        child_env = dict(os.environ)
        child_env["GX_TEST_GENERIC_SQL_DRIVER"] = "gx_test_unrecognized_dialect"

        result = subprocess.run(
            [sys.executable, "-c", script],
            env=child_env,
            capture_output=True,
            text=True,
            check=True,
        )

        child_member_map = json.loads(result.stdout)
        assert child_member_map == sorted(GXSqlDialect._value2member_map_)

    def test_source_reads_no_environment_variable_and_builds_no_dialect_member(self) -> None:
        source = pathlib.Path(sql_module.__file__).read_text()

        assert "os.environ" not in source
        assert "_register_generic_sql_driver" not in source
        assert "GX_TEST_GENERIC_SQL_DRIVER" not in source
        assert "GX_TEST_GENERIC_SQL_AUTOCOMMIT" not in source
        # No construction of the enumeration remains, and no reference to it at all: the insert
        # parameter limit that used to be inlined here now reads the declared value off the
        # backend's own spec instead of comparing against a dialect-enumeration member.
        assert "GXSqlDialect(" not in source
        assert "GXSqlDialect" not in source


class _UnrecognizedDialect(SQLiteDialect_pysqlite):
    """Sqlite's real driver implementation under a name `GXSqlDialect` has never heard of -
    standing in for a database driver the enumeration does not know about, the way
    `GX_TEST_GENERIC_SQL_DRIVER` used to let a caller register one."""

    name = "gx_test_unrecognized_dialect"
    supports_statement_cache = True


sa_dialect_registry.register(
    "gx_test_unrecognized_dialect",
    __name__,
    _UnrecognizedDialect.__name__,
)


class TestGenericSqlEscapeHatchWorksAgainstAnUnrecognizedDialect:
    def test_setup_and_teardown_do_not_raise_for_a_dialect_outside_the_enumeration(
        self, tmp_path: pathlib.Path
    ) -> None:
        assert "gx_test_unrecognized_dialect" not in GXSqlDialect._value2member_map_

        connection_string = f"gx_test_unrecognized_dialect:///{tmp_path / 'unrecognized.db'}"
        config = GenericSQLDatasourceTestConfig(connection_string=connection_string)
        batch_setup = GenericSQLBatchTestSetup(
            data=_DATA,
            config=config,
            extra_data=_EXTRA_DATA,
            context=gx.get_context(mode="ephemeral"),
        )

        batch_setup.setup()
        try:
            assert {c.name for c in batch_setup.main_table_data.table.columns} == {"col_a"}
        finally:
            batch_setup.teardown()
