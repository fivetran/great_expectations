import pandas as pd

import great_expectations.expectations as gxe
from tests.integration.conftest import (
    MultiSourceBatch,
    multi_source_batch_setup,
)
from tests.integration.data_sources_and_expectations.data_sources.test_source_to_target import (
    ALL_SOURCE_TO_TARGET_SOURCES,
)

# from tests.integration.conftest import (
#     MultiSourceBatch,
#     MultiSourceTestConfig,
#     multi_source_batch_setup,
# )
# from tests.integration.test_utils.data_source_config import (
#     PostgreSQLDatasourceTestConfig,
#     SqliteDatasourceTestConfig,
# )

# ALL_SOURCE_TO_TARGET_SOURCES = [
#     MultiSourceTestConfig(
#         source=PostgreSQLDatasourceTestConfig(), target=PostgreSQLDatasourceTestConfig()
#     ),
#     MultiSourceTestConfig(
#         source=PostgreSQLDatasourceTestConfig(),
#         target=SqliteDatasourceTestConfig(),
#     ),
# ]

SOURCE_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

TARGET_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_success_multiple_columns_multiple_rows(
    multi_source_batch: MultiSourceBatch,
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a, b",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name} ORDER BY a, b",
        )
    )
    assert result.success


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_success_one_column_multiple_rows(
    multi_source_batch: MultiSourceBatch,
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT a FROM {batch} ORDER BY a",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT a FROM {multi_source_batch.source_table_name} ORDER BY a",
        )
    )
    assert result.success


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_success_multiple_columns_one_row(
    multi_source_batch: MultiSourceBatch,
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT a, b FROM {batch} ORDER BY b LIMIT 1",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=(
                f"SELECT a, b FROM {multi_source_batch.source_table_name} ORDER BY b LIMIT 1"
            ),
        )
    )
    assert result.success


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_failure_multiple_columns_multiple_rows(
    multi_source_batch: MultiSourceBatch,
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} LIMIT 1",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name}",
        )
    )
    assert not result.success
    assert not result.exception_info


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_failure_multiple_columns_one_row(
    multi_source_batch: MultiSourceBatch,
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT a FROM {batch} ORDER BY a LIMIT 1",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT b FROM {multi_source_batch.source_table_name} ORDER BY b LIMIT 1",
        )
    )
    assert not result.success
    assert result.exception_info
