from __future__ import annotations

from dataclasses import fields
from typing import TYPE_CHECKING, Iterator, List, Mapping, Optional, Tuple

import pytest

from great_expectations.compatibility.typing_extensions import override
from tests.integration.test_utils.data_source_config import (
    ALL_DATA_SOURCES,
    CURATED_SQL_DATA_SOURCES,
    PANDAS_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    SQL_DATA_SOURCES,
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SingleStoreDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
    data_sources_for_tier_case,
)
from tests.integration.test_utils.data_source_config.backend_spec import (
    BackendProvisioning,
    BackendTier,
    CiLaneRef,
    SqlBackendSpec,
)
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)
from tests.integration.test_utils.data_source_config.registry import (
    isolated_registry,
    iter_sql_backends,
    register_sql_backend,
    sql_backends_for_tier,
)
from tests.integration.test_utils.data_source_config.sql_config import SqlDatasourceTestConfig

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.data_context.data_context.abstract_data_context import (
        AbstractDataContext,
    )
    from tests.integration.test_utils.data_source_config.sql import SessionSQLEngineManager

pytestmark = pytest.mark.project


def _make_spec(**overrides: object) -> SqlBackendSpec:
    defaults: dict[str, object] = dict(
        label="throwaway",
        marker="throwaway",
        provisioning=BackendProvisioning.LOCAL_FILE,
        ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="throwaway"),
        uses_schema=False,
    )
    defaults.update(overrides)
    return SqlBackendSpec(**defaults)  # type: ignore[arg-type]


def _make_config_class(name: str, spec: SqlBackendSpec) -> type:
    return type(name, (), {"BACKEND_SPEC": spec})


@pytest.fixture(autouse=True)
def _snapshot_registry() -> Iterator[None]:
    """Wrap every test in this module in the registry's snapshot/restore seam.

    The registry is process-global, so a throwaway registration in one test must not survive to
    the next test, and must not survive into the real registry that the wiring drift check and
    other consumers rely on.
    """
    with isolated_registry():
        yield


class TestSqlBackendSpecMarkRoundTrip:
    def test_pytest_mark_round_trips_marker_name_to_literal_mark(self) -> None:
        spec = _make_spec(marker="mysql")

        assert spec.pytest_mark == pytest.mark.mysql

    def test_pytest_mark_round_trips_a_different_marker_name(self) -> None:
        spec = _make_spec(marker="singlestore", tiers=frozenset({BackendTier.CURATED_SQL}))

        assert spec.pytest_mark == pytest.mark.singlestore


class TestSqlBackendSpecTableSchemaItemsDefault:
    def test_spec_with_no_table_schema_item_factory_reports_it_as_absent(self) -> None:
        spec = _make_spec()

        assert spec.table_schema_items is None


class TestIsolatedSnapshotEmptyRegistryCase:
    def test_registry_is_empty_within_a_fresh_isolated_snapshot(self) -> None:
        with isolated_registry():
            assert iter_sql_backends() == ()


class TestIsolatedSnapshotRestoresRealRegistry:
    def test_registering_a_throwaway_does_not_survive_the_snapshot(self) -> None:
        # Establish a populated baseline inside the module's own autouse isolation, so this test
        # proves both halves of the seam: that entering it clears down to empty, and that exiting
        # it restores exactly what was there beforehand — regardless of what the real registry
        # elsewhere happens to hold.
        register_sql_backend(_make_config_class("Baseline", _make_spec(label="baseline")))
        before = iter_sql_backends()
        assert before != ()

        with isolated_registry():
            assert iter_sql_backends() == ()
            register_sql_backend(_make_config_class("Throwaway", _make_spec()))
            assert iter_sql_backends() != before

        assert iter_sql_backends() == before


class TestRegisterSqlBackendOrdering:
    def test_iter_sql_backends_orders_registrations_by_label_not_registration_order(self) -> None:
        zebra = _make_config_class("Zebra", _make_spec(label="zebra", marker="zebra_marker"))
        apple = _make_config_class("Apple", _make_spec(label="apple", marker="apple_marker"))

        register_sql_backend(zebra)
        register_sql_backend(apple)

        assert iter_sql_backends() == (apple, zebra)


class TestSqlBackendsForTier:
    def test_returns_only_backends_declaring_the_tier_ordered_by_label(self) -> None:
        member = _make_config_class(
            "Member",
            _make_spec(
                label="member",
                marker="member_marker",
                tiers=frozenset({BackendTier.CURATED_SQL}),
            ),
        )
        non_member = _make_config_class(
            "NonMember", _make_spec(label="non-member", marker="non_member_marker")
        )

        register_sql_backend(member)
        register_sql_backend(non_member)

        assert sql_backends_for_tier(BackendTier.CURATED_SQL) == (member,)


