# TODO: Write tests


from typing import Sequence, Type

from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

SUPPORTED_DATA_SOURCE_TYPES: Sequence[Type[DataSourceTestConfig]] = [
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SqliteDatasourceTestConfig,
]


# [ds_type(table_name=...) for ds_type in SUPPORTED_DATA_SOURCE_TYPES]


class TestColumnQuotedIdentifiers:
    pass


class TestTableQuotedIdentifiers:
    pass
