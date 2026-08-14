import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
)

# This Expectation relies on a Pandas-only metric (scipy.stats.kstest + numpy bootstrapping), so it
# is exercised against the Pandas data source only. Because it draws random bootstrap samples, the
# observed_value is not deterministic; tests assert on success rather than the exact statistic, and
# use a large bootstrap_sample_size so the pass/fail outcome is stable. bootstrap_samples is kept
# small so each validation stays well under the unit-test timeout while remaining stable.

COL_NAME = "my_col"

DATA = pd.DataFrame({COL_NAME: [i / 100 for i in range(100)]})  # evenly spread over [0, 1)

MATCHING_PARTITION = {"bins": [0.0, 0.25, 0.5, 0.75, 1.0], "weights": [0.25, 0.25, 0.25, 0.25]}
SKEWED_PARTITION = {"bins": [0.0, 0.25, 0.5, 0.75, 1.0], "weights": [0.85, 0.05, 0.05, 0.05]}


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnBootstrappedKsTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object=MATCHING_PARTITION,
        p=0.05,
        bootstrap_samples=100,
        bootstrap_sample_size=100,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    # The full metric details are surfaced so a user can inspect why the test passed or failed:
    # bootstrap settings plus the observed/expected partitions and CDFs.
    assert result.result is not None
    details = result.result["details"]
    assert set(details) >= {
        "bootstrap_samples",
        "bootstrap_sample_size",
        "observed_partition",
        "expected_partition",
        "observed_cdf",
        "expected_cdf",
    }


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnBootstrappedKsTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object=SKEWED_PARTITION,
        p=0.05,
        bootstrap_samples=100,
        bootstrap_sample_size=100,
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param(MATCHING_PARTITION, True, id="success"),
        pytest.param(SKEWED_PARTITION, False, id="failure"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_partition_object_(
    batch_for_datasource: Batch, suite_param_value: dict, expected_result: bool
) -> None:
    suite_param_key = "expect_column_bootstrapped_ks_test_p_value_to_be_greater_than"
    expectation = gxe.ExpectColumnBootstrappedKsTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object={"$PARAMETER": suite_param_key},
        p=0.05,
        bootstrap_samples=100,
        bootstrap_sample_size=100,
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result