class TestDataSourcesForTierCase:
    """`data_sources_for_tier_case` is the one place a backend's `tier_case_exclusions` entry
    takes effect: it returns a tier's members, instantiated in label order, omitting only those
    declaring an exclusion for the given case key.
    """

    def test_omits_only_the_backend_excluding_the_case_and_keeps_the_rest_for_other_keys(
        self,
    ) -> None:
        # Registered zebra before apple - non-alphabetical - so a result in label order can only
        # come from `sql_backends_for_tier`'s own label sort, never from registration order.
        zebra = _make_config_class(
            "Zebra",
            _make_spec(
                label="zebra",
                marker="zebra_marker",
                tiers=frozenset({BackendTier.CURATED_SQL}),
                tier_case_exclusions={"flaky_case": "observed non-determinism, see issue #1"},
            ),
        )
        apple = _make_config_class(
            "Apple",
            _make_spec(
                label="apple",
                marker="apple_marker",
                tiers=frozenset({BackendTier.CURATED_SQL}),
            ),
        )
        register_sql_backend(zebra)
        register_sql_backend(apple)

        excluded_case = data_sources_for_tier_case(BackendTier.CURATED_SQL, "flaky_case")
        assert [type(config) for config in excluded_case] == [apple]

        other_case = data_sources_for_tier_case(BackendTier.CURATED_SQL, "unrelated_case")
        assert [type(config) for config in other_case] == [apple, zebra]

    def test_with_no_exclusions_declared_matches_the_tiers_call_time_membership(self) -> None:
        """The behavior-preservation oracle for this accessor, stated call-time-to-call-time
        rather than against `CURATED_SQL_DATA_SOURCES`.

        `sql_backends_for_tier` reads the registry fresh on every call. `CURATED_SQL_DATA_SOURCES`
        is a list built once, when the defining module is first imported, from whatever the
        registry held at that moment. This module's autouse fixture clears the registry around
        every test, so inside a test body a call-time read and that import-time snapshot are
        answering two different questions: comparing them here would pass vacuously today (both
        happen to be empty, since nothing yet declares the curated tier at import time) and would
        fail for a reason that has nothing to do with this accessor the first time a real backend
        joins that tier here without also being re-imported. Comparing `data_sources_for_tier_case`
        to `sql_backends_for_tier` instead keeps both sides of the comparison call-time, so the
        assertion is meaningful inside this isolated registry and stays correct regardless of what
        the real, outside-the-seam registry holds at any given moment. The published-key,
        `CURATED_SQL_DATA_SOURCES`-referencing form of this same oracle belongs in the curated
        suite's own module, which runs against the real, unmodified registry rather than this
        isolated one.
        """
        zebra = _make_config_class(
            "Zebra",
            _make_spec(
                label="zebra", marker="zebra_marker", tiers=frozenset({BackendTier.CURATED_SQL})
            ),
        )
        apple = _make_config_class(
            "Apple",
            _make_spec(
                label="apple", marker="apple_marker", tiers=frozenset({BackendTier.CURATED_SQL})
            ),
        )
        register_sql_backend(zebra)
        register_sql_backend(apple)

        result = data_sources_for_tier_case(BackendTier.CURATED_SQL, "arbitrary_case")

        assert [type(config) for config in result] == list(
            sql_backends_for_tier(BackendTier.CURATED_SQL)
        )

    def test_filters_the_tier_it_is_asked_for_rather_than_a_fixed_one(self) -> None:
        """Exclusion is a property of tiers in general, so the accessor has to honour whichever
        tier it is given. Without this, an implementation that ignored its `tier` argument and
        always read one particular tier would satisfy every other test in this class, because
        they all happen to ask about the same tier.
        """
        curated = _make_config_class(
            "Curated",
            _make_spec(
                label="curated-only",
                marker="curated_only_marker",
                tiers=frozenset({BackendTier.CURATED_SQL}),
            ),
        )
        standard = _make_config_class(
            "Standard",
            _make_spec(
                label="standard-only",
                marker="standard_only_marker",
                tiers=frozenset({BackendTier.STANDARD_SQL}),
                tier_case_exclusions={"skipped_case": "not meaningful for this dialect"},
            ),
        )
        register_sql_backend(curated)
        register_sql_backend(standard)

        # Each tier sees only its own member, so a hard-coded tier would return the wrong one.
        assert [
            type(config)
            for config in data_sources_for_tier_case(BackendTier.STANDARD_SQL, "unrelated_case")
        ] == [standard]
        assert [
            type(config)
            for config in data_sources_for_tier_case(BackendTier.CURATED_SQL, "unrelated_case")
        ] == [curated]

        # And the exclusion applies within the tier that declared it, not across tiers.
        assert data_sources_for_tier_case(BackendTier.STANDARD_SQL, "skipped_case") == []
        assert [
            type(config)
            for config in data_sources_for_tier_case(BackendTier.CURATED_SQL, "skipped_case")
        ] == [curated]


class TestRegisterSqlBackendDuplicateLabel:
    def test_duplicate_label_raises_naming_both_classes(self) -> None:
        first = _make_config_class("First", _make_spec(label="dup-label", marker="first_marker"))
        second = _make_config_class("Second", _make_spec(label="dup-label", marker="second_marker"))
        register_sql_backend(first)

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(second)

        message = str(excinfo.value)
        assert "First" in message
        assert "Second" in message
        assert "dup-label" in message


class TestRegisterSqlBackendDuplicateMarker:
    def test_duplicate_marker_raises_naming_both_classes(self) -> None:
        first = _make_config_class("First", _make_spec(label="first-label", marker="dup_marker"))
        second = _make_config_class("Second", _make_spec(label="second-label", marker="dup_marker"))
        register_sql_backend(first)

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(second)

        message = str(excinfo.value)
        assert "First" in message
        assert "Second" in message
        assert "dup_marker" in message


class TestRegisterSqlBackendContainerProvisioning:
    def test_local_container_without_container_service_raises(self) -> None:
        config_class = _make_config_class(
            "NoService",
            _make_spec(provisioning=BackendProvisioning.LOCAL_CONTAINER, container_service=None),
        )

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(config_class)

        assert "NoService" in str(excinfo.value)

    def test_container_service_without_local_container_raises(self) -> None:
        config_class = _make_config_class(
            "StrayService",
            _make_spec(provisioning=BackendProvisioning.LOCAL_FILE, container_service="throwaway"),
        )

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(config_class)

        assert "StrayService" in str(excinfo.value)


