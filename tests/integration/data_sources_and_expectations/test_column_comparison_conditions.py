"""Column-to-column row conditions, verified on every canonical data source.

A row condition that compares two columns is rendered by three different engines (pandas, Spark and
SQLAlchemy), each with its own operator semantics. This module is the end-to-end check that they
agree on which rows survive the filter.

Two design choices keep the cases honest:

* Rows are observed through ``ExpectColumnDistinctValuesToEqualSet`` on an id column, so the case
  passes only when the filtered rows' ids are exactly the expected ones. Asserting ``success`` on
  an aggregate alone cannot tell "filtered correctly" from "filtered nothing".
* The expected ids come from a Python oracle that applies the operator to the non-null pairs of the
  same data the backend loaded, never from the code under test. Every case must also expect a
  non-empty proper subset of all ids, so a filter that selects every row, or none, cannot pass.

Column names here avoid the substrings ``AND``, ``OR`` and ``NOT`` (in any case): the atomic
row-condition renderer splits on them even inside a name, which is unrelated to what this module
verifies.
"""

from __future__ import annotations

import math
import operator
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping, Sequence

import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.compatibility.aws import REDSHIFT_TYPES
from great_expectations.compatibility.bigquery import BIGQUERY_TYPES
from great_expectations.compatibility.postgresql import POSTGRESQL_TYPES
from great_expectations.compatibility.snowflake import SNOWFLAKE_TYPES
from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.compatibility.typing_extensions import override
from great_expectations.execution_engine.pandas_batch_data import PandasBatchData
from great_expectations.expectations.row_conditions import (
    AndCondition,
    Column,
    ColumnComparisonCondition,
    ComparisonCondition,
    Condition,
    NullityCondition,
    OrCondition,
    PassThroughCondition,
    RowConditionType,
)
from tests.integration.conftest import TestConfig as _TestConfig
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    ALL_DATA_SOURCES,
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqlDatasourceTestConfig,
    SqliteDatasourceTestConfig,
    SQLServerDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    from great_expectations.core.expectation_validation_result import ExpectationValidationResult
    from great_expectations.datasource.fluent.interfaces import Batch
    from great_expectations.datasource.fluent.sql_datasource import TableAsset
    from tests.integration.test_utils.data_source_config import DataSourceTestConfig

ID_COLUMN = "id"

_BATCH_SETUP_FIXTURE_NAME = "_batch_setup_for_datasource"


@pytest.fixture(autouse=True)
def _close_the_connections_of_each_test(request: pytest.FixtureRequest) -> Iterator[None]:
    """Close the database connections each test's batch opened once the test ends.

    Every batch the shared fixtures make adds a data source with its own engines, and those keep
    their pooled connections open until the session ends. At two connections per test, this
    module's SQL cases alone hold enough to exhaust a server's connection limit for the suites
    that run after it, so each test closes its own once it is done with them.
    """
    batch_setup = (
        request.getfixturevalue(_BATCH_SETUP_FIXTURE_NAME)
        if _BATCH_SETUP_FIXTURE_NAME in request.fixturenames
        else None
    )
    yield
    if isinstance(batch_setup, SQLBatchTestSetup):
        batch_setup.dispose_data_source_engines()


Comparison = Callable[[Any, Any], Any]
"""A binary comparison. The same function builds the condition (applied to two ``Column`` objects,
which overload the operators) and the oracle (applied to two plain values), so a case names an
operator once and cannot test one while its oracle checks another."""

OPERATORS = [
    pytest.param(operator.eq, id="eq"),
    pytest.param(operator.ne, id="ne"),
    pytest.param(operator.lt, id="lt"),
    pytest.param(operator.le, id="le"),
    pytest.param(operator.gt, id="gt"),
    pytest.param(operator.ge, id="ge"),
]

# Each pair has two rows where left < right, two where left == right and two where left > right, so
# every operator selects a non-empty proper subset. Each operator selects a different id set on
# each pair, so a condition that reads the wrong pair cannot happen to select the right ids. The int
# pair includes (9, 10) and (10, 9), which order the opposite way as text. The float values are
# exactly representable in binary, so equality is not at the mercy of rounding on any backend.
NUMERIC_DATA = pd.DataFrame(
    {
        ID_COLUMN: [1, 2, 3, 4, 5, 6],
        "int_left": [7, 5, 9, 10, -3, 1],
        "int_right": [3, 5, 10, 9, -3, 2],
        "float_left": [2.5, 0.5, -0.5, -4.0, 3.5, -2.5],
        "float_right": [2.5, 1.5, -1.5, -4.0, 0.25, -0.5],
    }
)

NUMERIC_COLUMN_PAIRS = [
    pytest.param(("int_left", "int_right"), id="int"),
    pytest.param(("float_left", "float_right"), id="float"),
]


def all_ids(frame: pd.DataFrame) -> list[int]:
    return [int(row_id) for row_id in frame[ID_COLUMN]]


def expected_ids(frame: pd.DataFrame, left: str, right: str, compare: Comparison) -> list[int]:
    """The ids whose ``left`` and ``right`` values satisfy ``compare``.

    A row with a missing value on either side never satisfies a comparison, so it is skipped
    rather than handed to the operator.
    """
    selected: list[int] = []
    for row in frame.to_dict("records"):
        left_value, right_value = row[left], row[right]
        if pd.isna(left_value) or pd.isna(right_value):
            continue
        if compare(left_value, right_value):
            selected.append(int(row[ID_COLUMN]))
    return selected


def assert_expectation_discriminates(expected: Iterable[int], every_id: Iterable[int]) -> None:
    """Fail unless ``expected`` is a non-empty proper subset of ``every_id``.

    An expectation that names no row, or every row, passes whether or not the filter worked, so it
    proves nothing about the condition.
    """
    expected_set, every_set = set(expected), set(every_id)
    assert expected_set, "expected ids are empty: a filter that selects no rows would pass"
    assert expected_set < every_set, (
        f"expected ids {sorted(expected_set)} are not a proper subset of {sorted(every_set)}: "
        "a filter that selects every row would pass"
    )


def assert_rows_selected(
    batch: Batch,
    row_condition: Any,
    expected: Sequence[int],
    every_id: Iterable[int],
) -> None:
    """Assert that filtering the batch by ``row_condition`` leaves exactly the ``expected`` ids."""
    assert_expectation_discriminates(expected, every_id)
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(
        column=ID_COLUMN,
        value_set=sorted(expected),
        row_condition=row_condition,
    )
    result = batch.validate(expectation)
    assert result.success, (
        f"{row_condition!r} should select ids {sorted(expected)}; "
        f"result={result.result}, exception_info={result.exception_info}"
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "expected",
    [pytest.param([], id="no_rows"), pytest.param([1, 2, 3], id="every_row")],
)
def test_expectation_that_cannot_discriminate_is_rejected(expected: list[int]) -> None:
    with pytest.raises(AssertionError):
        assert_expectation_discriminates(expected, [1, 2, 3])


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=NUMERIC_DATA)
@pytest.mark.parametrize("column_pair", NUMERIC_COLUMN_PAIRS)
@pytest.mark.parametrize("compare", OPERATORS)
def test_operator_over_numeric_columns(
    batch_for_datasource: Batch,
    column_pair: tuple[str, str],
    compare: Comparison,
) -> None:
    left, right = column_pair
    assert_rows_selected(
        batch_for_datasource,
        compare(Column(left), Column(right)),
        expected_ids(NUMERIC_DATA, left, right, compare),
        all_ids(NUMERIC_DATA),
    )


def _utc(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0
) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


# Again two rows where left < right, two where left == right and two where left > right, with the
# DATE and TIMESTAMP pairs giving those relations to different ids, so no operator selects the same
# ids on both pairs. The timestamps are whole seconds in UTC, so no backend's fractional-second
# precision can turn an equal pair into an unequal one. Four of the six differ only by a second or
# by hours within one day (or across midnight), so a backend that compared timestamps by their
# date part alone would order them wrongly. No value is near a daylight-saving transition, so a
# backend that stores local time cannot move a pair across the relation it was built to have.
DATE_LEFT = [
    date(2021, 1, 30),
    date(2022, 2, 28),
    date(2023, 3, 15),
    date(1999, 12, 31),
    date(2024, 2, 29),
    date(2024, 12, 1),
]
DATE_RIGHT = [
    date(2021, 1, 31),
    date(2021, 12, 25),
    date(2023, 3, 15),
    date(2000, 1, 1),
    date(2024, 2, 29),
    date(2024, 11, 30),
]
TIMESTAMP_LEFT = [
    _utc(2021, 1, 30, 10, 0, 1),
    _utc(2021, 6, 15, 8, 30, 0),
    _utc(2022, 3, 1, 0, 0, 0),
    _utc(2023, 5, 5, 12, 0, 0),
    _utc(2020, 12, 31, 23, 59, 59),
    _utc(2024, 7, 4, 18, 45, 30),
]
TIMESTAMP_RIGHT = [
    _utc(2021, 1, 30, 10, 0, 0),
    _utc(2021, 6, 15, 8, 30, 0),
    _utc(2022, 3, 1, 0, 0, 1),
    _utc(2023, 5, 5, 12, 0, 0),
    _utc(2021, 1, 1, 0, 0, 0),
    _utc(2024, 7, 4, 9, 0, 0),
]

