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


ALL_SOURCE_TO_TARGET_SOURCES = [
    MultiSourceTestConfig(
        source=PostgreSQLDatasourceTestConfig(), target=PostgreSQLDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        source=PostgreSQLDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=SnowflakeDatasourceTestConfig(), target=SnowflakeDatasourceTestConfig()
    ),
    MultiSourceTestConfig(
        source=SnowflakeDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=DatabricksDatasourceTestConfig(),
        target=DatabricksDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=DatabricksDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=RedshiftDatasourceTestConfig(),
        target=RedshiftDatasourceTestConfig(),
    ),
    MultiSourceTestConfig(
        source=RedshiftDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    ),
]


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=DATA_FRAME,
    source_data=DATA_FRAME,
)
def test_source_to_target_example(multi_source_batch: MultiSourceBatch):
    # placeholder test to demo fixture
    target_data_source = multi_source_batch.target_batch.datasource
    context = target_data_source.data_context
    if context is None:
        raise ValueError("DataContext cannot be None")
    source_data_source = context.data_sources.get(multi_source_batch.source_data_source_name)
    assert target_data_source != source_data_source
