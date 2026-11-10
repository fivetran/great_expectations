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
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, Sequence

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
from great_expectations.expectations.row_conditions import Column
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
    from great_expectations.datasource.fluent.interfaces import Batch
    from great_expectations.datasource.fluent.sql_datasource import TableAsset
    from tests.integration.test_utils.data_source_config import DataSourceTestConfig

# The distinct-values metrics on SQL backends pass a row-conditioned selectable to `select_from`
# without wrapping it in a subquery. SQLAlchemy coerces it and emits this deprecation warning, and
# this repository's pytest configuration turns warnings into errors, so the observation primitive
# below fails on every SQL backend once any row condition is present, literal or column
# comparison. The coercion is correct; only the warning trips the test, so only this message is
# ignored here.
pytestmark = pytest.mark.filterwarnings(
    "ignore:Implicit coercion of SELECT and textual SELECT constructs"
    ":sqlalchemy.exc.SADeprecationWarning"
)

ID_COLUMN = "id"

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
