from typing import Sequence, cast
from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

BASIC_PATTERNS = "basic_patterns"
PREFIXED_PATTERNS = "prefixed_patterns"
SUFFIXED_PATTERNS = "suffixed_patterns"
COMMON_PATTERN = "suffixed_patterns"
WITH_NULL = "with_null"

DATA = pd.DataFrame(
    {
        BASIC_PATTERNS: ["abc", "def", "ghi"],
        PREFIXED_PATTERNS: ["foo_abc", "foo_def", "foo_ghi"],
        SUFFIXED_PATTERNS: ["abc_foo", "def_foo", "ghi_foo"],
        COMMON_PATTERN: ["abc_foo", "def_foo", "ghi_foo"],
        WITH_NULL: ["ba", None, "ab"],
    }
)

SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_basic_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToMatchLikePatternList(
        column=PREFIXED_PATTERNS,
        like_pattern_list=["foo%"],
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_basic_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToMatchLikePatternList(
        column=BASIC_PATTERNS,
        like_pattern_list=["xyz%"],
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig(), RedshiftDatasourceTestConfig()],
    data=DATA,
)
def test_complete_results_failure(batch_for_datasource: Batch) -> None:
    ABOUT_TWO_THIRDS = pytest.approx(2 / 3 * 100)
    expectation = gxe.ExpectColumnValuesToMatchLikePatternList(
        column=BASIC_PATTERNS,
        like_pattern_list=["%b%"],
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    json_dict = result.to_json_dict()
    result_dict = json_dict.get("result")

    assert isinstance(result_dict, dict)
    assert not result.success
    assert "IS NOT NULL AND basic_patterns NOT LIKE '%b%'" in cast(
        str, result_dict.get("unexpected_index_query")
    )
    assert result.to_json_dict().get("result") == {
        "element_count": 3,
        "unexpected_count": 2,
        "unexpected_percent": ABOUT_TWO_THIRDS,
        "partial_unexpected_list": ["def", "ghi"],
        "missing_count": 0,
        "missing_percent": 0.0,
        "unexpected_percent_total": ABOUT_TWO_THIRDS,
        "unexpected_percent_nonmissing": ABOUT_TWO_THIRDS,
        "partial_unexpected_counts": [
            {"value": "def", "count": 1},
            {"value": "ghi", "count": 1},
        ],
        "unexpected_list": ["def", "ghi"],
        "unexpected_index_query": ANY,
    }


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=COMMON_PATTERN, like_pattern_list=["%foo"], match_on="any"
            ),
            id="match_all",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS, like_pattern_list=["abc", "def", "ghi"], match_on="any"
            ),
            id="multiple_patterns",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS, like_pattern_list=["a%", "d%", "g%"], match_on="any"
            ),
            id="multiple_patterns_with_prefix",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=COMMON_PATTERN, like_pattern_list=["%foo"], match_on="any"
            ),
            id="match_all",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=PREFIXED_PATTERNS, like_pattern_list=["foo%"], match_on="any"
            ),
            id="prefixed_pattern",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=SUFFIXED_PATTERNS, like_pattern_list=["%foo"], match_on="any"
            ),
            id="suffixed_pattern",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=PREFIXED_PATTERNS,
                like_pattern_list=["foo%", "bar%"],
                match_on="any",
            ),
            id="matches_one_of",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS, like_pattern_list=["%b%"], match_on="any", mostly=0.3
            ),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig(), RedshiftDatasourceTestConfig()],
    data=DATA,
)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToMatchLikePatternList,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS,
                like_pattern_list=["%xyz%"],
                match_on="any",
            ),
            id="no_matches",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS,
                like_pattern_list=["%b%"],
                match_on="any",
                mostly=0.4,
            ),
            id="mostly_threshold_not_met",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=PREFIXED_PATTERNS,
                like_pattern_list=["foo%", "bar%"],
                match_on="all",
            ),
            id="does_not_match_all",
        ),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig(), RedshiftDatasourceTestConfig()],
    data=DATA,
)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToMatchLikePatternList,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS,
                like_pattern_list=["[adg]%"],
                match_on="any",
            ),
        ),
        pytest.param(
            gxe.ExpectColumnValuesToMatchLikePatternList(
                column=BASIC_PATTERNS,
                like_pattern_list=["[a]%", "[d]%", "[g]%"],
                match_on="any",
            ),
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA)
def test_msql_fancy_syntax(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToMatchLikePatternList,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success
