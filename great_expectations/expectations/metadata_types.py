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
    MULTI_SOURCE = "Multi-source"


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
    AURORA = "Amazon Aurora PostgreSQL"
    CITUS = "Citus"
    ALLOY = "AlloyDB"
    NEON = "Neon"


class FailureSeverity(str, Enum):
    """Severity levels for expectation failures."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
