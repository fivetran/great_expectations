from enum import Enum


class DomainName(str, Enum):
    BATCH = "table"
    COLUMN_VALUES = "column_values"
    QUERY = "query"


class MetricNameSuffix(str, Enum):
    CONDITION = "condition"
    COUNT = "count"
