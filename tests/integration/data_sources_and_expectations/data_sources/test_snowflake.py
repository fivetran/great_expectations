from datetime import datetime, timezone

import pandas as pd
import pytest

from great_expectations import get_context
from great_expectations.compatibility.snowflake import SNOWFLAKE_TYPES
from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.expectations import (
    ExpectColumnDistinctValuesToContainSet,
    ExpectColumnSumToBeBetween,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeOfType,
)
from tests.integration.test_utils.data_source_config import SnowflakeDatasourceTestConfig
from tests.integration.test_utils.data_source_config.snowflake import SnowflakeBatchTestSetup


class TestSnowflakeDataTypes:
    """This set of tests ensures that we can run expectations against every data
    type supported by Snowflake.

    https://docs.snowflake.com/en/sql-reference/intro-summary-data-types
    """

    COLUMN = "col_a"

    @pytest.mark.snowflake
    def test_number(self):
        column_type = (
            SNOWFLAKE_TYPES.NUMBER
        )  # snowflake specific type equivalent to DECIMAL, NUMERIC
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3, 4]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnSumToBeBetween(
                    column=self.COLUMN,
                    min_value=9,
                    max_value=11,
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_int(self):
        column_type = sqltypes.INT  # equivalent to INTEGER, BIGINT, SMALLINT, TINYINT, BYTEINT
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3, 4]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnSumToBeBetween(
                    column=self.COLUMN,
                    min_value=9,
                    max_value=11,
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_float(self):
        column_type = sqltypes.FLOAT  # equivalent to FLOAT4, FLOAT8, DOUBLE, DOUBLE PRECISION, REAL
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3, 4]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnSumToBeBetween(
                    column=self.COLUMN,
                    min_value=9,
                    max_value=11,
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_varchar(self):
        column_type = sqltypes.VARCHAR  # equivalent to STRING, TEXT
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: ["a", "b", "c", "d"]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnDistinctValuesToContainSet(
                    column=self.COLUMN,
                    value_set=[
                        "a",
                        "b",
                    ],
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_char(self):
        column_type = sqltypes.CHAR  # length of 1, equivalent to CHARACTER
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: ["a", "b", "c", "d"]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnDistinctValuesToContainSet(
                    column=self.COLUMN,
                    value_set=[
                        "a",
                        "b",
                    ],
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_boolean(self):
        column_type = sqltypes.BOOLEAN
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [True, False, True, True]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(column=self.COLUMN, type_="BOOLEAN")
            )
        assert result.success

    @pytest.mark.snowflake
    def test_date(self):
        column_type = sqltypes.DATE
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).date(),
                        datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).date(),
                        datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).date(),
                    ]
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeBetween(
                    column=self.COLUMN,
                    min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).date(),
                    max_value=datetime(year=2024, month=1, day=1, tzinfo=timezone.utc).date(),
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_datetime(self):
        column_type = sqltypes.DATETIME
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        str(datetime(year=2021, month=1, day=31, tzinfo=timezone.utc)),
                        str(datetime(year=2022, month=1, day=31, tzinfo=timezone.utc)),
                        str(datetime(year=2023, month=1, day=31, tzinfo=timezone.utc)),
                    ]
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeBetween(
                    column=self.COLUMN,
                    min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc),
                    max_value=datetime(year=2024, month=1, day=1, tzinfo=timezone.utc),
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_timestamp_tz(self):
        column_type = SNOWFLAKE_TYPES.TIMESTAMP_TZ
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        str(datetime(year=2021, month=1, day=31, tzinfo=timezone.utc)),
                        str(datetime(year=2022, month=1, day=31, tzinfo=timezone.utc)),
                        str(datetime(year=2023, month=1, day=31, tzinfo=timezone.utc)),
                    ]
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeBetween(
                    column=self.COLUMN,
                    min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc),
                    max_value=datetime(year=2024, month=1, day=1, tzinfo=timezone.utc),
                )
            )
        assert result.success

    @pytest.mark.snowflake
    def test_timestamp_ntz(self):
        column_type = SNOWFLAKE_TYPES.TIMESTAMP_NTZ
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        str(datetime(year=2021, month=1, day=31, tzinfo=timezone.utc)),
                        str(datetime(year=2022, month=1, day=31, tzinfo=timezone.utc)),
                        str(datetime(year=2023, month=1, day=31, tzinfo=timezone.utc)),
                    ]
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeBetween(
                    column=self.COLUMN,
                    min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc),
                    max_value=datetime(year=2024, month=1, day=1, tzinfo=timezone.utc),
                )
            )
        assert result.success

    @pytest.mark.snowflake
    @pytest.mark.xfail(
        strict=True,
        reason="time is not an accepted min/max value parameter, and other date types "
        "(datetime, timestamp, etc) fail in the query.",
    )
    def test_time(self):
        column_type = sqltypes.TIME
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        datetime(year=2021, month=1, day=31, tzinfo=timezone.utc).time(),
                        datetime(year=2022, month=1, day=31, tzinfo=timezone.utc).time(),
                        datetime(year=2023, month=1, day=31, tzinfo=timezone.utc).time(),
                    ]
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeBetween(
                    column=self.COLUMN,
                    min_value=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc).time(),
                    max_value=datetime(year=2024, month=1, day=1, tzinfo=timezone.utc).time(),
                )
            )
        assert result.success
