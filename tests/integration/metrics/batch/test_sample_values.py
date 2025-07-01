import pandas as pd

from great_expectations.metrics.batch.sample_values import SampleValues, SampleValuesResult
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.metrics.conftest import ALL_DATA_SOURCES

COL_NAME = "my_column"

DATA_FRAME_WITH_MANY_ROWS = pd.DataFrame({COL_NAME: [i for i in range(100)]})
DATA_FRAME_WITH_FEW_ROWS = pd.DataFrame({COL_NAME: [1, 2, 3]})


class TestSampleValues:
    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_MANY_ROWS,
    )
    def test_correct_return_types(self, batch_for_datasource) -> None:
        metric_result = batch_for_datasource.compute_metrics(SampleValues())
        assert isinstance(metric_result, SampleValuesResult)

        values = set(metric_result.value[COL_NAME])
        assert values.issubset(range(100))

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_MANY_ROWS,
    )
    def test_default_n_rows(self, batch_for_datasource) -> None:
        metric_result = batch_for_datasource.compute_metrics(SampleValues())
        assert isinstance(metric_result, SampleValuesResult)
        assert len(metric_result.value) == 10

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_FEW_ROWS,
    )
    def test_fewer_rows_exist_than_default_n_rows(self, batch_for_datasource) -> None:
        metric_result = batch_for_datasource.compute_metrics(SampleValues())
        assert isinstance(metric_result, SampleValuesResult)
        assert len(metric_result.value) == 3

    @parameterize_batch_for_data_sources(
        data_source_configs=ALL_DATA_SOURCES,
        data=DATA_FRAME_WITH_MANY_ROWS,
    )
    def test_with_custom_n_rows(self, batch_for_datasource) -> None:
        n_rows = 5
        metric_result = batch_for_datasource.compute_metrics(SampleValues(n_rows=n_rows))
        assert isinstance(metric_result, SampleValuesResult)
        assert len(metric_result.value) == n_rows
