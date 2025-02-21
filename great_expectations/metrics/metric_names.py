from enum import Enum


class DomainNames(str, Enum):
    BATCH = "table"
    COLUMN_VALUES = "column_values"


class MetricNameSuffixes(str, Enum):
    CONDITION = "condition"
    COUNT = "count"


class MetricNames(str, Enum):
    BATCH_ROW_COUNT = ".".join((DomainNames.BATCH, "row_count"))
    COLUMN_VALUES_NON_NULL = ".".join(
        (DomainNames.COLUMN_VALUES, "nonnull", MetricNameSuffixes.CONDITION)
    )
    COLUMN_VALUES_NON_NULL_COUNT = ".".join(
        (DomainNames.COLUMN_VALUES, "nonnull", MetricNameSuffixes.COUNT)
    )
