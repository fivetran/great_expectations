from __future__ import annotations

import logging
import os
import pathlib
import uuid
from typing import TYPE_CHECKING, Final, Generator, Iterator

import numpy as np
import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.exceptions as gx_exceptions
from great_expectations.checkpoint import Checkpoint
from great_expectations.core import ExpectationSuite
from great_expectations.data_context import CloudDataContext
from great_expectations.execution_engine import (
    SparkDFExecutionEngine,
)
from great_expectations.expectations import ExpectColumnValuesToNotBeNull

if TYPE_CHECKING:
    from great_expectations.compatibility import pyspark

LOGGER: Final = logging.getLogger("tests")


@pytest.fixture(scope="package")
def context() -> CloudDataContext:
    context = gx.get_context(
        mode="cloud",
        cloud_base_url=os.environ.get("GX_CLOUD_BASE_URL"),
        cloud_organization_id=os.environ.get("GX_CLOUD_ORGANIZATION_ID"),
        cloud_access_token=os.environ.get("GX_CLOUD_ACCESS_TOKEN"),
    )
    assert isinstance(context, CloudDataContext)
    return context


@pytest.fixture(scope="module")
def test_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": [1, 2, 3, 4],
        },
    )


@pytest.fixture(scope="module")
def datasource_name(
    context: CloudDataContext,
) -> Iterator[str]:
    datasource_name = f"ds_{uuid.uuid4().hex}"
    yield datasource_name
    # if the test was skipped, we may not have a datasource to clean up
    # in that case, we create one simply to test get and delete
    try:
        _ = context.data_sources.get(name=datasource_name)
    except KeyError:
        _ = context.data_sources.add_pandas(name=datasource_name)
        context.data_sources.get(name=datasource_name)
    context.delete_datasource(name=datasource_name)
    with pytest.raises(KeyError):
        _ = context.data_sources.get(name=datasource_name)


@pytest.fixture(scope="module")
def expectation_suite(
    context: CloudDataContext,
) -> Iterator[ExpectationSuite]:
    """This ExpectationSuite is shared by each E2E test, so its expected that the data
    used by each test follows the same shape."""
    expectation_suite_name = f"es_{uuid.uuid4().hex}"
    context.suites.add(
        ExpectationSuite(
            name=expectation_suite_name,
            expectations=[ExpectColumnValuesToNotBeNull(column="name", mostly=1)],
        )
    )
    yield context.suites.get(name=expectation_suite_name)
    context.suites.delete(expectation_suite_name)
    with pytest.raises(gx_exceptions.DataContextError):
        context.suites.get(name=expectation_suite_name)


@pytest.fixture(scope="module")
def checkpoint(
    context: CloudDataContext,
) -> Generator[Checkpoint, None, None]:
    """This Checkpoint is used by each E2E test. It's expected that each test
    will override its list of validation definitions within the test module."""
    checkpoint_name = f"E2E Test Checkpoint {uuid.uuid4().hex}"

    checkpoint = Checkpoint(name=checkpoint_name, validation_definitions=[])
    checkpoint = context.checkpoints.add(checkpoint=checkpoint)
    yield checkpoint
    context.checkpoints.delete(name=checkpoint_name)

    with pytest.raises(gx_exceptions.DataContextError):
        context.checkpoints.get(name=checkpoint_name)


@pytest.fixture(scope="module")
def tmp_path(tmp_path_factory) -> pathlib.Path:
    return tmp_path_factory.mktemp("project")


def construct_spark_df_from_pandas(
    spark_session: pyspark.SparkSession,
    pandas_df: pd.DataFrame,
) -> pyspark.DataFrame:
    spark_df = spark_session.createDataFrame(
        [
            tuple(
                None if isinstance(x, (float, int)) and np.isnan(x) else x for x in record.tolist()
            )
            for record in pandas_df.to_records(index=False)
        ],
        pandas_df.columns.tolist(),
    )
    return spark_df


@pytest.fixture(scope="module")
def spark_session() -> pyspark.SparkSession:
    from great_expectations.compatibility import pyspark

    if pyspark.SparkSession:  # type: ignore[truthy-function] # FIXME CoP
        return SparkDFExecutionEngine.get_or_create_spark_session()

    raise ValueError("spark tests are requested, but pyspark is not installed")
