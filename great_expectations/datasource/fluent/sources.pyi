import sys
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    pass
else:
    pass

from great_expectations.compatibility import pydantic
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.interfaces import (
    DataAsset,
)
from great_expectations.datasource.fluent.pandas_file_path_datasource import (
    PandasFilePathDatasource,
)
from great_expectations.datasource.fluent.spark_datasource import (
    SparkDatasource,
)
from great_expectations.datasource.fluent.spark_file_path_datasource import (
    SparkFilePathDatasource,
)
from great_expectations.datasource.fluent.sql_datasource import (
    SQLDatasource,
)

class _SourceFactories:
    """
    This mixin provides factory methods for adding datasources to a DataContext.
    You can access this by calling `context.data_sources`.
    """

    def add_pandas(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        assets: Optional[list[DataAsset]] = None,
    ) -> PandasFilePathDatasource: ...
    def add_pandas_filesystem(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        base_directory: pydantic.DirectoryPath,
        data_context_root_directory: Optional[pydantic.DirectoryPath] = None,
        assets: Optional[list[DataAsset]] = None,
    ) -> PandasFilePathDatasource: ...
    def add_spark(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        assets: Optional[list[DataAsset]] = None,
    ) -> SparkDatasource: ...
    def add_spark_filesystem(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        base_directory: pydantic.DirectoryPath,
        data_context_root_directory: Optional[pydantic.DirectoryPath] = None,
        assets: Optional[list[DataAsset]] = None,
    ) -> SparkFilePathDatasource: ...
    def add_sql(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_postgres(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_sqlite(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_snowflake(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_bigquery(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_mysql(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_mssql(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_athena(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_redshift(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_trino(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
    def add_databricks_sql(
        self,
        name: str,
        *,
        id: Optional[str] = None,
        connection_string: ConfigStr,
        create_temp_table: bool = True,
        assets: Optional[list[DataAsset]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> SQLDatasource: ...
