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
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, FrozenSet, Iterable, Tuple

from tests.compatibility_reference.upstream_declarations import SupportTier


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
