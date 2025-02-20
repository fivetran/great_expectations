from pathlib import Path

import pandas
import pytest

from great_expectations.metrics.batch.batch import BatchRowCount, BatchRowCountResult
from great_expectations.validator.metrics_calculator import MetricsCalculator
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
            # todo: replace with batch.compute_metrics when available
            metrics_calculator = MetricsCalculator(
                execution_engine=batch.data.execution_engine,
                show_progress_bars=False,
            )
            batch.data.execution_engine.batch_manager.load_batch_list(batch_list=[batch])
            metric = BatchRowCount(
                batch_id=batch.id,
            )
            result = BatchRowCountResult(
                id=metric.id, value=metrics_calculator.get_metric(metric=metric.config)
            )
            assert result.value == self.ROW_COUNT

    @pytest.mark.spark
    def test_success_spark(self, tmp_path: Path) -> None:
        batch_setup = SparkFilesystemCsvBatchTestSetup(
            config=SparkFilesystemCsvDatasourceTestConfig(),
            data=self.DATA_FRAME,
            base_dir=tmp_path,
        )
        with batch_setup.batch_test_context() as batch:
            # todo: replace with batch.compute_metrics when available
            metrics_calculator = MetricsCalculator(
                execution_engine=batch.data.execution_engine,
                show_progress_bars=False,
            )
            batch.data.execution_engine.batch_manager.load_batch_list(batch_list=[batch])
            metric = BatchRowCount(
                batch_id=batch.id,
            )
            result = BatchRowCountResult(
                id=metric.id, value=metrics_calculator.get_metric(metric=metric.config)
            )
            assert result.value == self.ROW_COUNT

    @pytest.mark.postgresql
    def test_success_postgres(self) -> None:
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(), data=self.DATA_FRAME, extra_data={}
        )
        with batch_setup.batch_test_context() as batch:
            # todo: replace with batch.compute_metrics when available
            metrics_calculator = MetricsCalculator(
                execution_engine=batch.data.execution_engine,
                show_progress_bars=False,
            )
            batch.data.execution_engine.batch_manager.load_batch_list(batch_list=[batch])
            metric = BatchRowCount(batch_id=batch.id)
            result = BatchRowCountResult(
                id=metric.id, value=metrics_calculator.get_metric(metric=metric.config)
            )
            assert result.value == self.ROW_COUNT