# The names avoid the substrings `AND`, `OR` and `NOT` for the reason given in the module docstring.
DATETIME_DATA = pd.DataFrame(
    {
        ID_COLUMN: [1, 2, 3, 4, 5, 6],
        "date_left": DATE_LEFT,
        "date_right": DATE_RIGHT,
        "ts_left": TIMESTAMP_LEFT,
        "ts_right": TIMESTAMP_RIGHT,
    }
)

# The same rows with each timestamp as the ISO text `str(datetime)` gives, for the backends that
# are loaded from text (see `_STRING_TIMESTAMP_CONFIGS`). Every value has the same fixed-width
# form and offset, so text order is timestamp order and the oracle below holds unchanged.
STRING_TIMESTAMP_DATA = DATETIME_DATA.assign(
    ts_left=[str(value) for value in TIMESTAMP_LEFT],
    ts_right=[str(value) for value in TIMESTAMP_RIGHT],
)

DATETIME_COLUMN_PAIRS = [
    pytest.param(("date_left", "date_right"), id="date"),
    pytest.param(("ts_left", "ts_right"), id="timestamp"),
]

_TIMESTAMP_COLUMNS = ("ts_left", "ts_right")


def _timestamp_columns(column_type: Any) -> dict[str, Any]:
    return dict.fromkeys(_TIMESTAMP_COLUMNS, column_type)


try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    # A Spark schema is positional and must name every column, in the frame's order.
    _SPARK_DATETIME_COLUMN_TYPES: dict[str, Any] = {
        ID_COLUMN: PYSPARK_TYPES.IntegerType,
        "date_left": PYSPARK_TYPES.DateType,
        "date_right": PYSPARK_TYPES.DateType,
        "ts_left": PYSPARK_TYPES.TimestampType,
        "ts_right": PYSPARK_TYPES.TimestampType,
    }
except ModuleNotFoundError:
    _SPARK_DATETIME_COLUMN_TYPES = {}

# DATE needs no declared type on any SQL backend: it is a `datetime.date`, which the shared
# fixture defaults load as a native DATE column everywhere. TIMESTAMP is declared per backend with
# the types `test_expectation_conditions.py` uses for its literal comparisons, plus Redshift, which
# that module omits. SQL Server and SQLite state none there either, and take the default here.
# Keyed by the canonical configuration each entry stands in for.
_NATIVE_TIMESTAMP_CONFIGS: dict[type[DataSourceTestConfig], DataSourceTestConfig] = {
    BigQueryDatasourceTestConfig: BigQueryDatasourceTestConfig(
        column_types=_timestamp_columns(BIGQUERY_TYPES.DATETIME)
    ),
    SQLServerDatasourceTestConfig: SQLServerDatasourceTestConfig(),
    MySQLDatasourceTestConfig: MySQLDatasourceTestConfig(
        column_types=_timestamp_columns(sqltypes.TIMESTAMP(timezone=True))
    ),
    PandasDataFrameDatasourceTestConfig: PandasDataFrameDatasourceTestConfig(),
    # Read back with the dates parsed, so pandas compares dates and timestamps rather than the
    # text a CSV file holds.
    PandasFilesystemCsvDatasourceTestConfig: PandasFilesystemCsvDatasourceTestConfig(
        read_options={
            "parse_dates": ["date_left", "date_right", *_TIMESTAMP_COLUMNS],
            "date_format": "mixed",
        },
    ),
    PostgreSQLDatasourceTestConfig: PostgreSQLDatasourceTestConfig(
        column_types=_timestamp_columns(POSTGRESQL_TYPES.TIMESTAMP)
    ),
    # The same zone-less TIMESTAMP as PostgreSQL, in Redshift's own dialect type.
    RedshiftDatasourceTestConfig: RedshiftDatasourceTestConfig(
        column_types=_timestamp_columns(REDSHIFT_TYPES.TIMESTAMP)
    ),
    SparkFilesystemCsvDatasourceTestConfig: SparkFilesystemCsvDatasourceTestConfig(
        column_types=_SPARK_DATETIME_COLUMN_TYPES
    ),
    SqliteDatasourceTestConfig: SqliteDatasourceTestConfig(),
}

# These two are loaded from ISO text, as `test_expectation_conditions.py` loads them: its comment
# says some backends fail to load datetime objects unless they are strings. What the text becomes
# differs. Databricks declares no type, so the column is a string column and its TIMESTAMP case
# compares strings (ISO text orders the same as the timestamps it spells, which is why the oracle
# still holds, but it is not timestamp comparison). Snowflake declares TIMESTAMP_TZ, so the server
# parses the text into a timestamp column. Where a case compares strings rather than timestamps,
# the DATE case, loaded as a native DATE column on every backend, is that backend's date/time
# evidence.
_STRING_TIMESTAMP_CONFIGS: dict[type[DataSourceTestConfig], DataSourceTestConfig] = {
    DatabricksDatasourceTestConfig: DatabricksDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig: SnowflakeDatasourceTestConfig(
        column_types=_timestamp_columns(SNOWFLAKE_TYPES.TIMESTAMP_TZ)
    ),
}


def datetime_data_sources(
    canonical: Sequence[DataSourceTestConfig],
    native: Mapping[type[DataSourceTestConfig], DataSourceTestConfig],
    from_text: Mapping[type[DataSourceTestConfig], DataSourceTestConfig],
) -> tuple[list[DataSourceTestConfig], list[DataSourceTestConfig]]:
    """Replace each canonical source with its date/time configuration, split by how it loads.

    The canonical sources are no-argument instances, so a case that needs column types has to
    configure its own. This keeps that list in step with the canonical one: a canonical source
    with no configuration, a configuration for a source that is no longer canonical, and a source
    configured both ways are all errors, so membership cannot drift from ``ALL_DATA_SOURCES``.

    Returns the sources that load timestamps as timestamps, then those that load them from text,
    each in the canonical order.
    """
    canonical_types = {type(config) for config in canonical}
    both = native.keys() & from_text.keys()
    if both:
        raise ValueError(f"configured as both native and text-loaded: {_names(both)}")
    unconfigured = canonical_types - native.keys() - from_text.keys()
    if unconfigured:
        raise ValueError(f"no date and time configuration for: {_names(unconfigured)}")
    stale = (native.keys() | from_text.keys()) - canonical_types
    if stale:
        raise ValueError(f"configured but not a canonical data source: {_names(stale)}")
    return (
        [native[type(config)] for config in canonical if type(config) in native],
        [from_text[type(config)] for config in canonical if type(config) in from_text],
    )


def _names(config_types: Iterable[type[DataSourceTestConfig]]) -> str:
    return ", ".join(sorted(config_type.__name__ for config_type in config_types))


NATIVE_TIMESTAMP_SOURCES, STRING_TIMESTAMP_SOURCES = datetime_data_sources(
    ALL_DATA_SOURCES, _NATIVE_TIMESTAMP_CONFIGS, _STRING_TIMESTAMP_CONFIGS
)


def assert_operator_selects_oracle_ids(
    batch: Batch,
    frame: pd.DataFrame,
    column_pair: tuple[str, str],
    compare: Comparison,
) -> None:
    left, right = column_pair
    assert_rows_selected(
        batch,
        compare(Column(left), Column(right)),
        expected_ids(frame, left, right, compare),
        all_ids(frame),
    )


