from datetime import datetime, timezone

import pandas as pd
import pytest

import great_expectations.expectations as gxe
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

data = pd.DataFrame(
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

pandas_column_types = {"created_at": pd.Timestamp, "updated_at": datetime.date}

sql_column_types = {
    "created_at": sqltypes.TIMESTAMP(timezone=True),
    "updated_at": sqltypes.DATE,
}


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(column_types=pandas_column_types),
    ],
    data=data,
)
@pytest.mark.parametrize(
    "row_condition",
    [
        pytest.param(
            'name=="albert"',
            id="text - eq",
        ),
        pytest.param(
            "quantity<3",
            id="number - lt",
        ),
        pytest.param(
            "quantity==1",
            id="number - eq",
        ),
        pytest.param(
            'created_at=="2021-01-30 00:00:00+0000"',
            id="pd.Timestamp - eq",
        ),
        pytest.param(
            "updated_at==datetime.date(2021,1,31)",
            id="datetime.date - eq",
        ),
    ],
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
        PandasFilesystemCsvDatasourceTestConfig(
            column_types=pandas_column_types,
        ),
    ],
    data=data,
)
@pytest.mark.parametrize(
    "row_condition",
    [
        pytest.param(
            'name=="albert"',
            id="text - eq",
        ),
        pytest.param(
            "quantity<3",
            id="number - lt",
        ),
        pytest.param(
            "quantity==1",
            id="number - eq",
        ),
        pytest.param(
            'created_at=="2021-01-30 00:00:00+0000"',
            id="pd.Timestamp - eq",
            marks=pytest.mark.xfail(
                strict=True,
                reason="Issue with PandasFilesystemDatasource converting date types into strings",
            ),
        ),
        pytest.param(
            "updated_at==datetime.date(2021,1,31)",
            id="datetime.date - eq",
            marks=pytest.mark.xfail(
                strict=True,
                reason="Issue with PandasFilesystemDatasource converting date types into strings",
            ),
        ),
    ],
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


@parameterize_batch_for_data_sources(
    data_source_configs=[
        BigQueryDatasourceTestConfig(column_types=sql_column_types),
        SparkFilesystemCsvDatasourceTestConfig(column_types=sql_column_types),
        DatabricksDatasourceTestConfig(column_types=sql_column_types),
        MSSQLDatasourceTestConfig(column_types=sql_column_types),
        MySQLDatasourceTestConfig(column_types=sql_column_types),
        PostgreSQLDatasourceTestConfig(column_types=sql_column_types),
        SnowflakeDatasourceTestConfig(column_types=sql_column_types),
        SqliteDatasourceTestConfig(column_types=sql_column_types),
    ],
    data=data,
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
        pytest.param(
            'col("created_at")==date("2021-01-30"))',
            id="datetime - eq",
        ),
        pytest.param(
            'col("updated_at")==date("2021-01-31"))',
            id="date - eq",
        ),
    ],
)
def test_expect_column_min_to_be_between__spark_and_sql_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="amount",
        min_value=0.5,
        max_value=1.5,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )
    result = batch_for_datasource.validate(expectation, result_format="COMPLETE")
    assert result.success
