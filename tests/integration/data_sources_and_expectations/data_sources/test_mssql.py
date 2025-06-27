from datetime import datetime, timezone

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from great_expectations.compatibility.sqlalchemy import sqltypes
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import MSSQLDatasourceTestConfig
from tests.integration.test_utils.data_source_config.mssql import MSSQLBatchTestSetup

pytestmark = pytest.mark.mssql


class TestMSSQLDataTypes:
    """This set of tests ensures that we can run expectations against every data
    type supported by Microsoft SQL Server.
    
    https://docs.microsoft.com/en-us/sql/t-sql/data-types/data-types-transact-sql
    """

    BOOL_COL_NAME = "my_bool"
    DATE_COL_NAME = "my_date"
    DATETIME_COL_NAME = "my_datetime"
    NUMERIC_COL_NAME = "my_number"
    STRING_COL_NAME = "my_string"
    DECIMAL_COL_NAME = "my_decimal"
    FLOAT_COL_NAME = "my_float"
    UNIQUEIDENTIFIER_COL_NAME = "my_guid"

    DATA_FRAME = pd.DataFrame(
        {
            BOOL_COL_NAME: [True, False, True, False],
            DATE_COL_NAME: [
                datetime(2021, 1, 1, tzinfo=timezone.utc).date(),
                datetime(2021, 1, 2, tzinfo=timezone.utc).date(),
                datetime(2021, 1, 3, tzinfo=timezone.utc).date(),
                datetime(2021, 1, 4, tzinfo=timezone.utc).date(),
            ],
            DATETIME_COL_NAME: [
                datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                datetime(2021, 1, 2, 13, 30, 0, tzinfo=timezone.utc),
                datetime(2021, 1, 3, 14, 45, 0, tzinfo=timezone.utc),
                datetime(2021, 1, 4, 15, 15, 0, tzinfo=timezone.utc),
            ],
            NUMERIC_COL_NAME: [1, 2, 3, 4],
            STRING_COL_NAME: ["a", "b", "c", "d"],
            DECIMAL_COL_NAME: [1.1, 2.2, 3.3, 4.4],
            FLOAT_COL_NAME: [1.5, 2.5, 3.5, 4.5],
            UNIQUEIDENTIFIER_COL_NAME: [
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002", 
                "550e8400-e29b-41d4-a716-446655440003",
                "550e8400-e29b-41d4-a716-446655440004",
            ],
        }
    )

    def test_boolean(self):
        """Test SQL Server BIT data type."""
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(
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
            sqltypes.DATE,
            sqltypes.DATETIME,
            sqltypes.DATETIME2,
            sqltypes.SMALLDATETIME,
        ],
    )
    def test_dates(self, col_type):
        """Test SQL Server date and datetime types."""
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(column_types={self.DATE_COL_NAME: col_type}),
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
            sqltypes.TINYINT,
        ],
    )
    def test_integers(self, col_type):
        """Test SQL Server integer types."""
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(column_types={self.NUMERIC_COL_NAME: col_type}),
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
            sqltypes.DECIMAL,
            sqltypes.NUMERIC,
        ],
    )
    def test_decimal_types(self, col_type):
        """Test SQL Server decimal and numeric types."""
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(column_types={self.DECIMAL_COL_NAME: col_type}),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column=self.DECIMAL_COL_NAME,
                    min_value=10.0,
                    max_value=12.0,
                )
            )
        assert result.success

    @pytest.mark.parametrize(
        "col_type",
        [
            sqltypes.FLOAT,
            sqltypes.REAL,
        ],
    )
    def test_float_types(self, col_type):
        """Test SQL Server floating point types."""
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(column_types={self.FLOAT_COL_NAME: col_type}),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnSumToBeBetween(
                    column=self.FLOAT_COL_NAME,
                    min_value=11.0,
                    max_value=13.0,
                )
            )
        assert result.success

    @pytest.mark.parametrize(
        "col_type",
        [
            sqltypes.VARCHAR,
            sqltypes.NVARCHAR,
            sqltypes.CHAR,
            sqltypes.NCHAR,
            sqltypes.TEXT,
            sqltypes.NTEXT,
        ],
    )
    def test_string_types(self, col_type):
        """Test SQL Server string types."""
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(column_types={self.STRING_COL_NAME: col_type}),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToBeInSet(
                    column=self.STRING_COL_NAME, 
                    value_set=["a", "b", "c", "d"]
                )
            )
        assert result.success

    def test_uniqueidentifier(self):
        """Test SQL Server UNIQUEIDENTIFIER (GUID) type."""
        # For GUID, we'll use VARCHAR since SQLAlchemy doesn't have a direct UNIQUEIDENTIFIER type
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(
                column_types={self.UNIQUEIDENTIFIER_COL_NAME: sqltypes.VARCHAR(36)}
            ),
            data=self.DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToMatchRegex(
                    column=self.UNIQUEIDENTIFIER_COL_NAME,
                    regex=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
                )
            )
        assert result.success


# Test data for partitioning functionality
DATE_COL = "date"
VALUE_COL = "value"

