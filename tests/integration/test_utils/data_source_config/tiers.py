"""Single definition of the standard and curated data-source lists.

Before this module existed, two conftest modules each hand-maintained their own copy of these
lists, and the copies had already drifted: one defined a combined list the other did not. A
backend added to one copy and forgotten in the other would silently under-test without any
signal, since nothing checked the two against each other.

The two SQL lists here are derived from backend declarations rather than hand-maintained: a
backend states its tier membership once, on its own declaration (see `backend_spec.py`), and
this module reads that declaration through the registry rather than naming backends itself. That
leaves only one place a backend's tier membership is stated — its own declaration — instead of a
second, hand-maintained copy these lists could drift from. Stating membership in one place is not
the same as this module seeing it, though: the lists below are built once, when this module is
first imported, from whatever the registry holds at that moment, so a backend module imported
after this one has not yet run its registration and is silently absent from both lists even
though it is declared and registered. This package's `__init__.py` imports every backend module
before this one for exactly that reason; the regression test in
`tests/test_sql_backend_registry.py` that guards the ordering is what turns a violation of it into
a failing test instead of a silent gap. The pandas and Spark lists stay hand-written literals
because those data sources have no equivalent declarative record to read membership from;
deriving them would need a registry this module does not have anything to key off, so they remain
exactly what they were before this module existed.

This module imports the pandas and Spark config modules directly to build the two literal,
non-SQL lists - those configs carry no declaration to read membership from - and reads the
registry to build the two derived, SQL lists. It sits to the right of every other
module in this package's dependency direction (see `sql_config.py`'s module docstring), so
nothing else in this package may import it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, List, cast

from tests.integration.test_utils.data_source_config.backend_spec import BackendTier
from tests.integration.test_utils.data_source_config.pandas_data_frame import (
    PandasDataFrameDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.pandas_filesystem_csv import (
    PandasFilesystemCsvDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.registry import sql_backends_for_tier
from tests.integration.test_utils.data_source_config.spark_filesystem_csv import (
    SparkFilesystemCsvDatasourceTestConfig,
)

if TYPE_CHECKING:
    from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig

PANDAS_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    PandasFilesystemCsvDatasourceTestConfig(),
    PandasDataFrameDatasourceTestConfig(),
]

SPARK_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    SparkFilesystemCsvDatasourceTestConfig(),
]

SQL_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    # `sql_backends_for_tier` is typed against the registry's minimal registration protocol, not
    # against `DataSourceTestConfig`, so that `registry.py` need not import the SQL config base
    # (see this package's dependency direction, stated in `sql_config.py`). Every class actually
    # registered is a `SqlDatasourceTestConfig` — and therefore a `DataSourceTestConfig` — because
    # `register_sql_backend` is only ever applied to one; the cast below states that fact at the
    # one place it matters instead of widening the registry's own return type.
    cast("DataSourceTestConfig", config_class())
    for config_class in sql_backends_for_tier(BackendTier.STANDARD_SQL)
]
"""Every registered backend declaring `BackendTier.STANDARD_SQL` membership, instantiated with no
arguments, in label order (the order `sql_backends_for_tier` itself returns)."""

CURATED_SQL_DATA_SOURCES: Final[List[DataSourceTestConfig]] = [
    cast("DataSourceTestConfig", config_class())
    for config_class in sql_backends_for_tier(BackendTier.CURATED_SQL)
]
"""Every registered backend declaring `BackendTier.CURATED_SQL` membership, instantiated with no
arguments, in label order. Empty until a backend declares that tier."""

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
