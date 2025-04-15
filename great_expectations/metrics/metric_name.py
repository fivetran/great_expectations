from enum import Enum


class MetricNameSuffix(str, Enum):
    CONDITION = "condition"
    COUNT = "count"
    UNEXPECTED_COUNT = "unexpected_count"
