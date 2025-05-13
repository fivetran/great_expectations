import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    JUST_PANDAS_DATA_SOURCES,
)

# TODO: Full coverage to replace test_expect_column_kl_divergence_to_be_less_than.py

COL_NAME = "my_col"

DATA = pd.DataFrame(
    {
        COL_NAME: ["A"] * 5 + ["B"] * 3 + ["C"] * 2,
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_success(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnKLDivergenceToBeLessThan(
        column=COL_NAME,
        partition_object={"weights": [0.5, 0.3, 0.2], "values": ["A", "B", "C"]},
        threshold=0.01,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "observed_value": 0.0,
        "details": {
            "observed_partition": {"values": ["A", "B", "C"], "weights": [0.5, 0.3, 0.2]},
            "expected_partition": {"values": ["A", "B", "C"], "weights": [0.5, 0.3, 0.2]},
        },
    }


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnKLDivergenceToBeLessThan(
        column=COL_NAME,
        partition_object={
            "weights": [0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
            "values": ["A", "B", "C"],
        },
        threshold=0.01,
    )
    result = batch_for_datasource.validate(expectation)
    assert not result.success
