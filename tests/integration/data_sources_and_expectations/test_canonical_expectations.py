from datetime import datetime, timezone
from typing import Mapping, Sequence

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

ALL_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PandasDataFrameDatasourceTestConfig(),
    PandasFilesystemCsvDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_expect_column_min_to_be_between(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(column="a", min_value=1, max_value=1)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame(
        {
            "date": [
                datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
            ]
        }
    ),
)
def test_expect_column_min_to_be_between__date(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMinToBeBetween(
        column="date",
        min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).date(),
        max_value=datetime(year=2022, month=1, day=1, tzinfo=timezone.utc).date(),
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame(
        {
            "date": [
                datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
                datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
            ]
        }
    ),
)
def test_expect_column_max_to_be_between__date(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMaxToBeBetween(
        column="date",
        min_value=datetime(year=2023, month=1, day=1, tzinfo=timezone.utc).date(),
        max_value=datetime(year=2024, month=1, day=1, tzinfo=timezone.utc).date(),
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_expect_column_max_to_be_between(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMaxToBeBetween(column="a", min_value=2, max_value=2)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_expect_column_to_exist(batch_for_datasource):
    expectation = gxe.ExpectColumnToExist(column="a")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_expect_column_values_to_not_be_null(batch_for_datasource):
    expectation = gxe.ExpectColumnValuesToNotBeNull(column="a")
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2, 3, 4]}),
)
def test_expect_column_mean_to_be_between(batch_for_datasource):
    expectation = gxe.ExpectColumnMeanToBeBetween(column="a", min_value=2, max_value=3)
    result = batch_for_datasource.validate(expectation)
    assert result.success


class TestExpectTableRowCountToEqualOtherTable:
    MULTI_ASSET_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
        DatabricksDatasourceTestConfig(),
        MSSQLDatasourceTestConfig(),
        MySQLDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ]

    @parameterize_batch_for_data_sources(
        data_source_configs=MULTI_ASSET_DATA_SOURCES,
        data=pd.DataFrame({"a": [1, 2, 3, 4]}),
        extra_data={"other_table": pd.DataFrame({"col_b": ["a", "b", "c", "d"]})},
    )
    def test_success(
        self,
        batch_for_datasource: Batch,
        extra_table_names_for_datasource: Mapping[str, str],
    ):
        other_table_name = extra_table_names_for_datasource["other_table"]
        expectation = gxe.ExpectTableRowCountToEqualOtherTable(other_table_name=other_table_name)
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=MULTI_ASSET_DATA_SOURCES,
        data=pd.DataFrame({"a": [1, 2, 3, 4]}),
        extra_data={"other_table": pd.DataFrame({"col_b": ["just_this_one!"]})},
    )
    def test_different_counts(
        self,
        batch_for_datasource: Batch,
        extra_table_names_for_datasource: Mapping[str, str],
    ):
        other_table_name = extra_table_names_for_datasource["other_table"]
        expectation = gxe.ExpectTableRowCountToEqualOtherTable(other_table_name=other_table_name)
        result = batch_for_datasource.validate(expectation)
        assert not result.success
        assert result.result["observed_value"] == {
            "self": 4,
            "other": 1,
        }

    @parameterize_batch_for_data_sources(
        data_source_configs=MULTI_ASSET_DATA_SOURCES,
        data=pd.DataFrame({"a": [1, 2, 3, 4]}),
    )
    def test_missing_table(self, batch_for_datasource):
        expectation = gxe.ExpectTableRowCountToEqualOtherTable(other_table_name="where_am_i")
        result = batch_for_datasource.validate(expectation)
        assert not result.success, "We should not find the other table, since we didn't load it."
