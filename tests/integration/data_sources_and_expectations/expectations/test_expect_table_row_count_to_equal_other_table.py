from typing import Mapping, Sequence

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

MULTI_ASSET_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(
    data_source_configs=MULTI_ASSET_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2, 3, 4]}),
    extra_data={"other_table": pd.DataFrame({"col_b": ["a", "b", "c", "d"]})},
)
def test_success(
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
def test_missing_table(batch_for_datasource: Batch):
    expectation = gxe.ExpectTableRowCountToEqualOtherTable(other_table_name="where_am_i")
    result = batch_for_datasource.validate(expectation)
    assert not result.success, "We should not find the other table, since we didn't load it."
