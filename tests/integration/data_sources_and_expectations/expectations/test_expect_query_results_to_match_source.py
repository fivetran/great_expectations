import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.expectations.metrics.util import MAX_RESULT_RECORDS
from tests.integration.conftest import (
    MultiSourceBatch,
    MultiSourceTestConfig,
    multi_source_batch_setup,
)
from tests.integration.data_sources_and_expectations.data_sources.test_source_to_target import (
    ALL_SOURCE_TO_TARGET_SOURCES,
)
from tests.integration.test_utils.data_source_config import SqliteDatasourceTestConfig

SQLITE_ONLY = [
    MultiSourceTestConfig(
        source=SqliteDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    )
]

SOURCE_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

TARGET_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [4, 5, 6]})

SOURCE_DATA_WITH_DUPS = pd.DataFrame({"a": [1, 1, 2, 3], "b": [4, 4, 5, 6]})

TARGET_DATA_WITH_DUPS = pd.DataFrame({"a": [1, 1, 2, 3], "b": [4, 4, 5, 6]})

MAX_LENGTH_TARGET_DATA = pd.DataFrame(
    {"a": [idx for idx in range(300)][100:], "b": [idx for idx in range(400)][200:]}
)

MAX_LENGTH_SOURCE_DATA = pd.DataFrame(
    {"a": [idx for idx in range(200)], "b": [idx for idx in range(300)][100:]}
)

TOO_BIG_DATA = pd.DataFrame(
    {"a": [idx for idx in range(400)], "b": [idx for idx in range(500)][100:]}
)


@pytest.mark.parametrize(
    "target_query,source_query",
    [
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
    ],
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


@pytest.mark.parametrize(
    "target_query,source_query",
    [
        pytest.param(
            "SELECT * FROM {batch}",
            "SELECT * FROM {source_table}",
            id="duplicate_values_across_rows",
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
    ],
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


@pytest.mark.parametrize(
    "mostly,success",
    [
        pytest.param(0.9, False, id="mostly_failure"),
        pytest.param(0.5, True, id="mostly_success"),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
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


@pytest.mark.parametrize(
    "target_query,source_query,unexpected_percent,unexpected_count",
    [
        pytest.param(
            "SELECT * FROM {batch} ORDER BY a LIMIT 100",  # 100 records
            "SELECT * FROM {source_table} WHERE a >= 100 ORDER BY a",  # 100 records
            0,
            0,
            id="only_match",
        ),
        pytest.param(
            "SELECT * FROM {batch}",  # 200 records (half match)
            "SELECT * FROM {source_table} WHERE a >= 100",  # 100 records
            50,
            100,
            id="match_and_unexpected",
        ),
        pytest.param(
            "SELECT * FROM {batch} ORDER BY a LIMIT 100",  # 100 records
            "SELECT * FROM {source_table}",  # 200 records (half match)
            50,
            100,
            id="match_and_missing",
        ),
        pytest.param(
            "SELECT * FROM {batch} ORDER BY a DESC LIMIT 100",  # 100 different records
            "SELECT * FROM {source_table} ORDER BY a LIMIT 100",  # 100 records
            100,
            100,
            id="missing_and_unexpected",
        ),
        pytest.param(
            "SELECT * FROM {batch}",  # 200 records (half match)
            "SELECT * FROM {source_table}",  # 200 records
            50,
            100,
            id="match_and_missing_and_unexpected",
        ),
        pytest.param(
            "SELECT * FROM {batch}",  # 200 records
            "SELECT * FROM {source_table} ORDER BY a LIMIT 100",  # 100 different records
            100,
            200,
            id="only_unexpected",
        ),
        pytest.param(
            "SELECT * FROM {batch} ORDER BY a DESC LIMIT 100",  # 100 records
            "SELECT * FROM {source_table} LIMIT 0",  # 0 records
            100,
            100,
            id="only_missing",
        ),
        pytest.param(
            "SELECT * FROM {batch} LIMIT 0",  # 0 records
            "SELECT * FROM {source_table} LIMIT 0",  # 0 records
            0,
            0,
            id="nothing_to_compare",
        ),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    target_data=MAX_LENGTH_TARGET_DATA,
    source_data=MAX_LENGTH_SOURCE_DATA,
)
def test_expect_query_results_to_match_source_unexpected_percent(
    multi_source_batch: MultiSourceBatch,
    target_query: str,
    source_query: str,
    unexpected_percent: float,
    unexpected_count: int,
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
    assert result.result["unexpected_percent"] == unexpected_percent
    assert result.result["unexpected_count"] == unexpected_count


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    target_data=TOO_BIG_DATA,
    source_data=TOO_BIG_DATA,
)
def test_expect_query_results_to_match_source_limit(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name} ORDER BY a",
        )
    )
    assert result.success
    assert result.result["unexpected_count"] == 0

    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name} ORDER BY a DESC",
        )
    )
    assert not result.success
    assert result.result["unexpected_count"] == len(TOO_BIG_DATA) - MAX_RESULT_RECORDS


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
