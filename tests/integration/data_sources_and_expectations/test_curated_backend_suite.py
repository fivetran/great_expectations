"""The curated-tier suite: a small, blocking suite every curated-tier backend inherits.

A backend joins this suite by declaring curated-tier membership on its own backend declaration
(see `tests/integration/test_utils/data_source_config/backend_spec.py`) — no edit to this module
is required. Every case below is parameterized through
`data_sources_for_tier_case(BackendTier.CURATED_SQL, <case key>)` rather than directly over
`CURATED_SQL_DATA_SOURCES`, so a downstream backend's declared exclusion for a case takes effect
uniformly across every case in the suite. A case parameterized over the raw list instead would
silently ignore that backend's exclusion for exactly that case, which is worse than having no
exclusion mechanism at all: it would look excluded in the declaration but still run.

No backend declares an exclusion at the point this module was written, so every accessor call
below returns the full curated list, and the collected parameterization is identical to
parameterizing directly over `CURATED_SQL_DATA_SOURCES`. The mechanism is inert here but present.

This module also publishes the suite's case keys as `CURATED_CASE_KEYS`, a module-level frozen
set, and carries the two guards that consume it. Both guards live here rather than in the registry
test module because they need this module's own published key set — a registry test importing an
integration suite would run the dependency the wrong direction.
"""

