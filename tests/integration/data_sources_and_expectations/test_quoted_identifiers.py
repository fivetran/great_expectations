# TODO: Write tests


from typing import TYPE_CHECKING, Final, Literal, Mapping, Sequence, Type

import pandas as pd

from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

SUPPORTED_DATA_SOURCE_TYPES: Sequence[Type[DataSourceTestConfig]] = [
    DatabricksDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
]

TEST_TABLE_NAME: Final[Literal["test_table"]] = "test_table"

DatabaseType: TypeAlias = Literal["databricks", "postgresql", "snowflake", "sqlite"]
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
        "unquoted_lower": TEST_TABLE_NAME.lower(),
        "quoted_lower": f'"{TEST_TABLE_NAME.lower()}"',
        "unquoted_upper": TEST_TABLE_NAME.upper(),
        "quoted_upper": f'"{TEST_TABLE_NAME.upper()}"',
        "quoted_mixed": f'"{TEST_TABLE_NAME.title()}"',
        "unquoted_mixed": TEST_TABLE_NAME.title(),
    },
    "databricks": {
        "unquoted_lower": TEST_TABLE_NAME.lower(),
        "quoted_lower": f"`{TEST_TABLE_NAME.lower()}`",
        "unquoted_upper": TEST_TABLE_NAME.upper(),
        "quoted_upper": f"`{TEST_TABLE_NAME.upper()}`",
        "quoted_mixed": f"`{TEST_TABLE_NAME.title()}`",
        "unquoted_mixed": TEST_TABLE_NAME.title(),
    },
    "snowflake": {
        "unquoted_lower": TEST_TABLE_NAME.lower(),
        "quoted_lower": f'"{TEST_TABLE_NAME.lower()}"',
        "unquoted_upper": TEST_TABLE_NAME.upper(),
        "quoted_upper": f'"{TEST_TABLE_NAME.upper()}"',
        "quoted_mixed": f'"{TEST_TABLE_NAME.title()}"',
        "unquoted_mixed": TEST_TABLE_NAME.title(),
    },
    "sqlite": {
        "unquoted_lower": TEST_TABLE_NAME.lower(),
        "quoted_lower": f'"{TEST_TABLE_NAME.lower()}"',
        "unquoted_upper": TEST_TABLE_NAME.upper(),
        "quoted_upper": f'"{TEST_TABLE_NAME.upper()}"',
        "quoted_mixed": f'"{TEST_TABLE_NAME.title()}"',
        "unquoted_mixed": TEST_TABLE_NAME.title(),
    },
}

# Column names
UNQUOTED_UPPER_COL: Final[Literal["UNQUOTED_UPPER_COL"]] = "UNQUOTED_UPPER_COL"
UNQUOTED_LOWER_COL: Final[Literal["unquoted_lower_col"]] = "unquoted_lower_col"
QUOTED_UPPER_COL: Final[Literal["QUOTED_UPPER_COL"]] = "QUOTED_UPPER_COL"
QUOTED_LOWER_COL: Final[Literal["quoted_lower_col"]] = "quoted_lower_col"
QUOTED_MIXED_CASE: Final[Literal["quotedMixed"]] = "quotedMixed"
QUOTED_W_DOTS: Final[Literal["quoted.w.dots"]] = "quoted.w.dots"


class TestColumnQuotedIdentifiers:
    pass


class TestTableQuotedIdentifiers:
    @parameterize_batch_for_data_sources(
        data_source_configs=[
            ds_type(table_name=TABLE_NAME_MAPPING[ds_type.label]["unquoted_lower"])
            for ds_type in SUPPORTED_DATA_SOURCE_TYPES
        ],
        data=pd.DataFrame(),
    )
    def test_unquoted_lower(self, batch_for_datasource: Batch):
        pass

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            ds_type(table_name=TABLE_NAME_MAPPING[ds_type.label]["quoted_lower"])
            for ds_type in SUPPORTED_DATA_SOURCE_TYPES
        ],
        data=pd.DataFrame(),
    )
    def test_quoted_lower(self, batch_for_datasource: Batch):
        pass

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            ds_type(table_name=TABLE_NAME_MAPPING[ds_type.label]["unquoted_upper"])
            for ds_type in SUPPORTED_DATA_SOURCE_TYPES
        ],
        data=pd.DataFrame(),
    )
    def test_unquoted_upper(self, batch_for_datasource: Batch):
        pass

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            ds_type(table_name=TABLE_NAME_MAPPING[ds_type.label]["quoted_upper"])
            for ds_type in SUPPORTED_DATA_SOURCE_TYPES
        ],
        data=pd.DataFrame(),
    )
    def test_quoted_upper(self, batch_for_datasource: Batch):
        pass

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            ds_type(table_name=TABLE_NAME_MAPPING[ds_type.label]["unquoted_mixed"])
            for ds_type in SUPPORTED_DATA_SOURCE_TYPES
        ],
        data=pd.DataFrame(),
    )
    def test_unquoted_mixed(self, batch_for_datasource: Batch):
        pass

    @parameterize_batch_for_data_sources(
        data_source_configs=[
            ds_type(table_name=TABLE_NAME_MAPPING[ds_type.label]["quoted_mixed"])
            for ds_type in SUPPORTED_DATA_SOURCE_TYPES
        ],
        data=pd.DataFrame(),
    )
    def test_quoted_mixed(self, batch_for_datasource: Batch):
        pass
