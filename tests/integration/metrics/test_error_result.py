import pandas

from great_expectations.metrics.column.distinct_values import ColumnDistinctValues
from great_expectations.metrics.metric_results import MetricErrorResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

DATA_FRAME = pandas.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "number": [1, 2, 3, 4],
    },
)


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=DATA_FRAME,
)
def test_error_result(batch_for_datasource) -> None:
    batch = batch_for_datasource
    metric = ColumnDistinctValues(column="non_existent_column")
    metric_result = batch.compute_metrics(metric)
    assert isinstance(metric_result, MetricErrorResult)
    assert metric_result.value.exception_message is not None
    assert metric_result.value.exception_traceback is not None
