from typing import Optional

import pandas as pd

from great_expectations.core.id_dict import IDDict
from great_expectations.core.types import Comparable
from great_expectations.metrics.domain import ColumnValues
from great_expectations.metrics.metric import Metric
from great_expectations.metrics.metric_results import MetricResult


class ColumnValuesBetweenResult(MetricResult[tuple[pd.Series, IDDict, dict]]): ...


class ColumnValuesBetween(Metric[ColumnValuesBetweenResult], ColumnValues):
    name = "column_values.between.condition"

    min_value: Optional[Comparable] = None
    max_value: Optional[Comparable] = None
    strict_min: bool = False
    strict_max: bool = False
