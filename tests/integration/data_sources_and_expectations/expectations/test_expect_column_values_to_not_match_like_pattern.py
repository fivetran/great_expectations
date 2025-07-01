from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

COL_A = "col_a"
COL_B = "col_b"


DATA = pd.DataFrame(
    {
        COL_A: ["aa", "ab", "ac", None],
        COL_B: ["aa", "bb", "cc", None],
    }
)

SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    DatabricksDatasourceTestConfig(),
    MSSQLDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


class TestNormalSql:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="z%"),
                id="no_matches",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="_______"),
                id="too_many_underscores",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(
                    column=COL_B, like_pattern="a%", mostly=0.6
                ),
                id="mostly",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a%"),
                id="all_matches",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="__"),
                id="underscores_match",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(
                    column=COL_B, like_pattern="a%", mostly=0.7
                ),
                id="mostly_threshold_not_met",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success


class TestMSSQL:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a[xzy]"),
                id="bracket_notation",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA
    )
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePattern(column=COL_A, like_pattern="a[abc]"),
                id="bracket_notation_fail",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA
    )
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePattern,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success
