from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, List, Mapping, Optional

import pytest

from great_expectations.compatibility.typing_extensions import override
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
