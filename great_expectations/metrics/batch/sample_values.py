import pandas as pd

from great_expectations.metrics.batch.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult


class SampleValuesResult(MetricResult[pd.DataFrame]): ...


class SampleValues(BatchMetric[SampleValuesResult]):
    """Sample rows from a table"""

    name = "table.head"
    n_rows: int = 10
