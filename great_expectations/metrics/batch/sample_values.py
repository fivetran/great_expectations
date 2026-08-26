from typing import TYPE_CHECKING, Any

from great_expectations.compatibility.pandas import pandas as pd
from great_expectations.metrics.batch.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult

if TYPE_CHECKING:
    # mypy sees a real pd.DataFrame generic parameter, so `.value` type-checks as a
    # DataFrame everywhere it's used (e.g. subscripting in tests). At runtime, though,
    # table.head is a PandasExecutionEngine-only metric that's only resolvable (and
    # only needed) when pandas is installed, so parametrizing with the real class only
    # when it exists (or `Any` when absent) sidesteps pydantic's forward-ref
    # resolution entirely -- how eagerly a bare string generic parameter gets resolved
    # varies across pydantic v1 versions and isn't reliable at class-definition time.
    class SampleValuesResult(MetricResult["pd.DataFrame"]): ...
else:
    _SampleValueType = pd.DataFrame if pd else Any

    class SampleValuesResult(MetricResult[_SampleValueType]): ...


class SampleValues(BatchMetric[SampleValuesResult]):
    """Sample rows from a table"""

    name = "table.head"
    n_rows: int = 10
