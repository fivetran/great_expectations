import pandas as pd

from great_expectations.metrics.batch.sample_values import SampleValues, SampleValuesResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

DATA_FRAME_WITH_MANY_ROWS = pd.DataFrame({"value": [i for i in range(100)]})
DATA_FRAME_WITH_FEW_ROWS = pd.DataFrame({"value": [1, 2, 3]})


class TestSampleValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_MANY_ROWS,
    )
    def test_with_many_rows(self, batch_for_datasource) -> None:
        metric_result = batch_for_datasource.compute_metrics(SampleValues())
        assert isinstance(metric_result, SampleValuesResult)
        assert metric_result.value.equals(pd.DataFrame({"value": [i for i in range(10)]}))

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_FEW_ROWS,
    )
    def test_with_few_rows(self, batch_for_datasource) -> None:
        metric_result = batch_for_datasource.compute_metrics(SampleValues())
        assert isinstance(metric_result, SampleValuesResult)
        assert metric_result.value.equals(pd.DataFrame({"value": [1, 2, 3]}))

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_MANY_ROWS,
    )
    def test_with_custom_n_rows(self, batch_for_datasource) -> None:
        metric_result = batch_for_datasource.compute_metrics(SampleValues(n_rows=5))
        assert isinstance(metric_result, SampleValuesResult)
        assert metric_result.value.equals(pd.DataFrame({"value": [0, 1, 2, 3, 4]}))
