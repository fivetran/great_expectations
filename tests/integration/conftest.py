from dataclasses import dataclass
from typing import Callable, Generator, Mapping, Optional, Sequence, TypeVar

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context.data_context.context_factory import set_context
from great_expectations.datasource.fluent.interfaces import Batch, DataAsset
from tests.integration.test_utils.data_source_config import DataSourceTestConfig
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    dict_to_tuple,
    hash_data_frame,
)
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup

_F = TypeVar("_F", bound=Callable)


@dataclass(frozen=True)
class TestConfig:
    data_source_config: DataSourceTestConfig
    data: pd.DataFrame
    extra_data: Mapping[str, pd.DataFrame]

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self.__class__,
                self.data_source_config,
                hash_data_frame(self.data),
                dict_to_tuple(
                    {k: hash_data_frame(self.extra_data[k]) for k in sorted(self.extra_data)}
                ),
            )
        )

    @override
    def __eq__(self, value: object) -> bool:
        # We need to implement this ourselves to call `.equals` on dataframes.`
        if not isinstance(value, TestConfig):
            return False
        return all(
            [
                self.data_source_config == value.data_source_config,
                self.data.equals(value.data),
                self.extra_data.keys() == value.extra_data.keys(),
                all(self.extra_data[k].equals(value.extra_data[k]) for k in self.extra_data),
            ]
        )


def parameterize_batch_for_data_sources(
    data_source_configs: Sequence[DataSourceTestConfig],
    data: pd.DataFrame,
    extra_data: Optional[Mapping[str, pd.DataFrame]] = None,
) -> Callable[[_F], _F]:
    """Test decorator that parametrizes a test function with batches for various data sources.
    This injects a `batch_for_datasource` parameter into the test function for each data source
    type.

    Args:
        data_source_configs: The data source configurations to test.
        data: Data to load into the asset
        extra_data: Mapping of {asset_label: data} to load into other assets. Only relevant for SQL
                    mutli-table expectations. NOTE: This is NOT the table name. The label is used to
                    correlate the data with the types passed to
                    DataSourceTestConfig.extra_column_types.


    example use:
        @parameterize_batch_for_data_sources(
            data_source_configs=[DataSourceType.FOO, DataSourceType.BAR],
            data=pd.DataFrame{"col_name": [1, 2]},
            # description="test_stuff",
        )
        def test_stuff(batch_for_datasource) -> None:
            ...
    """

    def decorator(func: _F) -> _F:
        pytest_params = [
            pytest.param(
                TestConfig(
                    data_source_config=config,
                    data=data,
                    extra_data=extra_data or {},
                ),
                id=config.test_id,
                marks=[config.pytest_mark],
            )
            for config in data_source_configs
        ]
        parameterize_decorator = pytest.mark.parametrize(
            _batch_setup_for_datasource.__name__,
            pytest_params,
            indirect=True,
        )
        return parameterize_decorator(func)

    return decorator


# NOTE on performance setup/teardown:
# When we get equivalent TestConfigs, we only instantiate one BatchTestSetup for all of them, and
# only perform its setup/teardown once. batch_for_datasource instantiate the BatchTestSetup
# immediately before the first test that needs it and store it in cached_test_configs. Subsequent
# tests that use the same TestConfig will reuse the same BatchTestSetup. At the end of the test
# session, _cleanup will clean up all the BatchTestSetups.


@pytest.fixture(scope="session")
def _cached_test_configs() -> dict[TestConfig, BatchTestSetup]:
    """Fixture to hold cached test configurations across tests."""
    cached_test_configs: dict[TestConfig, BatchTestSetup] = {}

    return cached_test_configs


@pytest.fixture(scope="session")
def _cleanup(
    _cached_test_configs: Mapping[TestConfig, BatchTestSetup],
) -> Generator[None, None, None]:
    """Fixture to do all teardown at the end of the test session."""
    yield
    for batch_setup in _cached_test_configs.values():
        batch_setup.teardown()


@pytest.fixture
def _batch_setup_for_datasource(
    request: pytest.FixtureRequest,
    _cached_test_configs: dict[TestConfig, BatchTestSetup],
    _cleanup,
) -> Generator[BatchTestSetup, None, None]:
    """Fixture that yields a BatchSetup for a specific data source type.
    This must be used in conjunction with `indirect=True` to defer execution
    """
    config = request.param
    assert isinstance(config, TestConfig)

    if config not in _cached_test_configs:
        batch_setup = config.data_source_config.create_batch_setup(
            request=request,
            data=config.data,
            extra_data=config.extra_data,
        )
        _cached_test_configs[config] = batch_setup
        batch_setup.setup()

    yield _cached_test_configs[config]


@pytest.fixture
def batch_for_datasource(
    _batch_setup_for_datasource: BatchTestSetup,
) -> Generator[Batch, None, None]:
    """Fixture that yields a batch for a specific data source type.
    This must be used in conjunction with `indirect=True` to defer execution
    """
    set_context(_batch_setup_for_datasource.context)
    yield _batch_setup_for_datasource.make_batch()


@pytest.fixture
def asset_for_datasource(
    _batch_setup_for_datasource: BatchTestSetup,
) -> Generator[DataAsset, None, None]:
    """Fixture that yields an asset for a specific data source type.
    This must be used in conjunction with `indirect=True` to defer execution
    """
    set_context(_batch_setup_for_datasource.context)
    yield _batch_setup_for_datasource.asset


@pytest.fixture
def extra_table_names_for_datasource(
    _batch_setup_for_datasource: BatchTestSetup,
) -> Generator[Mapping[str, str], None, None]:
    """Fixture that yields extra table names"""
    assert isinstance(_batch_setup_for_datasource, SQLBatchTestSetup)
    yield {key: t.name for key, t in _batch_setup_for_datasource.extra_table_data.items()}
