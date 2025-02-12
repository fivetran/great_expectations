from typing import Optional

from great_expectations.core.types import Comparable
from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric import Metric


class ColumnValuesBetween(Metric, ColumnValues):
    min_value: Optional[Comparable] = None
    max_value: Optional[Comparable] = None
    strict_min: bool = False
    strict_max: bool = False
