import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
)

DATA = pd.DataFrame({"foo": [1, 2, 4], "bar": [1, 1, 1]})


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=DATA)
def test_success_complete_results(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnPairValuesToBeInSet(
        column_A="foo", column_B="bar", value_pairs_set=[(2, 1), (1, 1)], mostly=0.5
    )

    # act
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.BASIC)

    # assert
    assert result.success

    result_dict = result.to_json_dict()["result"]
    assert type(result_dict) is dict

    # these are not deterministic
    result_dict.pop("unexpected_index_query", None)
    result_dict.pop("unexpected_index_list", None)

    assert result_dict == {
        "element_count": 3,
        "missing_count": 0,
        "missing_percent": 0.0,
        "partial_unexpected_list": [
            [4, 1],
        ],
        "unexpected_count": 1,
        "unexpected_percent": 33.33333333333333,
        "unexpected_percent_nonmissing": 33.33333333333333,
        "unexpected_percent_total": 33.33333333333333,
    }
