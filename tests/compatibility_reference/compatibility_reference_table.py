"""What the public support tiers mean, declared once.

Each data source is placed in one of three public tiers by the criteria it meets. This module
is the only place that states which declarations satisfy each criterion and which combination
of criteria yields each tier. Tier placement and the per-row display of criteria both read it,
so a row's tier and the criteria shown beside it cannot disagree.

Principles the declarations below encode:

* Tier names do not reuse the names of the declarations behind them. The top tier is a
  conjunction of two criteria and no single declaration names a conjunction, so printing a
  declaration name would imply a correspondence that cannot exist.
* The lowest tier asserts nothing about who wrote or maintains a connection path. Most paths in
  it are maintained in the shipped package.
* The datasource API criterion is a claim about managing a data source, made with connection
  testing neutralized. It says nothing about whether expectations run, so it is displayed but
  never lifts a row out of the lowest tier.
* The full-gallery criterion without the datasource API criterion is the middle tier. Such a
  data source has passed every expectation the shipped package registers, which is more than the
  middle tier asks for; placing it lowest because it lacks a criterion about managing a data
  source would understate it. No record produces that combination today, and the mapping is
  specified over every combination anyway: a mapping correct only for the combinations that
  happen to occur is wrong the first time one changes.
* A declaration no criterion names is legal and silent. Rows are unaffected by it.
* A row is one public name, which several records may share. A criterion is met by a row only
  when every record under that name declares it, so one tested variant cannot advertise coverage
  for an untested sibling. A declared continuous-integration lane is evidence of nothing: it
  means dependencies are installed and something runs, whereas a tier means a suite passes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Dict, Final, FrozenSet, Iterable, List, Tuple

from tests.compatibility_reference.upstream_declarations import (
    CONNECTION_PATH_DESCRIPTIONS,
    SupportTier,
    UpstreamDeclarationError,
    UpstreamFacts,
)

if TYPE_CHECKING:
    from tests.integration.test_utils.data_source_config import DataSourceSpec


class PublicTier(Enum):
    FULLY_SUPPORTED = "Fully supported"
    TESTED = "Tested"
    BEST_EFFORT = "Best effort"


@dataclass(frozen=True)
class Criterion:
    key: str
    label: str
    """The public phrase printed on a row."""
    declarations: FrozenSet[SupportTier]
    """The declarations that satisfy this criterion. Any one of them suffices."""


GALLERY_KEY: Final = "gallery"
EXPECTATION_SUITE_KEY: Final = "expectation_suite"
DATASOURCE_API_KEY: Final = "datasource_api"

CRITERIA: Final[Tuple[Criterion, ...]] = (
    Criterion(
        key=GALLERY_KEY,
        label="Every shipped expectation",
        declarations=frozenset({SupportTier.GALLERY}),
    ),
    Criterion(
        key=EXPECTATION_SUITE_KEY,
        label="Expectation suite",
        declarations=frozenset({SupportTier.CANONICAL_EXPECTATIONS, SupportTier.CURATED_SQL}),
    ),
    Criterion(
        key=DATASOURCE_API_KEY,
        label="Datasource API contract",
        declarations=frozenset({SupportTier.FLUENT_API}),
    ),
)
"""Ordered; the display order of the criteria cell."""


def criteria_met_by(declarations: Iterable[SupportTier]) -> FrozenSet[str]:
    """The criterion keys satisfied by a collection of declarations.

    A declaration no criterion names contributes nothing and is not an error.
    """
    held = frozenset(declarations)
    return frozenset(
        criterion.key for criterion in CRITERIA if not criterion.declarations.isdisjoint(held)
    )


def tier_for(met: FrozenSet[str]) -> PublicTier:
    """The public tier yielded by a set of met criterion keys.

    Total over every subset of the criterion keys, including combinations no record produces.
    A key that names no criterion is ignored.
    """
    gallery = GALLERY_KEY in met
    suite = EXPECTATION_SUITE_KEY in met
    api = DATASOURCE_API_KEY in met
    if gallery and api:
        return PublicTier.FULLY_SUPPORTED
    if gallery or suite:
        return PublicTier.TESTED
    return PublicTier.BEST_EFFORT


@dataclass(frozen=True)
class PublishedRow:
    public_name: str
    specs: Tuple[DataSourceSpec, ...]
    """Every record carrying this public name, ordered by label."""
    criteria_met: FrozenSet[str]
    """Criterion keys every record in the row declares."""
    criteria_partial: FrozenSet[str]
    """Met, but with a recorded exclusion inside that criterion's suite.

    Assembly fills it: a met criterion is partial when a contributing record excludes a case
    under a declaration that satisfies the criterion, or, for the datasource API criterion,
    when a fluent type a contributing record names has excluded cases. A criterion that is not
    met is never partial, because it claims nothing for an exclusion to qualify. Assembly only
    marks the criterion; saying which case is excluded, and why, is left to the note derivation.
    """
    tier: PublicTier
    notes: Tuple[str, ...]
    """Where variants disagree about a criterion, one note per such criterion, in criterion
    order, naming the variants that fall short by what they connect to."""


def _variant_description(spec: DataSourceSpec) -> str:
    """A reader-facing phrase for one record, from the fluent types it declares.

    Neither the harness label (internal) nor the public name (shared by every variant) can tell
    two variants apart to a reader, and a type literal is an internal identifier, so the phrase
    comes from the declared description of each type. A record reached through several types is
    described by all of them.
    """
    if not spec.fluent_types:
        raise UpstreamDeclarationError(
            f"Records under {spec.public_name!r} disagree about a criterion, but the record "
            f"labelled {spec.label!r} declares no fluent datasource type, so nothing user-facing "
            f"can tell it apart from its siblings. Declare the type it is reached through."
        )
    undescribed = sorted(spec.fluent_types - CONNECTION_PATH_DESCRIPTIONS.keys())
    if undescribed:
        raise UpstreamDeclarationError(
            f"The record labelled {spec.label!r} declares fluent datasource type(s) {undescribed} "
            f"that CONNECTION_PATH_DESCRIPTIONS does not describe; an internal identifier must "
            f"not be printed in its place."
        )
    return " and ".join(sorted(CONNECTION_PATH_DESCRIPTIONS[t] for t in spec.fluent_types))


def _partial_criteria(
    met: FrozenSet[str], ordered: Tuple[DataSourceSpec, ...], facts: UpstreamFacts
) -> FrozenSet[str]:
    """The met criteria that carry a recorded per-case exclusion."""
    partial = set()
    for criterion in CRITERIA:
        if criterion.key not in met:
            continue
        recorded = any(
            exclusions and tier in criterion.declarations
            for spec in ordered
            for tier, exclusions in spec.tier_case_exclusions.items()
        )
        fluent = criterion.key == DATASOURCE_API_KEY and any(
            facts.fluent_case_exclusions.get(fluent_type)
            for spec in ordered
            for fluent_type in spec.fluent_types
        )
        if recorded or fluent:
            partial.add(criterion.key)
    return frozenset(partial)


def _assemble_row(
    public_name: str, specs: Iterable[DataSourceSpec], facts: UpstreamFacts
) -> PublishedRow:
    ordered = tuple(sorted(specs, key=lambda spec: spec.label))
    # One call per record, then an intersection. Calling it on the union of every record's
    # declarations would let two records that each lack a criterion jointly satisfy it.
    per_record = [criteria_met_by(spec.tiers) for spec in ordered]
    met = frozenset.intersection(*per_record)
    notes: List[str] = []
    for criterion in CRITERIA:
        short = [
            spec
            for spec, held in zip(ordered, per_record, strict=True)
            if criterion.key not in held
        ]
        if short and criterion.key in frozenset.union(*per_record):
            meeting = [spec for spec in ordered if spec not in short]
            for spec in short:
                shared = sorted(
                    spec.fluent_types & frozenset().union(*(m.fluent_types for m in meeting))
                )
                if shared:
                    raise UpstreamDeclarationError(
                        f"Records under {public_name!r} disagree about {criterion.label!r}, but "
                        f"the record labelled {spec.label!r} shares fluent datasource type(s) "
                        f"{shared} with a record that meets it, so no public-facing description "
                        f"distinguishes the variant that falls short from the ones that do not. "
                        f"Give the records distinct fluent types, or declare the criterion "
                        f"consistently across them."
                    )
            variants = "; ".join(sorted({_variant_description(spec) for spec in short}))
            notes.append(f"{criterion.label}: not met for {variants}.")
    return PublishedRow(
        public_name=public_name,
        specs=ordered,
        criteria_met=met,
        criteria_partial=_partial_criteria(met, ordered, facts),
        tier=tier_for(met),
        notes=tuple(notes),
    )


def assemble_rows(facts: UpstreamFacts) -> Tuple[PublishedRow, ...]:
    """One row per distinct public name, ordered case-insensitively by that name.

    Raises:
        ValueError: when the registry yields no record, so no row, or when a record carries no
            public name. An empty table would read as a data source list that legitimately
            shrank, and a dropped record is how a data source vanishes from a page nothing checks.
    """
    if not facts.specs:
        raise ValueError(
            "The data source registry yields no record, so there is no row to publish. An empty "
            "table would claim GX supports nothing; check that the registry is populated."
        )
    by_name: Dict[str, List[DataSourceSpec]] = {}
    for spec in facts.specs:
        if not spec.public_name or not spec.public_name.strip():
            raise ValueError(
                f"The record labelled {spec.label!r} carries no public name. It cannot be "
                f"dropped, since a dropped record disappears from the published table unnoticed, "
                f"and no name can be derived for it."
            )
        if spec.public_name != spec.public_name.strip():
            raise ValueError(
                f"The public name {spec.public_name!r} (record labelled {spec.label!r}) has "
                f"leading or trailing whitespace, so it would publish a row that looks identical "
                f"to one without. Remove the whitespace from the declaration."
            )
        by_name.setdefault(spec.public_name, []).append(spec)
    folded: Dict[str, str] = {}
    for name in sorted(by_name):
        if folded.setdefault(name.casefold(), name) != name:
            raise ValueError(
                f"The public names {folded[name.casefold()]!r} and {name!r} differ only in "
                f"letter case, so they would publish two rows that look like one. Declare one "
                f"spelling for the data source."
            )
    return tuple(
        _assemble_row(name, by_name[name], facts)
        for name in sorted(by_name, key=lambda name: (name.casefold(), name))
    )
