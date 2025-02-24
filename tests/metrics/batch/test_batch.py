from pathlib import Path

import pandas
import pytest

from great_expectations.metrics.batch.row_count import BatchRowCount, BatchRowCountResult
from tests.integration.test_utils.data_source_config import (
    PandasDataFrameDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.pandas_data_frame import (
    PandasDataFrameBatchTestSetup,
)
from tests.integration.test_utils.data_source_config.postgres import PostgresBatchTestSetup
from tests.integration.test_utils.data_source_config.spark_filesystem_csv import (
    SparkFilesystemCsvBatchTestSetup,
)


class TestBatchRowCount:
    DATA_FRAME = pandas.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": [1, 2, 3, 4],
        },
    )
    ROW_COUNT = 4

    @pytest.mark.unit
    def test_success_pandas(self) -> None:
        batch_setup = PandasDataFrameBatchTestSetup(
            config=PandasDataFrameDatasourceTestConfig(),
            data=self.DATA_FRAME,
        )
        with batch_setup.batch_test_context() as batch:
            metric = BatchRowCount(batch_id=batch.id)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, BatchRowCountResult)
            assert metric_result.value == self.ROW_COUNT

    @pytest.mark.spark
    def test_success_spark(self, tmp_path: Path) -> None:
        batch_setup = SparkFilesystemCsvBatchTestSetup(
            config=SparkFilesystemCsvDatasourceTestConfig(),
            data=self.DATA_FRAME,
            base_dir=tmp_path,
        )
        with batch_setup.batch_test_context() as batch:
            metric = BatchRowCount(
                batch_id=batch.id,
            )
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, BatchRowCountResult)
            assert metric_result.value == self.ROW_COUNT

    @pytest.mark.postgresql
    def test_success_postgres(self) -> None:
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(), data=self.DATA_FRAME, extra_data={}
        )
        with batch_setup.batch_test_context() as batch:
            metric = BatchRowCount(batch_id=batch.id)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, BatchRowCountResult)
            assert metric_result.value == self.ROW_COUNT
