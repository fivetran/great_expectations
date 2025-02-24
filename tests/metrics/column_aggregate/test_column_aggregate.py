from pathlib import Path

import pandas
import pytest
from pytest import FixtureRequest

from great_expectations.metrics.column_aggregate.mean import (
    ColumnValuesMean,
    ColumnValuesMeanResult,
)
from great_expectations.metrics.metric_results import MetricErrorResult
from tests.integration.test_utils.data_source_config import (
    PandasDataFrameDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.pandas_data_frame import (
    PandasDataFrameBatchTestSetup,
)
from tests.integration.test_utils.data_source_config.postgres import PostgresBatchTestSetup
from tests.integration.test_utils.data_source_config.snowflake import (
    SnowflakeBatchTestSetup,
)
from tests.integration.test_utils.data_source_config.spark_filesystem_csv import (
    SparkFilesystemCsvBatchTestSetup,
)


@pytest.fixture
def dataframe() -> pandas.DataFrame:
    return pandas.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "number": [1, 2, 3, 4],
            "string": ["a", "b", "c", "d"],
        },
    )


@pytest.fixture
def setup_pandas(dataframe: pandas.DataFrame) -> PandasDataFrameBatchTestSetup:
    return PandasDataFrameBatchTestSetup(
        config=PandasDataFrameDatasourceTestConfig(),
        data=dataframe,
    )


@pytest.fixture
def setup_spark(dataframe: pandas.DataFrame, tmp_path: Path) -> SparkFilesystemCsvBatchTestSetup:
    return SparkFilesystemCsvBatchTestSetup(
        config=SparkFilesystemCsvDatasourceTestConfig(),
        data=dataframe,
        base_dir=tmp_path,
    )


@pytest.fixture
def setup_postgres(dataframe: pandas.DataFrame) -> PostgresBatchTestSetup:
    return PostgresBatchTestSetup(
        config=PostgreSQLDatasourceTestConfig(), data=dataframe, extra_data={}
    )


@pytest.fixture
def setup_snowflake(dataframe: pandas.DataFrame) -> SnowflakeBatchTestSetup:
    return SnowflakeBatchTestSetup(
        config=SnowflakeDatasourceTestConfig(), data=dataframe, extra_data={}
    )


@pytest.mark.parametrize(
    "setup_datasource",
    [
        pytest.param("setup_pandas", marks=pytest.mark.unit),
        pytest.param("setup_spark", marks=pytest.mark.spark),
        pytest.param("setup_postgres", marks=pytest.mark.postgresql),
        pytest.param("setup_snowflake", marks=pytest.mark.snowflake),
    ],
)
def test_mean_success(setup_datasource: str, request: FixtureRequest) -> None:
    batch_setup = request.getfixturevalue(setup_datasource)
    with batch_setup.batch_test_context() as batch:
        metric = ColumnValuesMean(batch_id=batch.id, column="number")
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, ColumnValuesMeanResult)
        assert metric_result.value == 2.5


@pytest.mark.parametrize(
    "setup_datasource",
    [
        pytest.param("setup_pandas", marks=pytest.mark.unit),
        # The metric result for mean for spark is not `column.mean` but `column.aggregate.mean`.
        # There is a bug to track fixing this: https://greatexpectations.atlassian.net/browse/GX-448
        # pytest.param("setup_spark", marks=pytest.mark.spark),
        pytest.param("setup_postgres", marks=pytest.mark.postgresql),
        pytest.param("setup_snowflake", marks=pytest.mark.snowflake),
    ],
)
def test_mean_failure(setup_datasource: str, request: FixtureRequest) -> None:
    batch_setup = request.getfixturevalue(setup_datasource)
    with batch_setup.batch_test_context() as batch:
        metric = ColumnValuesMean(batch_id=batch.id, column="string")
        metric_result = batch.compute_metrics(metric)
        assert isinstance(metric_result, MetricErrorResult)