@pytest.mark.unit
def test_every_canonical_source_has_exactly_one_date_and_time_configuration() -> None:
    configured = [*NATIVE_TIMESTAMP_SOURCES, *STRING_TIMESTAMP_SOURCES]
    assert sorted(config.label for config in configured) == sorted(
        config.label for config in ALL_DATA_SOURCES
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("native", "from_text", "message"),
    [
        pytest.param([], [], "no date and time configuration", id="unconfigured"),
        pytest.param(
            [SqliteDatasourceTestConfig],
            [],
            "no date and time configuration for: PostgreSQLDatasourceTestConfig",
            id="one-missing",
        ),
        pytest.param(
            [SqliteDatasourceTestConfig, PostgreSQLDatasourceTestConfig],
            [MySQLDatasourceTestConfig],
            "not a canonical data source: MySQLDatasourceTestConfig",
            id="stale",
        ),
        pytest.param(
            [SqliteDatasourceTestConfig, PostgreSQLDatasourceTestConfig],
            [SqliteDatasourceTestConfig],
            "both native and text-loaded: SqliteDatasourceTestConfig",
            id="both",
        ),
    ],
)
def test_date_and_time_configurations_must_match_the_canonical_sources(
    native: list[type[DataSourceTestConfig]],
    from_text: list[type[DataSourceTestConfig]],
    message: str,
) -> None:
    canonical = [SqliteDatasourceTestConfig(), PostgreSQLDatasourceTestConfig()]
    with pytest.raises(ValueError, match=message):
        datetime_data_sources(
            canonical,
            {config_type: config_type() for config_type in native},
            {config_type: config_type() for config_type in from_text},
        )


@pytest.mark.unit
def test_every_operator_selects_different_ids_on_each_pair() -> None:
    pairs = [
        (NUMERIC_DATA, "int_left", "int_right"),
        (NUMERIC_DATA, "float_left", "float_right"),
        (DATETIME_DATA, "date_left", "date_right"),
        (DATETIME_DATA, "ts_left", "ts_right"),
    ]
    for param in OPERATORS:
        compare = param.values[0]
        assert callable(compare)
        selected = [
            tuple(expected_ids(frame, left, right, compare)) for frame, left, right in pairs
        ]
        assert len(set(selected)) == len(selected), (
            f"{param.id}: two pairs select the same ids, so a condition that read the wrong pair "
            f"could still pass: {selected}"
        )


@parameterize_batch_for_data_sources(
    data_source_configs=NATIVE_TIMESTAMP_SOURCES, data=DATETIME_DATA
)
@pytest.mark.parametrize("column_pair", DATETIME_COLUMN_PAIRS)
@pytest.mark.parametrize("compare", OPERATORS)
def test_operator_over_date_and_timestamp_columns(
    batch_for_datasource: Batch,
    column_pair: tuple[str, str],
    compare: Comparison,
) -> None:
    assert_operator_selects_oracle_ids(batch_for_datasource, DATETIME_DATA, column_pair, compare)


@parameterize_batch_for_data_sources(
    data_source_configs=STRING_TIMESTAMP_SOURCES, data=STRING_TIMESTAMP_DATA
)
@pytest.mark.parametrize("column_pair", DATETIME_COLUMN_PAIRS)
@pytest.mark.parametrize("compare", OPERATORS)
def test_operator_over_date_and_text_loaded_timestamp_columns(
    batch_for_datasource: Batch,
    column_pair: tuple[str, str],
    compare: Comparison,
) -> None:
    assert_operator_selects_oracle_ids(
        batch_for_datasource, STRING_TIMESTAMP_DATA, column_pair, compare
    )


# A row with a missing value on either side of a comparison never satisfies it, whatever the
# operator, so `!=` is the case that can go wrong: a database treats `NULL != 4` as unknown, but
# pandas evaluates `NaN != 4` as true. Every pair below has non-null rows that are less, equal and
# greater, and rows missing the left value, the right value and both. Each operator therefore
# selects a non-empty proper subset, and the null rows are the ones a backend would add if it let
# a missing value through. The columns of one pair are only missing on rows where the other pair
# holds values, so a backend that dropped a row for a null in an unrelated column would also fail.
#
# The integers are `Int64`, not a plain column: pandas turns an integer column holding a missing
# value into a float one, and the SQL harness infers a column's type from the values it holds, so
# without `Int64` the SQL backends would create these as FLOAT rather than INTEGER.
# `test_nullable_integer_columns_are_created_as_integer_columns_on_every_sql_source` checks, for
# every SQL source, that they are INTEGER (and the dates DATE). Spark declares IntegerType and
# DateType below. The in-memory pandas source passes the frame as it is: `Int64` integers, and
# dates held as objects with `None` for a missing one. Only the pandas CSV source cannot keep
# integers, because a file written with an empty field has no integer column to read back: it
# reads `int_left` and `int_right` as float64. The comparison and the oracle are unchanged by that.
NULL_DATA = pd.DataFrame(
    {
        ID_COLUMN: list(range(1, 13)),
        "int_left": pd.Series([7, 5, -3, 9, 10, 4, None, 6, None, 3, 8, 5], dtype="Int64"),
        "int_right": pd.Series([3, 5, 2, 10, 9, 4, 4, None, None, 8, 2, 5], dtype="Int64"),
        "date_left": [
            date(2021, 1, 30),
            date(2022, 2, 28),
            date(2023, 3, 15),
            date(2000, 1, 1),
            date(2024, 2, 28),
            date(2024, 2, 29),
            date(2024, 12, 1),
            date(2020, 6, 15),
            date(2022, 5, 5),
            None,
            date(2019, 9, 9),
            None,
        ],
        "date_right": [
            date(2021, 1, 31),
            date(2021, 12, 25),
            date(2023, 3, 15),
            date(1999, 12, 31),
            date(2024, 2, 29),
            date(2024, 2, 29),
            date(2024, 11, 30),
            date(2021, 6, 15),
            date(2022, 5, 5),
            date(2023, 1, 1),
            None,
            None,
        ],
    }
)

NULL_COLUMN_PAIRS = [
    pytest.param(("int_left", "int_right"), id="int"),
    pytest.param(("date_left", "date_right"), id="date"),
]


def _spark_null_column_types() -> dict[str, Any]:
    """The Spark schema for ``NULL_DATA``, empty where pyspark is not installed.

    A Spark schema is positional and must name every column, in the frame's order. The dates need
    one because a CSV file of dates would otherwise be read back as timestamps.
    """
    try:
        from great_expectations.compatibility.pyspark import types as spark_types

        return {
            ID_COLUMN: spark_types.IntegerType,
            "int_left": spark_types.IntegerType,
            "int_right": spark_types.IntegerType,
            "date_left": spark_types.DateType,
            "date_right": spark_types.DateType,
        }
    except ModuleNotFoundError:
        return {}


# Only the two file-backed sources need to say how to read these columns back; every SQL source
# takes the harness defaults (INTEGER and DATE) and the in-memory pandas frame is used as given.
_NULL_CONFIG_OVERRIDES: dict[type[DataSourceTestConfig], DataSourceTestConfig] = {
    PandasFilesystemCsvDatasourceTestConfig: PandasFilesystemCsvDatasourceTestConfig(
        read_options={"parse_dates": ["date_left", "date_right"], "date_format": "mixed"},
    ),
    SparkFilesystemCsvDatasourceTestConfig: SparkFilesystemCsvDatasourceTestConfig(
        column_types=_spark_null_column_types()
    ),
}


def canonical_sources_with(
    canonical: Sequence[DataSourceTestConfig],
    overrides: Mapping[type[DataSourceTestConfig], DataSourceTestConfig],
) -> list[DataSourceTestConfig]:
    """The canonical sources, each replaced by its override where it has one, in canonical order.

    An override for a source that is no longer canonical is an error rather than a case that
    silently stops running, so the list cannot drift from ``ALL_DATA_SOURCES``.
    """
    stale = overrides.keys() - {type(config) for config in canonical}
    if stale:
        raise ValueError(f"configured but not a canonical data source: {_names(stale)}")
    return [overrides.get(type(config), config) for config in canonical]


NULL_SOURCES = canonical_sources_with(ALL_DATA_SOURCES, _NULL_CONFIG_OVERRIDES)


def ids_with_a_null(frame: pd.DataFrame, left: str, right: str) -> list[int]:
    """The ids of the rows whose ``left`` or ``right`` value is missing."""
    missing = frame[left].isna() | frame[right].isna()
    return [int(row_id) for row_id in frame.loc[missing, ID_COLUMN]]


def assert_oracle_excludes_null_rows(
    frame: pd.DataFrame, left: str, right: str, expected: Iterable[int]
) -> None:
    """Fail if ``expected`` names a row that has a missing value in the compared pair.

    The id sets the cases compare already differ whenever a null row slips in, but only because the
    oracle skips those rows. This says it outright, so a change to the oracle that stopped skipping
    them is caught here rather than agreeing with a backend that let them through.
    """
    null_ids = ids_with_a_null(frame, left, right)
    assert null_ids, f"no row of {left!r}, {right!r} has a missing value, so nothing is checked"
    included = sorted(set(expected) & set(null_ids))
    assert not included, f"rows {included} have a missing value in {left!r} or {right!r}"


