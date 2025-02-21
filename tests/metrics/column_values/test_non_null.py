from pathlib import Path

import pandas as pd
import pytest

from great_expectations.compatibility.pyspark import pyspark
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.core.id_dict import IDDict
from great_expectations.metrics.column_values.non_null import (
    ColumnValuesNonNull,
    ColumnValuesNonNullCount,
    ColumnValuesNonNullCountResult,
    ColumnValuesNonNullResult,
)
from great_expectations.metrics.metric_results import ColumnValuesCondition
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


class TestColumnValuesNonNull:
    DATA_FRAME = pd.DataFrame(
        {
            "id": [1, 2, None, 4],
            "name": ["a", None, "c", "d"],
        },
    )
    NON_NULL: ColumnValuesCondition = ()

    @pytest.mark.unit
    def test_success_pandas(self) -> None:
        batch_setup = PandasDataFrameBatchTestSetup(
            config=PandasDataFrameDatasourceTestConfig(),
            data=self.DATA_FRAME,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNull(batch_id=batch.id, column="name")
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullResult)
            expected_value = (
                pd.Series([False, True, False, False], name="name", dtype=bool),
                IDDict({"batch_id": batch.id, "row_condition": None}),
                {"column": "name"},
            )
            assert metric_result.value[0].equals(expected_value[0])
            assert metric_result.value[1] == expected_value[1]
            assert metric_result.value[2] == expected_value[2]

    @pytest.mark.spark
    def test_success_spark(self, tmp_path: Path) -> None:
        batch_setup = SparkFilesystemCsvBatchTestSetup(
            config=SparkFilesystemCsvDatasourceTestConfig(),
            data=self.DATA_FRAME,
            base_dir=tmp_path,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNull(batch_id=batch.id, column="name")
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullResult)
            expected_value = (
                pyspark.Column(),
                IDDict({"batch_id": batch.id, "row_condition": None}),
                {"column": "name"},
            )
            assert metric_result.value == expected_value

    @pytest.mark.postgresql
    def test_success_postgres(self) -> None:
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(),
            data=self.DATA_FRAME,
            extra_data={},
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNull(batch_id=batch.id, column="name")
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullResult)
            expected_value = (
                sa.ColumnClause("name").is_(None),
                IDDict({"batch_id": batch.id, "row_condition": None}),
                {"column": "name"},
            )
            assert metric_result.value[0].compare(expected_value[0])
            assert metric_result.value[1] == expected_value[1]
            assert metric_result.value[2] == expected_value[2]


class TestColumnValuesNonNullCount:
    DATA_FRAME = pd.DataFrame(
        {
            "letter": ["a", None, "c", "d"],
        },
    )
    NON_NULL_COUNT = 3

    @pytest.mark.unit
    def test_success_pandas(self) -> None:
        batch_setup = PandasDataFrameBatchTestSetup(
            config=PandasDataFrameDatasourceTestConfig(),
            data=self.DATA_FRAME,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNullCount(batch_id=batch.id, column="letter")
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullCountResult)
            assert metric_result.value == self.NON_NULL_COUNT

    @pytest.mark.spark
    def test_success_spark(self, tmp_path: Path) -> None:
        batch_setup = SparkFilesystemCsvBatchTestSetup(
            config=SparkFilesystemCsvDatasourceTestConfig(),
            data=self.DATA_FRAME,
            base_dir=tmp_path,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNullCount(batch_id=batch.id, column="letter")
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullCountResult)
            assert metric_result.value == self.NON_NULL_COUNT

    @pytest.mark.postgresql
    def test_success_postgres(self) -> None:
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(),
            data=self.DATA_FRAME,
            extra_data={},
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNullCount(batch_id=batch.id, column="letter")
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullCountResult)
            assert metric_result.value == self.NON_NULL_COUNT
