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
from typing import Any, FrozenSet, Mapping, Optional, Tuple

import pytest

from tests.compatibility_reference import compatibility_reference_table as table
from tests.compatibility_reference import upstream_declarations
from tests.compatibility_reference.compatibility_reference_table import (
    CRITERIA,
    PublicTier,
    PublishedRow,
    assemble_rows,
    criteria_met_by,
    recorded_exclusion_notes,
    tier_for,
    uncovered_connection_paths_note,
)
from tests.compatibility_reference.upstream_declarations import (
    SupportTier,
    UpstreamDeclarationError,
    UpstreamFacts,
    load_upstream_facts,
)
from tests.integration.test_utils.data_source_config import (
    ClickHouseDatasourceTestConfig,
    DataSourceSpec,
    OracleDatasourceTestConfig,
    isolated_registry,
    iter_data_source_specs,
    register_data_source,
)
from tests.integration.test_utils.data_source_config.data_source_spec import (
    CiLaneRef,
    DataSourceProvisioning,
)

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


# ---------------------------------------------------------------------------------------------
# Row assembly
#
# Throwaway records are registered inside the registry's isolation seam, which empties the
# registry on entry. Anything reading the real registry from inside it would see nothing and pass
# vacuously, so the real-registry assertions are made outside it, each beside a throwaway twin.
# ---------------------------------------------------------------------------------------------

LANE = CiLaneRef(workflow_job="marker-tests", marker_token="throwaway")
ORACLE_SPEC = OracleDatasourceTestConfig.DATA_SOURCE_SPEC
CLICKHOUSE_SPEC = ClickHouseDatasourceTestConfig.DATA_SOURCE_SPEC

PANDAS_DESCRIPTION = "in-memory pandas DataFrames"
CSV_DESCRIPTION = "CSV and other files read with pandas"
S3_PANDAS_DESCRIPTION = "Amazon S3 objects read with pandas"
S3_SPARK_DESCRIPTION = "Amazon S3 objects read with Spark"
BOTH_S3 = f"{S3_SPARK_DESCRIPTION} and {S3_PANDAS_DESCRIPTION}"  # sorted by text

ALL_THREE = frozenset(
    {SupportTier.CANONICAL_EXPECTATIONS, SupportTier.FLUENT_API, SupportTier.GALLERY}
)


def _record(
    label: str,
    public_name: str,
    *,
    tiers: FrozenSet[SupportTier] = frozenset(),
    fluent_types: FrozenSet[str] = frozenset({"pandas"}),
    lane: Optional[CiLaneRef] = LANE,
    exclusions: Optional[Mapping[SupportTier, Mapping[str, str]]] = None,
    provisioning: DataSourceProvisioning = DataSourceProvisioning.IN_PROCESS,
    provisioning_note: Optional[str] = None,
) -> DataSourceSpec:
    return DataSourceSpec(
        label=label,
        public_name=public_name,
        provisioning=provisioning,
        provisioning_note=provisioning_note,
        fluent_types=fluent_types,
        marker=label,
        tiers=tiers,
        tier_case_exclusions=exclusions or {},
        ci_lane=lane,
    )


def _facts(
    *specs: DataSourceSpec,
    fluent_exclusions: Optional[Mapping[str, Mapping[str, str]]] = None,
    covered: FrozenSet[str] = frozenset(),
    uncovered_paths: FrozenSet[str] = frozenset(),
) -> UpstreamFacts:
    return UpstreamFacts(
        specs=specs,
        covered_but_unable_to_claim=covered,
        fluent_types_named_by_no_record=uncovered_paths,
        fluent_case_exclusions=fluent_exclusions or {},
    )


def register_real_records_the_loader_checks_against() -> None:
    """Register the two real records whose declarations the loader's own maps are checked against.

    ``TESTED_VERSION_NOTES`` names Oracle, and ``CASE_DESCRIPTIONS`` describes the one case
    only ClickHouse's record excludes. Inside an emptied registry the loader fails on each
    unless its record is present.
    """
    register_data_source(ORACLE_SPEC)
    register_data_source(CLICKHOUSE_SPEC)


def _rows_in_seam(*records: DataSourceSpec) -> Tuple[PublishedRow, ...]:
    """Register the records in an emptied registry and assemble what the loader returns.

    The loader raises about the Oracle version note unless an Oracle record with a lane is
    registered, and about a described case no record excludes unless the one record that
    excludes a case of its own is registered, so both real records go in beside the throwaways.
    """
    with isolated_registry():
        register_real_records_the_loader_checks_against()
        for record in records:
            register_data_source(record)
        # The real fluent suite's recorded exclusions would add notes to any throwaway row that
        # names the `pandas` type; they are asserted on the real row, not on these.
        return assemble_rows(replace(load_upstream_facts(), fluent_case_exclusions={}))


# Descriptions for the case keys the throwaway records below exclude. They are written to sort
# differently from their keys (alpha < beta < mid < zeta, but Z < Y < M < A), so a note that
# ordered by description instead of by key would not match an expected value written by hand.
THROWAWAY_CASE_DESCRIPTIONS = {
    "some_case": "the shared check",
    "a_case": "the first-A check",
    "z_case": "the last-Z check",
    "m_case": "the middle-M check",
    "canonical_case": "the canonical check",
    "curated_case": "the curated check",
    "suite_case": "the suite check",
    "api_case": "the API check",
    "gallery_case": "the gallery check",
    "alpha": "the Z-sorting check",
    "beta": "the Y-sorting check",
    "mid": "the M-sorting check",
    "zeta": "the A-sorting check",
}


@pytest.fixture
def throwaway_case_descriptions(monkeypatch):
    for case, description in THROWAWAY_CASE_DESCRIPTIONS.items():
        monkeypatch.setitem(upstream_declarations.CASE_DESCRIPTIONS, case, description)


WITH_CASE_DESCRIPTIONS = pytest.mark.usefixtures("throwaway_case_descriptions")


def _row(rows: Tuple[PublishedRow, ...], public_name: str) -> PublishedRow:
    matching = [row for row in rows if row.public_name == public_name]
    assert len(matching) == 1, [row.public_name for row in rows]
    return matching[0]


def test_two_records_sharing_a_name_make_one_row_and_a_criterion_one_lacks_is_not_met():
    rows = _rows_in_seam(
        _record(
            "variant-a", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"pandas"})
        ),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.CANONICAL_EXPECTATIONS, SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas_filesystem"}),
        ),
    )
    row = _row(rows, "Throwaway Source")
    assert [spec.label for spec in row.specs] == ["variant-a", "variant-b"]
    assert row.criteria_met == frozenset({SUITE, API})
    assert row.tier is PublicTier.TESTED
    assert row.notes == (f"Every shipped expectation: not met for {CSV_DESCRIPTION}.",)


def test_a_criterion_only_the_union_of_the_records_reaches_is_not_met():
    # Neither record alone reaches the top tier. Pooling their declarations would.
    rows = _rows_in_seam(
        _record(
            "variant-a",
            "Throwaway Source",
            tiers=frozenset({SupportTier.CANONICAL_EXPECTATIONS, SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas"}),
        ),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.GALLERY, SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas_filesystem"}),
        ),
    )
    row = _row(rows, "Throwaway Source")
    assert row.criteria_met == frozenset({API})
    assert row.tier is PublicTier.BEST_EFFORT
    assert row.notes == (
        f"Every shipped expectation: not met for {PANDAS_DESCRIPTION}.",
        f"Expectation suite: not met for {CSV_DESCRIPTION}.",
    )


def test_records_that_agree_produce_no_disagreement_note():
    rows = _rows_in_seam(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"sqlite"})
        ),
    )
    row = _row(rows, "Throwaway Source")
    assert row.criteria_met == frozenset({GALLERY, SUITE, API})
    assert row.tier is PublicTier.FULLY_SUPPORTED
    assert row.notes == ()


def test_a_criterion_no_record_declares_is_unmet_without_a_disagreement_note():
    rows = _rows_in_seam(
        _record("variant-a", "Throwaway Source", tiers=frozenset({SupportTier.FLUENT_API})),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"sqlite"}),
        ),
    )
    row = _row(rows, "Throwaway Source")
    assert row.criteria_met == frozenset({API})
    assert row.notes == ()


def test_a_shortfall_names_the_variant_by_what_it_connects_to_not_by_label_or_type():
    rows = _rows_in_seam(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "internal-label-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas_filesystem"}),
        ),
    )
    (note,) = [n for n in _row(rows, "Throwaway Source").notes if n.startswith("Expectation suite")]
    assert note == f"Expectation suite: not met for {CSV_DESCRIPTION}."
    for internal in ("internal-label-b", "pandas_filesystem"):
        assert internal not in note


def test_a_variant_reached_through_several_types_is_named_by_all_of_them():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas_s3", "spark_s3"}),
        ),
    )
    (row,) = assemble_rows(facts)
    assert row.notes == (
        f"Every shipped expectation: not met for {BOTH_S3}.",
        f"Expectation suite: not met for {BOTH_S3}.",
    )


