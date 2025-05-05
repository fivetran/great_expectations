import pandas as pd

import great_expectations.expectations as gxe
from tests.integration.conftest import (
    MultiSourceBatch,
    multi_source_batch_setup,
)
from tests.integration.data_sources_and_expectations.data_sources.test_source_to_target import (
    ALL_SOURCE_TO_TARGET_SOURCES,
)

SOURCE_DATA = pd.DataFrame({"a": [1, 2, 3]})

TARGET_DATA = pd.DataFrame({"a": [1, 2, 3]})


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_success(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch}",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name}",
        )
    )
    assert result.success
