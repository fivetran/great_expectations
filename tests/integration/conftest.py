from dataclasses import dataclass
from typing import Callable, Generator, Mapping, Optional, Sequence, TypeVar, Union
from uuid import UUID

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
    secondary_source_config: Union[DataSourceTestConfig, None] = None
    secondary_data: Union[pd.DataFrame, None] = None

    @override
    def __hash__(self) -> int:
        if self.secondary_data is None and self.secondary_source_config is not None:
            raise ValueError(
                "secondary_data cannot be None when secondary_source_config is provided"
            )
        return hash(
            (
                self.__class__,
                hash_data_frame(self.data),
                dict_to_tuple(
                    {k: hash_data_frame(self.extra_data[k]) for k in sorted(self.extra_data)}
                ),
                hash_data_frame(self.secondary_data) if self.secondary_data is not None else None,
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
                self.secondary_source_config == value.secondary_source_config,
                (self.secondary_data is None and value.secondary_data is None)
                or (
                    self.secondary_data is not None
                    and value.secondary_data is not None
                    and self.secondary_data.equals(value.secondary_data)
                ),
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
                    multi-table expectations. NOTE: This is NOT the table name. The label is used to
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
    if len(data_source_configs) == 0:
        raise ValueError("At least one data source configuration must be provided.")

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
def _cached_secondary_test_configs() -> dict[UUID, BatchTestSetup]:
    """Fixture to hold secondary test configurations across tests."""
    cached_test_configs: dict[UUID, BatchTestSetup] = {}
    return cached_test_configs


@pytest.fixture(scope="session")
def _cleanup(
    _cached_test_configs: Mapping[TestConfig, BatchTestSetup],
    _cached_secondary_test_configs: Mapping[TestConfig, BatchTestSetup],
) -> Generator[None, None, None]:
    """Fixture to do all teardown at the end of the test session."""
    yield
    for batch_setup in _cached_test_configs.values():
        batch_setup.teardown()
    for batch_setup in _cached_secondary_test_configs.values():
        batch_setup.teardown()


@pytest.fixture
def _batch_setup_for_datasource(
    request: pytest.FixtureRequest,
    _cached_test_configs: dict[TestConfig, BatchTestSetup],
    _cached_secondary_test_configs: dict[UUID, BatchTestSetup],
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
            context=None,
        )
        _cached_test_configs[config] = batch_setup
        batch_setup.setup()
        if config.secondary_source_config:
            assert config.secondary_data is not None, (
                "Secondary data is required when secondary config is provided."
            )
            secondary_batch_setup = config.secondary_source_config.create_batch_setup(
                request=request,
                data=config.secondary_data,
                extra_data={},
                context=batch_setup.context,
            )
            _cached_secondary_test_configs[batch_setup.id] = secondary_batch_setup
            secondary_batch_setup.setup()

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
    yield _batch_setup_for_datasource.make_asset()


@dataclass(frozen=True)
class SourceToTargetBatch:
    target_batch: Batch
    source_data_source_name: str


@pytest.fixture
def source_to_target_batch(
    _batch_setup_for_datasource: BatchTestSetup,
    _cached_secondary_test_configs: dict[UUID, BatchTestSetup],
) -> Generator[SourceToTargetBatch, None, None]:
    secondary_batch_setup = _cached_secondary_test_configs[_batch_setup_for_datasource.id]
    secondary_asset = secondary_batch_setup.make_asset()
    yield SourceToTargetBatch(
        target_batch=_batch_setup_for_datasource.make_batch(),
        source_data_source_name=secondary_asset.datasource.name,
    )


@pytest.fixture
def extra_table_names_for_datasource(
    _batch_setup_for_datasource: BatchTestSetup,
) -> Generator[Mapping[str, str], None, None]:
    """Fixture that yields extra table names"""
    assert isinstance(_batch_setup_for_datasource, SQLBatchTestSetup)
    yield {key: t.name for key, t in _batch_setup_for_datasource.extra_table_data.items()}


@pytest.fixture(scope="session")
def _source_to_target_map() -> Mapping[UUID, UUID]:
    """Get a source BatchTestSetup ID by its target BatchTestSetup ID."""
    return {}


def multi_source_batch_setup(
    primary_data_sources: list[DataSourceTestConfig],
    primary_data: pd.DataFrame,
    secondary_data_sources: list[DataSourceTestConfig],
    secondary_data: pd.DataFrame,
) -> Callable[[_F], _F]:
    def decorator(func: _F) -> _F:
        pytest_params = []
        for primary_config in primary_data_sources:
            for secondary_config in secondary_data_sources:
                if primary_config.pytest_mark == secondary_config.pytest_mark:
                    marks = [primary_config.pytest_mark]
                else:
                    marks = [primary_config.pytest_mark, secondary_config.pytest_mark]
                pytest_params.append(
                    pytest.param(
                        TestConfig(
                            data_source_config=primary_config,
                            data=primary_data,
                            extra_data={},
                            secondary_source_config=secondary_config,
                            secondary_data=secondary_data,
                        ),
                        id=f"{primary_config.test_id}-{secondary_config.test_id}",
                        marks=marks,
                    )
                )
        parameterize_decorator = pytest.mark.parametrize(
            _batch_setup_for_datasource.__name__,
            pytest_params,
            indirect=True,
        )
        return parameterize_decorator(func)

    return decorator
