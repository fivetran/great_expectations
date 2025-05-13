from typing import Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.datasource.fluent.pandas_datasource import DataFrameAsset
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


class PandasDataFrameDatasourceTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "pandas-data-frame"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.unit

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        assert not extra_data, "extra_data is not supported for this data source."
        return PandasDataFrameBatchTestSetup(data=data, config=self, context=context)


class PandasDataFrameBatchTestSetup(
    BatchTestSetup[PandasDataFrameDatasourceTestConfig, DataFrameAsset]
):
    @override
    def make_asset(self) -> DataFrameAsset:
        return self.context.data_sources.add_pandas(
            self._random_resource_name()
        ).add_dataframe_asset(self._random_resource_name())

    @override
    def make_batch(self) -> Batch:
        return (
            self.make_asset()
            .add_batch_definition_whole_dataframe(self._random_resource_name())
            .get_batch(batch_parameters={"dataframe": self.data})
        )

    @override
    def setup(self) -> None: ...

    @override
    def teardown(self) -> None: ...
