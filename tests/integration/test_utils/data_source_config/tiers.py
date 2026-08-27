"""Single definition of the standard and curated data-source lists.

Before this module existed, two conftest modules each hand-maintained their own copy of these
lists, and the copies had already drifted: one defined a combined list the other did not. A
backend added to one copy and forgotten in the other would silently under-test without any
signal, since nothing checked the two against each other.

Every list here is now derived from data-source declarations rather than hand-maintained: a data
source states what it is and what it claims once, on its own declaration (see `data_source_spec.py`
and its SQL sub-record in `backend_spec.py`), and this module reads that declaration through the
registry rather than naming data sources itself. That leaves only one place membership is stated —
the declaration — instead of a second, hand-maintained copy these lists could drift from.

The lists are derived on two different keys, and the difference is not an inconsistency: it is the
difference between the two kinds of thing being asked.

- A **tier** is a claim about coverage. `BackendTier.STANDARD_SQL` and `BackendTier.CURATED_SQL`
  say "a suite runs against this backend and proves this much", which is something a maintainer
  decides and a backend can join or leave without anything about the backend itself changing. The
  two SQL lists key on that claim, because they exist to answer "what does this tier's suite run
  against".
- An **execution engine** is a fact about the data source. `ExecutionEngineKind.PANDAS` and
  `ExecutionEngineKind.SPARK` say what actually executes the tests; no maintainer decision moves a
  Spark data source onto pandas. The pandas and Spark lists key on that fact, because they exist to
  answer "which data sources does this engine run", a question a coverage claim cannot answer.

Keying either list on the other's question would state something untrue: a tier claim would make
an engine look optional, and an engine would make a coverage claim look like a property of the
data source.

Stating membership in one place is not the same as this module seeing it, though: the lists below
are built once, when this module is first imported, from whatever the registry holds at that
moment, so a data source module imported after this one has not yet run its registration and is
silently absent from every list even though it is declared and registered. This package's
`__init__.py` imports every data source module before this one for exactly that reason; the
regression test in `tests/test_sql_backend_registry.py` that guards the ordering is what turns a
violation of it into a failing test instead of a silent gap.

This module reads the registry and imports nothing else from this package at runtime. It sits to
the right of every other module in this package's dependency direction (see `sql_config.py`'s
module docstring), so nothing else in this package may import it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, List, cast

from tests.integration.test_utils.data_source_config.data_source_spec import (
    BackendTier,
    ExecutionEngineKind,
)
from tests.integration.test_utils.data_source_config.registry import (
    data_source_configs_for_engine,
    sql_backends_for_tier,
)

if TYPE_CHECKING:
    from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig

# Both engine-keyed lists below, and both tier-keyed lists after them, take the same `cast`:
# the registry accessors are typed against its minimal registration protocol, not against
# `DataSourceTestConfig`, so that `registry.py` need not import the config base (see this
# package's dependency direction, stated in `sql_config.py`). Every class the registry hands back
# is a `DataSourceTestConfig`, because only a config class can be enrolled with one; the cast
# states that fact at the four places it matters instead of widening the registry's return type.
#
# `data_source_configs_for_engine` walks config-bound entries only, so the records registered
# without a config class — the data sources this repository declares but does not exercise — are
# not reachable from these lists at all, whatever engine they might name.

PANDAS_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    cast("DataSourceTestConfig", config_class())
    for config_class in data_source_configs_for_engine(ExecutionEngineKind.PANDAS)
]
"""Every registered config declaring `ExecutionEngineKind.PANDAS`, instantiated with no arguments,
in label order (the order `data_source_configs_for_engine` itself returns)."""

SPARK_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    cast("DataSourceTestConfig", config_class())
    for config_class in data_source_configs_for_engine(ExecutionEngineKind.SPARK)
]
"""Every registered config declaring `ExecutionEngineKind.SPARK`, instantiated with no arguments,
in label order."""

SQL_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    cast("DataSourceTestConfig", config_class())
    for config_class in sql_backends_for_tier(BackendTier.STANDARD_SQL)
]
"""Every registered backend declaring `BackendTier.STANDARD_SQL` membership, instantiated with no
arguments, in label order."""

CURATED_SQL_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    cast("DataSourceTestConfig", config_class())
    for config_class in sql_backends_for_tier(BackendTier.CURATED_SQL)
]
"""Every registered backend declaring `BackendTier.CURATED_SQL` membership, instantiated with no
arguments, in label order. Empty until a backend declares that tier; four do today."""

ALL_DATA_SOURCES: Final[List[DataSourceTestConfig]] = (
    PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES + SQL_DATA_SOURCES
)


def data_sources_for_tier_case(tier: BackendTier, case_key: str) -> List[DataSourceTestConfig]:
    """The tier's members, minus any declaring a `tier_case_exclusions` entry for `case_key`.

    A backend joins a tier as a whole; `tier_case_exclusions` (declared on `SqlBackendSpec`, see
    `backend_spec.py`) is the one way a member can sit out a single named case within that tier's
    suite instead of the whole tier. This accessor is the only place that mapping takes effect —
    registration validates it, but nothing else filters tier membership by case — which keeps
    "does this exclusion take
    effect" a one-module question instead of a property every future consumer has to reimplement
    correctly. It is written to take a tier and a case key, not to be specialized to one tier: the
    exclusion mechanism belongs to tiers in general, and a version hard-coded to one tier would
    have to be undone the moment a second tier needs the same mechanism.

    Unlike the module-level lists above, this reads the registry fresh on every call (through
    `sql_backends_for_tier`, itself call-time) rather than once at import — the exclusion mapping
    it filters on can only be known per call, from the tier's live membership, not baked into a
    list built before any caller has said which case it means.

    Returns instances, in the tier's label order, with an empty exclusion mapping on every member
    yielding exactly that tier's derived list.
    """
    return [
        cast("DataSourceTestConfig", config_class())
        for config_class in sql_backends_for_tier(tier)
        if case_key not in config_class.BACKEND_SPEC.tier_case_exclusions
    ]
