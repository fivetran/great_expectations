from typing import Final, Literal

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    SQL_DATA_SOURCES,
)

NAME: Final[Literal["test_table"]] = "quoted_id_test"


def single_quote(name: str) -> str:
    return f"'{name}'"


def double_quote(name: str) -> str:
    return f'"{name}"'


def back_tick(name: str) -> str:
    return f"`{name}`"


UNQUOTED_UPPER = "UNQUOTED_UPPER"
UNQUOTED_LOWER = "unquoted_lower"
UNQUOTED_MIXED = "UnquotedMixed"
UNQUOTED_DOTS = "unquoted.with.dots"


UNQUOTED_SPACES = "unquoted with dots"
DOUBLE_QUOTED_UPPER = '"DOUBLE_QUOTED_UPPER"'
DOUBLE_QUOTED_LOWER = '"double_quoted_lower"'
DOUBLE_QUOTED_MIXED = '"DoubleQuotedMixed"'
DOUBLE_QUOTED_DOTS = '"double.quoted.with.dots"'
SINGLE_QUOTED_UPPER = "'SINGLE_QUOTED_UPPER'"
SINGLE_QUOTED_LOWER = "'single_quoted_lower'"
SINGLE_QUOTED_MIXED = "'SingleQuotedMixed'"
SINGLE_QUOTED_DOTS = "'single.quoted.with.dots'"
TICK_QUOTED_UPPER = "`TICK_QUOTED_UPPER`"
TICK_QUOTED_LOWER = "`tick_quoted_lower`"
TICK_QUOTED_MIXED = "`TickQuotedMixed`"
TICK_QUOTED_DOTS = "`tick.quoted.with.dots`"


DATA = pd.DataFrame(
    {
        UNQUOTED_LOWER: [1, 2, 3],
        UNQUOTED_UPPER: [1, 2, 3],
        UNQUOTED_MIXED: [1, 2, 3],
        UNQUOTED_DOTS: [1, 2, 3],
        # UNQUOTED_SPACES: [1, 2, 3],
        # SINGLE_QUOTED_LOWER: [1, 2, 3],
        # SINGLE_QUOTED_UPPER: [1, 2, 3],
        # SINGLE_QUOTED_MIXED: [1, 2, 3],
        # SINGLE_QUOTED_DOTS: [1, 2, 3],
        # DOUBLE_QUOTED_LOWER: [1, 2, 3],
        # DOUBLE_QUOTED_UPPER: [1, 2, 3],
        # DOUBLE_QUOTED_MIXED: [1, 2, 3],
        # DOUBLE_QUOTED_DOTS: [1, 2, 3],
        # TICK_QUOTED_LOWER: [1, 2, 3],
        # TICK_QUOTED_UPPER: [1, 2, 3],
        # TICK_QUOTED_MIXED: [1, 2, 3],
        # TICK_QUOTED_DOTS: [1, 2, 3],
    }
)


@pytest.mark.parametrize(
    "col_name",
    [
        UNQUOTED_UPPER,
        UNQUOTED_LOWER,
        UNQUOTED_MIXED,
        UNQUOTED_DOTS,
        # UNQUOTED_SPACES,
        # DOUBLE_QUOTED_UPPER,
        # DOUBLE_QUOTED_LOWER,
        # DOUBLE_QUOTED_MIXED,
        # DOUBLE_QUOTED_DOTS,
        # SINGLE_QUOTED_UPPER,
        # SINGLE_QUOTED_LOWER,
        # SINGLE_QUOTED_MIXED,
        # SINGLE_QUOTED_DOTS,
        # TICK_QUOTED_UPPER,
        # TICK_QUOTED_LOWER,
        # TICK_QUOTED_MIXED,
        # TICK_QUOTED_DOTS,
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_column_name_allowed_formats(batch_for_datasource: Batch, col_name: str) -> None:
    """Is this testing anything?"""
    expectation = gxe.ExpectColumnValuesToBeBetween(column=col_name, min_value=0, max_value=10)
    result = batch_for_datasource.validate(expectation)
    assert result.success
