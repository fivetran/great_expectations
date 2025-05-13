from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

COL_NAME = "col_name"


DATA = pd.DataFrame({COL_NAME: ["aa", "ab", "ac", None]})

REGULAR_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
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
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["bc"]
                ),
                id="one_pattern",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["bc", "%de%"]
                ),
                id="multiple_patterns",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=REGULAR_DATA_SOURCES, data=DATA)
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePatternList,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["%a%"]
                ),
                id="one_pattern",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["%a%", "not_this"]
                ),
                id="multiple_patterns",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=REGULAR_DATA_SOURCES, data=DATA)
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePatternList,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success


class TestMSSQL:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["bc"]
                ),
                id="one_pattern",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["bc", "%de%"]
                ),
                id="multiple_patterns",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA
    )
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePatternList,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["%a[b]%"]
                ),
                id="one_pattern",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchLikePatternList(
                    column=COL_NAME, like_pattern_list=["%[a]%", "not_this"]
                ),
                id="multiple_patterns",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()], data=DATA
    )
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchLikePatternList,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success