def test_several_variants_falling_short_are_all_named_in_a_fixed_order():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas_filesystem"}),
        ),
        _record(
            "variant-c",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"sqlite"}),
        ),
    )
    (row,) = assemble_rows(facts)
    assert row.notes == (
        f"Every shipped expectation: not met for {CSV_DESCRIPTION}; SQLite databases.",
        f"Expectation suite: not met for {CSV_DESCRIPTION}; SQLite databases.",
    )


def test_a_shortfall_that_cannot_be_named_for_a_reader_fails_rather_than_printing_an_identifier():
    undescribed = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b", "Throwaway Source", tiers=frozenset(), fluent_types=frozenset({"made_up"})
        ),
    )
    with pytest.raises(UpstreamDeclarationError, match="made_up"):
        assemble_rows(undescribed)
    typeless = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record("variant-b", "Throwaway Source", tiers=frozenset(), fluent_types=frozenset()),
    )
    with pytest.raises(UpstreamDeclarationError, match="variant-b"):
        assemble_rows(typeless)


def test_a_lane_with_no_tier_is_evidence_of_nothing():
    rows = _rows_in_seam(_record("laned", "Throwaway Laned", tiers=frozenset(), lane=LANE))
    row = _row(rows, "Throwaway Laned")
    assert row.specs[0].ci_lane is not None
    assert row.specs[0].tiers == frozenset()
    assert row.criteria_met == frozenset()
    assert row.tier is PublicTier.BEST_EFFORT


def test_the_lane_adds_nothing_to_a_record_that_claims_a_tier():
    laned = _record(
        "laned", "Throwaway Laned", tiers=frozenset({SupportTier.FLUENT_API}), lane=LANE
    )
    (row,) = assemble_rows(_facts(laned))
    assert row.criteria_met == frozenset({API})
    assert row.tier is PublicTier.BEST_EFFORT


def test_the_real_object_stores_have_a_lane_and_no_expectation_suite_and_stay_lowest():
    rows = {row.public_name: row for row in assemble_rows(load_upstream_facts())}
    for name in ("Amazon S3", "Google Cloud Storage"):
        row = rows[name]
        assert all(spec.ci_lane is not None for spec in row.specs)
        assert row.criteria_met == frozenset({API})
        assert row.tier is PublicTier.BEST_EFFORT


def test_the_real_pandas_records_make_one_row_and_agree():
    real = [spec for spec in iter_data_source_specs() if spec.public_name == "Pandas"]
    assert len(real) == 2
    rows = [row for row in assemble_rows(load_upstream_facts()) if row.public_name == "Pandas"]
    assert len(rows) == 1
    assert rows[0].specs == tuple(sorted(real, key=lambda spec: spec.label))
    assert rows[0].tier is PublicTier.FULLY_SUPPORTED
    # The variants agree, so no disagreement note; the one note is the recorded exclusion.
    assert [note for note in rows[0].notes if ": not met for " in note] == []


def test_an_empty_registry_fails_in_row_assembly_rather_than_returning_no_rows():
    with isolated_registry():
        # The loader would stop first, on the Oracle version note, with its own error type.
        with pytest.raises(UpstreamDeclarationError):
            load_upstream_facts()
        # What the loader would hand over for an empty registry, read live from the seam.
        facts = _facts(*iter_data_source_specs())
        assert facts.specs == ()
        with pytest.raises(ValueError, match="yields no record") as raised:
            assemble_rows(facts)
    assert not isinstance(raised.value, UpstreamDeclarationError)


def test_a_record_with_no_public_name_fails_instead_of_being_dropped():
    nameless = _record("nameless", "")
    with isolated_registry():
        # Registration rejects it, so assembly can only meet one built outside the registry.
        with pytest.raises(ValueError, match="empty public data source name"):
            register_data_source(nameless)
    named = _record("a-named", "Throwaway Source", tiers=ALL_THREE)
    for blank in ("", "   "):
        with pytest.raises(ValueError, match=r"'nameless' carries no public name"):
            assemble_rows(_facts(named, _record("nameless", blank)))


def test_a_newly_registered_record_appears_as_a_row_without_any_other_edit():
    before = _rows_in_seam()
    after = _rows_in_seam(_record("fresh", "Entirely New Source", tiers=ALL_THREE))
    assert "Entirely New Source" not in [row.public_name for row in before]
    row = _row(after, "Entirely New Source")
    assert row.public_name == "Entirely New Source"
    assert row.tier is PublicTier.FULLY_SUPPORTED


def test_rows_are_ordered_by_public_name_ignoring_case_not_by_label():
    # The registry orders by label, which here runs opposite to the names; a plain code-point sort
    # of the names would put "Zed" before "alpha2".
    rows = _rows_in_seam(
        _record("a-label", "Zed"),
        _record("b-label", "Alpha"),
        _record("c-label", "beta"),
        _record("d-label", "alpha2"),
    )
    assert [row.public_name for row in rows] == [
        "Alpha",
        "alpha2",
        "beta",
        "ClickHouse",
        "Oracle",
        "Zed",
    ]


def test_the_records_within_a_row_are_ordered_by_label_whatever_order_they_arrive_in():
    facts = _facts(_record("zz", "Throwaway Source"), _record("aa", "Throwaway Source"))
    (row,) = assemble_rows(facts)
    assert [spec.label for spec in row.specs] == ["aa", "zz"]


def test_a_name_missing_from_the_shipped_vocabulary_is_printed_exactly_as_declared():
    (row,) = assemble_rows(_facts(_record("odd", "Odd-Name (beta) v2")))
    assert row.public_name == "Odd-Name (beta) v2"


def test_a_record_that_declares_no_criterion_leaves_every_criterion_unmet_and_is_named_for_each():
    # One record holding nothing must not be dropped from the conjunction: the row is the lowest
    # tier and each criterion its sibling meets reports the empty record as falling short.
    (row,) = assemble_rows(
        _facts(
            _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
            _record(
                "variant-b",
                "Throwaway Source",
                tiers=frozenset(),
                fluent_types=frozenset({"pandas_filesystem"}),
            ),
        )
    )
    assert row.criteria_met == frozenset()
    assert row.criteria_partial == frozenset()
    assert row.tier is PublicTier.BEST_EFFORT
    assert row.notes == (
        f"Every shipped expectation: not met for {CSV_DESCRIPTION}.",
        f"Expectation suite: not met for {CSV_DESCRIPTION}.",
        f"Datasource API contract: not met for {CSV_DESCRIPTION}.",
    )


def test_a_shortfall_naming_the_same_type_as_a_variant_that_meets_it_fails():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"sql"})),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"sql"}),
        ),
    )
    with pytest.raises(UpstreamDeclarationError) as raised:
        assemble_rows(facts)
    assert str(raised.value) == (
        "Records under 'Throwaway Source' disagree about 'Every shipped expectation', but the "
        "record labelled 'variant-b' shares fluent datasource type(s) ['sql'] with a record that "
        "meets it, so no public-facing description distinguishes the variant that falls short "
        "from the ones that do not. Give the records distinct fluent types, or declare the "
        "criterion consistently across them."
    )


def test_a_shortfall_whose_types_overlap_those_of_a_variant_that_meets_it_fails():
    facts = _facts(
        _record(
            "variant-a", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"pandas"})
        ),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas", "pandas_filesystem"}),
        ),
    )
    with pytest.raises(UpstreamDeclarationError) as raised:
        assemble_rows(facts)
    assert str(raised.value) == (
        "Records under 'Throwaway Source' disagree about 'Every shipped expectation', but the "
        "record labelled 'variant-b' shares fluent datasource type(s) ['pandas'] with a record "
        "that meets it, so no public-facing description distinguishes the variant that falls "
        "short from the ones that do not. Give the records distinct fluent types, or declare the "
        "criterion consistently across them."
    )


def _shares_pandas_with_a_variant_that_meets_it(label: str) -> str:
    return (
        "Records under 'Throwaway Source' disagree about 'Every shipped expectation', but the "
        f"record labelled {label!r} shares fluent datasource type(s) ['pandas'] with a record "
        "that meets it, so no public-facing description distinguishes the variant that falls "
        "short from the ones that do not. Give the records distinct fluent types, or declare the "
        "criterion consistently across them."
    )


@pytest.mark.parametrize(
    "ambiguous_label",
    ["variant-a", "variant-b", "variant-d"],
    ids=["first-shortfall", "middle-shortfall", "last-shortfall"],
)
def test_every_variant_that_falls_short_is_checked_for_ambiguity_wherever_it_sorts(
    ambiguous_label: str,
):
    # variant-c meets the criterion through pandas. Three variants fall short; exactly one also
    # declares pandas and the other two declare types variant-c does not. The ambiguous one is
    # placed first, in the middle and last of the shortfalls in label order, so a check that
    # skips any position, or stops at the first shortfall it finds unambiguous, fails a case.
    clean_types = iter([frozenset({"pandas_filesystem"}), frozenset({"sqlite"})])
    records = [
        _record(
            "variant-c", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"pandas"})
        )
    ]
    for label in ("variant-a", "variant-b", "variant-d"):
        records.append(
            _record(
                label,
                "Throwaway Source",
                tiers=frozenset({SupportTier.FLUENT_API}),
                fluent_types=(
                    frozenset({"pandas"}) if label == ambiguous_label else next(clean_types)
                ),
            )
        )
    with pytest.raises(UpstreamDeclarationError) as raised:
        assemble_rows(_facts(*records))
    assert str(raised.value) == _shares_pandas_with_a_variant_that_meets_it(ambiguous_label)


