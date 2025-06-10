import pandas as pd
import pytest

from great_expectations import get_context
from great_expectations.compatibility.aws import REDSHIFT_TYPES
from great_expectations.expectations import (
    ExpectColumnValuesToBeOfType,
)
from tests.integration.test_utils.data_source_config import RedshiftDatasourceTestConfig
from tests.integration.test_utils.data_source_config.redshift import RedshiftBatchTestSetup


class TestRedshiftDataTypes:
    """This set of tests ensures that we can run expectations against every data
    type supported by Redshift.

    """

    COLUMN = "col_a"

    @pytest.mark.redshift
    def test_geometry(self):
        column_type = REDSHIFT_TYPES.GEOMETRY
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        "0103000020E61000000100000005000000000000000000000000000000000000000000000000000000000000000000F03F000000000000F03F000000000000F03F000000000000F03F000000000000000000000000000000000000000000000000"
                    ]
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="GEOMETRY",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_super(self):
        column_type = REDSHIFT_TYPES.SUPER
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: ['{ "type": "Point", "coordinates": [1.0, 2.0] }']}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="SUPER",
                )
            )
        assert result.success
