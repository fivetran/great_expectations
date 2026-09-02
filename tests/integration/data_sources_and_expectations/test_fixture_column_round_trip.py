"""What a fixture frame declares is what the backend must store.

Every assertion in this directory rests on an unstated assumption: that the values a test
declares in a pandas frame are the values the backend holds once the harness has written them.
Where that fails it fails silently -- the DDL is valid, no error is raised, and an assertion
about a value quietly becomes an assertion about a different value.

The two shapes below are the ones that have actually broken. A decimal type carrying no scale
is read by several servers as scale zero, which rounds every fractional value to an integer on
write. A datetime type that a server does not have makes the table impossible to create at all.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.data_source_lists import (
    SPARK_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import ALL_DATA_SOURCES

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch

FRACTIONAL_COL = "fractional_value"
MOMENT_COL = "moment"

# A fractional part that survives no rounding: every value here differs from its nearest
# integer, so a backend storing these at scale zero cannot coincidentally agree.
ROUND_TRIP_DATA = pd.DataFrame(
    {
        FRACTIONAL_COL: [1.5, 2.25, -3.75],
        # Plain Python datetimes in an object column, deliberately, rather than a pandas
        # datetime64 column. Two backends cannot take a pandas timestamp as a bound parameter
        # at all, and one infers an empty struct for it rather than a time, so a frame built the
        # convenient way would fail on them for reasons that have nothing to do with the column
        # type under test here. Naive rather than tz-aware for the same reason: whether a
        # timezone survives the trip is a separate question with its own failure mode.
        MOMENT_COL: pd.Series(
            [
                datetime(2024, 1, 1, 12, 0, 0),  # noqa: DTZ001
                datetime(2024, 1, 2, 12, 0, 0),  # noqa: DTZ001
                datetime(2024, 1, 3, 12, 0, 0),  # noqa: DTZ001
            ],
            dtype=object,
        ),
    }
)


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=ROUND_TRIP_DATA)
def test_a_fractional_value_is_stored_as_declared(batch_for_datasource: Batch) -> None:
    """The largest value is 2.25. A backend that rounds to scale zero observes 2."""
    result = batch_for_datasource.validate(
        gxe.ExpectColumnMaxToBeBetween(column=FRACTIONAL_COL, min_value=2.25, max_value=2.25),
        result_format=ResultFormat.COMPLETE,
    )

    observed = result.result.get("observed_value")
    assert result.success, (
        f"the maximum of {FRACTIONAL_COL} came back as {observed!r} rather than 2.25, so the "
        "column's declared values are not the values this backend stored"
    )


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=ROUND_TRIP_DATA)
def test_a_datetime_column_can_be_created_and_read(batch_for_datasource: Batch) -> None:
    """Reaching this assertion at all is most of the point: a backend whose type vocabulary
    does not include the declared datetime type fails during table creation, before any
    expectation runs.
    """
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToNotBeNull(column=MOMENT_COL),
        result_format=ResultFormat.COMPLETE,
    )

    assert result.success


# A pandas-native datetime column, which is what a frame built the convenient way holds. The
# column above deliberately avoids this shape so that its own assertions are about the column
# type the backend was given; this one exists to pin that the convenient shape works too.
PANDAS_TIMESTAMP_DATA = pd.DataFrame(
    {MOMENT_COL: pd.to_datetime(["2024-01-01 12:00:00", "2024-01-02 12:00:00"])}
)


@parameterize_batch_for_data_sources(
    data_source_configs=SPARK_DATA_SOURCES, data=PANDAS_TIMESTAMP_DATA
)
def test_a_pandas_timestamp_column_is_written_as_a_time(batch_for_datasource: Batch) -> None:
    """Spark infers a column's type from the values when a test declares none, and matches on
    exact type. A pandas timestamp is a subclass rather than the type it looks for, so it reads
    as an empty struct -- which no file format can write, and which fails during setup rather
    than as an assertion. Reaching this assertion at all is the substance of the test.
    """
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToNotBeNull(column=MOMENT_COL),
        result_format=ResultFormat.COMPLETE,
    )

    assert result.success