@pytest.mark.parametrize(
    "overlapping_label",
    ["variant-a", "variant-c", "variant-d"],
    ids=["first-meeting", "middle-meeting", "last-meeting"],
)
def test_a_shortfall_is_compared_against_every_variant_that_meets_the_criterion_wherever_it_sorts(
    overlapping_label: str,
):
    # variant-b falls short through pandas. Three variants meet the criterion; exactly one also
    # declares pandas and the other two declare types variant-b does not. That one is placed
    # first, in the middle and last of the meeting variants in label order, so a comparison
    # that leaves out any position, or stops at the first meeting variant it shares nothing
    # with, fails a case.
    clean_types = iter([frozenset({"sqlite"}), frozenset({"pandas_s3"})])
    records = [
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"pandas"}),
        )
    ]
    for label in ("variant-a", "variant-c", "variant-d"):
        records.append(
            _record(
                label,
                "Throwaway Source",
                tiers=ALL_THREE,
                fluent_types=(
                    frozenset({"pandas"}) if label == overlapping_label else next(clean_types)
                ),
            )
        )
    with pytest.raises(UpstreamDeclarationError) as raised:
        assemble_rows(_facts(*records))
    assert str(raised.value) == _shares_pandas_with_a_variant_that_meets_it("variant-b")


def test_variants_that_share_a_type_only_where_both_fall_short_are_not_ambiguous():
    # The type is shared by the two variants that fall short, not with one that meets the
    # criterion, so the note names it once and nothing is ambiguous.
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"sqlite"}),
        ),
        _record(
            "variant-c",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"sqlite"}),
        ),
    )
    (row,) = assemble_rows(facts)
    assert row.notes == (
        "Every shipped expectation: not met for SQLite databases.",
        "Expectation suite: not met for SQLite databases.",
    )


REASON = "a recorded reason"


@WITH_CASE_DESCRIPTIONS
def test_a_met_criterion_is_partial_when_a_record_excludes_a_case_under_a_declaration_for_it():
    (row,) = assemble_rows(
        _facts(
            _record(
                "variant-a",
                "Throwaway Source",
                tiers=ALL_THREE,
                exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"a_case": REASON}},
            )
        )
    )
    assert row.criteria_met == frozenset({GALLERY, SUITE, API})
    assert row.criteria_partial == frozenset({SUITE})
    assert row.tier is PublicTier.FULLY_SUPPORTED
    assert row.notes == (
        "Expectation suite: not run for the first-A check. Recorded reason: a recorded reason",
    )


@WITH_CASE_DESCRIPTIONS
def test_every_declaration_that_satisfies_a_criterion_can_make_it_partial():
    cases = {
        SupportTier.CANONICAL_EXPECTATIONS: SUITE,
        SupportTier.CURATED_SQL: SUITE,
        SupportTier.FLUENT_API: API,
        SupportTier.GALLERY: GALLERY,
    }
    for declared, expected in cases.items():
        (row,) = assemble_rows(
            _facts(
                _record(
                    "variant-a",
                    "Throwaway Source",
                    tiers=ALL_THREE | {SupportTier.CURATED_SQL},
                    exclusions={declared: {"a_case": REASON}},
                )
            )
        )
        assert row.criteria_partial == frozenset({expected}), declared


@WITH_CASE_DESCRIPTIONS
def test_a_met_criterion_is_partial_when_a_fluent_type_a_record_names_excludes_a_case():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        fluent_exclusions={"pandas": {"a_case": REASON}},
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_met == frozenset({GALLERY, SUITE, API})
    assert row.criteria_partial == frozenset({API})
    assert row.notes == (
        "Datasource API contract: not run for the first-A check. "
        "Recorded reason: a recorded reason",
    )


@WITH_CASE_DESCRIPTIONS
def test_one_variants_exclusion_makes_the_criterion_partial_for_the_whole_row():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"sqlite"}),
            exclusions={SupportTier.GALLERY: {"a_case": REASON}},
        ),
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_partial == frozenset({GALLERY})


@WITH_CASE_DESCRIPTIONS
def test_a_later_variants_fluent_type_exclusion_makes_the_datasource_api_criterion_partial():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"sqlite"}),
        ),
        fluent_exclusions={"sqlite": {"a_case": REASON}},
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_partial == frozenset({API})


@WITH_CASE_DESCRIPTIONS
def test_a_criterion_that_is_not_met_is_never_partial():
    # Exclusions are recorded under the expectation suite and datasource API criteria, yet the
    # record declares neither, so there is no coverage for an exception to qualify.
    facts = _facts(
        _record(
            "variant-a",
            "Throwaway Source",
            tiers=frozenset({SupportTier.GALLERY}),
            exclusions={
                SupportTier.CANONICAL_EXPECTATIONS: {"a_case": REASON},
                SupportTier.FLUENT_API: {"a_case": REASON},
            },
        ),
        fluent_exclusions={"pandas": {"a_case": REASON}},
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_met == frozenset({GALLERY})
    assert row.criteria_partial == frozenset()


@WITH_CASE_DESCRIPTIONS
def test_a_criterion_one_variant_lacks_is_not_partial_through_the_other_variants_exclusion():
    facts = _facts(
        _record(
            "variant-a",
            "Throwaway Source",
            tiers=ALL_THREE,
            exclusions={SupportTier.GALLERY: {"a_case": REASON}},
        ),
        _record(
            "variant-b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.FLUENT_API}),
            fluent_types=frozenset({"sqlite"}),
        ),
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_met == frozenset({API})
    assert row.criteria_partial == frozenset()


@WITH_CASE_DESCRIPTIONS
def test_no_exclusion_means_no_partial_criterion():
    facts = _facts(
        _record(
            "variant-a",
            "Throwaway Source",
            tiers=ALL_THREE,
            exclusions={SupportTier.GALLERY: {}},
        ),
        fluent_exclusions={"pandas": {}, "sqlite": {"a_case": REASON}},
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_met == frozenset({GALLERY, SUITE, API})
    assert row.criteria_partial == frozenset()


def test_the_real_registry_marks_exactly_the_recorded_exclusions_partial():
    # Read outside the isolation seam. The throwaway twins above show the same marking can fail
    # to appear, so these are not vacuous.
    rows = {row.public_name: row for row in assemble_rows(load_upstream_facts())}
    partial = {name: row.criteria_partial for name, row in rows.items() if row.criteria_partial}
    assert partial == {"ClickHouse": frozenset({SUITE}), "Pandas": frozenset({API})}
    assert rows["ClickHouse"].criteria_met == frozenset({SUITE, API})
    assert rows["Pandas"].criteria_met == frozenset({GALLERY, SUITE, API})


def test_a_public_name_with_surrounding_whitespace_fails_rather_than_publishing_a_lookalike():
    facts = _facts(
        _record("a", "Pandas", tiers=ALL_THREE),
        _record("b", "Pandas ", tiers=ALL_THREE),
    )
    with pytest.raises(ValueError) as raised:
        assemble_rows(facts)
    assert str(raised.value) == (
        "The public name 'Pandas ' (record labelled 'b') has leading or trailing whitespace, so "
        "it would publish a row that looks identical to one without. Remove the whitespace from "
        "the declaration."
    )
    with pytest.raises(ValueError, match=r"' Pandas' \(record labelled 'c'\)"):
        assemble_rows(_facts(_record("c", " Pandas")))


def test_two_public_names_differing_only_in_case_fail_rather_than_publishing_a_lookalike():
    facts = _facts(
        _record("a", "pandas", tiers=ALL_THREE),
        _record("b", "Pandas", tiers=ALL_THREE),
    )
    with pytest.raises(ValueError) as raised:
        assemble_rows(facts)
    assert str(raised.value) == (
        "The public names 'Pandas' and 'pandas' differ only in letter case, so they would "
        "publish two rows that look like one. Declare one spelling for the data source."
    )


# ---------------------------------------------------------------------------------------------
# Notes that qualify what a row's tier means.
#
# Expected notes are written out in full. Deriving them with the code under test could not fail.
# ---------------------------------------------------------------------------------------------

COVERED_NOTE = (
    "The datasource API contract is verified for this data source, but that criterion is not "
    "shown as met because no continuous-integration lane is declared for it; what is missing "
    "is that declaration, not test evidence."
)
MANAGED_NOTE = (
    "No continuous-integration lane exercises the real service: reaching it needs credentials "
    "this repository does not provision."
)
ORACLE_NOTE = "Tested against Oracle 21c. 19c expected, not verified in CI."
CREDENTIALS = DataSourceProvisioning.EXTERNAL_CREDENTIALS
CONTAINER = DataSourceProvisioning.LOCAL_CONTAINER

ALL_LABELS = ("a", "b", "c")
POSITIONS = pytest.mark.parametrize("decisive", [0, 1, 2], ids=["first", "middle", "last"])
FLUENT_TYPES_BY_POSITION = ("pandas", "pandas_filesystem", "pandas_s3")
DESCRIPTION_BY_POSITION = (PANDAS_DESCRIPTION, CSV_DESCRIPTION, S3_PANDAS_DESCRIPTION)

# Every character the producers must treat as ending a line.
LINE_BREAKS = pytest.mark.parametrize(
    "character",
    ["\n", "\r", "\r\n", "\x0b", "\x0c", "\x85", "\N{LINE SEPARATOR}", "\N{PARAGRAPH SEPARATOR}"],
    ids=["lf", "cr", "crlf", "vt", "ff", "nel", "ls", "ps"],
)


def _notes_of(facts: UpstreamFacts, public_name: str) -> Tuple[str, ...]:
    return _row(assemble_rows(facts), public_name).notes


def _three_variants(decisive: int, **overrides_for_decisive) -> Tuple[DataSourceSpec, ...]:
    """Three records sharing one name that agree on every criterion; only ``decisive`` differs."""
    records = []
    for position, label in enumerate(ALL_LABELS):
        kwargs = overrides_for_decisive if position == decisive else {}
        records.append(
            _record(
                label,
                "Throwaway Source",
                tiers=ALL_THREE,
                fluent_types=frozenset({FLUENT_TYPES_BY_POSITION[position]}),
                **kwargs,
            )
        )
    return tuple(records)


# --- covered by a suite the record cannot claim ----------------------------------------------


def test_a_record_covered_but_unable_to_claim_gets_a_note_stating_both_halves():
    facts = _facts(_record("only", "Throwaway Source"), covered=frozenset({"only"}))
    assert _notes_of(facts, "Throwaway Source") == (COVERED_NOTE,)


def test_the_covered_note_disappears_with_the_declaration_it_came_from():
    record = _record("only", "Throwaway Source")
    covered = _facts(record, covered=frozenset({"only"}))
    assert _notes_of(covered, "Throwaway Source") == (COVERED_NOTE,)
    assert _notes_of(_facts(record, covered=frozenset()), "Throwaway Source") == ()
    other = _facts(record, covered=frozenset({"someone-else"}))
    assert _notes_of(other, "Throwaway Source") == ()


@POSITIONS
def test_the_covered_note_is_found_whichever_record_of_the_row_is_listed(decisive):
    facts = _facts(*_three_variants(decisive), covered=frozenset({ALL_LABELS[decisive]}))
    assert _notes_of(facts, "Throwaway Source") == (COVERED_NOTE,)


def test_the_covered_note_is_given_once_when_several_records_of_a_row_are_listed():
    facts = _facts(*_three_variants(0), covered=frozenset(ALL_LABELS))
    assert _notes_of(facts, "Throwaway Source") == (COVERED_NOTE,)


# --- a recorded exclusion inside a criterion's suite -----------------------------------------

BACKTICKED = (
    "Insert keys rows by the bind name, raising a `KeyError`. An issue still needs to be filed."
)


def test_a_recorded_case_exclusion_is_named_with_its_reason_printed_exactly_as_recorded():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=frozenset({SupportTier.CURATED_SQL, SupportTier.FLUENT_API}),
        exclusions={SupportTier.CURATED_SQL: {"quoted_identifiers": BACKTICKED}},
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for column names that need quoting. "
        f"Recorded reason: {BACKTICKED}",
    )


@WITH_CASE_DESCRIPTIONS
@pytest.mark.parametrize(
    ("declaration", "label"),
    [
        (SupportTier.GALLERY, "Every shipped expectation"),
        (SupportTier.CANONICAL_EXPECTATIONS, "Expectation suite"),
        (SupportTier.CURATED_SQL, "Expectation suite"),
        (SupportTier.FLUENT_API, "Datasource API contract"),
    ],
    ids=lambda value: getattr(value, "name", value),
)
def test_an_exclusion_under_any_declaration_is_attributed_to_the_criterion_it_satisfies(
    declaration, label
):
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={declaration: {"some_case": "Not run."}},
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        f"{label}: not run for the shared check. Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
def test_the_exclusion_note_disappears_with_the_exclusion():
    with_it = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}},
    )
    without = _record("only", "Throwaway Source", tiers=ALL_THREE)
    assert len(_notes_of(_facts(with_it), "Throwaway Source")) == 1
    assert _notes_of(_facts(without), "Throwaway Source") == ()


