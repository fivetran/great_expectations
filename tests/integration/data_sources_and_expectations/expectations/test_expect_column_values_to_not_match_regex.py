from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
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
    PandasDataFrameDatasourceTestConfig(),
    PandasFilesystemCsvDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


class TestNormalSql:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegex(column=COL_A, regex="a[x-z]"),
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegex(column=COL_A, regex="[a-z]{99}"),
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegex(column=COL_B, regex="a.", mostly=0.6),
                id="mostly",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchRegex,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegex(column=COL_A, regex="^a[abc]$"),
                id="all_matches",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegex(column=COL_B, regex="a.", mostly=0.7),
                id="mostly_threshold_not_met",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegex(column=COL_A, regex=""), id="empty_regex"
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchRegex,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success
