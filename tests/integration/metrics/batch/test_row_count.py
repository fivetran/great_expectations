import pandas as pd

from great_expectations.metrics.batch.row_count import BatchRowCount, BatchRowCountResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import PANDAS_DATA_SOURCES, SPARK_DATA_SOURCES, SQL_DATA_SOURCES

DATA_FRAME = pd.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "name": [1, 2, 3, 4],
    },
)


class TestBatchRowCount:
    ROW_COUNT = 4

    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_pandas(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = BatchRowCount()
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, BatchRowCountResult)
        assert metric_result.value == self.ROW_COUNT

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_spark(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = BatchRowCount()
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, BatchRowCountResult)
        assert metric_result.value == self.ROW_COUNT

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_success_sql(self, batch_for_datasource) -> None:
        batch = batch_for_datasource
        metric = BatchRowCount()
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, BatchRowCountResult)
        assert metric_result.value == self.ROW_COUNT
