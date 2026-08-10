"""Extension-point behavior tests for the shared SQL batch-setup layer.

Every declaration below is a throwaway, never decorated with `register_sql_backend`, so none of it
joins the registry that the derived data-source lists and completeness checks walk. The schema
items these declarations contribute are plain SQLAlchemy constructs with no dialect package
involved, so the whole module runs against a file-backed SQLite database and needs no server.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import TYPE_CHECKING, ClassVar, List, Mapping, Optional, Sequence

import pandas as pd
import pytest
import sqlalchemy as sa

import great_expectations as gx
from great_expectations.compatibility.typing_extensions import override
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config.backend_spec import (
    BackendProvisioning,
    CiLaneRef,
    SqlBackendSpec,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup
from tests.integration.test_utils.data_source_config.sql_config import SqlDatasourceTestConfig

if TYPE_CHECKING:
    from great_expectations.data_context import AbstractDataContext
    from great_expectations.datasource.fluent.sql_datasource import TableAsset
    from tests.integration.conftest import TestConfig
    from tests.integration.sql_session_manager import SessionSQLEngineManager
    from tests.integration.test_utils.data_source_config.base import BatchTestSetup

pytestmark = pytest.mark.sqlite


_BASE_SPEC = SqlBackendSpec(
    label="throwaway-table-schema-items",
    marker="sqlite",
    provisioning=BackendProvisioning.LOCAL_FILE,
    ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="sqlite"),
    uses_schema=False,
)
"""A minimal, well-formed declaration reused as the base for every throwaway declaration below.
Never registered, so its label never has to be globally unique the way a real backend's does -
only unique enough to keep this module's own throwaway configs distinguishable from each other."""


class _ThrowawayDatasourceTestConfig(SqlDatasourceTestConfig):
    """A file-backed declaration used only to drive the tests in this module."""

    BACKEND_SPEC: ClassVar[SqlBackendSpec] = _BASE_SPEC

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
    @override
    def use_schema(self) -> bool:
        return False

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
    BACKEND_SPEC: ClassVar[SqlBackendSpec] = _CACHE_REGRESSION_SPEC

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
