from datetime import datetime, timezone

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.compatibility.sqlalchemy import sqltypes
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        PandasFilesystemCsvDatasourceTestConfig(),
    ],
    data=pd.DataFrame(
        {
            "date": [
                datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
            ],
            "quantity": [1, 2, 3],
        }
    ),
)
def test_expect_column_min_to_be_between__pandas_row_condition(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="date",
        min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).date(),
        max_value=datetime(year=2022, month=1, day=1, tzinfo=timezone.utc).date(),
        row_condition="quantity<2",
        condition_parser="pandas",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        MSSQLDatasourceTestConfig(column_types={"date": sqltypes.DATE}),
        MySQLDatasourceTestConfig(column_types={"date": sqltypes.DATE}),
        PostgreSQLDatasourceTestConfig(column_types={"date": sqltypes.DATE}),
        SnowflakeDatasourceTestConfig(column_types={"date": sqltypes.DATE}),
        SqliteDatasourceTestConfig(column_types={"date": sqltypes.DATE}),
    ],
    data=pd.DataFrame(
        {
            "date": [
                datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
            ],
            "quantity": [1, 2, 3],
        }
    ),
)
def test_expect_column_min_to_be_between__sql_row_condition(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="date",
        min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).date(),
        max_value=datetime(year=2022, month=1, day=1, tzinfo=timezone.utc).date(),
        row_condition='col("quantity")<2',
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
