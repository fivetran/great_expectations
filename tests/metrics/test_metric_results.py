import pandas as pd

from great_expectations.metrics.metric_results import ColumnTypeMetricResult, _ColumnType, StringListMetricResult, \
    BooleanListMetricResult, IntegerMetricResult


class TestMetricResultInstantiation:
    def test_integer_metric_result(self):
        metric_id = ('column_values.null.unexpected_count', '73d1f59d321e58e8e8a0cfc2d22cca1f', ())
        metric_value = 0

        metric_result = IntegerMetricResult(
            id=metric_id,
            value=metric_value,
        )
        assert not metric_result.error

    def test_table_columns_metric_result(self):
        metric_id = ("table.columns", "a8ef4ee749d02d0e5f92719fc6ee8010", ())
        metric_value = [
            "existing_column",
            "another_existing_column",
        ]
        metric_result = StringListMetricResult(
            id=metric_id,
            value=metric_value,
        )
        assert not metric_result.error
        assert all(isinstance(val, str) for val in metric_result.value)

    def test_table_column_types_result(self):
        metric_id = (
            "table.column_types",
            "a8ef4ee749d02d0e5f92719fc6ee8010",
            "include_nested=True",
        )
        metric_value = [
            {"name": "existing_column", "type": "int64"},
            {"name": "another_existing_column", "type": "object"},
        ]

        metric_result = ColumnTypeMetricResult(
            id=metric_id,
            value=metric_value,
        )

        assert not metric_result.error
        assert all(isinstance(val, _ColumnType) for val in metric_result.value)

