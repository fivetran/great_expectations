import pandas as pd

from tests.integration.conftest import (
    MultiSourceBatch,
    MultiSourceTestConfig,
    multi_source_batch_setup,
)
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

DATA_FRAME = pd.DataFrame({"a": [1, 2, 3]})


ALL_COMPARISON_TO_BASE_SOURCES = [
    MultiSourceTestConfig(
        comparison=PostgreSQLDatasourceTestConfig(), base=PostgreSQLDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        comparison=PostgreSQLDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=SnowflakeDatasourceTestConfig(), base=SnowflakeDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        comparison=SnowflakeDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=DatabricksDatasourceTestConfig(),
        base=DatabricksDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=DatabricksDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=RedshiftDatasourceTestConfig(),
        base=RedshiftDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        comparison=RedshiftDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    ),
]


@multi_source_batch_setup(
    multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
    base_data=DATA_FRAME,
    comparison_data=DATA_FRAME,
)
def test_comparison_to_base_example(multi_source_batch: MultiSourceBatch):
    # placeholder test to demo fixture
    base_data_source = multi_source_batch.base_batch.datasource
    context = base_data_source.data_context
    if context is None:
        raise ValueError("DataContext cannot be None")
    comparison_data_source = context.data_sources.get(
        multi_source_batch.comparison_data_source_name
    )
    assert base_data_source != comparison_data_source
