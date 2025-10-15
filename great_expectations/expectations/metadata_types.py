from enum import Enum

from great_expectations.compatibility.typing_extensions import override


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
    """Severity levels for Expectation failures."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    @override
    def __lt__(self, other):
        """Implement semantic ordering: INFO < WARNING < CRITICAL"""
        if not isinstance(other, FailureSeverity):
            return NotImplemented

        # Semantic ordering: INFO < WARNING < CRITICAL
        order = {FailureSeverity.INFO: 0, FailureSeverity.WARNING: 1, FailureSeverity.CRITICAL: 2}
        return order[self] < order[other]

    @override
    def __gt__(self, other):
        """Implement semantic ordering: CRITICAL > WARNING > INFO"""
        if not isinstance(other, FailureSeverity):
            return NotImplemented
        return not self.__le__(other)

    @override
    def __le__(self, other):
        """Implement semantic ordering: INFO <= WARNING <= CRITICAL"""
        if not isinstance(other, FailureSeverity):
            return NotImplemented
        return self.__lt__(other) or self == other

    @override
    def __ge__(self, other):
        """Implement semantic ordering: CRITICAL >= WARNING >= INFO"""
        if not isinstance(other, FailureSeverity):
            return NotImplemented
        return not self.__lt__(other)
