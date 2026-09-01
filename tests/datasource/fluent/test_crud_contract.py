"""Tests over the CRUD contract's vocabulary, parameter table, and the contract cases
themselves.

The accessor tests below exercise only the accessors declared in ``crud_contract.py``: the
case-key vocabulary, the lookup that turns an unknown type into an actionable failure, the
exclusion resolvers, and the covered-type set.

The ``TestFluentDatasourceCrudContract`` class runs the contract's create-family cases
against every registered fluent datasource type, with connection testing neutralized for the
duration of each case. Neutralization is deliberate: a passing case in that class asserts
that the create, duplicate-rejection and create-or-update behavior described by the contract
holds for that type, and asserts nothing about whether any real service backing that type is
reachable. The completeness guards over the live registry belong to another module.
"""

from __future__ import annotations

import pathlib
import types
import uuid
from typing import TYPE_CHECKING, Callable, List, Mapping

import pytest

import great_expectations as gx
import great_expectations.exceptions as gx_exceptions
from great_expectations.core.yaml_handler import YAMLHandler
from great_expectations.datasource.fluent.sources import DataSourceManager
from tests.datasource.fluent.crud_contract import (
    CONTRACT_CASE_KEYS,
    CONTRACT_PARAMETERS,
    CREATE_OR_UPDATE_PERSISTS_ONE_ENTRY,
    CREATE_OR_UPDATE_REPLACES_WHEN_PRESENT,
    OVERLAY_DEPENDENT_CASE_KEYS,
    UPDATE_REJECTS_ABSENT_NAME,
    UPDATE_REPLACES_CONFIGURATION,
    case_exclusions_by_type,
    contract_parameters_for,
    covered_fluent_types,
    exclusion_reason,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Datasource


@pytest.mark.unit
def test_contract_case_keys_has_eight_entries() -> None:
    assert len(CONTRACT_CASE_KEYS) == 8
    assert all(isinstance(key, str) for key in CONTRACT_CASE_KEYS)


@pytest.mark.unit
def test_overlay_dependent_case_keys_is_a_subset_of_contract_case_keys() -> None:
    assert OVERLAY_DEPENDENT_CASE_KEYS <= CONTRACT_CASE_KEYS
    assert {
        UPDATE_REPLACES_CONFIGURATION,
        CREATE_OR_UPDATE_REPLACES_WHEN_PRESENT,
        CREATE_OR_UPDATE_PERSISTS_ONE_ENTRY,
    } == OVERLAY_DEPENDENT_CASE_KEYS


@pytest.mark.unit
def test_covered_fluent_types_matches_the_table_keys() -> None:
    assert covered_fluent_types() == frozenset(CONTRACT_PARAMETERS.keys())


@pytest.mark.unit
def test_covered_fluent_types_has_twenty_six_entries() -> None:
    assert len(covered_fluent_types()) == 26


@pytest.mark.unit
def test_contract_parameters_for_known_type_returns_the_table_entry() -> None:
    parameters = contract_parameters_for("postgres")
    assert parameters is CONTRACT_PARAMETERS["postgres"]


@pytest.mark.unit
def test_contract_parameters_for_unknown_type_names_the_type_and_the_module() -> None:
    with pytest.raises(KeyError) as excinfo:
        contract_parameters_for("not_a_real_fluent_type")

    message = str(excinfo.value)
    assert "not_a_real_fluent_type" in message
    assert "crud_contract.py" in message
    assert "CONTRACT_PARAMETERS" in message
    assert "creation_arguments" in message
    assert "update_overlay" in message
    assert "case_exclusions" in message


@pytest.mark.unit
def test_exclusion_reason_is_none_for_a_case_the_type_runs() -> None:
    assert exclusion_reason("postgres", UPDATE_REPLACES_CONFIGURATION) is None


@pytest.mark.unit
def test_exclusion_reason_returns_the_declared_reason() -> None:
    reason = exclusion_reason("pandas", UPDATE_REPLACES_CONFIGURATION)
    assert reason is not None
    assert isinstance(reason, str)
    assert reason != ""


@pytest.mark.unit
def test_pandas_excludes_exactly_the_overlay_dependent_cases() -> None:
    reasons = CONTRACT_PARAMETERS["pandas"].case_exclusions
    assert set(reasons.keys()) == OVERLAY_DEPENDENT_CASE_KEYS
    assert all(reason for reason in reasons.values())


@pytest.mark.unit
def test_pandas_has_no_update_overlay() -> None:
    assert CONTRACT_PARAMETERS["pandas"].update_overlay is None


@pytest.mark.unit
def test_no_type_is_excluded_from_every_case() -> None:
    for fluent_type in covered_fluent_types():
        excluded = set(CONTRACT_PARAMETERS[fluent_type].case_exclusions.keys())
        assert excluded != CONTRACT_CASE_KEYS, (
            f"{fluent_type!r} is excluded from every case; it must not read as covered"
        )


@pytest.mark.unit
def test_case_exclusions_by_type_returns_the_whole_declared_mapping() -> None:
    mapping = case_exclusions_by_type()
    assert set(mapping.keys()) == covered_fluent_types()
    assert mapping["pandas"] == {
        UPDATE_REPLACES_CONFIGURATION: exclusion_reason("pandas", UPDATE_REPLACES_CONFIGURATION),
        CREATE_OR_UPDATE_REPLACES_WHEN_PRESENT: exclusion_reason(
            "pandas", CREATE_OR_UPDATE_REPLACES_WHEN_PRESENT
        ),
        CREATE_OR_UPDATE_PERSISTS_ONE_ENTRY: exclusion_reason(
            "pandas", CREATE_OR_UPDATE_PERSISTS_ONE_ENTRY
        ),
    }
    assert mapping["postgres"] == {}


@pytest.mark.unit
def test_case_exclusions_by_type_is_immutable() -> None:
    mapping = case_exclusions_by_type()
    with pytest.raises(TypeError):
        mapping["pandas"] = {}  # type: ignore[index]

    inner = mapping["postgres"]
    with pytest.raises(TypeError):
        inner["create"] = "not allowed"  # type: ignore[index]


@pytest.mark.unit
def test_per_type_case_exclusions_is_immutable() -> None:
    # The per-type accessor must be just as immutable as the bulk one: a caller reaching
    # contract_parameters_for(...).case_exclusions directly gets a live reference to module
    # state one call away from the bulk accessor, and mutating it would silently and
    # permanently corrupt CONTRACT_PARAMETERS for every later reader.
    exclusions = contract_parameters_for("postgres").case_exclusions
    assert isinstance(exclusions, types.MappingProxyType)
    with pytest.raises(TypeError):
        exclusions["injected"] = "boom"  # type: ignore[index]

    assert "injected" not in contract_parameters_for("postgres").case_exclusions


@pytest.mark.unit
def test_contract_parameters_table_rejects_insertion() -> None:
    # CONTRACT_PARAMETERS itself must not be a plain dict a caller can grow or shrink; doing
    # so would move covered_fluent_types() away from the live registry without any of this
    # module's own guards noticing.
    assert isinstance(CONTRACT_PARAMETERS, types.MappingProxyType)
    with pytest.raises(TypeError):
        CONTRACT_PARAMETERS["injected"] = contract_parameters_for("postgres")  # type: ignore[index]

    assert "injected" not in covered_fluent_types()
    assert len(covered_fluent_types()) == 26


@pytest.mark.unit
def test_creation_arguments_are_produced_by_a_callable_over_a_scratch_directory(
    tmp_path: pathlib.Path,
) -> None:
    for fluent_type in covered_fluent_types():
        parameters = contract_parameters_for(fluent_type)
        arguments = parameters.creation_arguments(tmp_path)
        assert isinstance(arguments, (dict, types.MappingProxyType))
        if parameters.update_overlay is not None:
            overlay = parameters.update_overlay(tmp_path)
            assert isinstance(overlay, (dict, types.MappingProxyType))


# ---------------------------------------------------------------------------
# Connection-testing neutralization
# ---------------------------------------------------------------------------


@pytest.fixture
def neutralized_connection_testing(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str], type]:
    """Return a callable that neutralizes connection testing for one fluent type.

    Calling the returned function with a registered fluent type name patches
    ``test_connection`` on the concrete class the registry resolves for that type, then
    returns that class. Patching a shared base class does not reach every type: several
    concrete classes override ``test_connection`` themselves, so a base-class patch leaves
    those types making a real connection attempt. ``monkeypatch`` restores the original
    method for every patched class when the test ends, so no case leaves a lasting change to
    any datasource class.

    This neutralization is deliberate, not incidental. A case built on top of this fixture
    asserts the CRUD contract for the patched type. It never asserts, and cannot assert, that
    the type can actually reach the service it represents.
    """

    def _neutralize(fluent_type: str) -> type:
        datasource_class = DataSourceManager.type_lookup[fluent_type]

        def _fake_test_connection(self: Datasource, test_assets: bool = True) -> None:
            return None

        monkeypatch.setattr(datasource_class, "test_connection", _fake_test_connection)
        return datasource_class

    return _neutralize


