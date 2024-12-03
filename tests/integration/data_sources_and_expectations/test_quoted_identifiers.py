from typing import Final, Literal, Mapping

import pandas as pd
from typing_extensions import TypeAlias

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig


class TestColumnQuotedIdentifiers:
    # Column names
    UNQUOTED_UPPER_COL: Final[Literal["UNQUOTED_UPPER_COL"]] = "UNQUOTED_UPPER_COL"
    UNQUOTED_LOWER_COL: Final[Literal["unquoted_lower_col"]] = "unquoted_lower_col"
    UNQUOTED_MIXED_CASE: Final[Literal["unquotedMixed"]] = "unquotedMixed"
    QUOTED_UPPER_COL: Final[Literal["QUOTED_UPPER_COL"]] = "QUOTED_UPPER_COL"
    QUOTED_LOWER_COL: Final[Literal["quoted_lower_col"]] = "quoted_lower_col"
    QUOTED_MIXED_CASE: Final[Literal["quotedMixed"]] = "quotedMixed"

    SUPPORTED_DATA_SOURCES: list[DataSourceTestConfig] = [
        DatabricksDatasourceTestConfig(),
        PostgreSQLDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ]

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame({UNQUOTED_LOWER_COL: [1, 2, 3]}),
    # )
    # def test_unquoted_lower(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame({QUOTED_LOWER_COL: [1, 2, 3]}),
    # )
    # def test_quoted_lower(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=QUOTED_LOWER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_unquoted_upper(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_UPPER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_quoted_upper(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=QUOTED_UPPER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_unquoted_mixed(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_quoted_mixed(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_unquoted_with_dots(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER_COL))
    #     assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_quoted_with_dots(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER_COL))
    #     assert result.success


class TestTableQuotedIdentifiers:
    _TEST_TABLE_NAME: Final[Literal["test_table"]] = "test_table"
    _DATA: Final[pd.DataFrame] = pd.DataFrame({"a": [1, 2, 3]})

    DatabaseType: TypeAlias = Literal["databricks", "postgres", "snowflake", "sqlite"]
    TableNameCase: TypeAlias = Literal[
        "quoted_lower",
        "quoted_mixed",
        "quoted_upper",
        "unquoted_lower",
        "unquoted_mixed",
        "unquoted_upper",
    ]
    TABLE_NAME_MAPPING: Final[Mapping[DatabaseType, Mapping[TableNameCase, str]]] = {
        "postgres": {
            "unquoted_lower": _TEST_TABLE_NAME.lower(),
            "quoted_lower": f'"{_TEST_TABLE_NAME.lower()}"',
            "unquoted_upper": _TEST_TABLE_NAME.upper(),
            "quoted_upper": f'"{_TEST_TABLE_NAME.upper()}"',
            "quoted_mixed": f'"{_TEST_TABLE_NAME.title()}"',
            "unquoted_mixed": _TEST_TABLE_NAME.title(),
        },
        "databricks": {
            "unquoted_lower": _TEST_TABLE_NAME.lower(),
            "quoted_lower": f"`{_TEST_TABLE_NAME.lower()}`",
            "unquoted_upper": _TEST_TABLE_NAME.upper(),
            "quoted_upper": f"`{_TEST_TABLE_NAME.upper()}`",
            "quoted_mixed": f"`{_TEST_TABLE_NAME.title()}`",
            "unquoted_mixed": _TEST_TABLE_NAME.title(),
        },
        "snowflake": {
            "unquoted_lower": _TEST_TABLE_NAME.lower(),
            "quoted_lower": f'"{_TEST_TABLE_NAME.lower()}"',
            "unquoted_upper": _TEST_TABLE_NAME.upper(),
            "quoted_upper": f'"{_TEST_TABLE_NAME.upper()}"',
            "quoted_mixed": f'"{_TEST_TABLE_NAME.title()}"',
            "unquoted_mixed": _TEST_TABLE_NAME.title(),
        },
        "sqlite": {
            "unquoted_lower": _TEST_TABLE_NAME.lower(),
            "quoted_lower": f'"{_TEST_TABLE_NAME.lower()}"',
            "unquoted_upper": _TEST_TABLE_NAME.upper(),
            "quoted_upper": f'"{_TEST_TABLE_NAME.upper()}"',
            "quoted_mixed": f'"{_TEST_TABLE_NAME.title()}"',
            "unquoted_mixed": _TEST_TABLE_NAME.title(),
        },
    }

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["databricks"]["unquoted_lower"]
            ),
            PostgreSQLDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["postgres"]["unquoted_lower"]
            ),
            SnowflakeDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["snowflake"]["unquoted_lower"]
            ),
            SqliteDatasourceTestConfig(table_name=TABLE_NAME_MAPPING["sqlite"]["unquoted_lower"]),
        ],
        data=_DATA,
    )
    def test_unquoted_lower(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectTableRowCountToEqual(value=3))
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["databricks"]["quoted_lower"]
            ),
            PostgreSQLDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["postgres"]["quoted_lower"]
            ),
            SnowflakeDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["snowflake"]["quoted_lower"]
            ),
            SqliteDatasourceTestConfig(table_name=TABLE_NAME_MAPPING["sqlite"]["quoted_lower"]),
        ],
        data=_DATA,
    )
    def test_quoted_lower(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectTableRowCountToEqual(value=3))
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["databricks"]["unquoted_upper"]
            ),
            PostgreSQLDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["postgres"]["unquoted_upper"]
            ),
            SnowflakeDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["snowflake"]["unquoted_upper"]
            ),
            SqliteDatasourceTestConfig(table_name=TABLE_NAME_MAPPING["sqlite"]["unquoted_upper"]),
        ],
        data=_DATA,
    )
    def test_unquoted_upper(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectTableRowCountToEqual(value=3))
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["databricks"]["quoted_upper"]
            ),
            PostgreSQLDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["postgres"]["quoted_upper"]
            ),
            SnowflakeDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["snowflake"]["quoted_upper"]
            ),
            SqliteDatasourceTestConfig(table_name=TABLE_NAME_MAPPING["sqlite"]["quoted_upper"]),
        ],
        data=_DATA,
    )
    def test_quoted_upper(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectTableRowCountToEqual(value=3))
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["databricks"]["unquoted_mixed"]
            ),
            PostgreSQLDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["postgres"]["unquoted_mixed"]
            ),
            SnowflakeDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["snowflake"]["unquoted_mixed"]
            ),
            SqliteDatasourceTestConfig(table_name=TABLE_NAME_MAPPING["sqlite"]["unquoted_mixed"]),
        ],
        data=_DATA,
    )
    def test_unquoted_mixed(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectTableRowCountToEqual(value=3))
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            DatabricksDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["databricks"]["quoted_mixed"]
            ),
            PostgreSQLDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["postgres"]["quoted_mixed"]
            ),
            SnowflakeDatasourceTestConfig(
                table_name=TABLE_NAME_MAPPING["snowflake"]["quoted_mixed"]
            ),
            SqliteDatasourceTestConfig(table_name=TABLE_NAME_MAPPING["sqlite"]["quoted_mixed"]),
        ],
        data=_DATA,
    )
    def test_quoted_mixed(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectTableRowCountToEqual(value=3))
        assert result.success
