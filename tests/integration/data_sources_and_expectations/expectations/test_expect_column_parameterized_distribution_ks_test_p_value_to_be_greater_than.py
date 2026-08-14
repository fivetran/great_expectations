import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
)

# This Expectation relies on a Pandas-only metric (scipy.stats.kstest), so it is exercised against
# the Pandas data source only.

COL_NAME = "my_col"

DATA = pd.DataFrame({COL_NAME: [round(0.1 * i, 1) for i in range(1, 10)]})


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(
        column=COL_NAME,
        distribution="uniform",
        params=[0, 1],
        p_value=0.05,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "observed_value": pytest.approx(0.9998742840646804),
        "details": {
            "observed_ks_result": {
                "statistic": pytest.approx(0.1),
                "pvalue": pytest.approx(0.9998742840646804),
            }
        },
    }


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(
        column=COL_NAME,
        distribution="norm",
        params={"mean": 5, "std_dev": 1},
        p_value=0.05,
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(0.05, True, id="success"),
        pytest.param(0.9999, False, id="failure"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_p_value_(
    batch_for_datasource: Batch, suite_param_value: float, expected_result: bool
) -> None:
    suite_param_key = "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than"
    expectation = gxe.ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(
        column=COL_NAME,
        distribution="uniform",
        params=[0, 1],
        p_value={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result
