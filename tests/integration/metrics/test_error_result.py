import pandas

from great_expectations.metrics.column.mean import ColumnMean
from great_expectations.metrics.metric_results import MetricErrorResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

DATA_FRAME = pandas.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "number": [1, 2, 3, 4],
    },
)

DATA_SOURCES: list[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    PandasDataFrameDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=DATA_FRAME,
)
def test_error_result(batch_for_datasource) -> None:
    batch = batch_for_datasource
    metric = ColumnMean(column="non_existent_column")
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, MetricErrorResult)
    assert metric_result.value.exception_message is not None
    assert metric_result.value.exception_traceback is not None
