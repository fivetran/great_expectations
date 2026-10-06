"""The public tier taxonomy: which declarations satisfy which criterion, and the tier each
combination of criteria yields.

Expected values are written out by hand. Deriving them with the logic under test could not
fail.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from enum import Enum
from itertools import chain, combinations
from typing import Any, FrozenSet

import pytest

from tests.compatibility_reference import compatibility_reference_table as table
from tests.compatibility_reference import upstream_declarations
from tests.compatibility_reference.compatibility_reference_table import (
    CRITERIA,
    PublicTier,
    criteria_met_by,
    tier_for,
)
from tests.compatibility_reference.upstream_declarations import SupportTier

pytestmark = pytest.mark.project

GALLERY = "gallery"
SUITE = "expectation_suite"
API = "datasource_api"

# Every subset of the three criteria, with the tier it must yield. Written out in full so a
# reader checks each row against the stated rule, not against code.
EXPECTED_TIER_BY_COMBINATION = {
    frozenset(): PublicTier.BEST_EFFORT,
    frozenset({API}): PublicTier.BEST_EFFORT,
    frozenset({SUITE}): PublicTier.TESTED,
    frozenset({SUITE, API}): PublicTier.TESTED,
    frozenset({GALLERY}): PublicTier.TESTED,
    frozenset({GALLERY, SUITE}): PublicTier.TESTED,
    frozenset({GALLERY, API}): PublicTier.FULLY_SUPPORTED,
    frozenset({GALLERY, SUITE, API}): PublicTier.FULLY_SUPPORTED,
}


def _powerset(keys):
    items = sorted(keys)
    return [
        frozenset(subset)
        for subset in chain.from_iterable(combinations(items, n) for n in range(len(items) + 1))
    ]


def _name(combination: FrozenSet[str]) -> str:
    return "+".join(sorted(combination)) or "nothing"


def test_criteria_are_the_three_the_expected_table_covers():
    assert [criterion.key for criterion in CRITERIA] == [GALLERY, SUITE, API]


def test_expected_table_covers_every_subset_of_the_criteria():
    keys = {criterion.key for criterion in CRITERIA}
    assert set(EXPECTED_TIER_BY_COMBINATION) == set(_powerset(keys))
    assert len(EXPECTED_TIER_BY_COMBINATION) == 8


@pytest.mark.parametrize(
    "combination",
    list(EXPECTED_TIER_BY_COMBINATION),
    ids=[_name(c) for c in EXPECTED_TIER_BY_COMBINATION],
)
def test_tier_for_each_combination_of_criteria(combination):
    assert tier_for(combination) is EXPECTED_TIER_BY_COMBINATION[combination]


def test_datasource_api_alone_stays_in_the_lowest_tier_while_displaying_the_criterion():
    met = criteria_met_by({SupportTier.FLUENT_API})
    assert met == frozenset({API})
    assert tier_for(met) is PublicTier.BEST_EFFORT


def test_full_gallery_without_the_datasource_api_resolves_to_the_middle_tier():
    met = criteria_met_by({SupportTier.GALLERY})
    assert met == frozenset({GALLERY})
    assert tier_for(met) is PublicTier.TESTED


def test_each_declaration_satisfies_exactly_the_criteria_the_table_names():
    expected = {
        SupportTier.GALLERY: frozenset({GALLERY}),
        SupportTier.CANONICAL_EXPECTATIONS: frozenset({SUITE}),
        SupportTier.CURATED_SQL: frozenset({SUITE}),
        SupportTier.FLUENT_API: frozenset({API}),
    }
    assert set(expected) == set(SupportTier)
    for declaration, criteria in expected.items():
        assert criteria_met_by({declaration}) == criteria


def test_either_expectation_suite_declaration_alone_satisfies_the_suite_criterion():
    for declaration in (SupportTier.CANONICAL_EXPECTATIONS, SupportTier.CURATED_SQL):
        met = criteria_met_by({declaration})
        assert met == frozenset({SUITE})
        assert tier_for(met) is PublicTier.TESTED


def test_curated_suite_without_the_canonical_suite_reaches_the_top_tier():
    met = criteria_met_by({SupportTier.CURATED_SQL, SupportTier.FLUENT_API, SupportTier.GALLERY})
    assert met == frozenset({GALLERY, SUITE, API})
    assert tier_for(met) is PublicTier.FULLY_SUPPORTED


def test_no_declarations_meet_no_criteria():
    assert criteria_met_by(set()) == frozenset()


def test_a_declaration_the_table_does_not_name_leaves_the_result_unchanged(monkeypatch):
    # Simulate the enumeration gaining a member the table does not name: un-name a real member
    # from every criterion, then hold it alongside others.
    unnamed = SupportTier.FLUENT_API
    monkeypatch.setattr(
        table,
        "CRITERIA",
        tuple(
            replace(criterion, declarations=criterion.declarations - {unnamed})
            for criterion in table.CRITERIA
        ),
    )
    base = {SupportTier.GALLERY, SupportTier.CURATED_SQL}
    without = criteria_met_by(base)
    assert without == frozenset({GALLERY, SUITE})
    assert criteria_met_by(base | {unnamed}) == without
    assert tier_for(criteria_met_by(base | {unnamed})) is tier_for(without)
    assert tier_for(without) is PublicTier.TESTED
    assert criteria_met_by({unnamed}) == frozenset()
    assert tier_for(criteria_met_by({unnamed})) is PublicTier.BEST_EFFORT


def test_an_enumeration_member_added_before_the_table_loads_leaves_results_unchanged(
    monkeypatch: pytest.MonkeyPatch,
):
    # A member present when the module is first imported can be captured in import-time state
    # that patching the loaded module afterwards never reaches. Model that: extend the enumeration,
    # then execute a fresh copy of the module from its own source so it loads against the
    # extended enumeration.
    make_enum: Any = Enum  # members are computed, which the static enum check cannot follow
    extended: Any = make_enum(
        "SupportTier",
        [(member.name, member.value) for member in SupportTier] + [("NEWLY_ADDED", "newly_added")],
    )
    monkeypatch.setattr(upstream_declarations, "SupportTier", extended)
    module_name = "fresh_table_with_an_added_enumeration_member"
    spec = importlib.util.spec_from_file_location(module_name, table.__file__)
    assert spec is not None and spec.loader is not None
    fresh = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, fresh)
    spec.loader.exec_module(fresh)

    base = {extended.GALLERY, extended.CURATED_SQL, extended.FLUENT_API}
    added = extended.NEWLY_ADDED
    without = fresh.criteria_met_by(base)
    assert without == frozenset({GALLERY, SUITE, API})
    assert fresh.criteria_met_by(base | {added}) == without
    assert fresh.tier_for(fresh.criteria_met_by(base | {added})) is fresh.tier_for(without)
    assert fresh.criteria_met_by({added}) == frozenset()
    assert fresh.tier_for(fresh.criteria_met_by({added})).name == PublicTier.BEST_EFFORT.name


def test_a_criterion_key_the_table_does_not_name_does_not_raise_or_lift():
    assert tier_for(frozenset({"unplanned"})) is PublicTier.BEST_EFFORT
    assert tier_for(frozenset({"unplanned", GALLERY})) is PublicTier.TESTED


def test_tier_names_do_not_reuse_declaration_names_or_assert_authorship():
    values = {tier.value for tier in PublicTier}
    assert values == {"Fully supported", "Tested", "Best effort"}
    declaration_names = {m.name.lower().replace("_", " ") for m in SupportTier} | {
        m.value.replace("_", " ") for m in SupportTier
    }
    assert not {v.lower() for v in values} & declaration_names


def test_criterion_labels_are_the_public_phrases():
    assert [criterion.label for criterion in CRITERIA] == [
        "Every shipped expectation",
        "Expectation suite",
        "Datasource API contract",
    ]
