from enum import Enum


class DomainName(str, Enum):
    BATCH = "table"
    COLUMN_VALUES = "column_values"


class MetricNameSuffix(str, Enum):
    CONDITION = "condition"
    COUNT = "count"