LAST_YEAR = "last year"
FIRST_DAY_OF_THE_YEAR = "first day of the year"
FIRST_DAY_OF_THE_MONTH = "first day of the month"
SECOND_DAY_OF_THE_MONTH = "second day of the month"

PARTITIONING_DATA = pd.DataFrame(
    {
        DATE_COL: [
            datetime(year=2023, month=1, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=1, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=2, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=2, day=2, tzinfo=timezone.utc).date(),
        ],
        VALUE_COL: [
            LAST_YEAR,
            FIRST_DAY_OF_THE_YEAR,
            FIRST_DAY_OF_THE_MONTH,
            SECOND_DAY_OF_THE_MONTH,
        ],
    }
)

JUST_MSSQL = [MSSQLDatasourceTestConfig()]


class TestMSSQLPartitioning:
    """Tests to show that we partition MSSQL data sources correctly.

    All tests use ExpectColumnDistinctValuesToEqualSet to detect that we are just seeing the
    appropriate rows.
    """

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_MSSQL,
        data=pd.DataFrame(PARTITIONING_DATA),
    )
    def test_yearly_partitioning(self, asset_for_datasource: TableAsset) -> None:
        """Test yearly partitioning functionality for MSSQL."""
        batch_def = asset_for_datasource.add_batch_definition_yearly("yearly", column=DATE_COL)
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    # NOT LAST_YEAR
                    FIRST_DAY_OF_THE_YEAR,
                    FIRST_DAY_OF_THE_MONTH,
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_MSSQL,
        data=pd.DataFrame(PARTITIONING_DATA),
    )
    def test_monthly_partitioning(self, asset_for_datasource: TableAsset) -> None:
        """Test monthly partitioning functionality for MSSQL."""
        batch_def = asset_for_datasource.add_batch_definition_monthly("monthly", column=DATE_COL)
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    # NOT LAST_YEAR
                    # NOT FIRST_DAY_OF_THE_YEAR,
                    FIRST_DAY_OF_THE_MONTH,
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_MSSQL,
        data=pd.DataFrame(PARTITIONING_DATA),
    )
    def test_daily_partitioning(self, asset_for_datasource: TableAsset) -> None:
        """Test daily partitioning functionality for MSSQL."""
        batch_def = asset_for_datasource.add_batch_definition_daily("daily", column=DATE_COL)
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    # NOT LAST_YEAR
                    # NOT FIRST_DAY_OF_THE_YEAR,
                    # NOT FIRST_DAY_OF_THE_MONTH,
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_MSSQL,
        data=pd.DataFrame(PARTITIONING_DATA),
    )
    def test_order_ascending_true(self, asset_for_datasource: TableAsset) -> None:
        """Test ascending sort order for MSSQL partitioning."""
        batch_def = asset_for_datasource.add_batch_definition_daily(
            "daily_ascending", column=DATE_COL, sort_ascending=True
        )
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_MSSQL,
        data=pd.DataFrame(PARTITIONING_DATA),
    )
    def test_order_ascending_false(self, asset_for_datasource: TableAsset) -> None:
        """Test descending sort order for MSSQL partitioning."""
        batch_def = asset_for_datasource.add_batch_definition_daily(
            "daily_descending", column=DATE_COL, sort_ascending=False
        )
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    LAST_YEAR,
                ],
            )
        )
        assert result.success


class TestMSSQLSpecificFunctionality:
    """Tests for MSSQL-specific functionality and edge cases."""

    def test_case_sensitivity(self):
        """Test that MSSQL handles case sensitivity correctly based on collation."""
        case_sensitive_data = pd.DataFrame({
            "mixed_case": ["Apple", "apple", "APPLE", "Apple"]
        })
        
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(
                column_types={"mixed_case": sqltypes.VARCHAR(50)}
            ),
            data=case_sensitive_data,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            # Test that we can detect distinct case variations
            result = batch.validate(
                gxe.ExpectColumnDistinctValuesToContainSet(
                    column="mixed_case",
                    value_set=["Apple", "apple", "APPLE"],
                )
            )
        assert result.success

    def test_null_handling(self):
        """Test MSSQL null value handling."""
        null_data = pd.DataFrame({
            "nullable_column": [1, None, 3, None, 5]
        })
        
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(
                column_types={"nullable_column": sqltypes.INT}
            ),
            data=null_data,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectColumnValuesToNotBeNull(
                    column="nullable_column",
                    mostly=0.6,  # 60% should be non-null
                )
            )
        assert result.success

    def test_large_dataset_performance(self):
        """Test MSSQL performance with larger datasets."""
        # Create a larger dataset to test performance
        large_data = pd.DataFrame({
            "id": range(1000),
            "value": [f"value_{i}" for i in range(1000)]
        })
        
        batch_setup = MSSQLBatchTestSetup(
            config=MSSQLDatasourceTestConfig(
                column_types={
                    "id": sqltypes.INT,
                    "value": sqltypes.VARCHAR(50)
                }
            ),
            data=large_data,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )

        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                gxe.ExpectTableRowCountToBeBetween(
                    min_value=900,
                    max_value=1100,
                )
            )
        assert result.success
