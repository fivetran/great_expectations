"""Column-to-column row conditions, verified on every canonical data source.

A row condition that compares two columns is rendered by three different engines (pandas, Spark and
SQLAlchemy), each with its own operator semantics. This module is the end-to-end check that they
agree on which rows survive the filter.

Two design choices keep the cases honest:

* Rows are observed through ``ExpectColumnDistinctValuesToEqualSet`` on an id column, so the case
  passes only when the filtered rows' ids are exactly the expected ones. Asserting ``success`` on
  an aggregate alone cannot tell "filtered correctly" from "filtered nothing".
* The expected ids come from a Python oracle that applies the operator to the non-null pairs of the
  same data the backend loaded, never from the code under test. Every case must also expect a
  non-empty proper subset of all ids, so a filter that selects every row, or none, cannot pass.

Column names here avoid the substrings ``AND``, ``OR`` and ``NOT`` (in any case): the atomic
row-condition renderer splits on them even inside a name, which is unrelated to what this module
verifies.
"""

from __future__ import annotations

import operator
from typing import TYPE_CHECKING, Any, Callable, Iterable, Sequence

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.expectations.row_conditions import Column
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import ALL_DATA_SOURCES

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch

# The distinct-values metrics on SQL backends pass a row-conditioned selectable to `select_from`
# without wrapping it in a subquery. SQLAlchemy coerces it and emits this deprecation warning, and
# this repository's pytest configuration turns warnings into errors, so the observation primitive
# below fails on every SQL backend once any row condition is present, literal or column
# comparison. The coercion is correct; only the warning trips the test, so only this message is
# ignored here.
pytestmark = pytest.mark.filterwarnings(
    "ignore:Implicit coercion of SELECT and textual SELECT constructs"
    ":sqlalchemy.exc.SADeprecationWarning"
)

ID_COLUMN = "id"

Comparison = Callable[[Any, Any], Any]
"""A binary comparison. The same function builds the condition (applied to two ``Column`` objects,
which overload the operators) and the oracle (applied to two plain values), so a case names an
operator once and cannot test one while its oracle checks another."""

OPERATORS = [
    pytest.param(operator.eq, id="eq"),
    pytest.param(operator.ne, id="ne"),
    pytest.param(operator.lt, id="lt"),
    pytest.param(operator.le, id="le"),
    pytest.param(operator.gt, id="gt"),
    pytest.param(operator.ge, id="ge"),
]

# Each pair has two rows where left < right, two where left == right and two where left > right, so
# every operator selects a non-empty proper subset. Each operator selects a different id set on
# each pair, so a condition that reads the wrong pair cannot happen to select the right ids. The int
# pair includes (9, 10) and (10, 9), which order the opposite way as text. The float values are
# exactly representable in binary, so equality is not at the mercy of rounding on any backend.
NUMERIC_DATA = pd.DataFrame(
    {
        ID_COLUMN: [1, 2, 3, 4, 5, 6],
        "int_left": [7, 5, 9, 10, -3, 1],
        "int_right": [3, 5, 10, 9, -3, 2],
        "float_left": [2.5, 0.5, -0.5, -4.0, 3.5, -2.5],
        "float_right": [2.5, 1.5, -1.5, -4.0, 0.25, -0.5],
    }
)

NUMERIC_COLUMN_PAIRS = [
    pytest.param(("int_left", "int_right"), id="int"),
    pytest.param(("float_left", "float_right"), id="float"),
]


def all_ids(frame: pd.DataFrame) -> list[int]:
    return [int(row_id) for row_id in frame[ID_COLUMN]]


def expected_ids(frame: pd.DataFrame, left: str, right: str, compare: Comparison) -> list[int]:
    """The ids whose ``left`` and ``right`` values satisfy ``compare``.

    A row with a missing value on either side never satisfies a comparison, so it is skipped
    rather than handed to the operator.
    """
    selected: list[int] = []
    for row in frame.to_dict("records"):
        left_value, right_value = row[left], row[right]
        if pd.isna(left_value) or pd.isna(right_value):
            continue
        if compare(left_value, right_value):
            selected.append(int(row[ID_COLUMN]))
    return selected


def assert_expectation_discriminates(expected: Iterable[int], every_id: Iterable[int]) -> None:
    """Fail unless ``expected`` is a non-empty proper subset of ``every_id``.

    An expectation that names no row, or every row, passes whether or not the filter worked, so it
    proves nothing about the condition.
    """
    expected_set, every_set = set(expected), set(every_id)
    assert expected_set, "expected ids are empty: a filter that selects no rows would pass"
    assert expected_set < every_set, (
        f"expected ids {sorted(expected_set)} are not a proper subset of {sorted(every_set)}: "
        "a filter that selects every row would pass"
    )


def assert_rows_selected(
    batch: Batch,
    row_condition: Any,
    expected: Sequence[int],
    every_id: Iterable[int],
) -> None:
    """Assert that filtering the batch by ``row_condition`` leaves exactly the ``expected`` ids."""
    assert_expectation_discriminates(expected, every_id)
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(
        column=ID_COLUMN,
        value_set=sorted(expected),
        row_condition=row_condition,
    )
    result = batch.validate(expectation)
    assert result.success, (
        f"{row_condition!r} should select ids {sorted(expected)}; "
        f"result={result.result}, exception_info={result.exception_info}"
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "expected",
    [pytest.param([], id="no_rows"), pytest.param([1, 2, 3], id="every_row")],
)
def test_expectation_that_cannot_discriminate_is_rejected(expected: list[int]) -> None:
    with pytest.raises(AssertionError):
        assert_expectation_discriminates(expected, [1, 2, 3])


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=NUMERIC_DATA)
@pytest.mark.parametrize("column_pair", NUMERIC_COLUMN_PAIRS)
@pytest.mark.parametrize("compare", OPERATORS)
def test_operator_over_numeric_columns(
    batch_for_datasource: Batch,
    column_pair: tuple[str, str],
    compare: Comparison,
) -> None:
    left, right = column_pair
    assert_rows_selected(
        batch_for_datasource,
        compare(Column(left), Column(right)),
        expected_ids(NUMERIC_DATA, left, right, compare),
        all_ids(NUMERIC_DATA),
    )
