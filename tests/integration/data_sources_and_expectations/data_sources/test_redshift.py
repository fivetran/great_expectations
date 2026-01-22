import pandas as pd
import pytest
from typing_extensions import override

from great_expectations import get_context
from great_expectations.compatibility.aws import REDSHIFT_TYPES, redshiftdialect
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

    @pytest.mark.redshift
    def test_boolean(self):
        column_type = REDSHIFT_TYPES.BOOLEAN
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [True, False, True]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="BOOLEAN",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_smallint(self):
        column_type = REDSHIFT_TYPES.SMALLINT
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="SMALLINT",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_integer(self):
        column_type = REDSHIFT_TYPES.INTEGER
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="INTEGER",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_bigint(self):
        column_type = REDSHIFT_TYPES.BIGINT
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="BIGINT",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_real(self):
        column_type = redshiftdialect.REAL
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1.5, 2.5, 3.5]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="REAL",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_double_precision(self):
        column_type = REDSHIFT_TYPES.DOUBLE_PRECISION
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1.5, 2.5, 3.5]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="DOUBLE_PRECISION",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_decimal(self):
        column_type = REDSHIFT_TYPES.DECIMAL
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="DECIMAL",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_char(self):
        column_type = REDSHIFT_TYPES.CHAR
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: ["a", "b", "c"]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="CHAR",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_varchar(self):
        column_type = REDSHIFT_TYPES.VARCHAR
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: ["hello", "world", "test"]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="VARCHAR",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_date(self):
        column_type = REDSHIFT_TYPES.DATE
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame({self.COLUMN: ["2021-01-01", "2021-01-02", "2021-01-03"]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="DATE",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_timestamp(self):
        column_type = REDSHIFT_TYPES.TIMESTAMP
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        "2021-01-01 00:00:00",
                        "2021-01-02 00:00:00",
                        "2021-01-03 00:00:00",
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
                    type_="TIMESTAMP",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_timestamptz(self):
        column_type = redshiftdialect.TIMESTAMPTZ
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        "2021-01-01 00:00:00+00:00",
                        "2021-01-02 00:00:00+00:00",
                        "2021-01-03 00:00:00+00:00",
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
                    type_="TIMESTAMPTZ",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_timetz(self):
        column_type = redshiftdialect.TIMETZ
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types={self.COLUMN: column_type}),
            data=pd.DataFrame(
                {
                    self.COLUMN: [
                        "00:00:00+00:00",
                        "12:00:00+00:00",
                        "23:59:59+00:00",
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
                    type_="TIMETZ",
                )
            )
        assert result.success

    @pytest.mark.redshift
    def test_batch_columns_not_empty(self):
        """Test that batch.columns() returns column names correctly, not an empty list.

        This test validates the fix applied in fix/redshift-table-column-types branch
        (PR #11534), which ensures that batch.columns() does not return an empty list
        for Redshift batches. The fix adds a fallback mechanism when information_schema
        returns empty results, using SELECT * LIMIT 0 to retrieve column names.

        This was causing InvalidMetricAccessorDomainKwargsKeyError when trying to
        validate expectations on columns.
        """
        column_types = {
            "id": REDSHIFT_TYPES.INTEGER,
            "name": REDSHIFT_TYPES.VARCHAR,
            "amount": REDSHIFT_TYPES.DECIMAL,
        }
        batch_setup = RedshiftBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types=column_types),
            data=pd.DataFrame(
                {
                    "id": [1, 2, 3],
                    "name": ["Alice", "Bob", "Charlie"],
                    "amount": [10.50, 20.75, 30.00],
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            # This is the key test: batch.columns() should NOT return an empty list
            columns = batch.columns()

            # Validate that we got the columns (not an empty list)
            assert columns is not None
            assert isinstance(columns, list)
            assert len(columns) > 0, "batch.columns() should not return empty list"
            assert len(columns) == 3, "Should have exactly 3 columns"

            # Validate that all expected column names are present
            # Redshift returns column names in lowercase
            columns_lower = [col.lower() for col in columns]
            assert "id" in columns_lower
            assert "name" in columns_lower
            assert "amount" in columns_lower


class TestRedshiftSchemaQualifiedTables:
    """Tests for schema-qualified table name handling in Redshift.

    These tests validate the fix that ensures the fallback column detection
    uses schema-qualified table names (schema.table) when a schema is specified.
    Without this fix, queries like `SELECT * FROM table LIMIT 1` fail when the
    table is in a non-default schema.
    """

    COLUMN = "col_a"

    @pytest.mark.redshift
    def test_batch_columns_with_schema(self):
        """Test that batch.columns() works correctly when table is in a schema.

        This validates the schema_name parameter is properly passed to the fallback
        query, resulting in schema-qualified table references like `my_schema.my_table`
        instead of just `my_table`.
        """
        column_types = {
            "id": REDSHIFT_TYPES.INTEGER,
            "name": REDSHIFT_TYPES.VARCHAR,
            "value": REDSHIFT_TYPES.DECIMAL,
        }

        class RedshiftWithSchemaBatchTestSetup(RedshiftBatchTestSetup):
            @property
            @override
            def use_schema(self) -> bool:
                return True

        batch_setup = RedshiftWithSchemaBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types=column_types),
            data=pd.DataFrame(
                {
                    "id": [1, 2, 3],
                    "name": ["foo", "bar", "baz"],
                    "value": [1.1, 2.2, 3.3],
                }
            ),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            columns = batch.columns()

            assert columns is not None
            assert isinstance(columns, list)
            assert len(columns) > 0, "batch.columns() should not return empty list"
            assert len(columns) == 3, "Should have exactly 3 columns"

            columns_lower = [col.lower() for col in columns]
            assert "id" in columns_lower
            assert "name" in columns_lower
            assert "value" in columns_lower

    @pytest.mark.redshift
    def test_expectation_with_schema(self):
        """Test that expectations work correctly when table is in a schema.

        This is an end-to-end test ensuring the full validation flow works
        with schema-qualified tables.
        """
        column_types = {
            self.COLUMN: REDSHIFT_TYPES.INTEGER,
        }

        class RedshiftWithSchemaBatchTestSetup(RedshiftBatchTestSetup):
            @property
            @override
            def use_schema(self) -> bool:
                return True

        batch_setup = RedshiftWithSchemaBatchTestSetup(
            config=RedshiftDatasourceTestConfig(column_types=column_types),
            data=pd.DataFrame({self.COLUMN: [1, 2, 3]}),
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            result = batch.validate(
                expect=ExpectColumnValuesToBeOfType(
                    column=self.COLUMN,
                    type_="INTEGER",
                )
            )
        assert result.success
