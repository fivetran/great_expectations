import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    JUST_PANDAS_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config.databricks import (
    DatabricksDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.postgres import PostgreSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.snowflake import SnowflakeDatasourceTestConfig

COL_A = "col_a"
COL_B = "col_b"
COL_C = "col_c"


DATA = pd.DataFrame(
    {
        COL_A: [1],
        COL_B: [2],
        COL_C: [3],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_golden_path(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectTableColumnsToMatchSet(column_set=[COL_A, COL_B, COL_C])
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(column_set=[COL_C, COL_A, COL_B]),
            id="order_doesnt_matter",
        ),
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(column_set=[COL_A, COL_B], exact_match=False),
            id="allows_subset_for_non_exact_match",
        ),
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(column_set=[COL_A, COL_B, COL_C], exact_match=False),
            id="allows_all_for_non_exact_match",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectTableColumnsToMatchSet
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(column_set=[COL_A, COL_B], exact_match=True),
            id="requires_all_columns_for_exact_match",
        ),
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(column_set=[COL_A]),
            id="defaults_to_exact_match",
        ),
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(
                column_set=[COL_A, COL_B, COL_C, "col_d"], exact_match=True
            ),
            id="does_not_allow_extras",
        ),
        pytest.param(
            gxe.ExpectTableColumnsToMatchSet(
                column_set=[COL_A, COL_B, COL_C, "col_d"], exact_match=False
            ),
            id="does_not_allow_extrasfor_non_exact_match",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectTableColumnsToMatchSet
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(False, True, id="success"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_exact_match_(
    batch_for_datasource: Batch, suite_param_value: str, expected_result: bool
) -> None:
    suite_param_key = "test_expect_table_columns_to_match_set"
    expectation = gxe.ExpectTableColumnsToMatchSet(
        column_set=[COL_A, COL_B],
        exact_match={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


# Case insenstivity tests
CASE_INSENSITIVE_DATA = pd.DataFrame(
    {
        "column_a": [1],
        "COLUMN_B": [2],
        "CoLuMn_C": [3],
    }
)


@parameterize_batch_for_data_sources(
    data_source_configs=[
        PostgreSQLDatasourceTestConfig(),
        DatabricksDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
    ],
    data=CASE_INSENSITIVE_DATA,
)
def test_case_insensitive_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectTableColumnsToMatchSet(column_set=["COLUMN_A", "column_b", "COLumN_c"])
    result = batch_for_datasource.validate(expectation)
    assert result.success
