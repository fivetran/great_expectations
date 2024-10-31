from dataclasses import dataclass
from typing import Callable, Generator, Mapping, Optional, Sequence, TypeVar

import pandas as pd
import pytest

from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config import DataSourceTestConfig

_F = TypeVar("_F", bound=Callable)


@dataclass(frozen=True)
class _TestConfig:
    data_source_config: DataSourceTestConfig
    data: pd.DataFrame
    extra_data: Mapping[str, pd.DataFrame]


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
        extra_data: Mapping of {asset_name: data} to load into other assets. Only relevant for SQL
                    mutli-table expectations.


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
                _TestConfig(
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
            batch_for_datasource.__name__,
            pytest_params,
            indirect=True,
        )
        return parameterize_decorator(func)

    return decorator


@pytest.fixture
def batch_for_datasource(request: pytest.FixtureRequest) -> Generator[Batch, None, None]:
    """Fixture that yields a batch for a specific data source type.
    This must be used in conjunction with `indirect=True` to defer execution
    """
    config = request.param
    assert isinstance(config, _TestConfig)

    batch_setup = config.data_source_config.create_batch_setup(
        request=request,
        data=config.data,
        extra_data=config.extra_data,
    )

    batch_setup.setup()
    yield batch_setup.make_batch()
    batch_setup.teardown()