@WITH_CASE_DESCRIPTIONS
@POSITIONS
def test_a_variants_exclusion_is_found_and_scoped_to_it_wherever_it_sorts(decisive):
    facts = _facts(
        *_three_variants(
            decisive,
            exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}},
        )
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Expectation suite, {DESCRIPTION_BY_POSITION[decisive]}: not run for the shared check. "
        f"Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
@POSITIONS
def test_a_fluent_types_exclusion_is_found_and_scoped_to_it_wherever_it_sorts(decisive):
    facts = _facts(
        *_three_variants(decisive),
        fluent_exclusions={FLUENT_TYPES_BY_POSITION[decisive]: {"some_case": "Not run."}},
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Datasource API contract, {DESCRIPTION_BY_POSITION[decisive]}: "
        f"not run for the shared check. Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
def test_a_single_record_with_a_single_type_scopes_nothing():
    facts = _facts(
        _record("only", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"pandas_s3"})),
        fluent_exclusions={"pandas_s3": {"some_case": "Not run."}},
    )
    assert _notes_of(facts, "Throwaway Source") == (
        "Datasource API contract: not run for the shared check. Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
def test_a_single_record_reached_through_several_types_scopes_to_the_type_that_excludes():
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"pandas_s3", "spark_s3"}),
        ),
        fluent_exclusions={"pandas_s3": {"some_case": "Not run."}},
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Datasource API contract, {S3_PANDAS_DESCRIPTION}: not run for the shared check. "
        f"Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
@pytest.mark.parametrize(
    ("excluding", "description"),
    [("pandas_s3", S3_PANDAS_DESCRIPTION), ("spark_s3", S3_SPARK_DESCRIPTION)],
    ids=["first-type", "last-type"],
)
def test_each_type_of_a_multi_type_record_is_checked_for_exclusions(excluding, description):
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"pandas_s3", "spark_s3"}),
        ),
        fluent_exclusions={excluding: {"some_case": "Not run."}},
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Datasource API contract, {description}: not run for the shared check. "
        f"Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
def test_exclusions_on_every_type_of_a_multi_type_record_each_get_a_note_in_a_fixed_order():
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"pandas_s3", "spark_s3"}),
        ),
        fluent_exclusions={
            "spark_s3": {"some_case": "Not run."},
            "pandas_s3": {"some_case": "Not run."},
        },
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Datasource API contract, {S3_SPARK_DESCRIPTION}: not run for the shared check. "
        f"Recorded reason: Not run.",
        f"Datasource API contract, {S3_PANDAS_DESCRIPTION}: not run for the shared check. "
        f"Recorded reason: Not run.",
    )


@WITH_CASE_DESCRIPTIONS
def test_exclusions_under_both_declarations_of_one_criterion_are_both_noted():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE | {SupportTier.CURATED_SQL},
        exclusions={
            SupportTier.CANONICAL_EXPECTATIONS: {"canonical_case": "Canonical reason."},
            SupportTier.CURATED_SQL: {"curated_case": "Curated reason."},
        },
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for the canonical check. Recorded reason: Canonical reason.",
        "Expectation suite: not run for the curated check. Recorded reason: Curated reason.",
    )


@WITH_CASE_DESCRIPTIONS
def test_a_suites_exclusions_and_a_fluent_types_exclusions_are_kept_to_their_own_criteria():
    # One record, one decisive exclusion per criterion: neither may leak into the other's note.
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"suite_case": "Suite reason."}},
        ),
        fluent_exclusions={"pandas": {"api_case": "Api reason."}},
    )
    assert _notes_of(facts, "Throwaway Source") == (
        "Expectation suite: not run for the suite check. Recorded reason: Suite reason.",
        "Datasource API contract: not run for the API check. Recorded reason: Api reason.",
    )


@WITH_CASE_DESCRIPTIONS
def test_the_exclusion_producer_follows_the_criteria_assembly_marked_partial():
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}},
        )
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_partial == frozenset({SUITE})
    assert len(recorded_exclusion_notes(row, facts)) == 1
    unmarked = replace(row, criteria_partial=frozenset())
    assert recorded_exclusion_notes(unmarked, facts) == ()


@WITH_CASE_DESCRIPTIONS
def test_groups_are_ordered_by_their_first_case_not_their_last():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={
            SupportTier.CANONICAL_EXPECTATIONS: {
                "a_case": "Wide reason.",
                "z_case": "Wide reason.",
                "m_case": "Narrow reason.",
            }
        },
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for the first-A check and the last-Z check. "
        "Recorded reason: Wide reason.",
        "Expectation suite: not run for the middle-M check. Recorded reason: Narrow reason.",
    )


@WITH_CASE_DESCRIPTIONS
def test_a_reason_is_printed_exactly_as_recorded_including_its_surrounding_spaces():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "  Padded.  "}},
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for the shared check. Recorded reason:   Padded.  ",
    )


