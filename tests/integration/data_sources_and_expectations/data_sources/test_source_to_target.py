import pandas as pd

from tests.integration.conftest import MultiSourceBatch, multi_source_batch_setup
from tests.integration.test_utils.data_source_config import (
    PostgreSQLDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

DATA_FRAME = pd.DataFrame({"a": [1, 2, 3]})


ALL_SOURCE_TO_TARGET_SOURCES = [
    PostgreSQLDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@multi_source_batch_setup(
    primary_data_sources=ALL_SOURCE_TO_TARGET_SOURCES,
    primary_data=DATA_FRAME,
    secondary_data_sources=ALL_SOURCE_TO_TARGET_SOURCES,
    secondary_data=DATA_FRAME,
)
def test_source_to_target_example(multi_source_batch: MultiSourceBatch):
    # placeholder test to demo fixture
    target_data_source = multi_source_batch.target_batch.datasource
    context = target_data_source.data_context
    if context is None:
        raise ValueError("DataContext cannot be None")
    source_data_source = context.data_sources.get(multi_source_batch.source_data_source_name)
    assert target_data_source != source_data_source
