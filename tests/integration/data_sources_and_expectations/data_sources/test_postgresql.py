from datetime import datetime, timezone

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from great_expectations.compatibility.sqlalchemy import sqltypes
from tests.integration.test_utils.data_source_config import PostgreSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.postgres import PostgresBatchTestSetup

pytestmark = pytest.mark.postgresql


class TestPostgresqlDataTypes:
    """This set of tests ensures that we can run expectations against every data
    type supported by Postgres.

    https://www.postgresql.org/docs/current/datatype.html
    """

    BOOL_COL_NAME = "my_bool"
    DATE_COL_NAME = "my_date"
    NUMERIC_COL_NAME = "my_number"
    STRING_COL_NAME = "my_string"

    DATA_FRAME = pd.DataFrame(
        {
            BOOL_COL_NAME: [True, False, True, False],
            DATE_COL_NAME: [
                datetime(2021, 1, 1, tzinfo=timezone.utc).date(),
                datetime(2021, 1, 2, tzinfo=timezone.utc).date(),
                datetime(2021, 1, 3, tzinfo=timezone.utc).date(),
                datetime(2021, 1, 4, tzinfo=timezone.utc).date(),
            ],
            NUMERIC_COL_NAME: [1, 2, 3, 4],
            STRING_COL_NAME: ["a", "b", "c", "d"],
        }
    )

    def test_boolean(self):
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(
                column_types={self.BOOL_COL_NAME: sqltypes.BOOLEAN}
            ),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column=self.BOOL_COL_NAME,
                    value_set=[True, False],
                )
            )
        assert result.success

    @pytest.mark.parametrize(
        "col_type",
        [
            sqltypes.TIMESTAMP(timezone=False),
            sqltypes.TIMESTAMP(timezone=True),
            sqltypes.DATE,
        ],
    )
    def test_dates(self, col_type):
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(column_types={self.DATE_COL_NAME: col_type}),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeBetween(
                    column=self.DATE_COL_NAME,
                    min_value=datetime(2020, 1, 1, tzinfo=timezone.utc).date(),
                    max_value=datetime(2022, 1, 1, tzinfo=timezone.utc).date(),
                )
            )
        assert result.success

    @pytest.mark.parametrize(
        "col_type",
        [
            sqltypes.SMALLINT,
            sqltypes.INT,
            sqltypes.BIGINT,
            sqltypes.DECIMAL,
            sqltypes.FLOAT,
            sqltypes.NUMERIC,
            sqltypes.REAL,
        ],
    )
    def test_numbers(self, col_type):
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(column_types={self.NUMERIC_COL_NAME: col_type}),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column=self.NUMERIC_COL_NAME,
                    min_value=9,
                    max_value=11,
                )
            )
        assert result.success

    @pytest.mark.parametrize(
        "col_type",
        [
            sqltypes.CHAR,
            sqltypes.TEXT,
        ],
    )
    def test_strings(self, col_type):
        batch_setup = PostgresBatchTestSetup(
            config=PostgreSQLDatasourceTestConfig(column_types={self.STRING_COL_NAME: col_type}),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column=self.STRING_COL_NAME, value_set=["a", "b", "c", "d"]
                )
            )
        assert result.success