@WITH_CASE_DESCRIPTIONS
def test_several_cases_sharing_a_reason_are_named_together_in_sorted_order():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={
            SupportTier.CANONICAL_EXPECTATIONS: {"zeta": "Same.", "alpha": "Same.", "mid": "Same."}
        },
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for the Z-sorting check, the M-sorting check and the "
        "A-sorting check. Recorded reason: Same.",
    )


@WITH_CASE_DESCRIPTIONS
def test_two_cases_are_joined_with_and_alone():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"beta": "Same.", "alpha": "Same."}},
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for the Z-sorting check and the Y-sorting check. "
        "Recorded reason: Same.",
    )


@WITH_CASE_DESCRIPTIONS
def test_cases_with_different_reasons_get_separate_notes_ordered_by_first_case():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={
            SupportTier.CANONICAL_EXPECTATIONS: {"zeta": "Zed reason.", "alpha": "Alpha reason."}
        },
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Expectation suite: not run for the Z-sorting check. Recorded reason: Alpha reason.",
        "Expectation suite: not run for the A-sorting check. Recorded reason: Zed reason.",
    )


@WITH_CASE_DESCRIPTIONS
def test_two_variants_with_the_same_reason_are_not_merged_across_variants():
    shared = {SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Same."}}
    facts = _facts(
        _record("a", "Throwaway Source", tiers=ALL_THREE, exclusions=shared),
        _record(
            "b",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"pandas_filesystem"}),
            exclusions=shared,
        ),
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Expectation suite, {CSV_DESCRIPTION}: not run for the shared check. "
        f"Recorded reason: Same.",
        f"Expectation suite, {PANDAS_DESCRIPTION}: not run for the shared check. "
        f"Recorded reason: Same.",
    )


@WITH_CASE_DESCRIPTIONS
def test_exclusion_notes_follow_criterion_order_whatever_order_they_were_declared_in():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={
            SupportTier.FLUENT_API: {"api_case": "Api reason."},
            SupportTier.CANONICAL_EXPECTATIONS: {"suite_case": "Suite reason."},
            SupportTier.GALLERY: {"gallery_case": "Gallery reason."},
        },
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (
        "Every shipped expectation: not run for the gallery check. "
        "Recorded reason: Gallery reason.",
        "Expectation suite: not run for the suite check. Recorded reason: Suite reason.",
        "Datasource API contract: not run for the API check. Recorded reason: Api reason.",
    )


@WITH_CASE_DESCRIPTIONS
def test_an_exclusion_inside_a_criterion_the_row_does_not_meet_is_not_noted():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=frozenset({SupportTier.FLUENT_API}),
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}},
    )
    assert _notes_of(_facts(record), "Throwaway Source") == ()


@WITH_CASE_DESCRIPTIONS
def test_a_fluent_type_with_an_exclusion_that_no_description_names_fails_rather_than_printing_it():
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"pandas_s3", "mystery_type"}),
        ),
        fluent_exclusions={"mystery_type": {"some_case": "Not run."}},
    )
    with pytest.raises(UpstreamDeclarationError, match="'mystery_type'"):
        assemble_rows(facts)


@WITH_CASE_DESCRIPTIONS
@LINE_BREAKS
def test_a_line_break_in_a_recorded_reason_fails_instead_of_mangling_a_row(character):
    reason = f"First line.{character}Second line."
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": reason}},
    )
    with pytest.raises(ValueError, match="recorded reason for case 'some_case'") as raised:
        assemble_rows(_facts(record))
    assert "line break" in str(raised.value)


@WITH_CASE_DESCRIPTIONS
@LINE_BREAKS
def test_a_trailing_or_leading_line_break_in_a_reason_also_fails(character):
    for reason in (f"Reason.{character}", f"{character}Reason."):
        record = _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": reason}},
        )
        with pytest.raises(ValueError, match="line break"):
            assemble_rows(_facts(record))


@WITH_CASE_DESCRIPTIONS
def test_a_line_break_in_a_fluent_types_recorded_reason_fails_too():
    facts = _facts(
        _record("only", "Throwaway Source", tiers=ALL_THREE),
        fluent_exclusions={"pandas": {"some_case": "One.\nTwo."}},
    )
    with pytest.raises(ValueError, match="recorded reason for case 'some_case'"):
        assemble_rows(facts)


def test_a_case_key_with_a_line_break_and_no_description_fails_without_printing_the_key():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"two\nlines": "Reason."}},
    )
    with pytest.raises(UpstreamDeclarationError, match="CASE_DESCRIPTIONS does not describe it"):
        assemble_rows(_facts(record))


@LINE_BREAKS
def test_a_line_break_in_a_case_description_fails_instead_of_mangling_a_row(monkeypatch, character):
    monkeypatch.setitem(
        upstream_declarations.CASE_DESCRIPTIONS, "some_case", f"first{character}second"
    )
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}},
    )
    with pytest.raises(ValueError, match="description of case 'some_case'") as raised:
        assemble_rows(_facts(record))
    assert type(raised.value) is ValueError
    assert "line break" in str(raised.value)


@pytest.mark.parametrize("decisive", [0, 1, 2], ids=["first", "middle", "last"])
def test_every_case_description_in_a_group_is_checked_for_a_line_break(monkeypatch, decisive):
    cases = ("alpha", "beta", "mid")  # one reason, so one group of three; sorted by key
    monkeypatch.setitem(upstream_declarations.CASE_DESCRIPTIONS, cases[decisive], "first\nsecond")
    for case in cases:
        if case != cases[decisive]:
            monkeypatch.setitem(upstream_declarations.CASE_DESCRIPTIONS, case, f"fine {case}")
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: dict.fromkeys(cases, "Same.")},
    )
    with pytest.raises(ValueError, match=f"description of case '{cases[decisive]}'"):
        assemble_rows(_facts(record))


def test_a_case_without_a_description_fails_naming_the_key_rather_than_printing_it():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CURATED_SQL: {"undescribed_case": "Not run."}},
    )
    with pytest.raises(UpstreamDeclarationError, match="'undescribed_case'"):
        assemble_rows(_facts(record))
    fluent = _facts(
        _record("only", "Throwaway Source", tiers=ALL_THREE),
        fluent_exclusions={"pandas": {"undescribed_case": "Not run."}},
    )
    with pytest.raises(UpstreamDeclarationError, match="'undescribed_case'"):
        assemble_rows(fluent)


def test_a_note_names_the_case_by_its_description_and_never_by_its_key():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CURATED_SQL: {"quoted_identifiers": "Not run."}},
    )
    (note,) = _notes_of(_facts(record), "Throwaway Source")
    assert note == (
        "Expectation suite: not run for column names that need quoting. Recorded reason: Not run."
    )
    assert "quoted_identifiers" not in note


@WITH_CASE_DESCRIPTIONS
def test_no_note_prints_a_case_key_for_a_group_of_several_cases():
    record = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"zeta": "Same.", "alpha": "Same."}},
    )
    (note,) = _notes_of(_facts(record), "Throwaway Source")
    assert note == (
        "Expectation suite: not run for the Z-sorting check and the A-sorting check. "
        "Recorded reason: Same."
    )
    assert "alpha" not in note
    assert "zeta" not in note


def test_a_line_break_in_a_variant_description_fails_instead_of_mangling_a_heading(monkeypatch):
    monkeypatch.setitem(upstream_declarations.CONNECTION_PATH_DESCRIPTIONS, "pandas", "a\nb")
    facts = _facts(
        *_three_variants(
            0, exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}}
        )
    )
    with pytest.raises(ValueError) as raised:
        assemble_rows(facts)
    assert type(raised.value) is ValueError
    assert str(raised.value) == (
        "The variant description for 'Throwaway Source' contains a line break, which would "
        "break the table row it is printed in. Rewrite it as a single line where it is "
        "declared: 'a\\nb'"
    )


@WITH_CASE_DESCRIPTIONS
def test_a_line_break_in_a_fluent_types_description_fails_instead_of_mangling_a_heading(
    monkeypatch,
):
    monkeypatch.setitem(upstream_declarations.CONNECTION_PATH_DESCRIPTIONS, "pandas_s3", "a\nb")
    facts = _facts(
        _record(
            "only",
            "Throwaway Source",
            tiers=ALL_THREE,
            fluent_types=frozenset({"pandas_s3", "spark_s3"}),
        ),
        fluent_exclusions={"pandas_s3": {"some_case": "Not run."}},
    )
    with pytest.raises(ValueError, match="variant description for 'Throwaway Source'"):
        assemble_rows(facts)


@WITH_CASE_DESCRIPTIONS
def test_a_single_line_reason_is_accepted_where_the_same_reason_with_a_break_is_not():
    # The control for the failing cases above: nothing but the break differs.
    ok = _record(
        "only",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "First. Second."}},
    )
    assert len(_notes_of(_facts(ok), "Throwaway Source")) == 1


# --- the descriptions of excluded cases, pinned to the exclusions both ways --------------------

REAL_CASE_KEYS = (
    "quoted_identifiers",
    "update_replaces_configuration",
    "create_or_update_replaces_when_present",
    "create_or_update_persists_one_entry",
)