class TestRegisterSqlBackendEmptyFields:
    def test_empty_label_raises(self) -> None:
        config_class = _make_config_class("BlankLabel", _make_spec(label=""))

        with pytest.raises(ValueError, match="BlankLabel"):
            register_sql_backend(config_class)

    def test_empty_marker_raises(self) -> None:
        config_class = _make_config_class("BlankMarker", _make_spec(marker=""))

        with pytest.raises(ValueError, match="BlankMarker"):
            register_sql_backend(config_class)

    def test_empty_ci_lane_workflow_job_raises(self) -> None:
        config_class = _make_config_class(
            "BlankWorkflowJob",
            _make_spec(ci_lane=CiLaneRef(workflow_job="", marker_token="postgresql")),
        )

        with pytest.raises(ValueError, match="BlankWorkflowJob"):
            register_sql_backend(config_class)

    def test_empty_ci_lane_marker_token_raises(self) -> None:
        config_class = _make_config_class(
            "BlankCiLane",
            _make_spec(ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="")),
        )

        with pytest.raises(ValueError, match="BlankCiLane"):
            register_sql_backend(config_class)

    def test_non_positive_insert_parameter_limit_raises(self) -> None:
        config_class = _make_config_class("ZeroLimit", _make_spec(insert_parameter_limit=0))

        with pytest.raises(ValueError, match="ZeroLimit"):
            register_sql_backend(config_class)

    def test_negative_insert_parameter_limit_raises(self) -> None:
        config_class = _make_config_class("NegativeLimit", _make_spec(insert_parameter_limit=-1))

        with pytest.raises(ValueError, match="NegativeLimit"):
            register_sql_backend(config_class)


class TestRegisterSqlBackendTierCaseExclusionReasons:
    def test_empty_case_key_raises(self) -> None:
        config_class = _make_config_class(
            "BlankKey", _make_spec(tier_case_exclusions={"": "a reason"})
        )

        with pytest.raises(ValueError, match="BlankKey"):
            register_sql_backend(config_class)

    def test_empty_reason_raises_naming_class_and_case_key(self) -> None:
        config_class = _make_config_class(
            "BlankReason", _make_spec(tier_case_exclusions={"some_case": ""})
        )

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(config_class)

        message = str(excinfo.value)
        assert "BlankReason" in message
        assert "some_case" in message

    def test_whitespace_only_reason_raises_naming_class_and_case_key(self) -> None:
        config_class = _make_config_class(
            "WhitespaceReason", _make_spec(tier_case_exclusions={"some_case": "   "})
        )

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(config_class)

        message = str(excinfo.value)
        assert "WhitespaceReason" in message
        assert "some_case" in message


class TestRegisterSqlBackendTierCaseExclusionCeiling:
    def test_exactly_two_exclusions_registers_cleanly(self) -> None:
        config_class = _make_config_class(
            "TwoExclusions",
            _make_spec(
                tier_case_exclusions={
                    "case_one": "dialect gap, see issue #1",
                    "case_two": "dialect gap, see issue #2",
                }
            ),
        )

        register_sql_backend(config_class)

        assert config_class in iter_sql_backends()

    def test_three_exclusions_raises_naming_class_count_and_all_keys(self) -> None:
        config_class = _make_config_class(
            "ThreeExclusions",
            _make_spec(
                tier_case_exclusions={
                    "case_one": "dialect gap, see issue #1",
                    "case_two": "dialect gap, see issue #2",
                    "case_three": "observed non-determinism, see issue #3",
                }
            ),
        )

        with pytest.raises(ValueError) as excinfo:
            register_sql_backend(config_class)

        message = str(excinfo.value)
        assert "ThreeExclusions" in message
        assert "3" in message
        assert "case_one" in message
        assert "case_two" in message
        assert "case_three" in message


class TestRegisterSqlBackendTableSchemaItems:
    def test_non_callable_table_schema_items_raises(self) -> None:
        config_class = _make_config_class(
            "NotCallable",
            _make_spec(table_schema_items="not-a-callable"),
        )

        with pytest.raises(ValueError, match="NotCallable"):
            register_sql_backend(config_class)

    def test_callable_table_schema_items_is_validated_without_being_invoked(self) -> None:
        calls: List[None] = []

        def factory() -> List[object]:
            calls.append(None)
            return []

        config_class = _make_config_class("Callable", _make_spec(table_schema_items=factory))

        register_sql_backend(config_class)

        assert calls == []


class _HandWrittenControlConfig(DataSourceTestConfig):
    """A config written the way today's backends are, with `label` and `pytest_mark` as
    hand-coded properties. Used as the behavior-preservation control for
    `SqlDatasourceTestConfig`: the divergent label/marker pair (SQL Server's label is `mssql`,
    its marker is `sql_server`) is the case that most directly exercises whether a declaration-
    derived config produces the same identity as one written by hand.
    """

    @property
    @override
    def label(self) -> str:
        return "mssql"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.sql_server

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        raise NotImplementedError("not exercised by these tests")


_THROWAWAY_DECLARED_SPEC = SqlBackendSpec(
    label="mssql",
    marker="sql_server",
    provisioning=BackendProvisioning.LOCAL_FILE,
    ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="sql_server"),
    uses_schema=True,
)


class _DeclaredConfig(SqlDatasourceTestConfig):
    """Throwaway config that derives its identity from a declared `SqlBackendSpec`, mirroring
    `_HandWrittenControlConfig`'s label and marker exactly."""

    BACKEND_SPEC = _THROWAWAY_DECLARED_SPEC

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        raise NotImplementedError("not exercised by these tests")


