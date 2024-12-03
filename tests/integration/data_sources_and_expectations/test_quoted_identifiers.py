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

NAME: Final[Literal["test_table"]] = "quoted_id_test"
UNQUOTED_LOWER: Final[str] = NAME.lower()
UNQUOTED_UPPER: Final[str] = NAME.upper()
UNQUOTED_MIXED: Final[str] = NAME.title()

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
        "unquoted_lower": UNQUOTED_LOWER,
        "quoted_lower": f'"{NAME.lower()}"',
        "unquoted_upper": UNQUOTED_UPPER,
        "quoted_upper": f'"{NAME.upper()}"',
        "unquoted_mixed": UNQUOTED_MIXED,
        "quoted_mixed": f'"{NAME.title()}"',
    },
    "databricks": {
        "unquoted_lower": UNQUOTED_LOWER,
        "quoted_lower": f"`{NAME.lower()}`",
        "unquoted_upper": UNQUOTED_UPPER,
        "quoted_upper": f"`{NAME.upper()}`",
        "unquoted_mixed": UNQUOTED_MIXED,
        "quoted_mixed": f"`{NAME.title()}`",
    },
    "snowflake": {
        "unquoted_lower": UNQUOTED_LOWER,
        "quoted_lower": f'"{NAME.lower()}"',
        "unquoted_upper": UNQUOTED_UPPER,
        "quoted_upper": f'"{NAME.upper()}"',
        "unquoted_mixed": UNQUOTED_MIXED,
        "quoted_mixed": f'"{NAME.title()}"',
    },
    "sqlite": {
        "unquoted_lower": UNQUOTED_LOWER,
        "quoted_lower": f'"{NAME.lower()}"',
        "unquoted_upper": UNQUOTED_UPPER,
        "quoted_upper": f'"{NAME.upper()}"',
        "unquoted_mixed": UNQUOTED_MIXED,
        "quoted_mixed": f'"{NAME.title()}"',
    },
}


class TestColumnQuotedIdentifiers:
    GENERIC_SQL_CONFIGS: list[DataSourceTestConfig] = [
        PostgreSQLDatasourceTestConfig(),
        SnowflakeDatasourceTestConfig(),
        SqliteDatasourceTestConfig(),
    ]
    DATABRICKS_SQL_CONFIGS: list[DataSourceTestConfig] = [DatabricksDatasourceTestConfig()]
    ALL_SQL_CONFIGS: list[DataSourceTestConfig] = [*GENERIC_SQL_CONFIGS, *DATABRICKS_SQL_CONFIGS]

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_SQL_CONFIGS,
        data=pd.DataFrame({UNQUOTED_LOWER: [1, 2, 3]}),
    )
    def test_unquoted_lower(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER))
        assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=GENERIC_SQL_CONFIGS,
    #     data=pd.DataFrame({f'"{UNQUOTED_LOWER}"': [1, 2, 3]}),
    # )
    # def test_quoted_lower_generic_sql(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_LOWER))
    #     assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_SQL_CONFIGS,
        data=pd.DataFrame({UNQUOTED_UPPER: [1, 2, 3]}),
    )
    def test_unquoted_upper(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_UPPER))
        assert result.success

    # @parameterize_batch_for_data_sources(
    #     data_source_configs=SUPPORTED_DATA_SOURCES,
    #     data=pd.DataFrame(),
    # )
    # def test_quoted_upper(self, batch_for_datasource: Batch):
    #     result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=QUOTED_UPPER_COL))
    #     assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_SQL_CONFIGS,
        data=pd.DataFrame({UNQUOTED_MIXED: [1, 2, 3]}),
    )
    def test_unquoted_mixed(self, batch_for_datasource: Batch):
        result = batch_for_datasource.validate(gxe.ExpectColumnToExist(column=UNQUOTED_MIXED))
        assert result.success

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
    _DATA: Final[pd.DataFrame] = pd.DataFrame({"a": [1, 2, 3]})

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