from typing import FrozenSet, List

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.expectations.row_conditions import Column
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BackendTier,
    DataSourceTestConfig,
    data_sources_for_tier_case,
    iter_sql_backends,
)
from tests.integration.test_utils.data_source_config.singlestore import (
    SingleStoreDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.tiers import CURATED_SQL_DATA_SOURCES

# Every case key this suite defines. A backend excludes a case by name, so this name is the one
# thing a backend's `tier_case_exclusions` declaration and this suite must agree on; renaming or
# removing a case here without updating a backend's declaration is exactly what
# `test_every_declared_exclusion_key_is_a_published_case_key` below is meant to catch.
#
# Eight keys, not eleven test functions: `QUOTED_IDENTIFIERS` is one case covering four assertions
# (a spaced, a reserved-word, and a mixed-case column name, plus uniqueness under quoting) because
# all four exercise the same quoted-identifier code path and a backend excluding one would have no
# reason to keep the others.
VALUE_SET_VALIDATION = "value_set_validation"
NUMERIC_AGGREGATION = "numeric_aggregation"
ROW_COUNT = "row_count"
REGEX_MATCH = "regex_match"
UNIQUENESS = "uniqueness"
ROW_CONDITION = "row_condition"
UNEXPECTED_ROWS_QUERY = "unexpected_rows_query"
QUOTED_IDENTIFIERS = "quoted_identifiers"

CURATED_CASE_KEYS: FrozenSet[str] = frozenset(
    {
        VALUE_SET_VALIDATION,
        NUMERIC_AGGREGATION,
        ROW_COUNT,
        REGEX_MATCH,
        UNIQUENESS,
        ROW_CONDITION,
        UNEXPECTED_ROWS_QUERY,
        QUOTED_IDENTIFIERS,
    }
)


def _sources(case_key: str) -> List[DataSourceTestConfig]:
    """The curated tier's members for one case, routed through the per-case exclusion accessor.

    Every case in this module calls this helper rather than reading `CURATED_SQL_DATA_SOURCES`
    directly, so a backend's declared exclusion for `case_key` is honored no matter which case
    asks."""
    return data_sources_for_tier_case(BackendTier.CURATED_SQL, case_key)


DATA = pd.DataFrame(
    {
        "name": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
    }
)

QUOTED_IDENTIFIER_DATA = pd.DataFrame(
    {
        "user name": ["Alice", "Bob", "Charlie"],
        "select": [10, 20, 30],
        "UserName": ["alice", "bob", "charlie"],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=_sources(VALUE_SET_VALIDATION), data=DATA)
def test_value_set_validation(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeInSet(
            column="name",
            value_set=["Alice", "Bob", "Charlie"],
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=_sources(NUMERIC_AGGREGATION), data=DATA)
def test_numeric_aggregation(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnSumToBeBetween(
            column="age",
            min_value=89,
            max_value=91,
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=_sources(ROW_COUNT), data=DATA)
def test_row_count(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectTableRowCountToBeBetween(
            min_value=3,
            max_value=3,
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=_sources(REGEX_MATCH), data=DATA)
def test_regex_match(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToMatchRegex(
            column="name",
            regex="^[A-Z].*",
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=_sources(UNIQUENESS), data=DATA)
def test_uniqueness(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeUnique(
            column="name",
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=_sources(ROW_CONDITION), data=DATA)
def test_row_condition(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeUnique(
            column="name",
            row_condition=Column("name").is_not_in(["Alice"]),
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=_sources(UNEXPECTED_ROWS_QUERY), data=DATA)
def test_unexpected_rows_query(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query="SELECT * FROM {batch} WHERE age < 0",
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=_sources(QUOTED_IDENTIFIERS), data=QUOTED_IDENTIFIER_DATA
)
def test_column_with_space(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeInSet(
            column="user name",
            value_set=["Alice", "Bob", "Charlie"],
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=_sources(QUOTED_IDENTIFIERS), data=QUOTED_IDENTIFIER_DATA
)
def test_column_with_reserved_word(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnSumToBeBetween(
            column="select",
            min_value=59,
            max_value=61,
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=_sources(QUOTED_IDENTIFIERS), data=QUOTED_IDENTIFIER_DATA
)
def test_unique_values_quoted_column(batch_for_datasource: Batch) -> None:
    """Exercises the quoted-identifier path in the uniqueness temp-table logic."""
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeUnique(
            column="user name",
        )
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=_sources(QUOTED_IDENTIFIERS), data=QUOTED_IDENTIFIER_DATA
)
def test_mixed_case_column(batch_for_datasource: Batch) -> None:
    """Verifies that a mixed-case column name round-trips correctly through quoting."""
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeInSet(
            column="UserName",
            value_set=["alice", "bob", "charlie"],
        )
    )
    assert result.success


@pytest.mark.project
def test_every_declared_exclusion_key_is_a_published_case_key() -> None:
    """Every case key any registered backend excludes must be one this module actually defines.

    Vacuously true today: no backend declares an exclusion. It stays here anyway, because without
    it a typo'd or stale case key would silently exclude nothing while reading, on inspection, as
    a completed exclusion.
    """
    assert CURATED_CASE_KEYS, "the curated suite must publish at least one case key"

    for config_class in iter_sql_backends():
        for excluded_key in config_class.BACKEND_SPEC.tier_case_exclusions:
            assert excluded_key in CURATED_CASE_KEYS, (
                f"{config_class.__name__} declares a tier case exclusion for "
                f"{excluded_key!r}, which is not one of this suite's published case keys "
                f"{sorted(CURATED_CASE_KEYS)!r}"
            )


@pytest.mark.project
def test_case_accessor_matches_full_curated_list_while_no_exclusions_are_declared() -> None:
    """For every published case key, the exclusion accessor returns the whole curated list.

    True precisely because no backend declares an exclusion right now; the published-key form of
    the same behavior-preservation oracle that guards the accessor at the registry level. The
    registry test module compares call-time membership to call-time membership because its own
    autouse fixture clears the registry around every test; this module carries no such fixture, so
    the registry stays live for the whole run and comparing against `CURATED_SQL_DATA_SOURCES`
    (built once, at this package's import time, from that same live registry) is exact here.
    """
    for case_key in CURATED_CASE_KEYS:
        assert data_sources_for_tier_case(BackendTier.CURATED_SQL, case_key) == (
            CURATED_SQL_DATA_SOURCES
        )


@pytest.mark.project
def test_singlestore_declares_no_case_exclusions() -> None:
    """SingleStore's exclusion ceiling is zero, not the general two.

    Every case in this suite is one of the eight assertion groups this module ports from the
    hand-written module it replaces, so for SingleStore an exclusion here would not be reduced
    coverage — it would be an assertion that held against a running SingleStore instance before
    this suite existed and no longer holds after it. That is a regression, not a triage decision,
    so it is asserted directly rather than left to the general per-backend ceiling.
    """
    assert SingleStoreDatasourceTestConfig.BACKEND_SPEC.tier_case_exclusions == {}
