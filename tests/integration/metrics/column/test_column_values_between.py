import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import SQL_DATA_SOURCES

STRING_COLUMN_NAME = "letter"

DATA_FRAME = pd.DataFrame(
    {
        STRING_COLUMN_NAME: ["a", "b", "c", "d"],
    },
)


class TestColumnValuesBetween:
    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA_FRAME,
    )
    def test_fails_when_run_against_invalid_column_type(self, batch_for_datasource: Batch) -> None:
        expect = gxe.ExpectColumnValuesToBeBetween(
            column=STRING_COLUMN_NAME,
            min_value=0,
            max_value=1,
        )
        result = batch_for_datasource.validate(expect=expect)
        exception_info = list(result.exception_info.values())
        assert len(exception_info) == 1
        assert (
            exception_info[0]["exception_message"]
            == "ColumnValuesBetween metrics cannot be computed on column of type VARCHAR."
        )