def test_the_declared_case_descriptions_are_exactly_the_four_recorded_exclusions():
    assert set(upstream_declarations.CASE_DESCRIPTIONS) == set(REAL_CASE_KEYS)
    assert upstream_declarations.CASE_DESCRIPTIONS == {
        "quoted_identifiers": "column names that need quoting",
        "update_replaces_configuration": "replacing a datasource's configuration on update",
        "create_or_update_replaces_when_present": (
            "replacing an existing datasource on create-or-update"
        ),
        "create_or_update_persists_one_entry": (
            "keeping a single saved entry after create-or-update"
        ),
    }


def test_the_real_exclusions_are_the_four_the_descriptions_cover():
    facts = load_upstream_facts()
    recorded = {
        case
        for spec in facts.specs
        for cases in spec.tier_case_exclusions.values()
        for case in cases
    }
    fluent = {case for cases in facts.fluent_case_exclusions.values() for case in cases}
    assert recorded == {"quoted_identifiers"}
    assert fluent == set(REAL_CASE_KEYS) - {"quoted_identifiers"}


def _excluding_record() -> DataSourceSpec:
    return _record(
        "excluding",
        "Throwaway Source",
        tiers=ALL_THREE,
        exclusions={SupportTier.CURATED_SQL: {"record_case": "Not run."}},
    )


def _guard(descriptions, *, specs=None, fluent=None) -> None:
    upstream_declarations.check_case_descriptions(
        (_excluding_record(),) if specs is None else specs,
        {"pandas": {"fluent_case": "Not run."}} if fluent is None else fluent,
        descriptions,
    )


def test_the_case_guard_accepts_descriptions_that_are_exactly_the_excluded_cases():
    _guard({"record_case": "a record case", "fluent_case": "a fluent case"})


@pytest.mark.parametrize("missing", ["record_case", "fluent_case"])
def test_the_case_guard_fails_naming_an_excluded_case_that_has_no_description(missing):
    described = {"record_case": "a record case", "fluent_case": "a fluent case"}
    del described[missing]
    with pytest.raises(UpstreamDeclarationError) as raised:
        _guard(described)
    assert str(raised.value).startswith(f"A declaration excludes case(s) ['{missing}'] ")


def test_the_case_guard_names_every_undescribed_case_in_sorted_order():
    with pytest.raises(UpstreamDeclarationError) as raised:
        _guard({})
    assert str(raised.value).startswith(
        "A declaration excludes case(s) ['fluent_case', 'record_case'] "
    )


@pytest.mark.parametrize("stale", ["one_extra", "another_extra"])
def test_the_case_guard_fails_naming_a_description_no_declaration_excludes(stale):
    described = {"record_case": "a record case", "fluent_case": "a fluent case", stale: "stale"}
    with pytest.raises(UpstreamDeclarationError) as raised:
        _guard(described)
    assert str(raised.value).startswith(f"CASE_DESCRIPTIONS describes case(s) ['{stale}'] that ")


def test_the_case_guard_notices_a_description_whose_exclusion_was_removed_from_either_source():
    described = {"record_case": "a record case", "fluent_case": "a fluent case"}
    with pytest.raises(UpstreamDeclarationError, match=r"\['record_case'\]"):
        _guard(described, specs=(_record("quiet", "Throwaway Source"),))
    with pytest.raises(UpstreamDeclarationError, match=r"\['fluent_case'\]"):
        _guard(described, fluent={})


SPREAD_CASES = ("case_one", "case_two", "case_three")
SPREAD_DESCRIPTIONS = {case: f"description of {case}" for case in SPREAD_CASES}
SPREAD_TIERS = (SupportTier.CURATED_SQL, SupportTier.GALLERY, SupportTier.FLUENT_API)


def _spread_over_records() -> Tuple[DataSourceSpec, ...]:
    return tuple(
        _record(label, "Throwaway Source", exclusions={SPREAD_TIERS[0]: {case: "Not run."}})
        for label, case in zip("abc", SPREAD_CASES, strict=True)
    )


def _spread_over_tiers() -> Tuple[DataSourceSpec, ...]:
    return (
        _record(
            "only",
            "Throwaway Source",
            exclusions={
                tier: {case: "Not run."}
                for tier, case in zip(SPREAD_TIERS, SPREAD_CASES, strict=True)
            },
        ),
    )


def _spread_over_types() -> Tuple[Mapping[str, Mapping[str, str]], ...]:
    return (
        {
            "pandas": {SPREAD_CASES[0]: "x"},
            "spark": {SPREAD_CASES[1]: "x"},
            "sql": {SPREAD_CASES[2]: "x"},
        },
    )


SPREAD_SOURCES = pytest.mark.parametrize(
    ("specs", "fluent"),
    [
        (_spread_over_records(), {}),
        (_spread_over_tiers(), {}),
        ((), _spread_over_types()[0]),
    ],
    ids=["over-records", "over-tiers-of-one-record", "over-fluent-types"],
)


@SPREAD_SOURCES
def test_the_case_guard_accepts_cases_spread_over_every_record_tier_and_type(specs, fluent):
    # The control for the failing cases below: a description for each of the three is not stale.
    _guard(SPREAD_DESCRIPTIONS, specs=specs, fluent=fluent)


@SPREAD_SOURCES
@pytest.mark.parametrize("decisive", [0, 1, 2], ids=["first", "middle", "last"])
def test_the_case_guard_checks_every_record_tier_and_type_for_an_undescribed_case(
    specs, fluent, decisive
):
    described = {k: v for k, v in SPREAD_DESCRIPTIONS.items() if k != SPREAD_CASES[decisive]}
    with pytest.raises(UpstreamDeclarationError) as raised:
        _guard(described, specs=specs, fluent=fluent)
    assert str(raised.value).startswith(
        f"A declaration excludes case(s) ['{SPREAD_CASES[decisive]}'] "
    )


@pytest.mark.parametrize("key", REAL_CASE_KEYS)
def test_the_loader_fails_when_a_declared_exclusion_has_no_description(monkeypatch, key):
    load_upstream_facts()  # control: the declarations as they stand load
    monkeypatch.delitem(upstream_declarations.CASE_DESCRIPTIONS, key)
    with pytest.raises(UpstreamDeclarationError) as raised:
        load_upstream_facts()
    assert str(raised.value).startswith(f"A declaration excludes case(s) ['{key}'] ")


def test_the_loader_fails_when_a_description_names_a_case_no_declaration_excludes(monkeypatch):
    monkeypatch.setitem(upstream_declarations.CASE_DESCRIPTIONS, "extra_case", "an extra case")
    with pytest.raises(UpstreamDeclarationError) as raised:
        load_upstream_facts()
    assert str(raised.value).startswith("CASE_DESCRIPTIONS describes case(s) ['extra_case'] ")


def test_the_loader_fails_when_the_registry_no_longer_excludes_a_described_record_case():
    with isolated_registry():
        register_data_source(ORACLE_SPEC)  # no record excludes quoted_identifiers
        with pytest.raises(UpstreamDeclarationError) as raised:
            load_upstream_facts()
    assert str(raised.value).startswith(
        "CASE_DESCRIPTIONS describes case(s) ['quoted_identifiers'] "
    )


def test_the_loader_reads_the_fluent_exclusions_it_checks_from_the_accessor(monkeypatch):
    monkeypatch.setattr(upstream_declarations, "case_exclusions_by_type", lambda: {})
    with pytest.raises(UpstreamDeclarationError) as raised:
        load_upstream_facts()
    assert str(raised.value).startswith(
        "CASE_DESCRIPTIONS describes case(s) ['create_or_update_persists_one_entry', "
        "'create_or_update_replaces_when_present', 'update_replaces_configuration'] "
    )


def test_the_loader_hands_over_the_fluent_exclusions_it_checked(monkeypatch):
    altered = {"pandas": {"update_replaces_configuration": "x"}}
    monkeypatch.setattr(upstream_declarations, "case_exclusions_by_type", lambda: altered)
    monkeypatch.setattr(
        upstream_declarations,
        "CASE_DESCRIPTIONS",
        {"quoted_identifiers": "q", "update_replaces_configuration": "u"},
    )
    assert load_upstream_facts().fluent_case_exclusions == altered


SHORT_TYPES = ("pandas", "pandas_s3", "pandas_gcs")
GCS_PANDAS_DESCRIPTION = "Google Cloud Storage objects read with pandas"


def _short_variants() -> Tuple[DataSourceSpec, ...]:
    """Three records fall short of every criterion a fourth meets, told apart by their types."""
    shorts = [
        _record(label, "Throwaway Source", fluent_types=frozenset({fluent_type}))
        for label, fluent_type in zip("abc", SHORT_TYPES, strict=True)
    ]
    meeting = _record(
        "d", "Throwaway Source", tiers=ALL_THREE, fluent_types=frozenset({"pandas_filesystem"})
    )
    return (*shorts, meeting)


def test_variants_falling_short_are_all_named_when_each_description_is_a_single_line():
    # The control for the failing cases below.
    (row,) = assemble_rows(_facts(*_short_variants()))
    assert row.notes[0] == (
        "Every shipped expectation: not met for Amazon S3 objects read with pandas; "
        "Google Cloud Storage objects read with pandas; in-memory pandas DataFrames."
    )


