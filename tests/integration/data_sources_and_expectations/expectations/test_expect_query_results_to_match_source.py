import pandas as pd
import pytest

import great_expectations.expectations as gxe
from tests.integration.conftest import (
    MultiSourceBatch,
    multi_source_batch_setup,
)
from tests.integration.data_sources_and_expectations.data_sources.test_source_to_target import (
    ALL_SOURCE_TO_TARGET_SOURCES,
)

SOURCE_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

TARGET_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [4, 5, 6]})

SOURCE_DATA_WITH_DUPS = pd.DataFrame({"a": [1, 1, 2, 3], "b": [4, 4, 5, 6]})

TARGET_DATA_WITH_DUPS = pd.DataFrame({"a": [1, 1, 2, 3], "b": [4, 4, 5, 6]})


SUCCESS_TEST_CASES = [
    pytest.param(
        "SELECT a, b FROM {batch} ORDER BY a, b",
        "SELECT a, b FROM {source_table} ORDER BY a, b",
        id="multiple_columns_multiple_rows",
    ),
    pytest.param(
        "SELECT a FROM {batch} ORDER BY a",
        "SELECT a FROM {source_table} ORDER BY a",
        id="one_column_multiple_rows",
    ),
    pytest.param(
        "SELECT a, b FROM {batch} ORDER BY b LIMIT 1",
        "SELECT a, b FROM {source_table} ORDER BY b LIMIT 1",
        id="multiple_columns_one_row",
    ),
    pytest.param(
        "SELECT a, b FROM {batch} LIMIT 0",
        "SELECT a, b FROM {source_table} LIMIT 0",
        id="both_results_are_empty",
    ),
    pytest.param(
        "SELECT a, c FROM {batch} ORDER BY c",
        "SELECT a, b FROM {source_table} ORDER BY b",
        id="column_names_different_values_the_same",
    ),
]


@pytest.mark.parametrize(
    "target_query,source_query",
    SUCCESS_TEST_CASES,
)
@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_success(
    multi_source_batch: MultiSourceBatch, target_query: str, source_query: str
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=source_query.replace(
                "{source_table}", multi_source_batch.source_table_name
            ),
        )
    )
    assert result.success


FAILURE_TEST_CASES = [
    pytest.param(
        "SELECT * FROM {batch}", "SELECT * FROM {source_table}", id="duplicate_values_across_rows"
    ),
    pytest.param(
        "SELECT a, b FROM {batch} LIMIT 2",
        "SELECT a, b FROM {source_table}",
        id="row_count_mismatch",
    ),
    pytest.param(
        "SELECT a FROM {batch} ORDER BY a",
        "SELECT b FROM {source_table} ORDER BY a",
        id="column_value_mismatch",
    ),
    pytest.param(
        "SELECT * FROM {batch} LIMIT 0",
        "SELECT * FROM {source_table} ORDER BY a",
        id="one_result_is_empty",
    ),
]


@pytest.mark.parametrize(
    "target_query,source_query",
    FAILURE_TEST_CASES,
)
@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_failure(
    multi_source_batch: MultiSourceBatch, target_query: str, source_query: str
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=source_query.replace(
                "{source_table}", multi_source_batch.source_table_name
            ),
        )
    )
    assert not result.success
    assert not result.exception_info["raised_exception"]


MOSTLY_TEST_CASES = [
    pytest.param(0.9, False, id="mostly_failure"),
    pytest.param(0.5, True, id="mostly_success"),
]


@pytest.mark.parametrize(
    "mostly,success",
    MOSTLY_TEST_CASES,
)
@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_mostly(
    multi_source_batch: MultiSourceBatch, mostly: float, success: bool
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT a, b FROM {batch} LIMIT 2",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT a, b FROM {multi_source_batch.source_table_name}",
            mostly=mostly,
        )
    )
    assert result.success is success


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA_WITH_DUPS,
    source_data=SOURCE_DATA_WITH_DUPS,
)
def test_expect_query_results_to_match_source_dups_success(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name} ORDER BY a",
        )
    )
    assert result.success
    assert result.result["unexpected_count"] == 0
    assert result.result["unexpected_percent"] == 0.0


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA_WITH_DUPS,
    source_data=SOURCE_DATA_WITH_DUPS,
)
def test_expect_query_results_to_match_source_dups_failure(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a DESC LIMIT 3",  # exclude one dup
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name}",
        )
    )
    assert not result.success
    assert not result.exception_info["raised_exception"]
    assert result.result["unexpected_count"] == 0
    assert result.result["unexpected_percent"] == 25.0


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_error(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT b FROM {batch}",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT invalid_column FROM {multi_source_batch.source_table_name}",
        )
    )
    assert not result.success
    assert list(result.exception_info.values())[0]["raised_exception"]