def assert_missing_values_loaded(batch: Batch, frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Assert that each column holds the rows of ``frame``, with its missing values as nulls.

    The exclusion cases also pass if a backend drops the null rows, or loads a missing value as a
    number or as text, so this is what makes them evidence about null handling.
    """
    for column in columns:
        result = batch.validate(gxe.ExpectColumnValuesToNotBeNull(column=column))
        assert result.result["element_count"] == len(frame), f"{column}: {result.result}"
        assert result.result["unexpected_count"] == int(frame[column].isna().sum()), (
            f"{column}: {result.result}"
        )


class _ColumnTypeResolution(SQLBatchTestSetup[SqlDatasourceTestConfig]):
    """The harness's column-type inference for one SQL source, without connecting to it."""

    @override
    def build_connection_string(self, schema: str | None = None) -> str:
        raise NotImplementedError

    @override
    def make_asset(self) -> TableAsset:
        raise NotImplementedError


@pytest.mark.unit
@pytest.mark.parametrize(
    "config",
    [
        pytest.param(config, id=config.label)
        for config in ALL_DATA_SOURCES
        if isinstance(config, SqlDatasourceTestConfig)
    ],
)
def test_nullable_integer_columns_are_created_as_integer_columns_on_every_sql_source(
    config: SqlDatasourceTestConfig,
) -> None:
    setup = _ColumnTypeResolution(
        config=config, data=NULL_DATA, extra_data={}, context=gx.get_context(mode="ephemeral")
    )
    column_types = setup._infer_column_types(NULL_DATA)
    for column, expected_type in [
        ("int_left", sqltypes.Integer),
        ("int_right", sqltypes.Integer),
        ("date_left", sqltypes.Date),
        ("date_right", sqltypes.Date),
    ]:
        resolved = column_types[column]
        column_type = resolved() if isinstance(resolved, type) else resolved
        assert isinstance(column_type, expected_type), f"{column} is created as {resolved!r}"


@pytest.mark.unit
def test_a_null_in_one_pair_never_falls_on_a_row_with_a_null_in_the_other() -> None:
    int_nulls = set(ids_with_a_null(NULL_DATA, "int_left", "int_right"))
    date_nulls = set(ids_with_a_null(NULL_DATA, "date_left", "date_right"))
    assert int_nulls
    assert date_nulls
    assert not int_nulls & date_nulls


@pytest.mark.unit
def test_a_null_configuration_for_a_source_that_is_not_canonical_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a canonical data source: MySQLDatasourceTestConfig"):
        canonical_sources_with(
            [SqliteDatasourceTestConfig()], {MySQLDatasourceTestConfig: MySQLDatasourceTestConfig()}
        )


@parameterize_batch_for_data_sources(data_source_configs=NULL_SOURCES, data=NULL_DATA)
@pytest.mark.parametrize("column_pair", NULL_COLUMN_PAIRS)
def test_missing_values_load_as_nulls_on_every_source(
    batch_for_datasource: Batch, column_pair: tuple[str, str]
) -> None:
    assert_missing_values_loaded(batch_for_datasource, NULL_DATA, column_pair)


@parameterize_batch_for_data_sources(data_source_configs=NULL_SOURCES, data=NULL_DATA)
@pytest.mark.parametrize("column_pair", NULL_COLUMN_PAIRS)
@pytest.mark.parametrize("compare", OPERATORS)
def test_rows_with_a_null_on_either_side_are_never_selected(
    batch_for_datasource: Batch,
    column_pair: tuple[str, str],
    compare: Comparison,
) -> None:
    left, right = column_pair
    assert_oracle_excludes_null_rows(
        NULL_DATA, left, right, expected_ids(NULL_DATA, left, right, compare)
    )
    assert_operator_selects_oracle_ids(batch_for_datasource, NULL_DATA, column_pair, compare)


@dataclass(frozen=True)
class MissingValueForm:
    """One way pandas holds a missing value, and the four ascending values its column compares."""

    name: str
    dtype: str
    ladder: tuple[Any, Any, Any, Any]
    is_missing_value: Callable[[Any], bool]
    """Whether a scalar read out of the column is this form's own missing-value marker."""

    @property
    def left(self) -> str:
        return f"{self.name}_left"

    @property
    def right(self) -> str:
        return f"{self.name}_right"


# Each form is a different dtype and a different marker: `NaN` in a float column, `None` in an
# object column, `NaT` in a datetime column, and `pd.NA` in the nullable integer and string dtypes.
# The names avoid the substrings `AND`, `OR` and `NOT` for the reason given in the module docstring.
MISSING_VALUE_FORMS = [
    MissingValueForm(
        name="float_nan",
        dtype="float64",
        ladder=(0.5, 2.5, 4.0, 6.5),
        is_missing_value=lambda value: isinstance(value, float) and math.isnan(value),
    ),
    MissingValueForm(
        name="object_none",
        dtype="object",
        ladder=("apple", "banana", "cherry", "damson"),
        is_missing_value=lambda value: value is None,
    ),
    MissingValueForm(
        name="datetime_nat",
        dtype="datetime64[ns]",
        ladder=(
            pd.Timestamp("2020-01-01"),
            pd.Timestamp("2021-06-15 08:30:00"),
            pd.Timestamp("2021-06-15 08:30:01"),
            pd.Timestamp("2023-12-31"),
        ),
        is_missing_value=lambda value: value is pd.NaT,
    ),
    MissingValueForm(
        name="int64_na",
        dtype="Int64",
        ladder=(-3, 5, 9, 10),
        is_missing_value=lambda value: value is pd.NA,
    ),
    MissingValueForm(
        name="string_na",
        dtype="string",
        ladder=("apple", "banana", "cherry", "damson"),
        is_missing_value=lambda value: value is pd.NA,
    ),
]


def missing_value_pairs(form: MissingValueForm, rotation: int) -> tuple[list[Any], list[Any]]:
    """The left and right values of one form: nine rows, three of them with a missing value.

    The rows are two where left < right, two where they are equal, two where left > right, and one
    each missing the left value, the right value and both. ``rotation`` moves where each kind falls
    among the ids, so no two forms select the same ids under an operator.
    """
    low, middle, high, top = form.ladder
    missing = None
    rows = [
        (middle, middle),
        (low, high),
        (high, low),
        (missing, middle),
        (middle, missing),
        (missing, missing),
        (middle, top),
        (top, top),
        (top, low),
    ]
    rows = rows[rotation:] + rows[:rotation]
    return [left for left, _ in rows], [right for _, right in rows]


def missing_value_frame(forms: Sequence[MissingValueForm]) -> pd.DataFrame:
    columns: dict[str, Any] = {ID_COLUMN: list(range(1, 10))}
    for index, form in enumerate(forms):
        lefts, rights = missing_value_pairs(form, rotation=2 * index)
        columns[form.left] = pd.Series(lefts, dtype=form.dtype)
        columns[form.right] = pd.Series(rights, dtype=form.dtype)
    return pd.DataFrame(columns)


MISSING_VALUE_DATA = missing_value_frame(MISSING_VALUE_FORMS)

# The CSV source cannot keep these forms (a file holds text), and the harness loads each of them
# into Spark and the SQL sources as a plain null, so only the in-memory pandas source holds them as
# they are.
PANDAS_DATA_FRAME_SOURCES = [
    config for config in ALL_DATA_SOURCES if isinstance(config, PandasDataFrameDatasourceTestConfig)
]

MISSING_VALUE_FORM_PARAMS = [pytest.param(form, id=form.name) for form in MISSING_VALUE_FORMS]


@pytest.mark.unit
def test_there_is_exactly_one_in_memory_pandas_source() -> None:
    assert len(PANDAS_DATA_FRAME_SOURCES) == 1


@pytest.mark.unit
def test_every_operator_selects_different_ids_on_each_pair_of_missing_value_forms() -> None:
    pairs = [(MISSING_VALUE_DATA, form.left, form.right) for form in MISSING_VALUE_FORMS]
    for param in OPERATORS:
        compare = param.values[0]
        assert callable(compare)
        selected = [
            tuple(expected_ids(frame, left, right, compare)) for frame, left, right in pairs
        ]
        assert len(set(selected)) == len(selected), (
            f"{param.id}: two forms select the same ids, so a condition that read the wrong "
            f"form's pair could still pass: {selected}"
        )


NULL_ORACLE_CASES = [
    pytest.param(NULL_DATA, "int_left", "int_right", id="int"),
    pytest.param(NULL_DATA, "date_left", "date_right", id="date"),
    *[
        pytest.param(MISSING_VALUE_DATA, form.left, form.right, id=form.name)
        for form in MISSING_VALUE_FORMS
    ],
]


@pytest.mark.unit
@pytest.mark.parametrize(("frame", "left", "right"), NULL_ORACLE_CASES)
def test_every_pair_has_a_null_on_the_left_the_right_and_both(
    frame: pd.DataFrame, left: str, right: str
) -> None:
    missing_left, missing_right = frame[left].isna(), frame[right].isna()
    assert (missing_left & ~missing_right).any()
    assert (~missing_left & missing_right).any()
    assert (missing_left & missing_right).any()
    assert (~missing_left & ~missing_right).any()


@pytest.mark.unit
def test_an_expectation_that_selects_a_null_row_is_rejected() -> None:
    (null_id, *_) = ids_with_a_null(NULL_DATA, "int_left", "int_right")
    with pytest.raises(AssertionError, match=r"have a missing value in 'int_left' or 'int_right'"):
        assert_oracle_excludes_null_rows(NULL_DATA, "int_left", "int_right", [null_id])


@parameterize_batch_for_data_sources(
    data_source_configs=PANDAS_DATA_FRAME_SOURCES, data=MISSING_VALUE_DATA
)
@pytest.mark.parametrize("form", MISSING_VALUE_FORM_PARAMS)
def test_the_pandas_engine_receives_each_missing_value_form_unchanged(
    batch_for_datasource: Batch, form: MissingValueForm
) -> None:
    assert isinstance(batch_for_datasource.data, PandasBatchData)
    engine_frame = batch_for_datasource.data.dataframe
    for column in (form.left, form.right):
        seen = engine_frame[column]
        assert str(seen.dtype) == form.dtype
        expected_missing = MISSING_VALUE_DATA[column].isna()
        assert seen.isna().equals(expected_missing)
        for value in seen[expected_missing]:
            assert form.is_missing_value(value), f"{column}: the engine holds {value!r}"


@parameterize_batch_for_data_sources(
    data_source_configs=PANDAS_DATA_FRAME_SOURCES, data=MISSING_VALUE_DATA
)
@pytest.mark.parametrize("form", MISSING_VALUE_FORM_PARAMS)
@pytest.mark.parametrize("compare", OPERATORS)
def test_every_pandas_missing_value_form_is_excluded_by_every_operator(
    batch_for_datasource: Batch, form: MissingValueForm, compare: Comparison
) -> None:
    assert_oracle_excludes_null_rows(
        MISSING_VALUE_DATA,
        form.left,
        form.right,
        expected_ids(MISSING_VALUE_DATA, form.left, form.right, compare),
    )
    assert_operator_selects_oracle_ids(
        batch_for_datasource, MISSING_VALUE_DATA, (form.left, form.right), compare
    )


# A column comparison joined to other conditions. A comparison whose value is missing is unknown
# rather than false, and a row passes a filter only when the whole condition is true, so a row with
# a null in `a` or `b` is selected through an OR only if the other branch selects it, and never
# through an AND. These rows hold the same pair relations as above (two less, two equal, two
# greater) and mark which of them the other branches select:
#
# * `k` is 1 on one row of each relation and of each kind of null row, and 0 on the other, so
#   `k == 1` splits the null rows and splits the rows of every relation, whatever the operator.
# * `c` is missing on one row of each relation, so `c IS NOT NULL` removes a row the comparison
#   selected under every operator that selects that relation. It is present on every null row, so
#   an AND that kept a null row could not be explained by `c`.
# * Rows 7 to 12 are the null rows: `a` missing, `b` missing, and both, each with `k` of 0 and 1.
#   `a IS NULL` selects the first and third kinds but not the second, whose `a` is present.
#
# Every operator then selects a different, non-empty proper subset under each form below.
#
# The compared columns are float64, so a missing value is NaN. pandas compares NaN as unequal
# rather than unknown, which is what makes the pandas cases fail if the null rule is not applied;
# an `Int64` column's `pd.NA` is already false in `df.query` and would not show that. The whole
# numbers are exactly representable, so no backend's rounding can move a pair across its relation.
COMBINATOR_DATA = pd.DataFrame(
    {
        ID_COLUMN: list(range(1, 13)),
        "a": [2.0, -4.0, 7.0, 3.0, 9.0, 8.0, None, None, 6.0, 6.0, None, None],
        "b": [5.0, 1.0, 7.0, 3.0, 4.0, 6.0, 5.0, 5.0, None, None, None, None],
        "c": [10.0, None, None, 20.0, None, 30.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0],
        "k": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
)


def _spark_combinator_column_types() -> dict[str, Any]:
    """The Spark schema for ``COMBINATOR_DATA``, empty where pyspark is not installed.

    A Spark schema is positional and must name every column, in the frame's order.
    """
    try:
        from great_expectations.compatibility.pyspark import types as spark_types

        return {
            ID_COLUMN: spark_types.IntegerType,
            "a": spark_types.DoubleType,
            "b": spark_types.DoubleType,
            "c": spark_types.DoubleType,
            "k": spark_types.IntegerType,
        }
    except ModuleNotFoundError:
        return {}


COMBINATOR_SOURCES = canonical_sources_with(
    ALL_DATA_SOURCES,
    {
        SparkFilesystemCsvDatasourceTestConfig: SparkFilesystemCsvDatasourceTestConfig(
            column_types=_spark_combinator_column_types()
        )
    },
)

Row = Mapping[Any, Any]


def compare_truth(row: Row, compare: Comparison) -> bool | None:
    """Whether the row's ``a`` and ``b`` satisfy ``compare``, or ``None`` if either is missing."""
    left_value, right_value = row["a"], row["b"]
    if pd.isna(left_value) or pd.isna(right_value):
        return None
    return bool(compare(left_value, right_value))


def is_missing(row: Row, column: str) -> bool:
    return bool(pd.isna(row[column]))


def and_selects(*branches: bool | None) -> bool:
    """A row passes an AND only when every branch is true; an unknown branch is not true."""
    return all(branch is not None and bool(branch) for branch in branches)


def or_selects(*branches: bool | None) -> bool:
    """A row passes an OR when any branch is true; an unknown branch does not make it true."""
    return any(branch is not None and bool(branch) for branch in branches)


def ids_where(frame: pd.DataFrame, selects: Callable[[Row], bool]) -> list[int]:
    return [int(row[ID_COLUMN]) for row in frame.to_dict("records") if selects(row)]


@pytest.mark.unit
def test_each_kind_of_null_row_is_paired_with_both_values_of_the_key() -> None:
    kinds = {
        "a missing": COMBINATOR_DATA["a"].isna() & COMBINATOR_DATA["b"].notna(),
        "b missing": COMBINATOR_DATA["a"].notna() & COMBINATOR_DATA["b"].isna(),
        "both missing": COMBINATOR_DATA["a"].isna() & COMBINATOR_DATA["b"].isna(),
    }
    for kind, rows in kinds.items():
        assert set(COMBINATOR_DATA.loc[rows, "k"]) == {0, 1}, kind


@parameterize_batch_for_data_sources(data_source_configs=COMBINATOR_SOURCES, data=COMBINATOR_DATA)
def test_combinator_data_loads_with_its_missing_values_as_nulls(
    batch_for_datasource: Batch,
) -> None:
    assert_missing_values_loaded(batch_for_datasource, COMBINATOR_DATA, ["a", "b", "c"])


@parameterize_batch_for_data_sources(data_source_configs=COMBINATOR_SOURCES, data=COMBINATOR_DATA)
@pytest.mark.parametrize("compare", OPERATORS)
def test_and_never_selects_a_row_with_a_null_in_the_comparison(
    batch_for_datasource: Batch, compare: Comparison
) -> None:
    expected = ids_where(
        COMBINATOR_DATA,
        lambda row: and_selects(compare_truth(row, compare), not is_missing(row, "c")),
    )
    assert_oracle_excludes_null_rows(COMBINATOR_DATA, "a", "b", expected)
    assert_rows_selected(
        batch_for_datasource,
        compare(Column("a"), Column("b")) & Column("c").is_not_null(),
        expected,
        all_ids(COMBINATOR_DATA),
    )


# The other branch of an OR, as the condition and as the row test the oracle applies to it.
OTHER_OR_BRANCHES = [
    pytest.param(Column("k") == 1, lambda row: row["k"] == 1, id="key_is_one"),
    pytest.param(Column("a").is_null(), lambda row: is_missing(row, "a"), id="a_is_null"),
]


@parameterize_batch_for_data_sources(data_source_configs=COMBINATOR_SOURCES, data=COMBINATOR_DATA)
@pytest.mark.parametrize(("other_branch", "other_selects"), OTHER_OR_BRANCHES)
@pytest.mark.parametrize("compare", OPERATORS)
def test_or_selects_a_row_with_a_null_in_the_comparison_only_if_the_other_branch_does(
    batch_for_datasource: Batch,
    compare: Comparison,
    other_branch: Condition,
    other_selects: Callable[[Row], bool],
) -> None:
    expected = ids_where(
        COMBINATOR_DATA,
        lambda row: or_selects(compare_truth(row, compare), other_selects(row)),
    )
    assert_rows_selected(
        batch_for_datasource,
        compare(Column("a"), Column("b")) | other_branch,
        expected,
        all_ids(COMBINATOR_DATA),
    )


@parameterize_batch_for_data_sources(data_source_configs=COMBINATOR_SOURCES, data=COMBINATOR_DATA)
@pytest.mark.parametrize("compare", OPERATORS)
def test_or_with_both_columns_is_null_selects_every_null_row_and_the_matching_rows(
    batch_for_datasource: Batch, compare: Comparison
) -> None:
    null_ids = ids_with_a_null(COMBINATOR_DATA, "a", "b")
    expected = ids_where(
        COMBINATOR_DATA,
        lambda row: or_selects(
            compare_truth(row, compare), is_missing(row, "a"), is_missing(row, "b")
        ),
    )
    assert set(null_ids) <= set(expected)
    assert_rows_selected(
        batch_for_datasource,
        OrCondition(
            conditions=[
                compare(Column("a"), Column("b")),
                Column("a").is_null(),
                Column("b").is_null(),
            ]
        ),
        expected,
        all_ids(COMBINATOR_DATA),
    )


def _all_subclasses(base: type) -> set[type]:
    found: set[type] = set()
    for subclass in base.__subclasses__():
        found.add(subclass)
        found |= _all_subclasses(subclass)
    return found


# The null rule lives in how each engine renders the comparison itself, so AND and OR keep it only
# because they render the comparison the same way inside them. A new kind of condition that
# wraps or inverts a comparison, a negation for instance, would turn a null from "not selected"
# into "selected" on a backend that treats the unknown as false, so it needs a case of its own.
CONDITION_TYPES_WITH_THE_NULL_RULE_VERIFIED: set[type] = {
    ComparisonCondition,
    ColumnComparisonCondition,
    NullityCondition,
    AndCondition,
    OrCondition,
    PassThroughCondition,
}


@pytest.mark.unit
def test_every_condition_type_has_had_the_column_comparison_null_rule_verified() -> None:
    # Only classes defined in great_expectations count: `__subclasses__()` sees every subclass in
    # the test process, including any a test module defines for its own purposes.
    defined = {
        condition_type
        for condition_type in _all_subclasses(Condition)
        if condition_type.__module__.startswith("great_expectations.")
    }
    added = sorted(
        condition_type.__name__
        for condition_type in defined - CONDITION_TYPES_WITH_THE_NULL_RULE_VERIFIED
    )
    removed = sorted(
        condition_type.__name__
        for condition_type in CONDITION_TYPES_WITH_THE_NULL_RULE_VERIFIED - defined
    )
    assert not added and not removed, (
        f"The row-condition classes changed: added {added}, removed {removed}. Before updating "
        "CONDITION_TYPES_WITH_THE_NULL_RULE_VERIFIED, verify on every backend that a column "
        "comparison still excludes a row with a null on either side when it is combined through "
        "the new condition type, with a case for it beside the AND and OR cases above."
    )


ABSENT_ID = 0
"""An id no row holds."""


def selected_ids(batch: Batch, row_condition: Any) -> list[int]:
    """The ids the backend itself leaves after filtering by ``row_condition``.

    Where the expected ids come from the backend's own behavior, as they do for a collation, they
    cannot be written down in advance. The distinct-values Expectation lists every id outside its
    value set, and no row has the id below, so what it lists is every id that survived the filter.
    A condition the backend could not evaluate fails here rather than reading as an empty result.
    """
    result = batch.validate(
        gxe.ExpectColumnDistinctValuesToEqualSet(
            column=ID_COLUMN, value_set=[ABSENT_ID], row_condition=row_condition
        )
    )
    survivors = result.result.get("partial_unexpected_list")
    assert survivors is not None, (
        f"{row_condition!r} was not evaluated: exception_info={result.exception_info}"
    )
    return sorted(int(row_id) for row_id in survivors)


# A column name a backend has to quote: one with a space in it, one that is a reserved word, and
# one in mixed case, which a backend that folds an unquoted name to one case would otherwise change.
# The names avoid the substrings `AND`, `OR` and `NOT` for the reason given in the module docstring.
QUOTED_NAMES = {
    "space": "user name",
    "reserved_word": "select",
    "mixed_case": "UserName",
}

PLAIN_COLUMN = "plain"

# Each name gets a table of its own, built from the same values, so a backend that cannot store one
# of the names still runs the others. In rows 1 and 2 the quoted column is below the plain one, in
# rows 3 and 4 it is equal, and in rows 5 and 6 it is above, so `quoted < plain` and `plain <
# quoted` each select a different, non-empty proper subset of the ids. `quoted > QUOTED_PIVOT` is
# the literal comparison on the same name, and selects a third.
_QUOTED_COLUMN_VALUES = [3, 12, 30, 30, 40, 60]
_PLAIN_COLUMN_VALUES = [10, 20, 30, 30, 15, 25]
QUOTED_PIVOT = 12


def quoted_name_frame(name: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            ID_COLUMN: [1, 2, 3, 4, 5, 6],
            PLAIN_COLUMN: _PLAIN_COLUMN_VALUES,
            name: _QUOTED_COLUMN_VALUES,
        }
    )


def expected_ids_against_value(
    frame: pd.DataFrame, column: str, value: Any, compare: Comparison
) -> list[int]:
    """The ids whose ``column`` value satisfies ``compare`` against the literal ``value``."""
    return [int(row[ID_COLUMN]) for row in frame.to_dict("records") if compare(row[column], value)]


# The names a source cannot store, by canonical source and then by name, each with the reason. A
# source listed here still runs every other name; the skip is explicit and recorded where it is
# collected, not a case that quietly stops running.
#
# BigQuery's support for a space in a column name was not verified when this was written. Column
# names there were limited to letters, digits and underscores until flexible column names were
# added, and nothing here shows that the CI dataset accepts a space, so that one name is skipped
# until a run on that dataset shows otherwise. The other canonical sources are not listed: the
# ones that run locally store all three names, and the rest are confirmed by their own CI run.
_QUOTED_NAMES_A_SOURCE_CANNOT_STORE: dict[type[DataSourceTestConfig], dict[str, str]] = {
    DatabricksDatasourceTestConfig: {
        "user name": (
            "Delta tables reject a space in a column name unless column mapping is enabled "
            "(DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES)"
        ),
    },
}


def quoted_name_skips(
    canonical: Sequence[DataSourceTestConfig],
    names: Mapping[str, str],
    cannot_store: Mapping[type[DataSourceTestConfig], Mapping[str, str]],
) -> dict[tuple[str, str], str]:
    """The reason each (source label, name) pair is skipped, checked against what exists.

    A source that is not canonical, or a name this module does not test, is an error rather than
    an entry that silently matches nothing, so the table cannot drift from the sources and names
    it describes.
    """
    labels = {type(config): config.label for config in canonical}
    stale = cannot_store.keys() - labels.keys()
    if stale:
        raise ValueError(f"configured but not a canonical data source: {_names(stale)}")
    skips: dict[tuple[str, str], str] = {}
    for config_type, reasons in cannot_store.items():
        unknown = reasons.keys() - set(names.values())
        if unknown:
            raise ValueError(f"{config_type.__name__} skips names not tested: {sorted(unknown)}")
        for name, reason in reasons.items():
            skips[(labels[config_type], name)] = reason
    return skips


def sources_running_no_quoted_name(
    canonical: Sequence[DataSourceTestConfig],
    names: Mapping[str, str],
    skips: Mapping[tuple[str, str], str],
) -> list[str]:
    """The labels of canonical sources that skip every quoted name, which should be none."""
    return [
        config.label
        for config in canonical
        if all((config.label, name) in skips for name in names.values())
    ]


def quoted_name_params(
    canonical: Sequence[DataSourceTestConfig],
    names: Mapping[str, str],
    skips: Mapping[tuple[str, str], str],
) -> list[ParameterSet]:
    """One case per (canonical source, name), skipped with its reason where the source cannot store
    the name.

    The skip is a mark on the case rather than a call in the test body: pytest skips a marked case
    before it builds the table, and the table is the thing that cannot be built.
    """
    return [
        pytest.param(
            _TestConfig(data_source_config=config, data=quoted_name_frame(name), extra_data={}),
            name,
            id=f"{config.test_id}-{kind}",
            marks=[
                config.pytest_mark,
                *(
                    [pytest.mark.skip(reason=skips[(config.label, name)])]
                    if (config.label, name) in skips
                    else []
                ),
            ],
        )
        for config in canonical
        for kind, name in names.items()
    ]


QUOTED_NAME_SKIPS = quoted_name_skips(
    ALL_DATA_SOURCES, QUOTED_NAMES, _QUOTED_NAMES_A_SOURCE_CANNOT_STORE
)


quoted_name_cases = pytest.mark.parametrize(
    [_BATCH_SETUP_FIXTURE_NAME, "quoted_name"],
    quoted_name_params(ALL_DATA_SOURCES, QUOTED_NAMES, QUOTED_NAME_SKIPS),
    indirect=[_BATCH_SETUP_FIXTURE_NAME],
)


@pytest.mark.unit
def test_every_canonical_source_runs_at_least_one_quoted_name() -> None:
    assert sources_running_no_quoted_name(ALL_DATA_SOURCES, QUOTED_NAMES, QUOTED_NAME_SKIPS) == []


@pytest.mark.unit
def test_a_source_that_skips_every_quoted_name_is_reported() -> None:
    canonical = [SqliteDatasourceTestConfig(), PostgreSQLDatasourceTestConfig()]
    every_name = dict.fromkeys(QUOTED_NAMES.values(), "cannot store it")
    skips = quoted_name_skips(canonical, QUOTED_NAMES, {PostgreSQLDatasourceTestConfig: every_name})
    assert sources_running_no_quoted_name(canonical, QUOTED_NAMES, skips) == ["postgresql"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("cannot_store", "message"),
    [
        pytest.param(
            {MySQLDatasourceTestConfig: {"user name": "r"}},
            "not a canonical data source: MySQLDatasourceTestConfig",
            id="stale-source",
        ),
        pytest.param(
            {SqliteDatasourceTestConfig: {"user_name": "r"}},
            r"SqliteDatasourceTestConfig skips names not tested: \['user_name'\]",
            id="unknown-name",
        ),
    ],
)
def test_a_skip_for_a_source_or_name_that_does_not_exist_is_rejected(
    cannot_store: dict[type[DataSourceTestConfig], dict[str, str]], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        quoted_name_skips([SqliteDatasourceTestConfig()], QUOTED_NAMES, cannot_store)


@pytest.mark.unit
def test_a_skipped_name_is_collected_as_a_skip_with_its_reason() -> None:
    canonical = [SqliteDatasourceTestConfig(), PostgreSQLDatasourceTestConfig()]
    params = quoted_name_params(
        canonical, QUOTED_NAMES, {("postgresql", "user name"): "no spaces here"}
    )
    skipped = {
        param.id: [mark.kwargs["reason"] for mark in param.marks if mark.name == "skip"]
        for param in params
    }
    assert skipped == {
        "sqlite-space": [],
        "sqlite-reserved_word": [],
        "sqlite-mixed_case": [],
        "postgresql-space": ["no spaces here"],
        "postgresql-reserved_word": [],
        "postgresql-mixed_case": [],
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "name", [pytest.param(name, id=kind) for kind, name in QUOTED_NAMES.items()]
)
def test_each_side_and_the_literal_select_different_ids_on_every_quoted_name(name: str) -> None:
    frame = quoted_name_frame(name)
    on_left = expected_ids(frame, name, PLAIN_COLUMN, operator.lt)
    on_right = expected_ids(frame, PLAIN_COLUMN, name, operator.lt)
    against_literal = expected_ids_against_value(frame, name, QUOTED_PIVOT, operator.gt)
    selected = [on_left, on_right, against_literal]
    for ids in selected:
        assert_expectation_discriminates(ids, all_ids(frame))
    assert len({tuple(ids) for ids in selected}) == len(selected), (
        f"two forms select the same ids, so a condition that read the wrong side could still "
        f"pass: {selected}"
    )


@quoted_name_cases
@pytest.mark.parametrize(
    "name_on_left", [pytest.param(True, id="name_on_left"), pytest.param(False, id="name_on_right")]
)
def test_a_quoted_name_resolves_on_either_side_of_a_column_comparison(
    batch_for_datasource: Batch, quoted_name: str, name_on_left: bool
) -> None:
    pair = (quoted_name, PLAIN_COLUMN) if name_on_left else (PLAIN_COLUMN, quoted_name)
    assert_operator_selects_oracle_ids(
        batch_for_datasource, quoted_name_frame(quoted_name), pair, operator.lt
    )


@quoted_name_cases
def test_a_quoted_name_resolves_in_a_literal_comparison(
    batch_for_datasource: Batch, quoted_name: str
) -> None:
    frame = quoted_name_frame(quoted_name)
    assert_rows_selected(
        batch_for_datasource,
        Column(quoted_name) > QUOTED_PIVOT,
        expected_ids_against_value(frame, quoted_name, QUOTED_PIVOT, operator.gt),
        all_ids(frame),
    )


# Strings that differ only in case, to put each backend's own collation on show. `t == "banana"`
# holds for "banana" under every collation and for "Banana" only under one that ignores case.
#
# * Row 1 is selected, and rows 2, 6 and 7 are not, whatever the collation.
# * Row 4 is selected only where case is ignored: its `t` is "Banana" and "cherry" is above it.
# * Row 3 compares "Banana" with "banana". A binary order puts the capital first and a
#   case-insensitive one calls them equal, so neither selects it, but a locale order that puts lower
#   case first does.
# * Row 5 compares "Cherry" with "banana". A binary order puts every capital before every lower-case
#   letter, so it is not selected there; the other two orders select it.
#
# A binary collation therefore selects {1}, a case-insensitive one {1, 4, 5} and a lower-case-first
# locale one {1, 3, 5}: each a non-empty proper subset, and each different.
COLLATION_PIVOT = "banana"
COLLATION_DATA = pd.DataFrame(
    {
        ID_COLUMN: [1, 2, 3, 4, 5, 6, 7],
        "s": ["cherry", "apple", "Banana", "cherry", "Cherry", "apple", "Apple"],
        "t": ["banana", "banana", "banana", "Banana", "banana", "apple", "Banana"],
    }
)
ROWS_EVERY_COLLATION_SELECTS = {1}
ROWS_NO_COLLATION_SELECTS = {2, 6, 7}


def assert_rows_that_ignore_collation(selected: Iterable[int]) -> None:
    """Fail unless ``selected`` holds the rows every collation selects and none that none does."""
    chosen = set(selected)
    assert chosen.issuperset(ROWS_EVERY_COLLATION_SELECTS), sorted(chosen)
    assert chosen.isdisjoint(ROWS_NO_COLLATION_SELECTS), sorted(chosen)


BINARY_ORDER: Callable[[str], str] = str
CASE_INSENSITIVE_ORDER: Callable[[str], str] = str.casefold


def collation_oracle_ids(order: Callable[[str], str], *, against_column: bool) -> list[int]:
    """The ids of ``(s > <t or the pivot>) & (t == pivot)`` when ``order`` decides both tests."""
    selected: list[int] = []
    for row in COLLATION_DATA.to_dict("records"):
        other = row["t"] if against_column else COLLATION_PIVOT
        if order(row["s"]) > order(other) and order(row["t"]) == order(COLLATION_PIVOT):
            selected.append(int(row[ID_COLUMN]))
    return selected


@pytest.mark.unit
@pytest.mark.parametrize(
    "order",
    [
        pytest.param(BINARY_ORDER, id="binary"),
        pytest.param(CASE_INSENSITIVE_ORDER, id="case_insensitive"),
    ],
)
def test_the_collation_data_gives_a_non_trivial_result_under_one_consistent_collation(
    order: Callable[[str], str],
) -> None:
    literal = collation_oracle_ids(order, against_column=False)
    assert_expectation_discriminates(literal, all_ids(COLLATION_DATA))
    assert collation_oracle_ids(order, against_column=True) == literal
    assert_rows_that_ignore_collation(literal)


@pytest.mark.unit
def test_the_collation_data_shows_a_difference_between_collations() -> None:
    binary = collation_oracle_ids(BINARY_ORDER, against_column=False)
    insensitive = collation_oracle_ids(CASE_INSENSITIVE_ORDER, against_column=False)
    assert binary != insensitive
    # A column comparison that ordered strings by a different rule from the literal one would be
    # seen: it selects other ids than the literal comparison does.
    assert collation_oracle_ids(CASE_INSENSITIVE_ORDER, against_column=True) != binary
    assert collation_oracle_ids(BINARY_ORDER, against_column=True) != insensitive


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=COLLATION_DATA)
def test_string_columns_are_compared_under_the_same_collation_as_a_literal(
    batch_for_datasource: Batch,
) -> None:
    literal = (Column("s") > COLLATION_PIVOT) & (Column("t") == COLLATION_PIVOT)
    between_columns = (Column("s") > Column("t")) & (Column("t") == COLLATION_PIVOT)
    # The literal comparison says what this backend's collation selects; it cannot be written down
    # in advance. The ids that do not depend on a collation are still pinned, so the literal form
    # cannot be wrong in the same way as the column form and agree with it.
    literal_ids = selected_ids(batch_for_datasource, literal)
    assert_rows_that_ignore_collation(literal_ids)
    assert_rows_selected(
        batch_for_datasource, between_columns, literal_ids, all_ids(COLLATION_DATA)
    )


def exception_messages(result: ExpectationValidationResult) -> list[str]:
    """Every exception message the result reports, or an empty list if nothing was raised.

    A metric that cannot be resolved is reported once per failed metric: ``exception_info`` maps
    each one to its own exception. Any other failure is reported once, in ``exception_info``
    itself, and a result that raised nothing carries a message of ``None``. A case that expects an
    error asserts the list is not empty, so a result that merely did not succeed cannot pass.
    """
    info = result.exception_info
    entries = [info] if "exception_message" in info else list(info.values())
    return [entry["exception_message"] for entry in entries if entry["exception_message"]]


def observing_expectation(row_condition: RowConditionType) -> gxe.Expectation:
    """The Expectation ``selected_ids`` uses: it lists the ids that survive the row condition."""
    return gxe.ExpectColumnDistinctValuesToEqualSet(
        column=ID_COLUMN, value_set=[ABSENT_ID], row_condition=row_condition
    )


def assert_fails_naming_the_comparison(
    batch: Batch, expectation: gxe.Expectation, comparison: str
) -> None:
    """Assert that validating ``expectation`` raises, and that every error names ``comparison``.

    Unsuccessful alone is not evidence: the Expectations used here also fail when they are
    evaluated and their values simply do not match. An exception message is. And the comparison
    appearing somewhere in the message is not evidence either: a SQL backend quotes the statement
    it rejected, which already holds ``a > no_such_column``. So this looks for the sentence the
    engine appends, which names the comparison and nothing else does.
    """
    result = batch.validate(expectation)
    assert result.success is False, f"expected a failure, got result={result.result}"
    messages = exception_messages(result)
    assert messages, f"the Expectation did not raise: result={result.result}"
    named = f"Row condition column comparisons: {comparison}."
    for message in messages:
        assert named in message, f"{named!r} is not in the error: {message}"


def canonical_sources_of_types(
    canonical: Sequence[DataSourceTestConfig], config_types: Iterable[type[DataSourceTestConfig]]
) -> list[DataSourceTestConfig]:
    """The canonical sources that are of ``config_types``, in canonical order.

    A type that is not canonical is an error rather than a case that silently stops running.
    """
    wanted = set(config_types)
    missing = wanted - {type(config) for config in canonical}
    if missing:
        raise ValueError(f"not a canonical data source: {_names(missing)}")
    return [config for config in canonical if type(config) in wanted]


# A column comparison against a column that does not exist is one no backend can evaluate. It is
# validated through the observation primitive and through a column aggregate, and in each case every
# error the result reports must carry the sentence the engine appends to name the comparison,
# whichever metric fails to resolve first and however the backend words its own error. Which engine
# code raises depends on the backend: pandas computes each metric on its own, the SQL backends fail
# the bundled row-count aggregate before any other metric runs, and Spark fails some metrics each
# way, so a single Spark case checks both.
MISSING_COLUMN = "no_such_column"
MISSING_COLUMN_DATA = pd.DataFrame({ID_COLUMN: [1, 2, 3], "a": [10, 20, 30]})

EXPECTATIONS_ON_A_COLUMN_COMPARISON = [
    pytest.param(observing_expectation, id="distinct_values"),
    pytest.param(
        lambda row_condition: gxe.ExpectColumnMaxToBeBetween(
            column=ID_COLUMN, min_value=0, max_value=100, row_condition=row_condition
        ),
        id="column_max",
    ),
]


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=MISSING_COLUMN_DATA)
@pytest.mark.parametrize("expectation_for", EXPECTATIONS_ON_A_COLUMN_COMPARISON)
def test_a_column_comparison_against_a_missing_column_fails_naming_the_comparison(
    batch_for_datasource: Batch, expectation_for: Callable[[RowConditionType], gxe.Expectation]
) -> None:
    assert_fails_naming_the_comparison(
        batch_for_datasource,
        expectation_for(Column("a") > Column(MISSING_COLUMN)),
        f"a > {MISSING_COLUMN}",
    )


