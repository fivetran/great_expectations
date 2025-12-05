import pandas as pd
import pytest

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
