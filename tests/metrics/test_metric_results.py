import pytest

from great_expectations.metrics.metric_results import (
    ColumnType,
    MetricErrorResult,
    MetricErrorResultValue,
    TableColumnsResult,
    TableColumnTypesResult,
    UnexpectedCountResult,
    UnexpectedValuesResult,
)
from great_expectations.validator.metric_configuration import (
    MetricConfigurationID,
)


class TestMetricResultInstantiation:
    @pytest.mark.unit
    def test_unexpected_count_result(self):
        metric_id = MetricConfigurationID(
            metric_name="column_values.null.unexpected_count",
            metric_domain_kwargs_id="73d1f59d321e58e8e8a0cfc2d22cca1f",
            metric_value_kwargs_id=(),
        )
        metric_value = 0

        metric_result = UnexpectedCountResult(
            id=metric_id,
            value=metric_value,
        )
        assert metric_result.dict() == {"id": metric_id, "value": metric_value}

    @pytest.mark.unit
    def test_unexpected_values_result(self):
        metric_id = MetricConfigurationID(
            metric_name="column_values.null.unexpected_values",
            metric_domain_kwargs_id="a8ef4ee749d02d0e5f92719fc6ee8010",
            metric_value_kwargs_id="include_nested=True",
        )
        metric_value = [
            # these are values coming from the user, so can be anything
            "foo",
            3.14,
            False,
        ]

        metric_result = UnexpectedValuesResult(
            id=metric_id,
            value=metric_value,
        )
        assert metric_result.dict() == {"id": metric_id, "value": metric_value}

    @pytest.mark.unit
    def test_table_columns_metric_result(self):
        metric_id = MetricConfigurationID(
            metric_name="table.columns",
            metric_domain_kwargs_id="a8ef4ee749d02d0e5f92719fc6ee8010",
            metric_value_kwargs_id=(),
        )
        metric_value = [
            "existing_column",
            "another_existing_column",
        ]
        metric_result = TableColumnsResult(
            id=metric_id,
            value=metric_value,
        )
        assert metric_result.dict() == {"id": metric_id, "value": metric_value}

    @pytest.mark.unit
    def test_table_column_types_result(self):
        metric_id = MetricConfigurationID(
            metric_name="table.column_types",
            metric_domain_kwargs_id="a8ef4ee749d02d0e5f92719fc6ee8010",
            metric_value_kwargs_id="include_nested=True",
        )
        metric_value = [
            {"name": "existing_column", "type": "int64"},
            {"name": "another_existing_column", "type": "object"},
        ]

        metric_result = TableColumnTypesResult(
            id=metric_id,
            value=metric_value,
        )

        assert all(isinstance(val, ColumnType) for val in metric_result.value)
        assert metric_result.dict() == {"id": metric_id, "value": metric_value}

    @pytest.mark.unit
    def test_metric_error_result(self):
        metric_id = MetricConfigurationID(
            metric_name="column.mean",
            metric_domain_kwargs_id="8a975130e802d66f85ab0cac8d10fbec",
            metric_value_kwargs_id=(),
        )
        metric_value = MetricErrorResultValue(
            exception_traceback="Traceback (most recent call last)...",
            exception_message="Error: The column does not exist.",
        )
        metric_result = MetricErrorResult(
            id=metric_id,
            value=metric_value,
        )
        assert metric_result.dict() == {"id": metric_id, "value": metric_value}
