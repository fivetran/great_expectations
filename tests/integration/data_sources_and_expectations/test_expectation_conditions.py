from datetime import datetime, timezone

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.compatibility.bigquery import BIGQUERY_TYPES
from great_expectations.compatibility.postgresql import POSTGRESQL_TYPES
from great_expectations.compatibility.snowflake import SNOWFLAKE_TYPES
from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

DATA = pd.DataFrame(
    {
        "created_at": [
            datetime(year=2021, month=1, day=30, tzinfo=timezone.utc),
            datetime(year=2022, month=1, day=30, tzinfo=timezone.utc),
            datetime(year=2023, month=1, day=30, tzinfo=timezone.utc),
        ],
        "updated_at": [
            datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
        ],
        "amount": [1.00, 2.00, 3.00],
        "quantity": [1, 2, 3],
        "name": ["albert", "issac", "galileo"],
    }
)


# some backends fail to load datetimes into the database unless they are strings
DATA_WITH_STRING_DATETIMES = pd.DataFrame(
    {
        "created_at": [
            str(datetime(year=2021, month=1, day=30, tzinfo=timezone.utc)),
            str(datetime(year=2022, month=1, day=30, tzinfo=timezone.utc)),
            str(datetime(year=2023, month=1, day=30, tzinfo=timezone.utc)),
        ],
        "updated_at": [
            datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
        ],
        "amount": [1.00, 2.00, 3.00],
        "quantity": [1, 2, 3],
        "name": ["albert", "issac", "galileo"],
    }
)


PANDAS_DATAFRAME_TEST_CASES = [
    pytest.param(
        'name=="albert"',
        id="text-eq",
    ),
    pytest.param(
        "quantity<3",
        id="number-lt",
    ),
    pytest.param(
        "quantity==1",
        id="number-eq",
    ),
    pytest.param(
        "updated_at<datetime.date(2021,2,1)",
        id="datetime.date-lt",
    ),
    pytest.param(
        "updated_at>datetime.date(2021,1,30)",
        id="datetime.date-gt",
    ),
    pytest.param(
        "updated_at==datetime.date(2021,1,31)",
        id="datetime.date-eq",
    ),
    pytest.param(
        "created_at<datetime.datetime(2021,1,31,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-lt",
    ),
    pytest.param(
        "created_at>datetime.datetime(2021,1,29,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-gt",
    ),
    pytest.param(
        "created_at==datetime.datetime(2021,1,30,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-eq",
    ),
]


PANDAS_FILESYSTEM_TEST_CASES = [
    pytest.param(
        'name=="albert"',
        id="text-eq",
    ),
    pytest.param(
        "quantity<3",
        id="number-lt",
    ),
    pytest.param(
        "quantity==1",
        id="number-eq",
    ),
    pytest.param(
        "updated_at<datetime.date(2021,2,1)",
        id="datetime.date-lt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        "updated_at>datetime.date(2021,1,30)",
        id="datetime.date-gt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        "updated_at==datetime.date(2021,1,31)",
        id="datetime.date-eq",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        "created_at<datetime.datetime(2021,1,31,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-lt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        "created_at>datetime.datetime(2021,1,29,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-gt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        "created_at==datetime.datetime(2021,1,30,0,0,0,tzinfo=datetime.timezone.utc)",
        id="datetime.datetime-eq",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
]


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    PANDAS_DATAFRAME_TEST_CASES,
)
def test_expect_column_min_to_be_between__pandas_dataframe_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="pandas",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasFilesystemCsvDatasourceTestConfig(),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    PANDAS_FILESYSTEM_TEST_CASES,
)
def test_expect_column_min_to_be_between__pandas_filesystem_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="pandas",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


SQL_TEST_CASES = [
    pytest.param(
        'col("name")=="albert"',
        id="text-eq",
    ),
    pytest.param(
        'col("quantity")<3',
        id="number-lt",
    ),
    pytest.param(
        'col("quantity")==1',
        id="number-eq",
    ),
    pytest.param(
        'col("updated_at")<date("2021-02-01"))',
        id="date-lt",
    ),
    pytest.param(
        'col("updated_at")>date("2021-01-30"))',
        id="date-gt",
    ),
    pytest.param(
        'col("updated_at")==date("2021-01-31"))',
        id="date-eq",
    ),
    pytest.param(
        'col("created_at")<date("2021-01-31 00:00:00"))',
        id="datetime-lt",
    ),
    pytest.param(
        'col("created_at")>date("2021-01-29 00:00:00"))',
        id="datetime-gt",
    ),
]


@parameterize_batch_for_data_sources(
    data_source_configs=[
        BigQueryDatasourceTestConfig(
            column_types={
                "created_at": BIGQUERY_TYPES.DATETIME,
                "updated_at": BIGQUERY_TYPES.DATE,
            }
        ),
        MSSQLDatasourceTestConfig(),
        MySQLDatasourceTestConfig(
            column_types={
                "created_at": sqltypes.TIMESTAMP(timezone=True),
                "updated_at": sqltypes.DATE,
            }
        ),
        PostgreSQLDatasourceTestConfig(
            column_types={
                "created_at": POSTGRESQL_TYPES.TIMESTAMP,
                "updated_at": POSTGRESQL_TYPES.DATE,
            }
        ),
        SqliteDatasourceTestConfig(),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    SQL_TEST_CASES,
)
def test_expect_column_min_to_be_between__sql_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        DatabricksDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(
            column_types={
                "created_at": SNOWFLAKE_TYPES.TIMESTAMP_TZ,
                "updated_at": sqltypes.DATE,  # snowflake.sqlalchemy missing snowflake DATE type
            }
        ),
    ],
    data=DATA_WITH_STRING_DATETIMES,
)
@pytest.mark.parametrize(
    "row_condition",
    SQL_TEST_CASES,
)
def test_expect_column_min_to_be_between__snowflake_databricks_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


SPARK_TEST_CASES = [
    pytest.param(
        'col("name")=="albert"',
        id="text-eq",
    ),
    pytest.param(
        'col("quantity")<3',
        id="number-lt",
    ),
    pytest.param(
        'col("quantity")==1',
        id="number-eq",
    ),
    pytest.param(
        'col("updated_at")<date("2021-02-01"))',
        id="date-lt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        'col("updated_at")>date("2021-01-30"))',
        id="date-gt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        'col("updated_at")==date("2021-01-31"))',
        id="date-eq",
    ),
    pytest.param(
        'col("created_at")<date("2021-01-31 00:00:00"))',
        id="datetime-lt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
    pytest.param(
        'col("created_at")>date("2021-01-29 00:00:00"))',
        id="datetime-gt",
        marks=pytest.mark.xfail(
            strict=True,
            reason="Lack of support for date i/o in test framework",
        ),
    ),
]


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SparkFilesystemCsvDatasourceTestConfig(),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    SPARK_TEST_CASES,
)
def test_expect_column_min_to_be_between__spark_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