# Text compared with an integer: pandas cannot order them (a string and a number do not compare)
# and PostgreSQL has no operator for text against integer. Both raise while evaluating the
# comparison, so the error must name it. The words stay non-numeric because a CSV file would read
# a numeric-looking value back as an integer, and the column would then compare. `>` is the
# operator because pandas does not raise on `==` and `!=` between a string and a number.
UNCOMPARABLE_DATA = pd.DataFrame(
    {
        ID_COLUMN: [1, 2, 3],
        "label": pd.Series(["apple", "banana", "cherry"], dtype=object),
        "size": [1, 2, 3],
    }
)

UNCOMPARABLE_SOURCES = canonical_sources_of_types(
    ALL_DATA_SOURCES,
    [
        PandasDataFrameDatasourceTestConfig,
        PandasFilesystemCsvDatasourceTestConfig,
        PostgreSQLDatasourceTestConfig,
    ],
)


@parameterize_batch_for_data_sources(
    data_source_configs=UNCOMPARABLE_SOURCES, data=UNCOMPARABLE_DATA
)
def test_a_column_comparison_between_values_that_cannot_be_compared_fails_naming_the_comparison(
    batch_for_datasource: Batch,
) -> None:
    assert_fails_naming_the_comparison(
        batch_for_datasource,
        observing_expectation(Column("label") > Column("size")),
        "label > size",
    )


