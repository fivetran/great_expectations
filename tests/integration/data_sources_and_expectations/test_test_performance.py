"""Tests to ensure we are reusing BatchTestSetup instances across tests when appropriate.

The tests here work together to give some confidence that we aren't running the same setup/teardown
multiple times for equivalent TestConfigs. This is primarily to prevent regressions in this process.

Note that we aren't testing to ensure we don't over-reuse BatchTestSetup instances, e.g. for
different TestConfigs; that would be caught by our regular tests.
"""

from dataclasses import dataclass
from functools import cache
from typing import Mapping

import pandas as pd
import pytest
import sqlalchemy.dialects.postgresql as POSTGRESQL_TYPES

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.datasource.fluent.pandas_datasource import DataFrameAsset
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


@dataclass
class SetupTeardownCounts:
    setup_count = 0
    teardown_count = 0


class DummyTestConfig(DataSourceTestConfig):
    @property
    @override
    def label(self) -> str:
        return "test"

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
        return DummyBatchTestSetup(data=data, config=self, context=context)


class DummyBatchTestSetup(BatchTestSetup[DummyTestConfig, DataFrameAsset]):
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
    def setup(self) -> None:
        counts = DummyBatchTestSetup._get_setup_teardown_counts()
        if counts.setup_count:
            assert False, "Setup is not being cached"
        counts.setup_count += 1

    @override
    def teardown(self) -> None:
        counts = DummyBatchTestSetup._get_setup_teardown_counts()
        if counts.teardown_count:
            assert False, "Teardown is not being cached"
        counts.teardown_count -= 1

    @staticmethod
    @cache
    def _get_setup_teardown_counts() -> SetupTeardownCounts:
        return SetupTeardownCounts()


@parameterize_batch_for_data_sources(
    data_source_configs=[
        DummyTestConfig(column_types={"a": POSTGRESQL_TYPES.INTEGER}),
        DummyTestConfig(column_types={"a": POSTGRESQL_TYPES.INTEGER}),
    ],
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_caching_within_a_test(batch_for_datasource) -> None:
    # This should fail in setup or teardown if the setup and teardown are not being cached
    ...


@parameterize_batch_for_data_sources(
    data_source_configs=[
        DummyTestConfig(column_types={"a": POSTGRESQL_TYPES.INTEGER}),
    ],
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_caching_across_tests(batch_for_datasource) -> None:
    # This should fail in setup or teardown if the setup and teardown are not being cached
    ...
