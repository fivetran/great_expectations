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
    tier_for,
)
from tests.compatibility_reference.upstream_declarations import (
    SupportTier,
    UpstreamDeclarationError,
    UpstreamFacts,
    load_upstream_facts,
)
from tests.integration.test_utils.data_source_config import (
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
) -> DataSourceSpec:
    return DataSourceSpec(
        label=label,
        public_name=public_name,
        provisioning=DataSourceProvisioning.IN_PROCESS,
        fluent_types=fluent_types,
        marker=label,
        tiers=tiers,
        tier_case_exclusions=exclusions or {},
        ci_lane=lane,
    )


def _facts(
    *specs: DataSourceSpec, fluent_exclusions: Optional[Mapping[str, Mapping[str, str]]] = None
) -> UpstreamFacts:
    return UpstreamFacts(
        specs=specs,
        covered_but_unable_to_claim=frozenset(),
        fluent_types_named_by_no_record=frozenset(),
        fluent_case_exclusions=fluent_exclusions or {},
    )


def _rows_in_seam(*records: DataSourceSpec) -> Tuple[PublishedRow, ...]:
    """Register the records in an emptied registry and assemble what the loader returns.

    The loader raises about the Oracle version note unless an Oracle record with a lane is
    registered, so the real Oracle record goes in beside the throwaways.
    """
    with isolated_registry():
        register_data_source(ORACLE_SPEC)
        for record in records:
            register_data_source(record)
        return assemble_rows(load_upstream_facts())


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
    assert rows[0].notes == ()


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
    assert [row.public_name for row in rows] == ["Alpha", "alpha2", "beta", "Oracle", "Zed"]


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
    assert row.notes == ()


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


def test_a_met_criterion_is_partial_when_a_fluent_type_a_record_names_excludes_a_case():
    facts = _facts(
        _record("variant-a", "Throwaway Source", tiers=ALL_THREE),
        fluent_exclusions={"pandas": {"a_case": REASON}},
    )
    (row,) = assemble_rows(facts)
    assert row.criteria_met == frozenset({GALLERY, SUITE, API})
    assert row.criteria_partial == frozenset({API})
    assert row.notes == ()


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