class TestSqlDatasourceTestConfigDerivesIdentity:
    def test_derives_label_and_mark_matching_a_hand_written_control(self) -> None:
        control = _HandWrittenControlConfig()
        declared = _DeclaredConfig()

        assert declared.label == control.label == "mssql"
        assert declared.pytest_mark == control.pytest_mark == pytest.mark.sql_server
        assert declared.test_id == control.test_id
        assert hash(declared) == hash(control)
        assert declared == control


class TestSqlDatasourceTestConfigOverrideSeam:
    def test_instance_level_backend_spec_overrides_the_class_declaration(self) -> None:
        override_spec = SqlBackendSpec(
            label="ad-hoc",
            marker="generic_sql",
            provisioning=BackendProvisioning.EXTERNAL_CREDENTIALS,
            ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="generic_sql"),
            uses_schema=False,
        )

        default_instance = _DeclaredConfig()
        overridden_instance = _DeclaredConfig(backend_spec_override=override_spec)

        assert default_instance.label == "mssql"
        assert default_instance.pytest_mark == pytest.mark.sql_server
        assert overridden_instance.label == "ad-hoc"
        assert overridden_instance.pytest_mark == pytest.mark.generic_sql
        # The class-level declaration itself is untouched by the per-instance override.
        assert _DeclaredConfig.BACKEND_SPEC is _THROWAWAY_DECLARED_SPEC


class TestSqlDatasourceTestConfigSatisfiesRegistrationProtocol:
    def test_a_declared_config_class_registers_successfully(self) -> None:
        # `register_sql_backend` is typed to accept only a class exposing
        # `BACKEND_SPEC: ClassVar[SqlBackendSpec]`. This call site is the first proof, under
        # mypy, that a real config class built on the declaration-derived base satisfies that
        # shape structurally rather than by explicit inheritance.
        with isolated_registry():
            register_sql_backend(_DeclaredConfig)

            assert _DeclaredConfig in iter_sql_backends()


