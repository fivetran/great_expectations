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

data = pd.DataFrame(
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


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PandasDataFrameDatasourceTestConfig(),
        PandasFilesystemCsvDatasourceTestConfig(),
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
    ],
)
def test_expect_column_min_to_be_between__pandas_row_condition(
    batch_for_datasource: Batch, row_condition: str
) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="date",
        min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).date(),
        max_value=datetime(year=2022, month=1, day=1, tzinfo=timezone.utc).date(),
        row_condition=row_condition,
        condition_parser="pandas",
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[
        SparkFilesystemCsvDatasourceTestConfig(),
        DatabricksDatasourceTestConfig(),
        MSSQLDatasourceTestConfig(),
        MySQLDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
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
