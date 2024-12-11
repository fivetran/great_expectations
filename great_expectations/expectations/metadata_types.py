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
