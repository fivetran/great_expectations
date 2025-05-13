import pytest

import great_expectations.exceptions as gx_exceptions
import great_expectations.expectations as gxe
from great_expectations.compatibility import sqlalchemy
from great_expectations.execution_engine.sqlite_execution_engine import SqliteExecutionEngine
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.expectations.registry import (
    get_expectation_impl,
    get_metric_provider,
    get_sqlalchemy_metric_provider,
)

# module level markers
pytestmark = pytest.mark.unit


def test_registry_basics():
    expectation = get_expectation_impl("expect_column_values_to_be_in_set")
    assert expectation == gxe.ExpectColumnValuesToBeInSet


def test_registry_from_configuration():
    configuration = ExpectationConfiguration(
        type="expect_column_values_to_be_in_set",
        kwargs={"column": "PClass", "value_set": [1, 2, 3]},
    )
    assert configuration._get_expectation_impl() == gxe.ExpectColumnValuesToBeInSet


def test_registry_raises_error_when_invalid_expectation_requested():
    with pytest.raises(gx_exceptions.ExpectationNotFoundError):
        get_expectation_impl("expect_something_in_beta")


def test_get_metric_provider_for_sqlalchemy_engine_subclass():
    # This is a regression test to show that we can register a metric for
    # a sqlalchemy engine subclass and it doesn't overwrite the default metric.
    metric_name = "column.standard_deviation.aggregate_fn"

    sa_metric_provider, sa_metric_provider_fn = get_sqlalchemy_metric_provider(
        metric_name,
    )

    # get the sqlite metric provider
    sqlite_metric_provider, sqlite_metric_provider_fn = get_metric_provider(
        metric_name,
        SqliteExecutionEngine(engine=sqlalchemy.create_engine("sqlite://")),
    )
    assert sa_metric_provider is not None
    assert sqlite_metric_provider is not None
    assert sa_metric_provider != sqlite_metric_provider
    assert sa_metric_provider_fn is not None
    assert sqlite_metric_provider_fn is not None
    assert sa_metric_provider_fn != sqlite_metric_provider_fn
