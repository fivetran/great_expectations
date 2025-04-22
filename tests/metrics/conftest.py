from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    PandasDataFrameDatasourceTestConfig,
    PandasFilesystemCsvDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    SqliteDatasourceTestConfig,
)

PANDAS_DATA_SOURCES: list[DataSourceTestConfig] = [
    PandasFilesystemCsvDatasourceTestConfig(),
    PandasDataFrameDatasourceTestConfig(),
]

SPARK_DATA_SOURCES: list[DataSourceTestConfig] = [
    SparkFilesystemCsvDatasourceTestConfig(),
]

SQL_DATA_SOURCES: list[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SqliteDatasourceTestConfig(),
]

ALL_DATA_SOURCES: list[DataSourceTestConfig] = (
    PANDAS_DATA_SOURCES + SPARK_DATA_SOURCES + SQL_DATA_SOURCES
)
