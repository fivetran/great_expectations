"""Accessor-level tests over the CRUD contract's vocabulary and parameter table.

This module exercises only the accessors declared in ``crud_contract.py``: the case-key
vocabulary, the lookup that turns an unknown type into an actionable failure, the exclusion
resolvers, and the covered-type set. The contract cases themselves, and the completeness
guards over the live registry, belong to other modules.
"""

from __future__ import annotations

import pathlib
import types

import pytest

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
