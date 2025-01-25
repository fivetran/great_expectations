import pathlib
from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd
import pytest

from great_expectations.compatibility import pyspark
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.data_asset.path.spark.csv_asset import CSVAsset
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.execution_engine import SparkDFExecutionEngine
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


@dataclass(frozen=True)
class SparkFilesystemCsvDatasourceTestConfig(DataSourceTestConfig):
    # see "read" options at https://spark.apache.org/docs/3.5.3/sql-data-sources-csv.html#data-source-option
    spark_read_options: dict[str, Any] = field(default_factory=dict)
    # see "write" options at https://spark.apache.org/docs/3.5.3/sql-data-sources-csv.html#data-source-option
    spark_write_options: dict[str, Any] = field(default_factory=dict)

    @property
    @override
    def label(self) -> str:
        return "spark-filesystem-csv"

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
        assert not extra_data, "extra_data is not supported for this data source yet."

        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)

        return SparkFilesystemCsvBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
        )


class SparkFilesystemCsvBatchTestSetup(
    BatchTestSetup[SparkFilesystemCsvDatasourceTestConfig, CSVAsset]
):
    def __init__(
        self,
        config: SparkFilesystemCsvDatasourceTestConfig,
        data: pd.DataFrame,
        base_dir: pathlib.Path,
    ) -> None:
        super().__init__(config=config, data=data)
        self._base_dir = base_dir

    @property
    def spark_session(self) -> pyspark.SparkSession:
        return SparkDFExecutionEngine.get_or_create_spark_session()

    @override
    def make_asset(self) -> CSVAsset:
        return self.context.data_sources.add_spark_filesystem(
            name=self._random_resource_name(), base_directory=self._base_dir
        ).add_csv_asset(
            name=self._random_resource_name(),
            header=True,
            infer_schema=True,
            **self.config.spark_read_options,
        )

    @override
    def make_batch(self) -> Batch:
        return (
            self.make_asset()
            .add_batch_definition_path(name=self._random_resource_name(), path=self.csv_path)
            .get_batch()
        )

    @override
    def setup(self) -> None:
        file_path = self._base_dir / self.csv_path
        self.spark_session.createDataFrame(self.data).write.format("csv").options(
            **self.config.spark_write_options
        ).save(str(file_path))

    @override
    def teardown(self) -> None: ...

    @property
    def csv_path(self) -> pathlib.Path:
        return pathlib.Path(f"{self._random_resource_name()}.csv")
