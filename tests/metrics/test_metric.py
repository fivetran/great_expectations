import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.core.types import Comparable
from great_expectations.metrics.domain import AbstractClassInstantiationError, ColumnValues, Domain
from great_expectations.metrics.metric import Metric, MixinTypeError
from great_expectations.validator.metric_configuration import (
    MetricConfiguration,
    MetricConfigurationID,
)

BATCH_ID = "my_data_source-my_data_asset-year_2025"
TABLE = "my_table"
COLUMN = "my_column"

FULLY_QUALIFIED_METRIC_NAME = "column_values.above"


class MockDomain(Domain):
    galaxy: str


class NotADomain: ...


class TestMetric:
    @pytest.mark.unit
    def test_metric_instantiation_raises(self):
        with pytest.raises(AbstractClassInstantiationError):
            Metric(batch_id=BATCH_ID, table=TABLE, column=COLUMN)


class TestMetricDefinition:
    @pytest.mark.unit
    def test_success(self):
        class ColumnValuesAbove(Metric, ColumnValues):
            min_value: Comparable
            strict_min: bool = False

    @pytest.mark.unit
    def test_missing_domain_mixin_raises(self):
        with pytest.raises(MixinTypeError):

            class ColumnValuesAbove(Metric):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_more_than_one_domain_mixin_raises(self):
        with pytest.raises(MixinTypeError):

            class ColumnValuesAbove(Metric, ColumnValues, MockDomain):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_non_domain_mixin_raises(self):
        with pytest.raises(MixinTypeError):

            class ColumnValuesAbove(Metric, NotADomain):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_metric_name_inference(self):
        class ColumnValuesAbove(Metric, ColumnValues):
            min_value: Comparable
            strict_min: bool = False

        assert (
            ColumnValuesAbove(
                batch_id=BATCH_ID,
                table=TABLE,
                column=COLUMN,
                min_value=42,
            ).name
            == FULLY_QUALIFIED_METRIC_NAME
        )


class TestMetricInstantiation:
    class ColumnValuesAbove(Metric, ColumnValues):
        min_value: Comparable
        strict_min: bool = False

    @pytest.mark.unit
    def test_instantiation_success(self):
        self.ColumnValuesAbove(
            batch_id=BATCH_ID,
            table=TABLE,
            column=COLUMN,
            min_value=42,
        )

    @pytest.mark.unit
    def test_instantiation_missing_domain_parameters_raises(self):
        with pytest.raises(ValidationError):
            self.ColumnValuesAbove(min_value=42)


class TestMetricConfig:
    class ColumnValuesAbove(Metric, ColumnValues):
        min_value: Comparable
        strict_min: bool = False

    @pytest.mark.unit
    def test_success(self):
        expected_config = MetricConfiguration(
            metric_name=FULLY_QUALIFIED_METRIC_NAME,
            metric_domain_kwargs={
                "batch_id": BATCH_ID,
                "table": TABLE,
                "row_condition": None,
                "column": COLUMN,
            },
            metric_value_kwargs={
                "min_value": 42,
                "strict_min": False,
            },
        )

        actual_config = self.ColumnValuesAbove(
            batch_id=BATCH_ID,
            table=TABLE,
            column=COLUMN,
            min_value=42,
        ).config

        assert actual_config.metric_name == expected_config.metric_name
        assert actual_config.metric_domain_kwargs == expected_config.metric_domain_kwargs
        assert actual_config.metric_value_kwargs == expected_config.metric_value_kwargs
        assert isinstance(actual_config.id, MetricConfigurationID)


class TestMetricImmutability:
    class ColumnValuesAbove(Metric, ColumnValues):
        min_value: Comparable
        strict_min: bool = False

    @pytest.mark.unit
    def test_domain_kwarg_immutability_success(self):
        column_values_above = self.ColumnValuesAbove(
            batch_id=BATCH_ID,
            table=TABLE,
            column=COLUMN,
            min_value=42,
        )

        with pytest.raises(TypeError):
            column_values_above.table = "updated_table"

    @pytest.mark.unit
    def test_value_kwarg_immutability_success(self):
        column_values_above = self.ColumnValuesAbove(
            batch_id=BATCH_ID,
            table=TABLE,
            column=COLUMN,
            min_value=42,
        )

        with pytest.raises(TypeError):
            column_values_above.min_value = 42
