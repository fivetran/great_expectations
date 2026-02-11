import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from tests.integration.test_utils.data_source_config import MSSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.mssql import MSSQLBatchTestSetup

DATA_FRAME = pd.DataFrame(
    {
        "words": [
            "apple",
            "banana",
            "cherry",
        ],
    }
)


class TestMSSQLSchema:
    @pytest.mark.parametrize("schema_name", ["regular_ol_lowercase", "FANCY_UPPER_CASE", None])
    def test_schema(
        self,
        schema_name: str | None,
    ) -> None:
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(),
            data=DATA_FRAME,
            schema_name=schema_name,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            expectation = gxe.ExpectTableRowCountToEqual(value=3)

            result = batch.validate(expectation)

            assert result.success
