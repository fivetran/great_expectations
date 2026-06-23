import logging
from typing import Any

import pytest

import great_expectations as gx
from great_expectations.compatibility.pyspark import ConnectDataFrame, Row, SparkConnectSession
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.exceptions.exceptions import BuildBatchRequestError

DISTINCT_VALUES_DATAFRAME_VALUES = ["red", "green", "blue"]

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.spark_connect

DATAFRAME_VALUES = [1, 2, 3]


@pytest.fixture
def spark_validation_definition(
    ephemeral_context_with_defaults: AbstractDataContext,
) -> ValidationDefinition:
    context = ephemeral_context_with_defaults
    bd = (
        context.data_sources.add_spark(name="spark-connect-ds")
        .add_dataframe_asset(name="spark-connect-asset")
        .add_batch_definition_whole_dataframe(name="spark-connect-bd")
    )
    suite = context.suites.add(
        gx.ExpectationSuite(
            name="spark-connect-suite",
            expectations=[
                gx.expectations.ExpectColumnValuesToBeInSet(
                    column="column",
                    value_set=DATAFRAME_VALUES,
                ),
            ],
        )
    )
    return context.validation_definitions.add(
        gx.ValidationDefinition(name="spark-connect-vd", suite=suite, data=bd)
    )


def test_spark_connect(
    spark_connect_session: SparkConnectSession,
    spark_validation_definition: ValidationDefinition,
):
    df = spark_connect_session.createDataFrame(
        [Row(column=x) for x in DATAFRAME_VALUES],
    )
    assert isinstance(df, ConnectDataFrame)

    results = spark_validation_definition.run(batch_parameters={"dataframe": df})

    assert results.success


@pytest.mark.parametrize("not_a_dataframe", [None, 1, "string", 1.0, True])
def test_error_messages_if_we_get_an_invalid_dataframe(
    not_a_dataframe: Any,
    spark_validation_definition: ValidationDefinition,
):
    with pytest.raises(
        BuildBatchRequestError, match=r"Cannot build batch request without a Spark DataFrame."
    ):
        spark_validation_definition.run(batch_parameters={"dataframe": not_a_dataframe})


@pytest.mark.parametrize(
    "expectation,value_set,expected_success",
    [
        (
            gx.expectations.ExpectColumnDistinctValuesToEqualSet,
            DISTINCT_VALUES_DATAFRAME_VALUES,
            True,
        ),
        (
            gx.expectations.ExpectColumnDistinctValuesToEqualSet,
            ["red", "green"],
            False,
        ),
        (
            gx.expectations.ExpectColumnDistinctValuesToContainSet,
            ["red", "green"],
            True,
        ),
        (
            gx.expectations.ExpectColumnDistinctValuesToContainSet,
            ["red", "green", "blue", "yellow"],
            False,
        ),
        (
            gx.expectations.ExpectColumnDistinctValuesToBeInSet,
            DISTINCT_VALUES_DATAFRAME_VALUES,
            True,
        ),
        (
            gx.expectations.ExpectColumnDistinctValuesToBeInSet,
            ["red", "green"],
            False,
        ),
    ],
)
def test_distinct_values_expectations_spark_connect(
    spark_connect_session: SparkConnectSession,
    ephemeral_context_with_defaults: AbstractDataContext,
    expectation: type,
    value_set: list,
    expected_success: bool,
) -> None:
    """Regression test: distinct-value metrics must not call .rdd (unsupported in Spark Connect)."""
    df = spark_connect_session.createDataFrame(
        [Row(column=v) for v in DISTINCT_VALUES_DATAFRAME_VALUES],
    )
    assert isinstance(df, ConnectDataFrame)

    context = ephemeral_context_with_defaults
    bd = (
        context.data_sources.add_spark(
            name=f"spark-connect-ds-{expectation.__name__}-{expected_success}"
        )
        .add_dataframe_asset(name="asset")
        .add_batch_definition_whole_dataframe(name="bd")
    )
    suite = context.suites.add(
        gx.ExpectationSuite(
            name=f"suite-{expectation.__name__}-{expected_success}",
            expectations=[expectation(column="column", value_set=value_set)],
        )
    )
    vd = context.validation_definitions.add(
        gx.ValidationDefinition(
            name=f"vd-{expectation.__name__}-{expected_success}", suite=suite, data=bd
        )
    )

    results = vd.run(batch_parameters={"dataframe": df})

    assert results.success is expected_success


def test_spark_connect_with_spark_connect_session_factory_method(
    spark_validation_definition: ValidationDefinition,
):
    """This test demonstrates that SparkConnectionSession can be used to create a session.

    This test is being added because in some scenarios, this appeared to fail, but it was
    the result of other active spark sessions.
    """
    spark_connect_session = SparkConnectSession.builder.remote("sc://localhost:15002").getOrCreate()
    assert isinstance(spark_connect_session, SparkConnectSession)
    df = spark_connect_session.createDataFrame(
        [Row(column=x) for x in DATAFRAME_VALUES],
    )

    results = spark_validation_definition.run(batch_parameters={"dataframe": df})

    assert results.success