class TestLocallyVerifiableBackendsRegisterInLabelOrder:
    def test_postgres_mysql_sql_server_and_sqlite_appear_in_label_order(self) -> None:
        # Re-register the four real, locally verifiable backend configs inside this module's
        # isolation seam. Each class is already enrolled once, for real, at import time via its
        # own `@register_sql_backend` decorator; re-registering it here (against the seam's
        # cleared, isolated dicts, not the real registry) proves the same fact the real import
        # already established, without depending on import order relative to the eight other
        # backend modules that will be added in later tasks.
        from tests.integration.test_utils.data_source_config.mysql import (
            MySQLDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.postgres import (
            PostgreSQLDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.sql_server import (
            SQLServerDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.sqlite import (
            SqliteDatasourceTestConfig,
        )

        for config_class in (
            PostgreSQLDatasourceTestConfig,
            MySQLDatasourceTestConfig,
            SQLServerDatasourceTestConfig,
            SqliteDatasourceTestConfig,
        ):
            register_sql_backend(config_class)

        # This is the seam-local ordering subset, not the registered-set pin further down this
        # module. The two literals look alike - same classes, same trailing label comments - but
        # they answer different questions, and only the other one has to grow when a backend is
        # added. Edit by line, not by matching on these lines.
        assert iter_sql_backends() == (
            SQLServerDatasourceTestConfig,  # mssql
            MySQLDatasourceTestConfig,  # mysql
            PostgreSQLDatasourceTestConfig,  # postgresql
            SqliteDatasourceTestConfig,  # sqlite
        )


class TestCredentialGatedBackendsRegisterInLabelOrder:
    def test_bigquery_databricks_redshift_and_snowflake_appear_in_label_order(self) -> None:
        # These four cannot have their suites run locally (no credentials for any of the four
        # hosted services), but registration itself has no dependency on credentials or on the
        # dialect package being installed - it only reads the declared spec. Re-registering the
        # real classes here, against this module's isolated seam, proves label ordering without
        # depending on import order relative to the other backend modules.
        from tests.integration.test_utils.data_source_config.big_query import (
            BigQueryDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.databricks import (
            DatabricksDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.redshift import (
            RedshiftDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.snowflake import (
            SnowflakeDatasourceTestConfig,
        )

        # Registered deliberately out of label order: an implementation returning insertion
        # order would produce this tuple instead of the sorted one asserted below, so the
        # assertion discriminates label ordering rather than merely recording these labels.
        for config_class in (
            SnowflakeDatasourceTestConfig,
            BigQueryDatasourceTestConfig,
            RedshiftDatasourceTestConfig,
            DatabricksDatasourceTestConfig,
        ):
            register_sql_backend(config_class)

        assert iter_sql_backends() == (
            BigQueryDatasourceTestConfig,  # big-query
            DatabricksDatasourceTestConfig,  # databricks
            RedshiftDatasourceTestConfig,  # redshift
            SnowflakeDatasourceTestConfig,  # snowflake
        )


class TestGenericSqlEscapeHatchIsDeclaredButUnregistered:
    """The ad-hoc, caller-supplied-connection-string config has no fixed identity to enrol, so
    unlike the eight dialect-specific backends it must never appear in the registry that gates
    CI - even though, like them, it now derives its identity from a declared spec.
    """

    def test_is_absent_from_the_registry(self) -> None:
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        assert GenericSQLDatasourceTestConfig not in iter_sql_backends()
        assert "generic_sql" not in {backend.BACKEND_SPEC.label for backend in iter_sql_backends()}

    def test_registering_it_would_still_succeed_if_it_were_ever_registered(self) -> None:
        # Proves the absence above is a deliberate omission, not a side effect of the spec
        # failing registration's own validation.
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        with isolated_registry():
            register_sql_backend(GenericSQLDatasourceTestConfig)

            assert GenericSQLDatasourceTestConfig in iter_sql_backends()


class TestGenericSqlEscapeHatchAutocommitSeam:
    def test_default_instance_reports_explicit_commit(self) -> None:
        from tests.integration.test_utils.data_source_config.backend_spec import TransactionMode
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        config = GenericSQLDatasourceTestConfig()

        assert config.backend_spec.transaction_mode == TransactionMode.EXPLICIT_COMMIT

    def test_autocommit_instance_reports_autocommit_mode(self) -> None:
        from tests.integration.test_utils.data_source_config.backend_spec import TransactionMode
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        config = GenericSQLDatasourceTestConfig(autocommit=True)

        assert config.backend_spec.transaction_mode == TransactionMode.AUTOCOMMIT

    def test_autocommit_does_not_mutate_the_class_level_declaration(self) -> None:
        from tests.integration.test_utils.data_source_config.backend_spec import TransactionMode
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        GenericSQLDatasourceTestConfig(autocommit=True)

        assert (
            GenericSQLDatasourceTestConfig.BACKEND_SPEC.transaction_mode
            == TransactionMode.EXPLICIT_COMMIT
        )

    def test_autocommit_varies_the_label_so_two_configs_no_longer_collide(self) -> None:
        """An instance whose only observable difference from another is its transaction mode
        must not compare equal to it and must not share a cache key with it: the session-scoped
        batch-setup cache is a plain `dict` keyed on config equality, and equality here is
        defined in terms of `label`, so two configs sharing a label but disagreeing on
        transaction mode would collide - the second one silently reusing the first one's cached
        setup and inheriting its commit behavior.
        """
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        explicit = GenericSQLDatasourceTestConfig(
            connection_string="mysql+pymysql://x/y", autocommit=False
        )
        autocommit = GenericSQLDatasourceTestConfig(
            connection_string="mysql+pymysql://x/y", autocommit=True
        )

        assert explicit.label != autocommit.label
        assert explicit != autocommit
        assert hash(explicit) != hash(autocommit)

        # The exact shape the session-scoped cache uses: a plain dict keyed on the config.
        cache = {explicit: "setup-for-explicit"}
        assert autocommit not in cache


class TestGenericSqlEscapeHatchEnvironmentAutocommit:
    """`GX_TEST_GENERIC_SQL_AUTOCOMMIT` is an out-of-code way to ask for the same behavior the
    `autocommit` field declares in code. It is read once a batch setup is constructed for a
    config, not when the config itself is constructed or when the harness is imported - so a
    config built before the variable is set still picks it up once a batch setup is built for
    it.
    """

    def test_env_var_is_read_at_batch_setup_construction_not_at_config_construction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from typing import cast

        import pandas as pd

        from tests.integration.test_utils.data_source_config.backend_spec import TransactionMode
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLBatchTestSetup,
            GenericSQLDatasourceTestConfig,
        )

        monkeypatch.setenv("GX_TEST_GENERIC_SQL_AUTOCOMMIT", "1")

        config = GenericSQLDatasourceTestConfig(connection_string="sqlite:///:memory:")
        # The config's own field is untouched by the environment, so its declaration - read on
        # its own, with no batch setup involved - still reports the explicit-commit default.
        assert config.autocommit is False
        assert config.backend_spec.transaction_mode == TransactionMode.EXPLICIT_COMMIT

        batch_setup = GenericSQLBatchTestSetup(
            config=config,
            data=pd.DataFrame({"a": [1]}),
            extra_data={},
            context=cast("AbstractDataContext", object()),
        )

        # Once a batch setup exists for that same config, the environment variable it read at
        # construction takes effect.
        assert batch_setup.backend_spec.transaction_mode == TransactionMode.AUTOCOMMIT

    def test_env_var_unset_leaves_explicit_commit_in_place(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Clear the variable rather than assuming it is unset: exporting it is the escape
        # hatch's own documented usage, so a developer running that way would otherwise turn
        # this negative control red for a reason that has nothing to do with what it asserts.
        monkeypatch.delenv("GX_TEST_GENERIC_SQL_AUTOCOMMIT", raising=False)
        from typing import cast

        import pandas as pd

        from tests.integration.test_utils.data_source_config.backend_spec import TransactionMode
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLBatchTestSetup,
            GenericSQLDatasourceTestConfig,
        )

        config = GenericSQLDatasourceTestConfig(connection_string="sqlite:///:memory:")
        batch_setup = GenericSQLBatchTestSetup(
            config=config,
            data=pd.DataFrame({"a": [1]}),
            extra_data={},
            context=cast("AbstractDataContext", object()),
        )

        assert batch_setup.backend_spec.transaction_mode == TransactionMode.EXPLICIT_COMMIT


class TestGenericSqlEscapeHatchHashRegression:
    """Regression coverage for a trap in re-decorating a `SqlDatasourceTestConfig` subclass with
    a bare `@dataclass(frozen=True)`: doing so silently regenerates `__eq__`/`__hash__`,
    discarding the hand-written `__hash__` that reduces `extra_column_types` to a hashable tuple
    before hashing it. The generated replacement hashes the raw `dict` value instead, which
    raises unconditionally - even for a config with no `extra_column_types` at all, since the
    empty-dict default is still a `dict`. This has no test-suite-visible symptom (nothing calls
    `hash()` on a config directly in the ordinary suite), which is exactly why it must be pinned
    here rather than left to be noticed by whatever else happens to depend on it.
    """

    def test_hash_does_not_raise_on_a_default_instance(self) -> None:
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        hash(GenericSQLDatasourceTestConfig())  # must not raise TypeError: unhashable type: dict

    def test_hash_does_not_raise_with_non_empty_extra_column_types(self) -> None:
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        config = GenericSQLDatasourceTestConfig(extra_column_types={"other_table": {"col": str}})

        hash(config)  # must not raise TypeError: unhashable type: dict

    def test_eq_and_hash_resolve_to_the_shared_base_implementation(self) -> None:
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLDatasourceTestConfig,
        )

        assert (
            GenericSQLDatasourceTestConfig.__eq__.__qualname__
            == DataSourceTestConfig.__eq__.__qualname__
        )
        assert (
            GenericSQLDatasourceTestConfig.__hash__.__qualname__
            == DataSourceTestConfig.__hash__.__qualname__
        )


class TestGenericSqlEscapeHatchPublicNames:
    """The escape hatch is imported by name from several call sites across the suite; this pins
    that both names used elsewhere in the repo still resolve after the base class changes.
    """

    def test_config_and_batch_setup_classes_are_still_importable_and_constructible(self) -> None:
        from tests.integration.test_utils.data_source_config.generic_sql import (
            GenericSQLBatchTestSetup,
            GenericSQLDatasourceTestConfig,
        )

        config = GenericSQLDatasourceTestConfig(connection_string="sqlite:///:memory:")

        assert config.label == "generic_sql"
        assert config.pytest_mark == pytest.mark.generic_sql
        assert GenericSQLBatchTestSetup is not None


class TestRegisteredBackendsKeepTheInheritedHash:
    def test_no_registered_backend_regenerated_eq_or_hash(self) -> None:
        """Every registered config must inherit `DataSourceTestConfig`'s `__eq__`/`__hash__`.

        Those are hand-written to reduce `extra_column_types` to a hashable tuple first. A config
        re-decorated with a bare `@dataclass(frozen=True)` silently regenerates both, and the
        generated `__hash__` hashes that raw `dict` and raises `TypeError` on every instance.

        This is checked here rather than in `__init_subclass__` because a class decorator runs
        *after* class creation: `__init_subclass__` observes the class before `@dataclass` has
        replaced anything, so it cannot see the regeneration it would be trying to prevent.

        The failure this guards against costs session time rather than turning a test red — a
        config that cannot be hashed, or that hashes inconsistently, degrades the batch-setup
        cache instead of failing — which is why it needs a mechanical check rather than a
        convention.
        """

        # Walks subclasses rather than the registry: this module's autouse fixture wraps every
        # test in the isolation seam, which clears the registry, so iterating it here would
        # examine nothing and pass vacuously. Subclasses also reach configs that are declared
        # but deliberately unregistered.
        def _descendants(cls: type) -> Iterator[type]:
            for sub in cls.__subclasses__():
                yield sub
                yield from _descendants(sub)

        checked = [
            c for c in _descendants(SqlDatasourceTestConfig) if not c.__name__.startswith("_")
        ]
        assert checked, "no concrete SQL config subclasses were found to check"

        for config_class in checked:
            assert config_class.__eq__ is DataSourceTestConfig.__eq__, (
                f"{config_class.__name__} regenerated __eq__; a subclass re-decorated with "
                f"@dataclass must pass eq=False"
            )
            assert config_class.__hash__ is DataSourceTestConfig.__hash__, (
                f"{config_class.__name__} regenerated __hash__; a subclass re-decorated with "
                f"@dataclass must pass eq=False"
            )
            hash(config_class())  # a regenerated hash raises TypeError here


class TestStandardDataSourceListsMatchPreChangeMembership:
    """Regression pin for the four standard data-source lists now defined once in `tiers.py`.

    Every literal below is transcribed from the two metrics conftest modules exactly as they
    existed before those lists gained a single shared definition, not derived from the module
    under test — so a mistake in the derivation shows up as a mismatch here rather than agreeing
    with itself. `PANDAS_DATA_SOURCES` is deliberately not alphabetical: the filesystem CSV
    config is listed before the DataFrame config, and that order is preserved on purpose.

    The four constants imported above are captured at module-import time, before any test in this
    module runs. That matters because this module's `_snapshot_registry` fixture clears the
    registry around every test: asserting against those already-built module-level objects, or
    reading `PANDAS_DATA_SOURCES` and `SPARK_DATA_SOURCES` (which never touch the registry) is
    safe, while re-deriving `SQL_DATA_SOURCES` from the registry *inside* a test body would
    observe the isolation seam's emptied registry and pass vacuously.
    """

    def test_pandas_data_sources_match_pre_change_membership_and_order(self) -> None:
        assert [
            PandasFilesystemCsvDatasourceTestConfig(),
            PandasDataFrameDatasourceTestConfig(),
        ] == PANDAS_DATA_SOURCES

    def test_spark_data_sources_match_pre_change_membership_and_order(self) -> None:
        assert [
            SparkFilesystemCsvDatasourceTestConfig(),
        ] == SPARK_DATA_SOURCES

    def test_sql_data_sources_match_pre_change_membership_and_order(self) -> None:
        assert [
            BigQueryDatasourceTestConfig(),
            DatabricksDatasourceTestConfig(),
            PostgreSQLDatasourceTestConfig(),
            SnowflakeDatasourceTestConfig(),
            SqliteDatasourceTestConfig(),
        ] == SQL_DATA_SOURCES

    def test_all_data_sources_match_pre_change_membership_and_order(self) -> None:
        assert [
            PandasFilesystemCsvDatasourceTestConfig(),
            PandasDataFrameDatasourceTestConfig(),
            SparkFilesystemCsvDatasourceTestConfig(),
            BigQueryDatasourceTestConfig(),
            DatabricksDatasourceTestConfig(),
            PostgreSQLDatasourceTestConfig(),
            SnowflakeDatasourceTestConfig(),
            SqliteDatasourceTestConfig(),
        ] == ALL_DATA_SOURCES


class TestCuratedSqlDataSourcesEqualsSingleStoreAndTrino:
    """Regression pin for the curated tier's members, in label order.

    `CURATED_SQL_DATA_SOURCES` was empty until a backend declared curated-tier membership, so
    every assertion involving it was vacuously true (empty equals empty). SingleStore was the
    first backend to join that tier, and Trino is the second — both are what make this pin
    non-vacuous: it fails on a curated-tier backend registering without also joining this
    literal, and fails just as loudly on the reverse — a config landing in this literal without
    the corresponding registration.

    `CURATED_SQL_DATA_SOURCES` is imported at this module's own import time (see the module
    docstring on `TestStandardDataSourceListsMatchPreChangeMembership` above for why that
    matters): it is safe to assert against directly here, unlike a call-time re-derivation from
    the registry, which this module's `_snapshot_registry` autouse fixture would observe as
    empty.
    """

    def test_curated_sql_data_sources_equals_singlestore_and_trino_in_label_order(self) -> None:
        from tests.integration.test_utils.data_source_config.trino import (
            TrinoDatasourceTestConfig,
        )

        assert [
            SingleStoreDatasourceTestConfig(),
            TrinoDatasourceTestConfig(),
        ] == CURATED_SQL_DATA_SOURCES


class TestMetricsConftestsReexportTheSharedDefinition:
    """Both metrics conftest modules must expose the exact same list objects `tiers.py` builds,
    not equal-but-separate copies: an equal-but-separate list would let the two drift again the
    next time someone edits one and not the other, which is the failure mode this whole change
    removes.
    """

    def test_both_conftests_expose_objects_identical_to_the_shared_definition(self) -> None:
        import tests.integration.metrics.conftest as integration_metrics_conftest
        import tests.metrics.conftest as metrics_conftest

        assert metrics_conftest.PANDAS_DATA_SOURCES is PANDAS_DATA_SOURCES
        assert metrics_conftest.SPARK_DATA_SOURCES is SPARK_DATA_SOURCES
        assert metrics_conftest.SQL_DATA_SOURCES is SQL_DATA_SOURCES
        assert metrics_conftest.ALL_DATA_SOURCES is ALL_DATA_SOURCES

        assert integration_metrics_conftest.PANDAS_DATA_SOURCES is PANDAS_DATA_SOURCES
        assert integration_metrics_conftest.SPARK_DATA_SOURCES is SPARK_DATA_SOURCES
        assert integration_metrics_conftest.SQL_DATA_SOURCES is SQL_DATA_SOURCES
        assert integration_metrics_conftest.ALL_DATA_SOURCES is ALL_DATA_SOURCES


# Captured at this module's own import time — after the `tests.integration.test_utils.
# data_source_config` import above has already run that package's `__init__`, which imports every
# backend module and only then imports `tiers`, and before any test in this module runs (in
# particular, before this module's own `_snapshot_registry` autouse fixture ever clears the
# registry). `tiers.py` builds `SQL_DATA_SOURCES` and `CURATED_SQL_DATA_SOURCES` once, at *its*
# import time, from whatever the registry holds at that moment. If some backend module were
# imported after `tiers` instead of before it, that backend would finish registering only once
# this module's own top-level import statement reaches it — later than `tiers` already built its
# lists — so it would be absent from both lists even though `sql_backends_for_tier` called here,
# afterward, reports it correctly. Comparing the two below is what turns that ordering accident
# into a failing test instead of a silent gap: the repo's own import-sorter routinely places a new
# backend module's import after `tiers`'s for any module name that sorts alphabetically later, and
# nothing else in this suite would catch the result.
_REGISTERED_STANDARD_SQL = tuple(sql_backends_for_tier(BackendTier.STANDARD_SQL))
_REGISTERED_CURATED_SQL = tuple(sql_backends_for_tier(BackendTier.CURATED_SQL))

# Also captured here, at this module's own import time and for the same reason as the two tuples
# above: this module's `_snapshot_registry` autouse fixture clears the registry around every test,
# so a test body calling `iter_sql_backends()` directly would iterate nothing and pass vacuously.
# Unlike the two tuples above, this one is not sensitive to import order relative to `tiers.py` -
# it is the whole registered set, not a tier-filtered derivation of it - but it still has to be
# read before any test runs, hence the same module-scope placement.
_REGISTERED_SQL_BACKENDS: Tuple[type, ...] = tuple(iter_sql_backends())


class TestRegisteredSqlBackendsEqualTheTenInLabelOrder:
    """Pins the registry itself: every registered SQL backend, named individually, in label order.

    This is an *equality* assertion against an *ordered* literal naming every registered class -
    not a subset check, not a membership check, not a count. That shape is what makes registering
    an eleventh backend without extending this literal fail immediately: "register the config" and
    "extend this literal" become one change with a single, same-change failure signal, rather than
    a widening nobody notices until something downstream quietly starts seeing one more backend
    than it expected. A subset or count check would let a new registration pass silently here,
    which defeats the point, so neither is an acceptable substitute for the other.

    This module runs in a lane that installs no SQL dialect driver at all, and importing this
    module imports the whole harness package first, which in turn imports every backend module -
    each one registering itself as a side effect of being imported. An equality assertion over all
    ten registered classes therefore runs only in a process where every backend module imported
    successfully with every dialect driver absent.

    Be precise about which half of that each mechanism carries. A backend module that fails to
    import takes the whole package down with it, so every test here dies at collection - the
    import statement is what proves importability, not this assertion. What this assertion adds
    is that all ten modules actually *registered*: importing a module and registering from it
    are separate events, and only the second is observable here. Weakening this to a subset or
    count check would discard exactly that, letting a backend that imported but never enrolled
    itself pass unnoticed.

    Distinct from its neighbours: two test classes earlier in this module prove label ordering for
    two named subsets of backends (the ones verifiable without external credentials, and the ones
    gated on them), and another test elsewhere in this module pins the curated tier's one member.
    This one pins the full registered set - every backend that exists, not a subset of them - which
    is why it, and not either of those, is the assertion that fails when a new backend is
    registered without a matching update here.
    """

    def test_registered_backends_equal_the_ten_in_label_order(self) -> None:
        from tests.integration.test_utils.data_source_config.mysql import (
            MySQLDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.redshift import (
            RedshiftDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.sql_server import (
            SQLServerDatasourceTestConfig,
        )
        from tests.integration.test_utils.data_source_config.trino import (
            TrinoDatasourceTestConfig,
        )

        assert (
            BigQueryDatasourceTestConfig,  # big-query
            DatabricksDatasourceTestConfig,  # databricks
            SQLServerDatasourceTestConfig,  # mssql
            MySQLDatasourceTestConfig,  # mysql
            PostgreSQLDatasourceTestConfig,  # postgresql
            RedshiftDatasourceTestConfig,  # redshift
            SingleStoreDatasourceTestConfig,  # singlestore
            SnowflakeDatasourceTestConfig,  # snowflake
            SqliteDatasourceTestConfig,  # sqlite
            TrinoDatasourceTestConfig,  # trino
        ) == _REGISTERED_SQL_BACKENDS


class TestDerivedSqlListsReachEveryRegisteredBackend:
    """Guards `tiers.py`'s derived lists against a backend that is declared and registered but
    never reaches `SQL_DATA_SOURCES` or `CURATED_SQL_DATA_SOURCES`, because its own module was
    imported after `tiers`'s in this package's `__init__.py`. Both derived lists are built once,
    at `tiers.py`'s own import time; a backend that registers later is invisible to the
    already-built list even though the registry itself reports it correctly from then on, since
    `iter_sql_backends`/`sql_backends_for_tier` re-read the live registry on every call. This
    covers both SQL tiers, not just the standard one, since both lists are built the same way and
    are equally exposed to the same import-order accident.
    """

    def test_standard_sql_data_sources_includes_every_registered_standard_backend(self) -> None:
        assert [type(config) for config in SQL_DATA_SOURCES] == list(_REGISTERED_STANDARD_SQL)

    def test_curated_sql_data_sources_includes_every_registered_curated_backend(self) -> None:
        assert [type(config) for config in CURATED_SQL_DATA_SOURCES] == list(
            _REGISTERED_CURATED_SQL
        )


class TestRegisteredBackendDeclarationsSurviveAnAbsentDialectPackage:
    """This whole module runs in a lane that installs no third-party SQL dialect driver (no
    `pymysql`, no `psycopg2`, no Snowflake connector, and so on) - the same lane the registered-
    set membership pins above already run in. Those pins prove the package-level import succeeds
    with every dialect absent, since importing this module imports every backend module first;
    this test makes the *reason* that matters explicit rather than leaving it implicit in a pin
    whose primary purpose reads as something else.

    It catches a backend that reaches for its dialect driver at module scope without an import
    guard - which would already fail collection of this whole module - and, independently, a
    declared field whose value is only unsafe to touch once the instance exists (for example a
    property that dereferences the driver lazily instead of at class-body evaluation time, which
    an import failure alone would not catch). Instantiating with no arguments and reading every
    field is what exercises that second case; the table-schema-item field is checked for shape
    only; calling it is exactly the operation that would need the driver, so this test never does.

    What this deliberately does not cover: the *contents* of a `column_type_overrides` mapping
    built at module scope behind an import guard. That is a permitted shape for a backend whose
    override values come from its own driver - the same source line yields a populated mapping
    where the driver is installed and an empty one where it is not. Because no driver is installed
    in this lane, reading *such a mapping* here always observes its empty variant, which is the
    correct, intended behavior for *this* lane and says nothing about what it holds in a lane
    where the driver is present. An assertion pinning override contents belongs under that
    backend's own marker, in the lane that installs its driver.

    That scoping matters: it is a claim about the guarded shape, not about the field. A backend
    whose overrides come from core SQLAlchemy rather than from a driver declares the same mapping
    in every lane, so its entries are visible here too.
    """

    def test_no_argument_construction_and_full_field_read_raise_nothing(self) -> None:
        assert _REGISTERED_SQL_BACKENDS, "no SQL backends were registered to check"

        for config_class in _REGISTERED_SQL_BACKENDS:
            config = config_class()  # no arguments
            spec = config.backend_spec

            for declared_field in fields(spec):
                getattr(spec, declared_field.name)  # every field; must not raise

            # Checked for shape only. Calling it is exactly the operation that would require the
            # driver this lane does not install, so it is never invoked here.
            assert spec.table_schema_items is None or callable(spec.table_schema_items)
