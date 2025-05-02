import pandas as pd

from tests.integration.conftest import (
    MultiSourceBatch,
    multi_source_batch_setup,
)
from tests.integration.data_sources_and_expectations.data_sources.test_source_to_target import (
    ALL_SOURCE_TO_TARGET_SOURCES,
)

DATA_FRAME = pd.DataFrame({"a": [1, 2, 3]})


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=DATA_FRAME,
    source_data=DATA_FRAME,
)
def test_expect_query_results_to_match_source_success(multi_source_batch: MultiSourceBatch):
    target_data_source = multi_source_batch.target_batch.datasource
    context = target_data_source.data_context
    if context is None:
        raise ValueError("DataContext cannot be None")
    source_data_source = context.data_sources.get(multi_source_batch.source_data_source_name)
    assert target_data_source != source_data_source
