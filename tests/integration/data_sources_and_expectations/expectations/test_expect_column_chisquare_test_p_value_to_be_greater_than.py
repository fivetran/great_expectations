import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
)

# This Expectation computes a Chi-square goodness-of-fit p-value with scipy on the column's value
# counts, so it is exercised against the Pandas data source only.

COL_NAME = "my_col"

DATA = pd.DataFrame({COL_NAME: ["A"] * 5 + ["B"] * 3 + ["C"] * 2})


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnChisquareTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object={"values": ["A", "B", "C"], "weights": [0.5, 0.3, 0.2]},
        p=0.05,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "observed_value": 1.0,
        "details": {
            "observed_partition": {"values": ["A", "B", "C"], "weights": [0.5, 0.3, 0.2]},
            "expected_partition": {"values": ["A", "B", "C"], "weights": [0.5, 0.3, 0.2]},
        },
    }


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnChisquareTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object={"values": ["A", "B", "C"], "weights": [0.1, 0.1, 0.8]},
        p=0.05,
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@pytest.mark.parametrize(
    "suite_param_value,expected_result",
    [
        pytest.param({"values": ["A", "B", "C"], "weights": [0.5, 0.3, 0.2]}, True, id="success"),
        pytest.param({"values": ["A", "B", "C"], "weights": [0.1, 0.1, 0.8]}, False, id="failure"),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success_with_suite_param_partition_object_(
    batch_for_datasource: Batch, suite_param_value: dict, expected_result: bool
) -> None:
    suite_param_key = "expect_column_chisquare_test_p_value_to_be_greater_than"
    expectation = gxe.ExpectColumnChisquareTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object={"$PARAMETER": suite_param_key},
        p=0.05,
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: suite_param_value}
    )
    assert result.success == expected_result


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_tail_weight_holdout_covers_unexpected_values(batch_for_datasource: Batch) -> None:
    # The partition only lists A and B, but the data also contains C. tail_weight_holdout reserves
    # probability mass for such unexpected values so the test does not treat C as impossible.
    expectation = gxe.ExpectColumnChisquareTestPValueToBeGreaterThan(
        column=COL_NAME,
        partition_object={"values": ["A", "B"], "weights": [0.6, 0.4]},
        p=0.05,
        tail_weight_holdout=0.25,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.result is not None
    details = result.result["details"]
    # C is folded into the expected partition via the holdout rather than being dropped.
    assert "C" in details["expected_partition"]["values"]
