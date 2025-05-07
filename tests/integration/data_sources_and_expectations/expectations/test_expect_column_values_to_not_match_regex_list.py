from typing import Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.compatibility import pydantic
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MySQLDatasourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
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
    SnowflakeDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotMatchRegexList(column=COL_A, regex_list=["x.", "a.."])
    result = batch_for_datasource.validate(expectation)
    assert result.success


class TestNormalSql:
    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(column=COL_A, regex_list=["a[x-z]"]),
                id="non_matching",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(
                    column=COL_A,
                    regex_list=["x.", "a.."],
                ),
                id="multiple_non_matching",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(
                    column=COL_B, regex_list=["a."], mostly=0.6
                ),
                id="mostly",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
    def test_success(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchRegexList,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert result.success

    @pytest.mark.parametrize(
        "expectation",
        [
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(column=COL_A, regex_list=["^a[abc]$"]),
                id="all_matches",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(
                    column=COL_A,
                    regex_list=["a.", "x."],
                ),
                id="one_matching",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(
                    column=COL_A,
                    regex_list=["a.", "\\w+"],
                ),
                id="all_matching",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(
                    column=COL_B, regex_list=["a."], mostly=0.7
                ),
                id="mostly_threshold_not_met",
            ),
            pytest.param(
                gxe.ExpectColumnValuesToNotMatchRegexList(column=COL_A, regex_list=[""]),
                id="empty_regex",
            ),
        ],
    )
    @parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
    def test_failure(
        self,
        batch_for_datasource: Batch,
        expectation: gxe.ExpectColumnValuesToNotMatchRegexList,
    ) -> None:
        result = batch_for_datasource.validate(expectation)
        assert not result.success


@pytest.mark.unit
def test_invalid_config() -> None:
    with pytest.raises(pydantic.ValidationError):
        gxe.ExpectColumnValuesToNotMatchRegexList(column=COL_A, regex_list=[])
