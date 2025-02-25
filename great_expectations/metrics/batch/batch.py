from typing import Optional

from great_expectations.compatibility.pydantic import StrictStr
from great_expectations.metrics.metric import Metric, NonEmptyString, _MetricResult


class BatchMetric(Metric[_MetricResult]):
    batch_id: NonEmptyString
    row_condition: Optional[StrictStr] = None
