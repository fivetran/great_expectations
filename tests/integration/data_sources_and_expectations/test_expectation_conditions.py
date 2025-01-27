from datetime import datetime, timezone

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
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

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    spark_filesystem_csv_datasource_test_config = SparkFilesystemCsvDatasourceTestConfig(
        column_types={
            "created_at": PYSPARK_TYPES.TimestampType,
            "updated_at": PYSPARK_TYPES.DateType,
            "amount": PYSPARK_TYPES.FloatType,
            "quantity": PYSPARK_TYPES.IntegerType,
            "name": PYSPARK_TYPES.StringType,
        },
    )
except ModuleNotFoundError:
    spark_filesystem_csv_datasource_test_config = SparkFilesystemCsvDatasourceTestConfig()

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

SQL_DATA = pd.DataFrame(
    {
        "date": [
            datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
            datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
        ],
        "quantity": [1, 2, 3],
        "name": ["albert", "issac", "galileo"],
    }
)


PANDAS_TEST_CASES = [
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


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        PandasFilesystemCsvDatasourceTestConfig(
            read_options={
                "parse_dates": ["created_at", "updated_at"],
                "date_format": "mixed",
            },
        ),
    ],
    data=DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    PANDAS_TEST_CASES,
)
def test_expect_column_min_to_be_between__pandas_row_condition(
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
        DatabricksDatasourceTestConfig(),
        MSSQLDatasourceTestConfig(),
        MySQLDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ],
    data=SQL_DATA,
)
@pytest.mark.parametrize(
    "row_condition",
    [
        pytest.param(
            'col("name")=="albert"',
            id="text - eq",
        ),
        pytest.param(
            'col("quantity")<3',
            id="number - lt",
        ),
        pytest.param(
            'col("quantity")==1',
            id="number - eq",
        ),
    ],
)
def test_expect_column_min_to_be_between__spark_and_sql_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="date",
        min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).date(),
        max_value=datetime(year=2022, month=1, day=1, tzinfo=timezone.utc).date(),
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
    data_source_configs=[spark_filesystem_csv_datasource_test_config],
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
