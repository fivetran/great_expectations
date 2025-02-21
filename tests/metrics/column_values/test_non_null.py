from pathlib import Path

import pandas as pd
import pytest

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.core.id_dict import IDDict
from great_expectations.metrics.column_values.non_null import (
    ColumnValuesNonNull,
    ColumnValuesNonNullCount,
    ColumnValuesNonNullCountResult,
    ColumnValuesNonNullResult,
)
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

STRING_COLUMN_NAME = "letter"
DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: ["a", None, "c", "d"],
    },
)

try:
    from great_expectations.compatibility.pyspark import types as PYSPARK_TYPES

    SPARK_COLUMN_TYPES = {
        STRING_COLUMN_NAME: PYSPARK_TYPES.StringType,
    }
except ModuleNotFoundError:
    SPARK_COLUMN_TYPES = {}


class TestColumnValuesNonNull:
    @pytest.mark.unit
    def test_success_pandas(self) -> None:
        batch_setup = PandasDataFrameBatchTestSetup(
            config=PandasDataFrameDatasourceTestConfig(),
            data=DATA_FRAME,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNull(batch_id=batch.id, column=STRING_COLUMN_NAME)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullResult)
            expected_value = (
                pd.Series([False, True, False, False], name=STRING_COLUMN_NAME, dtype=bool),
                IDDict({"batch_id": batch.id, "row_condition": None}),
                {"column": STRING_COLUMN_NAME},
            )
            assert metric_result.value[0].equals(expected_value[0])
            assert metric_result.value[1] == expected_value[1]
            assert metric_result.value[2] == expected_value[2]

    @pytest.mark.spark
    def test_success_spark(self, tmp_path: Path) -> None:
        batch_setup = SparkFilesystemCsvBatchTestSetup(
            config=SparkFilesystemCsvDatasourceTestConfig(
                column_types=SPARK_COLUMN_TYPES,
            ),
            data=DATA_FRAME,
            base_dir=tmp_path,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNull(batch_id=batch.id, column=STRING_COLUMN_NAME)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullResult)
            expected_value = (
                ~(F.col(STRING_COLUMN_NAME).isNotNull()),
                IDDict({"batch_id": batch.id, "row_condition": None}),
                {"column": STRING_COLUMN_NAME},
            )
            assert str(metric_result.value[0]) == str(expected_value[0])
            assert metric_result.value[1] == expected_value[1]
            assert metric_result.value[2] == expected_value[2]

    @pytest.mark.postgresql
    def test_success_postgres(self) -> None:
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(),
            data=DATA_FRAME,
            extra_data={},
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNull(batch_id=batch.id, column=STRING_COLUMN_NAME)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullResult)
            expected_value = (
                sa.ColumnClause(STRING_COLUMN_NAME).is_(None),
                IDDict({"batch_id": batch.id, "row_condition": None}),
                {"column": STRING_COLUMN_NAME},
            )
            assert metric_result.value[0].compare(expected_value[0])
            assert metric_result.value[1] == expected_value[1]
            assert metric_result.value[2] == expected_value[2]


class TestColumnValuesNonNullCount:
    NON_NULL_COUNT = 3

    @pytest.mark.unit
    def test_success_pandas(self) -> None:
        batch_setup = PandasDataFrameBatchTestSetup(
            config=PandasDataFrameDatasourceTestConfig(),
            data=DATA_FRAME,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNullCount(batch_id=batch.id, column=STRING_COLUMN_NAME)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullCountResult)
            assert metric_result.value == self.NON_NULL_COUNT

    @pytest.mark.spark
    def test_success_spark(self, tmp_path: Path) -> None:
        batch_setup = SparkFilesystemCsvBatchTestSetup(
            config=SparkFilesystemCsvDatasourceTestConfig(),
            data=DATA_FRAME,
            base_dir=tmp_path,
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNullCount(batch_id=batch.id, column=STRING_COLUMN_NAME)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullCountResult)
            assert metric_result.value == self.NON_NULL_COUNT

    @pytest.mark.postgresql
    def test_success_postgres(self) -> None:
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(),
            data=DATA_FRAME,
            extra_data={},
        )
        with batch_setup.batch_test_context() as batch:
            metric = ColumnValuesNonNullCount(batch_id=batch.id, column=STRING_COLUMN_NAME)
            metric_result = batch.compute_metrics(metric)
            assert isinstance(metric_result, ColumnValuesNonNullCountResult)
            assert metric_result.value == self.NON_NULL_COUNT
