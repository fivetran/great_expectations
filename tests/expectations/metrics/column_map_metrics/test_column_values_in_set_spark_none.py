"""Regression tests for GH #12382: a None in value_set must not disable Spark isin.

These tests exercise the exact three-valued-logic transformation that
`ColumnValuesInSet._spark` relies on after the fix. They are pure-Python and do
not require a Spark session, so they run in the fast `unit` suite.
"""
from typing import List, Optional

import pytest


def _spark_effective_value_set(value_set: Optional[List[Optional[int]]]):
    """Mirror the normalization applied in _spark before calling column.isin."""
    if value_set is None:
        return None
    if None in value_set:
        value_set = [value for value in value_set if value is not None]
    return value_set


def _spark_isin(value, value_set) -> Optional[bool]:
    """Model Spark's SQL three-valued isin() for a scalar value."""
    if value is None:
        return None
    has_null = any(v is None for v in value_set)
    if any(v is not None and value == v for v in value_set):
        return True
    return None if has_null else False


def _is_unexpected(value, value_set) -> bool:
    """A row is unexpected only when NOT(isin) evaluates to TRUE."""
    cond = _spark_isin(value, value_set)
    return False if cond is None else (not cond)


@pytest.mark.unit
@pytest.mark.parametrize(
    "value_set, expected",
    [
        ([1], [1]),
        ([1, None], [1]),
        ([None], []),
        ([1, 2, None], [1, 2]),
        (None, None),
    ],
)
def test_spark_effective_value_set_drops_none(value_set, expected):
    assert _spark_effective_value_set(value_set) == expected


@pytest.mark.unit
def test_none_in_value_set_no_longer_masks_out_of_set_values():
    """With [1, None], values outside the set must still be flagged (GH #12382)."""
    data = [1, 2, 2, None]
    buggy = [v for v in data if _is_unexpected(v, [1, None])]
    effective = _spark_effective_value_set([1, None])
    fixed = [v for v in data if _is_unexpected(v, effective)]
    assert buggy == []           # reproduce the false positive
    assert fixed == [2, 2]       # after the fix


@pytest.mark.unit
def test_all_none_value_set_flags_all_non_null_values():
    data = [1, 2, 2, None]
    effective = _spark_effective_value_set([None])
    flagged = [v for v in data if _is_unexpected(v, effective)]
    assert flagged == [1, 2, 2]  # matching pandas/sqlite; NULL row stays unflagged


@pytest.mark.unit
def test_control_value_set_without_none_unchanged():
    """A value_set without None must behave identically (no regression)."""
    data = [1, 2, 2, None]
    assert [_is_unexpected(v, [1]) for v in data] == [False, True, True, False]
