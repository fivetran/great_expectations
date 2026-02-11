import pandas as pd

import great_expectations.expectations as gxe
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import MSSQLDatasourceTestConfig

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
    @parameterize_batch_for_data_sources(
        data_source_configs=[MSSQLDatasourceTestConfig()],
        data=DATA_FRAME,
    )
    def test_schema(
        self,
        batch_for_datasource,
    ) -> None:
        expectation = gxe.ExpectTableRowCountToEqual(value=3)

        result = batch_for_datasource.validate(expectation)

        assert result.success
