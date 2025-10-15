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

    @parameterize_batch_for_data_sources(
        data_source_configs=[PostgreSQLDatasourceTestConfig()], data=DATA
    )
    def test_include_unexpected_rows_postgres(self, batch_for_datasource: Batch) -> None:
        """Test include_unexpected_rows for ExpectColumnValuesToNotMatchLikePatternList."""
        expectation = gxe.ExpectColumnValuesToNotMatchLikePatternList(
            column=COL_NAME, like_pattern_list=["%a%"]
        )
        result = batch_for_datasource.validate(
            expectation, result_format={"result_format": "BASIC", "include_unexpected_rows": True}
        )

        assert not result.success
        result_dict = result["result"]

        # Verify that unexpected_rows is present and contains the expected data
        assert "unexpected_rows" in result_dict
        assert result_dict["unexpected_rows"] is not None

        unexpected_rows_data = result_dict["unexpected_rows"]
        assert isinstance(unexpected_rows_data, list)

        # Should contain 3 rows where COL_NAME matches like_pattern_list ["%a%"]
        # ("aa", "ab", "ac" all contain 'a')
        assert len(unexpected_rows_data) == 3

        # Check that "aa", "ab", and "ac" appear in the unexpected rows data
        unexpected_rows_str = str(unexpected_rows_data)
        assert "aa" in unexpected_rows_str
        assert "ab" in unexpected_rows_str
        assert "ac" in unexpected_rows_str


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