@pytest.mark.parametrize(
    ("position", "fluent_type"),
    list(enumerate(SHORT_TYPES)),
    ids=["first", "middle", "last"],
)
def test_a_line_break_in_any_variant_description_of_a_disagreement_note_fails(
    monkeypatch, position, fluent_type
):
    monkeypatch.setitem(upstream_declarations.CONNECTION_PATH_DESCRIPTIONS, fluent_type, "a\nb")
    with pytest.raises(ValueError) as raised:
        assemble_rows(_facts(*_short_variants()))
    assert type(raised.value) is ValueError
    assert str(raised.value) == (
        "The variant description in a disagreement note for 'Throwaway Source' contains a line "
        "break, which would break the table row it is printed in. Rewrite it as a single line "
        "where it is declared: 'a\\nb'"
    )


# --- connection paths no record names --------------------------------------------------------


def test_the_footnote_lists_each_uncovered_path_by_description_in_sorted_order():
    facts = _facts(
        _record("only", "Throwaway Source"),
        uncovered_paths=frozenset({"spark", "pandas_dbfs", "fabric_powerbi", "spark_dbfs"}),
    )
    assert uncovered_connection_paths_note(facts) == (
        "Connection paths GX ships that no row above covers: Databricks File System paths read "
        "with Spark; Databricks File System paths read with pandas; Power BI semantic models; "
        "Spark in-memory DataFrames."
    )


def test_the_footnote_names_a_single_path_without_separators():
    facts = _facts(_record("only", "x"), uncovered_paths=frozenset({"spark"}))
    assert uncovered_connection_paths_note(facts) == (
        "Connection paths GX ships that no row above covers: Spark in-memory DataFrames."
    )


def test_the_footnote_fails_when_a_description_spans_more_than_one_line(monkeypatch):
    # "spark" is an uncovered path here, so its description is printed in the footnote.
    monkeypatch.setitem(upstream_declarations.CONNECTION_PATH_DESCRIPTIONS, "spark", "a\nb")
    facts = _facts(_record("only", "x"), uncovered_paths=frozenset({"spark"}))
    with pytest.raises(ValueError) as raised:
        uncovered_connection_paths_note(facts)
    assert type(raised.value) is ValueError
    assert str(raised.value) == (
        "The uncovered connection paths footnote contains a line break, which would break the "
        "table row it is printed in. Rewrite it as a single line where it is declared: "
        "'Connection paths GX ships that no row above covers: a\\nb.'"
    )


def test_the_footnote_disappears_when_no_path_is_uncovered():
    assert uncovered_connection_paths_note(_facts(_record("only", "x"))) is None


def test_the_footnote_fails_naming_a_path_nothing_describes_rather_than_printing_it():
    facts = _facts(
        _record("only", "x"), uncovered_paths=frozenset({"spark", "mystery_path", "another"})
    )
    with pytest.raises(UpstreamDeclarationError) as raised:
        uncovered_connection_paths_note(facts)
    assert "['another', 'mystery_path']" in str(raised.value)


def test_the_real_footnote_names_the_four_paths_no_record_names():
    footnote = uncovered_connection_paths_note(load_upstream_facts())
    assert footnote == (
        "Connection paths GX ships that no row above covers: Databricks File System paths read "
        "with Spark; Databricks File System paths read with pandas; Power BI semantic models; "
        "Spark in-memory DataFrames."
    )


def test_the_loader_fails_when_the_pinned_uncovered_path_literal_names_an_undescribed_path(
    monkeypatch,
):
    # Through the loader, not the pure guard: a loader that stopped passing the literal to the
    # guard would leave the guard's own tests green.
    load_upstream_facts()  # control: the declarations as they stand load
    altered = upstream_declarations.FLUENT_TYPES_NAMED_BY_NO_RECORD | {"mystery_path"}
    monkeypatch.setattr(upstream_declarations, "FLUENT_TYPES_NAMED_BY_NO_RECORD", altered)
    with pytest.raises(UpstreamDeclarationError, match="mystery_path"):
        load_upstream_facts()


def test_the_loader_hands_the_pinned_uncovered_path_literal_to_the_facts_unaltered():
    assert load_upstream_facts().fluent_types_named_by_no_record == frozenset(
        {"spark", "pandas_dbfs", "spark_dbfs", "fabric_powerbi"}
    )


# --- managed-service provisioning ------------------------------------------------------------


def test_external_credentials_with_a_recorded_note_produces_the_managed_service_note():
    record = _record(
        "only", "Throwaway Source", provisioning=CREDENTIALS, provisioning_note="Needs a tenant."
    )
    assert _notes_of(_facts(record), "Throwaway Source") == (MANAGED_NOTE,)


def test_external_credentials_alone_produces_no_managed_service_note():
    record = _record("only", "Throwaway Source", provisioning=CREDENTIALS, lane=LANE)
    assert _notes_of(_facts(record), "Throwaway Source") == ()


def test_a_recorded_note_alone_produces_no_managed_service_note():
    record = _record(
        "only",
        "Throwaway Source",
        provisioning=CONTAINER,
        provisioning_note="Costs seven surfaces.",
    )
    assert _notes_of(_facts(record), "Throwaway Source") == ()


@pytest.mark.parametrize("blank", ["", "   ", "\t"], ids=["empty", "spaces", "tab"])
def test_a_blank_recorded_note_does_not_count_as_a_recorded_note(blank):
    record = _record("only", "Throwaway Source", provisioning=CREDENTIALS, provisioning_note=blank)
    assert _notes_of(_facts(record), "Throwaway Source") == ()


def test_the_two_halves_must_hold_on_one_record_not_across_a_row():
    facts = _facts(
        _record(
            "a", "Throwaway Source", provisioning=CREDENTIALS, fluent_types=frozenset({"pandas"})
        ),
        _record(
            "b",
            "Throwaway Source",
            provisioning=CONTAINER,
            provisioning_note="Costs seven surfaces.",
            fluent_types=frozenset({"pandas_filesystem"}),
        ),
    )
    assert _notes_of(facts, "Throwaway Source") == ()


@POSITIONS
def test_the_managed_service_note_is_found_whichever_record_of_the_row_holds_both_halves(decisive):
    facts = _facts(
        *_three_variants(decisive, provisioning=CREDENTIALS, provisioning_note="Needs a tenant.")
    )
    assert _notes_of(facts, "Throwaway Source") == (MANAGED_NOTE,)


def test_the_managed_service_note_is_given_once_when_every_record_of_the_row_qualifies():
    facts = _facts(
        *(
            _record(
                label,
                "Throwaway Source",
                provisioning=CREDENTIALS,
                provisioning_note="Needs a tenant.",
                fluent_types=frozenset({FLUENT_TYPES_BY_POSITION[position]}),
            )
            for position, label in enumerate(ALL_LABELS)
        )
    )
    assert _notes_of(facts, "Throwaway Source") == (MANAGED_NOTE,)


def _live_notes() -> dict:
    return {row.public_name: row.notes for row in assemble_rows(load_upstream_facts())}


def test_against_the_real_declarations_the_managed_service_note_is_microsoft_fabrics_alone():
    # Read outside the isolation seam; the throwaway twins above show each half can fail.
    carrying = {name for name, notes in _live_notes().items() if MANAGED_NOTE in notes}
    assert carrying == {"Microsoft Fabric"}


def test_against_the_real_declarations_citus_whose_note_is_about_cost_produces_none():
    live = _live_notes()
    citus_specs = [s for s in load_upstream_facts().specs if s.public_name == "Citus"]
    assert [s.provisioning for s in citus_specs] == [CONTAINER]
    assert citus_specs[0].provisioning_note  # the recorded note is real, which is the point
    assert MANAGED_NOTE not in live["Citus"]


def test_against_the_real_declarations_credential_gated_data_sources_with_lanes_produce_none():
    live = _live_notes()
    by_name = {s.public_name: s for s in load_upstream_facts().specs}
    for name in ("BigQuery", "Databricks (SQL)", "Redshift", "Snowflake"):
        assert by_name[name].provisioning is CREDENTIALS, name
        assert by_name[name].ci_lane is not None, name
        assert by_name[name].provisioning_note is None, name
        assert MANAGED_NOTE not in live[name], name


def test_the_externally_provisioned_data_sources_with_no_note_and_no_lane_get_no_such_note():
    # The residual, stated from the declarations rather than counted by hand: credentials this
    # repository does not hold, no note to key on, and no lane. The remedy is upstream.
    specs = load_upstream_facts().specs
    residual = {
        s.public_name
        for s in specs
        if s.provisioning is CREDENTIALS and not s.provisioning_note and s.ci_lane is None
    }
    assert residual == {"AlloyDB", "Amazon Aurora PostgreSQL", "Azure Blob Storage", "Neon"}
    live = _live_notes()
    for name in residual:
        assert MANAGED_NOTE not in live[name], name


# --- the version bound -----------------------------------------------------------------------


