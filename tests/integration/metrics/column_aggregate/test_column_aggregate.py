import pandas

from great_expectations.metrics.column_aggregate.mean import (
    ColumnValuesMean,
    ColumnValuesMeanResult,
)
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
        "string": ["a", "b", "c", "d"],
    },
)

DATA_SOURCES_WITHOUT_SPARK_SQLITE: list[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    PandasDataFrameDatasourceTestConfig(),
]

DATA_SOURCES: list[DataSourceTestConfig] = DATA_SOURCES_WITHOUT_SPARK_SQLITE + [
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=DATA_FRAME,
)
def test_mean_success(batch_for_datasource) -> None:
    batch = batch_for_datasource
    metric = ColumnValuesMean(batch_id=batch.id, column="number")
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, ColumnValuesMeanResult)
    assert metric_result.value == 2.5


# For spark, when computing the mean, if it fails, the metric name changes from
# `column.mean` to `column.aggregate.mean`.
# There is a bug to track fixing this: https://greatexpectations.atlassian.net/browse/GX-448
# For sqlite, when computing the mean, any non-numeric values are ignored (or maybe treated
# as 0) so we don't an error.
@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES_WITHOUT_SPARK_SQLITE,
    data=DATA_FRAME,
)
def test_mean_failure(batch_for_datasource) -> None:
    batch = batch_for_datasource
    metric = ColumnValuesMean(batch_id=batch.id, column="string")
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, MetricErrorResult)