# SQLite converts between types by affinity instead of raising. A TEXT column compared with an
# INTEGER column has the integer's numeric affinity applied to the text first, so text that reads
# as a number is compared as that number. Text that does not is compared by storage class, and
# every TEXT value sorts above every INTEGER. GX adds no type check of its own, so `label > size`
# keeps exactly the rows SQLite itself keeps:
#
# * Row 1, "10" against 9: converted, and 10 > 9.
# * Row 2, "9" against 10: converted, and 9 > 10 is false. With no conversion TEXT would sort
#   above INTEGER and the row would be kept, so this row shows the conversion happened.
# * Row 3, "abc" against 5: it cannot be converted, so TEXT sorts above INTEGER and the row is kept.
# * Row 4, "5" against 5: converted, equal, not kept.
# * Row 5, "-2" against 3: converted, and -2 > 3 is false.
IMPLICIT_CONVERSION_DATA = pd.DataFrame(
    {
        ID_COLUMN: [1, 2, 3, 4, 5],
        "label": ["10", "9", "abc", "5", "-2"],
        "size": [9, 10, 5, 5, 3],
    }
)
IDS_SQLITE_KEEPS = [1, 3]

SQLITE_SOURCES = canonical_sources_of_types(ALL_DATA_SOURCES, [SqliteDatasourceTestConfig])


@parameterize_batch_for_data_sources(
    data_source_configs=SQLITE_SOURCES, data=IMPLICIT_CONVERSION_DATA
)
def test_sqlite_returns_its_own_result_for_text_compared_with_an_integer_column(
    batch_for_datasource: Batch,
) -> None:
    assert_expectation_discriminates(IDS_SQLITE_KEEPS, all_ids(IMPLICIT_CONVERSION_DATA))
    result = batch_for_datasource.validate(observing_expectation(Column("label") > Column("size")))
    assert exception_messages(result) == [], f"the comparison raised: {result.exception_info}"
    assert sorted(result.result["partial_unexpected_list"]) == IDS_SQLITE_KEEPS, result.result
