from enum import Enum


class DataQualityIssues(str, Enum):
    """Data quality issues addressed by Core Expectations."""

    VOLUME = "Volume"
    SCHEMA = "Schema"
    COMPLETENESS = "Completeness"
    UNIQUENESS = "Uniqueness"
    NUMERIC = "Numeric"
    VALIDITY = "Validity"
    SQL = "SQL"


class SupportedDataSources(str, Enum):
    """Data sources supported by Core Expectations."""

    PANDAS = "Pandas"
    SPARK = "Spark"
    SQLITE = "SQLite"
    POSTGRESQL = "PostgreSQL"
    MYSQL = "MySQL"
    MSSQL = "MSSQL"
    BIGQUERY = "BigQuery"
    SNOWFLAKE = "Snowflake"
    DATABRICKS = "Databricks (SQL)"
    REDSHIFT = "Redshift"
