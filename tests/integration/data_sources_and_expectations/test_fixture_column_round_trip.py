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

from typing import TYPE_CHECKING

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from tests.integration.conftest import parameterize_batch_for_data_sources
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
        # Deliberately naive. Whether a tz-aware value survives the round trip is a separate
        # question with its own failure mode, and pinning it here would conflate the two.
        MOMENT_COL: pd.to_datetime(
            ["2024-01-01 12:00:00", "2024-01-02 12:00:00", "2024-01-03 12:00:00"]
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
