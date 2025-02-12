from unittest import mock
from uuid import uuid4

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.core.types import Comparable
from great_expectations.metrics import Metric
from great_expectations.metrics.domain import AbstractClassInstantiationError, ColumnMap, Domain
from great_expectations.metrics.metric import MixinTypeError, UnregisteredMetricTypeError
from great_expectations.validator.metric_configuration import (
    MetricConfiguration,
    MetricConfigurationID,
)

BATCH_ID = str(uuid4())
TABLE = "my_table"
COLUMN = "my_column"

MOCK_METRIC_REGISTRY = {
    "column_values": ("above",),
}
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
        with mock.patch("great_expectations.metrics.metric.METRIC_REGISTRY", MOCK_METRIC_REGISTRY):

            class Above(Metric, ColumnMap):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_missing_domain_mixin_raises(self):
        with pytest.raises(MixinTypeError):

            class Above(Metric):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_more_than_one_domain_mixin_raises(self):
        with pytest.raises(MixinTypeError):

            class Above(Metric, ColumnMap, MockDomain):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_non_domain_mixin_raises(self):
        with pytest.raises(MixinTypeError):

            class Above(Metric, NotADomain):
                min_value: Comparable
                strict_min: bool = False

    @pytest.mark.unit
    def test_unregistered_domain_raises(self):
        with mock.patch("great_expectations.metrics.metric.METRIC_REGISTRY", MOCK_METRIC_REGISTRY):
            with pytest.raises(UnregisteredMetricTypeError):

                class Above(Metric, MockDomain):
                    min_value: Comparable
                    strict_min: bool = False

    @pytest.mark.unit
    def test_unregistered_metric_raises(self):
        with pytest.raises(UnregisteredMetricTypeError):

            class Above(Metric, ColumnMap):
                min_value: Comparable
                strict_min: bool = False


class TestMetricInstantiation:
    with mock.patch("great_expectations.metrics.metric.METRIC_REGISTRY", MOCK_METRIC_REGISTRY):

        class Above(Metric, ColumnMap):
            min_value: Comparable
            strict_min: bool = False

    @pytest.mark.unit
    def test_instantiation_success(self):
        self.Above(
            batch_id=BATCH_ID,
            table=TABLE,
            column=COLUMN,
            min_value=42,
        )

    @pytest.mark.unit
    def test_instantiation_missing_domain_parameters_raises(self):
        with pytest.raises(ValidationError):
            self.Above(min_value=42)


class TestMetricToConfig:
    with mock.patch("great_expectations.metrics.metric.METRIC_REGISTRY", MOCK_METRIC_REGISTRY):

        class Above(Metric, ColumnMap):
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

        metric = self.Above(
            batch_id=BATCH_ID,
            table=TABLE,
            column=COLUMN,
            min_value=42,
        )
        actual_config = metric.to_config()

        assert actual_config.metric_name == expected_config.metric_name
        assert actual_config.metric_domain_kwargs == expected_config.metric_domain_kwargs
        assert actual_config.metric_value_kwargs == expected_config.metric_value_kwargs
        assert isinstance(actual_config.id, MetricConfigurationID)