# ---------------------------------------------------------------------------
# The create-family contract cases
# ---------------------------------------------------------------------------


def _registered_fluent_types() -> List[str]:
    """Every registered fluent datasource type name, sorted, read from the live registry.

    Built as a module-level function so a collection-time failure names this module, and so a
    type registered after this suite is written is exercised without editing this list.
    """
    return sorted(name for name in DataSourceManager.type_lookup if isinstance(name, str))


_registered_fluent_type_parameters = pytest.mark.parametrize(
    "fluent_type", _registered_fluent_types(), ids=_registered_fluent_types()
)


def _configuration_of(datasource: Datasource) -> Mapping[str, object]:
    """The full field mapping of a stored datasource, with assets and identity excluded.

    Assets are excluded because none of these cases add one, and comparing the identifier
    separately keeps a case's identifier assertion distinct from its configuration
    assertion rather than folding both into one dict equality.
    """
    return datasource.dict(exclude={"assets", "id"})


@pytest.mark.unit
class TestFluentDatasourceCrudContract:
    """The CRUD contract every registered fluent datasource type satisfies.

    Every case in this class runs with connection testing neutralized for the type under
    test. That neutralization is deliberate: a passing case here is evidence about the
    create, duplicate-rejection and create-or-update behavior the contract describes, and is
    never evidence that the underlying service the type represents can be reached.
    """

    @_registered_fluent_type_parameters
    def test_create_returns_the_stored_datasource(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
    ) -> None:
        datasource_class = neutralized_connection_testing(fluent_type)
        context = gx.get_context(mode="ephemeral")
        name = f"contract-create-{fluent_type}"
        seeded_id = uuid.uuid4()
        arguments = contract_parameters_for(fluent_type).creation_arguments(tmp_path)

        add_method = getattr(context.data_sources, f"add_{fluent_type}")
        created = add_method(name=name, id=seeded_id, **arguments)

        assert isinstance(created, datasource_class)
        assert created.name == name
        assert created.id == seeded_id
        assert context.data_sources.get(name) is created

    @_registered_fluent_type_parameters
    def test_create_rejects_duplicate_name(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
    ) -> None:
        neutralized_connection_testing(fluent_type)
        context = gx.get_context(mode="ephemeral")
        name = f"contract-duplicate-{fluent_type}"
        arguments = contract_parameters_for(fluent_type).creation_arguments(tmp_path)

        add_method = getattr(context.data_sources, f"add_{fluent_type}")
        original = add_method(name=name, id=uuid.uuid4(), **arguments)

        with pytest.raises(gx_exceptions.DataContextError) as excinfo:
            add_method(name=name, id=uuid.uuid4(), **arguments)

        message = str(excinfo.value)
        assert name in message
        assert "already exists" in message
        assert context.data_sources.get(name) is original

    @_registered_fluent_type_parameters
    def test_create_or_update_creates_when_absent(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
    ) -> None:
        datasource_class = neutralized_connection_testing(fluent_type)
        context = gx.get_context(mode="ephemeral")
        name = f"contract-create-or-update-{fluent_type}"
        arguments = contract_parameters_for(fluent_type).creation_arguments(tmp_path)

        add_or_update_method = getattr(context.data_sources, f"add_or_update_{fluent_type}")
        created = add_or_update_method(name=name, id=uuid.uuid4(), **arguments)

        assert isinstance(created, datasource_class)
        assert context.data_sources.get(name) is created

    @_registered_fluent_type_parameters
    def test_update_replaces_configuration(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
    ) -> None:
        reason = exclusion_reason(fluent_type, UPDATE_REPLACES_CONFIGURATION)
        if reason is not None:
            pytest.skip(reason)

        datasource_class = neutralized_connection_testing(fluent_type)
        context = gx.get_context(mode="ephemeral")
        name = f"contract-update-{fluent_type}"
        seeded_id = uuid.uuid4()
        parameters = contract_parameters_for(fluent_type)
        creation_arguments = parameters.creation_arguments(tmp_path)
        overlay_arguments = parameters.update_overlay(tmp_path)  # type: ignore[misc]

        add_method = getattr(context.data_sources, f"add_{fluent_type}")
        created = add_method(name=name, id=seeded_id, **creation_arguments)
        created_configuration = _configuration_of(created)

        update_method = getattr(context.data_sources, f"update_{fluent_type}")
        updated = update_method(name=name, **overlay_arguments)

        assert updated.id == seeded_id
        assert context.data_sources.get(name).id == seeded_id

        stored_configuration = _configuration_of(context.data_sources.get(name))
        expected_configuration = _configuration_of(datasource_class(name=name, **overlay_arguments))
        assert stored_configuration == expected_configuration
        assert stored_configuration != created_configuration

    @_registered_fluent_type_parameters
    def test_update_rejects_absent_name(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
    ) -> None:
        reason = exclusion_reason(fluent_type, UPDATE_REJECTS_ABSENT_NAME)
        if reason is not None:
            pytest.skip(reason)

        neutralized_connection_testing(fluent_type)
        context = gx.get_context(mode="ephemeral")
        name = f"contract-update-absent-{fluent_type}"
        arguments = contract_parameters_for(fluent_type).creation_arguments(tmp_path)

        update_method = getattr(context.data_sources, f"update_{fluent_type}")

        with pytest.raises(ValueError) as excinfo:
            update_method(name=name, **arguments)

        assert name in str(excinfo.value)
        with pytest.raises(KeyError):
            context.data_sources.get(name)

    @_registered_fluent_type_parameters
    def test_create_or_update_replaces_when_present(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
    ) -> None:
        reason = exclusion_reason(fluent_type, CREATE_OR_UPDATE_REPLACES_WHEN_PRESENT)
        if reason is not None:
            pytest.skip(reason)

        datasource_class = neutralized_connection_testing(fluent_type)
        context = gx.get_context(mode="ephemeral")
        name = f"contract-create-or-update-replace-{fluent_type}"
        seeded_id = uuid.uuid4()
        parameters = contract_parameters_for(fluent_type)
        creation_arguments = parameters.creation_arguments(tmp_path)
        overlay_arguments = parameters.update_overlay(tmp_path)  # type: ignore[misc]

        add_method = getattr(context.data_sources, f"add_{fluent_type}")
        created = add_method(name=name, id=seeded_id, **creation_arguments)
        created_configuration = _configuration_of(created)

        add_or_update_method = getattr(context.data_sources, f"add_or_update_{fluent_type}")
        replaced = add_or_update_method(name=name, **overlay_arguments)

        assert replaced.id == seeded_id
        assert context.data_sources.get(name).id == seeded_id

        stored_configuration = _configuration_of(context.data_sources.get(name))
        expected_configuration = _configuration_of(datasource_class(name=name, **overlay_arguments))
        assert stored_configuration == expected_configuration
        assert stored_configuration != created_configuration


