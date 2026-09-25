from typing import Sequence

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    PandasDataFrameDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig

COLUMN = "event_at"

# column_values.increasing and column_values.decreasing register a pandas and a Spark
# provider only, and Spark's parallel read gives these row-order-dependent metrics no
# ordering guarantee, so pandas is the engine these cases can assert against.
DATA_SOURCES: Sequence[DataSourceTestConfig] = [PandasDataFrameDatasourceTestConfig()]

ASCENDING_DATETIMES = pd.DataFrame(
    {COLUMN: pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])}
)
DESCENDING_DATETIMES = pd.DataFrame(
    {COLUMN: pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-01"])}
)
# The middle row goes backwards, so it is the one value that breaks the order.
ASCENDING_DATETIMES_WITH_ONE_STEP_BACK = pd.DataFrame(
    {COLUMN: pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-02"])}
)
# A repeated timestamp is in order for the default comparison and out of order for
# strictly=True.
ASCENDING_DATETIMES_WITH_A_TIE = pd.DataFrame(
    {COLUMN: pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"])}
)


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=ASCENDING_DATETIMES,
)
def test_increasing_datetime_column_passes(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(gxe.ExpectColumnValuesToBeIncreasing(column=COLUMN))

    assert result.success
    assert result.result["unexpected_count"] == 0


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=ASCENDING_DATETIMES,
)
def test_strictly_increasing_datetime_column_passes(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeIncreasing(column=COLUMN, strictly=True)
    )

    assert result.success
    assert result.result["unexpected_count"] == 0


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=ASCENDING_DATETIMES_WITH_ONE_STEP_BACK,
)
def test_datetime_column_that_goes_backwards_fails(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeIncreasing(column=COLUMN),
        result_format=ResultFormat.COMPLETE,
    )

    assert not result.success
    assert result.result["unexpected_count"] == 1


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=ASCENDING_DATETIMES_WITH_A_TIE,
)
def test_repeated_datetime_fails_only_when_strictly_increasing(
    batch_for_datasource: Batch,
) -> None:
    assert batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeIncreasing(column=COLUMN)
    ).success

    strict_result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeIncreasing(column=COLUMN, strictly=True),
        result_format=ResultFormat.COMPLETE,
    )

    assert not strict_result.success
    assert strict_result.result["unexpected_count"] == 1


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=DESCENDING_DATETIMES,
)
def test_decreasing_datetime_column_passes(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(gxe.ExpectColumnValuesToBeDecreasing(column=COLUMN))

    assert result.success
    assert result.result["unexpected_count"] == 0


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=DESCENDING_DATETIMES,
)
def test_strictly_decreasing_datetime_column_passes(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeDecreasing(column=COLUMN, strictly=True)
    )

    assert result.success
    assert result.result["unexpected_count"] == 0


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES,
    data=ASCENDING_DATETIMES,
)
def test_ascending_datetime_column_is_not_decreasing(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeDecreasing(column=COLUMN),
        result_format=ResultFormat.COMPLETE,
    )

    assert not result.success
    assert result.result["unexpected_count"] == 2