def test_a_row_named_in_the_version_map_carries_its_note_verbatim(monkeypatch):
    note = "Tested against Throwaway 9.2. 9.0 expected, not verified in CI."
    monkeypatch.setitem(upstream_declarations.TESTED_VERSION_NOTES, "Throwaway Source", note)
    facts = _facts(
        _record("a", "Aardvark Source"),
        _record("b", "Throwaway Source"),
        _record("c", "Zebra Source"),
    )
    rows = {row.public_name: row.notes for row in assemble_rows(facts)}
    assert rows == {"Aardvark Source": (), "Throwaway Source": (note,), "Zebra Source": ()}


def test_the_version_note_is_looked_up_when_rows_are_built_not_when_the_module_loads(monkeypatch):
    monkeypatch.setattr(
        upstream_declarations, "TESTED_VERSION_NOTES", {"Throwaway Source": "Replaced map."}
    )
    assert _notes_of(_facts(_record("a", "Throwaway Source")), "Throwaway Source") == (
        "Replaced map.",
    )


def test_the_version_note_is_keyed_by_the_whole_public_name(monkeypatch):
    monkeypatch.setitem(upstream_declarations.TESTED_VERSION_NOTES, "Throwaway", "Bound.")
    assert _notes_of(_facts(_record("a", "Throwaway Source")), "Throwaway Source") == ()


def test_a_line_break_in_a_version_note_fails(monkeypatch):
    monkeypatch.setitem(
        upstream_declarations.TESTED_VERSION_NOTES, "Throwaway Source", "One.\nTwo."
    )
    with pytest.raises(ValueError, match="version note for 'Throwaway Source'"):
        assemble_rows(_facts(_record("a", "Throwaway Source")))


def test_the_real_oracle_row_carries_the_settled_wording_and_no_other_row_carries_it():
    live = _live_notes()
    assert live["Oracle"] == (ORACLE_NOTE,)
    assert [name for name, notes in live.items() if ORACLE_NOTE in notes] == ["Oracle"]


def test_the_loader_fails_when_a_version_key_resolves_to_no_published_row(monkeypatch):
    # Through the loader, so a loader that skipped the guard fails here by name.
    assert load_upstream_facts().specs  # control: the map as declared loads
    monkeypatch.setattr(
        upstream_declarations, "TESTED_VERSION_NOTES", {"No Such Source": "Tested against 1."}
    )
    with pytest.raises(
        UpstreamDeclarationError, match=r"'No Such Source'.*resolves to no published row"
    ):
        load_upstream_facts()


def test_the_loader_fails_when_the_named_data_source_declares_no_lane():
    with isolated_registry():
        register_data_source(replace(ORACLE_SPEC, ci_lane=None, tiers=frozenset()))
        with pytest.raises(
            UpstreamDeclarationError, match="declare no continuous-integration lane"
        ):
            load_upstream_facts()


def test_the_loader_accepts_the_same_data_source_once_its_record_declares_a_lane():
    # The control for the failing case above: only the lane differs.
    with isolated_registry():
        register_data_source(replace(ORACLE_SPEC, ci_lane=LANE))
        register_data_source(CLICKHOUSE_SPEC)
        names = {spec.public_name for spec in load_upstream_facts().specs}
        assert names == {"Oracle", "ClickHouse"}


def _oracle_variant(label: str, *, lane: bool) -> DataSourceSpec:
    return replace(
        ORACLE_SPEC,
        label=label,
        marker=label,
        ci_lane=LANE if lane else None,
        tiers=ORACLE_SPEC.tiers if lane else frozenset(),
    )


@POSITIONS
def test_the_loader_fails_when_any_one_of_several_records_under_the_name_has_no_lane(decisive):
    labels = ("oracle-a", "oracle-b", "oracle-c")
    with isolated_registry():
        for position, label in enumerate(labels):
            register_data_source(_oracle_variant(label, lane=position != decisive))
        with pytest.raises(UpstreamDeclarationError, match=rf"\['{labels[decisive]}'\]"):
            load_upstream_facts()


def test_the_loader_accepts_several_records_under_the_name_when_every_one_has_a_lane():
    # The control for the failing cases above.
    with isolated_registry():
        for label in ("oracle-a", "oracle-b", "oracle-c"):
            register_data_source(_oracle_variant(label, lane=True))
        register_data_source(CLICKHOUSE_SPEC)
        assert len(load_upstream_facts().specs) == 4


KEYED_SOURCES = ("Alpha Source", "Oracle", "Zulu Source")  # sorted, so first, middle and last


def _register_keyed_sources(*, unpublished: str = "", laneless: str = "") -> None:
    for name in KEYED_SOURCES:
        if name == unpublished:
            continue
        if name == "Oracle":
            record = _oracle_variant("oracle", lane=name != laneless)
        else:
            record = _record(
                name.lower().replace(" ", "-"),
                name,
                lane=None if name == laneless else LANE,
                tiers=frozenset() if name == laneless else frozenset({SupportTier.FLUENT_API}),
            )
        register_data_source(record)


@pytest.fixture
def three_version_keys(monkeypatch):
    monkeypatch.setattr(
        upstream_declarations,
        "TESTED_VERSION_NOTES",
        {name: f"Tested against {name} 1." for name in KEYED_SOURCES},
    )


def test_the_loader_accepts_a_version_map_whose_every_key_is_published_with_a_lane(
    three_version_keys,
):
    # The control for the failing cases below.
    with isolated_registry():
        _register_keyed_sources()
        register_data_source(CLICKHOUSE_SPEC)
        assert len(load_upstream_facts().specs) == 4


@pytest.mark.parametrize("name", KEYED_SOURCES, ids=["first-key", "middle-key", "last-key"])
def test_the_loader_checks_every_key_of_the_version_map_for_a_published_row(
    three_version_keys, name
):
    with isolated_registry():
        _register_keyed_sources(unpublished=name)
        with pytest.raises(
            UpstreamDeclarationError, match="resolves to no published row"
        ) as raised:
            load_upstream_facts()
    assert f"names {name!r}" in str(raised.value)


@pytest.mark.parametrize("name", KEYED_SOURCES, ids=["first-key", "middle-key", "last-key"])
def test_the_loader_checks_every_key_of_the_version_map_for_a_lane(three_version_keys, name):
    with isolated_registry():
        _register_keyed_sources(laneless=name)
        with pytest.raises(
            UpstreamDeclarationError, match="declare no continuous-integration lane"
        ) as raised:
            load_upstream_facts()
    assert f"names {name!r}" in str(raised.value)


# --- order, composition, and the live rows ---------------------------------------------------


@WITH_CASE_DESCRIPTIONS
def test_every_note_kind_is_appended_after_the_disagreement_notes_in_a_fixed_order(monkeypatch):
    monkeypatch.setitem(
        upstream_declarations.TESTED_VERSION_NOTES, "Throwaway Source", "Version bound."
    )
    facts = _facts(
        _record(
            "a",
            "Throwaway Source",
            tiers=ALL_THREE,
            exclusions={SupportTier.CANONICAL_EXPECTATIONS: {"some_case": "Not run."}},
        ),
        _record(
            "b",
            "Throwaway Source",
            tiers=frozenset({SupportTier.CANONICAL_EXPECTATIONS}),
            fluent_types=frozenset({"pandas_filesystem"}),
            provisioning=CREDENTIALS,
            provisioning_note="Needs a tenant.",
        ),
        covered=frozenset({"b"}),
    )
    assert _notes_of(facts, "Throwaway Source") == (
        f"Every shipped expectation: not met for {CSV_DESCRIPTION}.",
        f"Datasource API contract: not met for {CSV_DESCRIPTION}.",
        COVERED_NOTE,
        f"Expectation suite, {PANDAS_DESCRIPTION}: not run for the shared check. "
        f"Recorded reason: Not run.",
        MANAGED_NOTE,
        "Version bound.",
    )


def test_the_notes_every_real_row_carries_are_exactly_these():
    # Printed from the live declarations and pinned by hand. A row not listed carries none.
    live = {name: notes for name, notes in _live_notes().items() if notes}
    assert live == {
        "AlloyDB": (COVERED_NOTE,),
        "Amazon Aurora PostgreSQL": (COVERED_NOTE,),
        "Azure Blob Storage": (COVERED_NOTE,),
        "Citus": (COVERED_NOTE,),
        "ClickHouse": (
            "Expectation suite: not run for column names that need quoting. Recorded reason: This "
            "dialect's SQLAlchemy/driver insert path keys each row by the sanitized "
            "bind-parameter name instead of the real column name for identifiers requiring "
            "quoting, raising a `KeyError` at insert time and leaving the table empty. An issue "
            "still needs to be filed for this defect.",
        ),
        "Microsoft Fabric": (COVERED_NOTE, MANAGED_NOTE),
        "Neon": (COVERED_NOTE,),
        "Oracle": (ORACLE_NOTE,),
        "Pandas": (
            f"Datasource API contract, {PANDAS_DESCRIPTION}: not run for keeping a single saved "
            "entry after create-or-update, replacing an existing datasource on create-or-update "
            "and replacing a datasource's configuration on update. Recorded reason: "
            "PandasDatasource "
            "declares no field beyond name, type, identifier and assets, so no update of its "
            "configuration can be observed to have replaced anything.",
        ),
    }
