import pathlib
from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.data_asset.path.pandas.generated_assets import CSVAsset
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


@dataclass(frozen=True)
class PandasFilesystemCsvDatasourceTestConfig(DataSourceTestConfig):
    # see options: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
    read_options: dict[str, Any] = field(default_factory=dict)
    # see options: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
    write_options: dict[str, Any] = field(default_factory=dict)

    @property
    @override
    def label(self) -> str:
        return "pandas-filesystem-csv"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.filesystem

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        assert not extra_data, "extra_data is not supported for this data source."
        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)

        return PandasFilesystemCsvBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
            context=context,
        )


class PandasFilesystemCsvBatchTestSetup(
    BatchTestSetup[PandasFilesystemCsvDatasourceTestConfig, CSVAsset]
):
    def __init__(
        self,
        config: PandasFilesystemCsvDatasourceTestConfig,
        data: pd.DataFrame,
        base_dir: pathlib.Path,
        context: AbstractDataContext,
    ) -> None:
        super().__init__(config=config, data=data, context=context)
        self._base_dir = base_dir

    @override
    def make_asset(self) -> CSVAsset:
        return self.context.data_sources.add_pandas_filesystem(
            name=self._random_resource_name(), base_directory=self._base_dir
        ).add_csv_asset(
            name=self._random_resource_name(),
            **self.config.read_options,
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
        self.data.to_csv(file_path, index=False, **self.config.write_options)

    @override
    def teardown(self) -> None: ...

    @property
    def csv_path(self) -> pathlib.Path:
        return pathlib.Path("data.csv")
