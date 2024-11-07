from typing import Mapping

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
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
    ) -> BatchTestSetup:
        assert not extra_data, "extra_data is not supported for this data source."
        return PandasDataFrameBatchTestSetup(data=data, config=self)


class PandasDataFrameBatchTestSetup(BatchTestSetup[PandasDataFrameDatasourceTestConfig]):
    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self.context.data_sources.add_pandas(name)
            .add_dataframe_asset(name)
            .add_batch_definition_whole_dataframe(name)
            .get_batch(batch_parameters={"dataframe": self.data})
        )

    @override
    def setup(self) -> None: ...

    @override
    def teardown(self) -> None: ...
