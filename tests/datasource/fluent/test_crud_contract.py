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
from typing import TYPE_CHECKING, Callable, List

import pytest

import great_expectations as gx
import great_expectations.exceptions as gx_exceptions
from great_expectations.datasource.fluent.sources import DataSourceManager
from tests.datasource.fluent.crud_contract import (
    CONTRACT_CASE_KEYS,
    CONTRACT_PARAMETERS,
    CREATE_OR_UPDATE_REPLACES_WHEN_PRESENT,
    OVERLAY_DEPENDENT_CASE_KEYS,
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
def test_pandas_excludes_exactly_the_two_overlay_dependent_cases() -> None:
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