# ---------------------------------------------------------------------------
# Persistence round-trip against a file-backed context
# ---------------------------------------------------------------------------


def _fluent_datasources_config(config_file_path: pathlib.Path) -> Mapping[str, object]:
    """The ``fluent_datasources`` mapping as it is actually written to the project config file."""
    yaml_dict = YAMLHandler().load(config_file_path.read_text())
    return yaml_dict.get("fluent_datasources", {})


@pytest.mark.filesystem
class TestFluentDatasourceCrudContractPersistence:
    """The subset of the CRUD contract that only a real, file-backed project can verify.

    These cases reopen the project from a fresh context instance rooted at the same
    directory, rather than reusing the context object that performed the write, so a
    passing case is evidence that the configuration actually reached disk rather than
    evidence about in-process state the two context objects happen to share.

    There is no delete case here. Delete's own persistence is already exercised, against a
    file-backed context reopened from disk the same way this class's cases reopen theirs, by
    tests elsewhere in this suite; a per-type copy of that coverage here would duplicate an
    existing check rather than add signal.
    """

    @_registered_fluent_type_parameters
    def test_configuration_survives_a_fresh_read_from_disk(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
        file_dc_config_dir_init: pathlib.Path,
    ) -> None:
        datasource_class = neutralized_connection_testing(fluent_type)
        writing_context = gx.get_context(context_root_dir=file_dc_config_dir_init, cloud_mode=False)
        name = f"contract-persist-roundtrip-{fluent_type}"
        seeded_id = uuid.uuid4()
        arguments = contract_parameters_for(fluent_type).creation_arguments(tmp_path)

        add_method = getattr(writing_context.data_sources, f"add_{fluent_type}")
        created = add_method(name=name, id=seeded_id, **arguments)
        expected_configuration = _configuration_of(created)

        assert created.assets == []

        config_file_path = pathlib.Path(writing_context.root_directory, writing_context.GX_YML)
        assert name in _fluent_datasources_config(config_file_path)

        # Discard `writing_context` entirely and build a genuinely new context object over
        # the same directory, so the read below can only be satisfied from disk.
        del writing_context
        reread_context = gx.get_context(context_root_dir=file_dc_config_dir_init, cloud_mode=False)

        reread_datasource = reread_context.data_sources.get(name)
        assert isinstance(reread_datasource, datasource_class)
        assert reread_datasource.id == seeded_id
        assert _configuration_of(reread_datasource) == expected_configuration

    @_registered_fluent_type_parameters
    def test_create_then_create_or_update_leaves_exactly_one_persisted_entry(
        self,
        fluent_type: str,
        neutralized_connection_testing: Callable[[str], type],
        tmp_path: pathlib.Path,
        file_dc_config_dir_init: pathlib.Path,
    ) -> None:
        # A count over a mapping keyed by datasource name can never exceed one by
        # construction, so it cannot by itself detect the create-or-update path failing to
        # persist. The case also has to show that the persisted entry is the *replacement*:
        # that only holds if create-or-update's own save actually reached disk, rather than
        # riding on the save the preceding create already performed. A type with no update
        # overlay cannot produce a materially different replacement, so it is excluded here
        # exactly as the in-memory replaces-when-present case excludes it.
        reason = exclusion_reason(fluent_type, CREATE_OR_UPDATE_PERSISTS_ONE_ENTRY)
        if reason is not None:
            pytest.skip(reason)

        datasource_class = neutralized_connection_testing(fluent_type)
        writing_context = gx.get_context(context_root_dir=file_dc_config_dir_init, cloud_mode=False)
        name = f"contract-persist-create-or-update-{fluent_type}"
        parameters = contract_parameters_for(fluent_type)
        creation_arguments = parameters.creation_arguments(tmp_path)
        overlay_arguments = parameters.update_overlay(tmp_path)  # type: ignore[misc]

        add_method = getattr(writing_context.data_sources, f"add_{fluent_type}")
        add_method(name=name, id=uuid.uuid4(), **creation_arguments)

        add_or_update_method = getattr(writing_context.data_sources, f"add_or_update_{fluent_type}")
        add_or_update_method(name=name, id=uuid.uuid4(), **overlay_arguments)

        expected_configuration = _configuration_of(datasource_class(name=name, **overlay_arguments))

        config_file_path = pathlib.Path(writing_context.root_directory, writing_context.GX_YML)
        persisted_datasources = _fluent_datasources_config(config_file_path)
        matching_entries = [
            entry_name for entry_name in persisted_datasources if entry_name == name
        ]
        assert len(matching_entries) == 1

        # Discard `writing_context` and reread from disk, so the assertion below can only be
        # satisfied by create-or-update's own save having reached the file, not by in-process
        # state the two context objects happen to share.
        del writing_context
        reread_context = gx.get_context(context_root_dir=file_dc_config_dir_init, cloud_mode=False)
        reread_datasource = reread_context.data_sources.get(name)
        assert _configuration_of(reread_datasource) == expected_configuration
