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

import operator
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.compatibility.aws import REDSHIFT_TYPES
from great_expectations.compatibility.bigquery import BIGQUERY_TYPES
from great_expectations.compatibility.postgresql import POSTGRESQL_TYPES
from great_expectations.compatibility.snowflake import SNOWFLAKE_TYPES
from great_expectations.compatibility.sqlalchemy import sqltypes
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
    SqliteDatasourceTestConfig,
    SQLServerDatasourceTestConfig,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch
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
