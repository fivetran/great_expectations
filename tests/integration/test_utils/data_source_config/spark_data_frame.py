from typing import TYPE_CHECKING, Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.datasource.fluent.spark_datasource import DataFrameAsset
from great_expectations.execution_engine import SparkDFExecutionEngine
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)

if TYPE_CHECKING:
    from great_expectations.compatibility.pyspark import SparkSession


class SparkDataFrameDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "spark-data-frame"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.spark

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> BatchTestSetup:
        assert not extra_data, "extra_data is not supported for this data source."
        return SparkDataFrameBatchTestSetup(data=data, config=self)


class SparkDataFrameBatchTestSetup(
    BatchTestSetup[SparkDataFrameDatasourceTestConfig, DataFrameAsset]
):
    @override
    def make_asset(self) -> DataFrameAsset:
        return self.context.data_sources.add_spark(
            self._random_resource_name()
        ).add_dataframe_asset(self._random_resource_name())

    @override
    def make_batch(self) -> Batch:
        data_frame = self._spark_session.createDataFrame(self.data)
        return (
            self.make_asset()
            .add_batch_definition_whole_dataframe(self._random_resource_name())
            .get_batch(batch_parameters={"dataframe": data_frame})
        )

    @property
    def _spark_session(self) -> SparkSession:
        return SparkDFExecutionEngine.get_or_create_spark_session()

    @override
    def setup(self) -> None: ...

    @override
    def teardown(self) -> None: ...
