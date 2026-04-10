"""Unit tests for great_expectations.expectations.core.type_comparison."""

from __future__ import annotations

import pytest

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from great_expectations.expectations.core.type_comparison import (
    CASE_INSENSITIVE_DIALECTS,
    compare_column_type,
    compare_column_type_list,
    native_type_type_map,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# CASE_INSENSITIVE_DIALECTS
# ---------------------------------------------------------------------------


class TestCaseInsensitiveDialects:
    def test_contains_expected_dialects(self):
        expected = {
            GXSqlDialect.DATABRICKS,
            GXSqlDialect.POSTGRESQL,
            GXSqlDialect.SNOWFLAKE,
            GXSqlDialect.SQL_SERVER,
            GXSqlDialect.TRINO,
        }
        assert expected == CASE_INSENSITIVE_DIALECTS

    def test_is_frozenset(self):
        assert isinstance(CASE_INSENSITIVE_DIALECTS, frozenset)


# ---------------------------------------------------------------------------
# native_type_type_map
# ---------------------------------------------------------------------------


class TestNativeTypeTypeMap:
    @pytest.mark.parametrize(
        "type_str, expected",
        [
            ("none", (type(None),)),
            ("None", (type(None),)),
            ("bool", (bool,)),
            ("int", (int,)),
            ("long", (int,)),
            ("float", (float,)),
            ("bytes", (bytes,)),
            ("complex", (complex,)),
            ("str", (str,)),
            ("string_types", (str,)),
            ("list", (list,)),
            ("dict", (dict,)),
        ],
    )
    def test_known_types(self, type_str, expected):
        assert native_type_type_map(type_str) == expected

    def test_unicode_returns_none(self):
        assert native_type_type_map("unicode") is None

    def test_unrecognized_returns_none(self):
        assert native_type_type_map("some_unknown_type") is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubEngine:
    """Lightweight stub to avoid mutating shared MagicMock class metadata."""

    def __init__(self, dialect_name, dialect_module=None):
        self.dialect_name = dialect_name
        self.dialect_module = dialect_module


class _NonStringType:
    """Stub for a non-string column type with controllable __str__ and __name__."""

    def __str__(self):
        return "INTEGER"


# Ensure type(instance).__name__ returns "INTEGER" — this is a per-class
# attribute, not per-instance, so we need a dedicated class.
_NonStringType.__name__ = "INTEGER"


# ---------------------------------------------------------------------------
# compare_column_type — case-insensitive path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeCaseInsensitive:
    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_string_match(self, dialect):
        engine = _StubEngine(dialect)
        success, observed = compare_column_type(engine, "INTEGER", "INTEGER")
        assert success is True
        assert observed == "INTEGER"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_case_insensitive_match(self, dialect):
        engine = _StubEngine(dialect)
        success, _observed = compare_column_type(engine, "INTEGER", "integer")
        assert success is True

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_mismatch(self, dialect):
        engine = _StubEngine(dialect)
        success, observed = compare_column_type(engine, "INTEGER", "VARCHAR")
        assert success is False
        assert observed == "INTEGER"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_non_string_fallback(self, dialect):
        engine = _StubEngine(dialect)
        mock_type = _NonStringType()
        success, _observed = compare_column_type(engine, mock_type, "integer")
        assert success is True


# ---------------------------------------------------------------------------
# compare_column_type — isinstance path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeByClass:
    def test_match(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        success, observed = compare_column_type(engine, sa.types.INTEGER(), "INTEGER")
        assert success is True
        assert observed == "INTEGER"

    def test_mismatch(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        success, _observed = compare_column_type(engine, sa.types.INTEGER(), "VARCHAR")
        assert success is False

    def test_unrecognized_type(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        success, _observed = compare_column_type(engine, sa.types.INTEGER(), "NONEXISTENT_TYPE")
        assert success is False

    def test_observed_value_is_class_name(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        _success, observed = compare_column_type(engine, sa.types.INTEGER(), "INTEGER")
        assert observed == "INTEGER"


# ---------------------------------------------------------------------------
# compare_column_type_list — case-insensitive path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeListCaseInsensitive:
    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_match_in_list(self, dialect):
        engine = _StubEngine(dialect)
        success, observed = compare_column_type_list(engine, "INTEGER", ["VARCHAR", "INTEGER"])
        assert success is True
        assert observed == "INTEGER"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_no_match_in_list(self, dialect):
        engine = _StubEngine(dialect)
        success, observed = compare_column_type_list(engine, "BOOLEAN", ["VARCHAR", "INTEGER"])
        assert success is False
        assert observed == "BOOLEAN"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_case_insensitive_list_match(self, dialect):
        engine = _StubEngine(dialect)
        success, _observed = compare_column_type_list(engine, "integer", ["VARCHAR", "INTEGER"])
        assert success is True

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_non_string_type(self, dialect):
        engine = _StubEngine(dialect)
        mock_type = _NonStringType()
        success, observed = compare_column_type_list(engine, mock_type, ["VARCHAR", "INTEGER"])
        assert success is True
        assert observed == "INTEGER"


# ---------------------------------------------------------------------------
# compare_column_type_list — isinstance path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeListByClass:
    def test_match_in_list(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        success, _observed = compare_column_type_list(
            engine, sa.types.INTEGER(), ["VARCHAR", "INTEGER"]
        )
        assert success is True

    def test_no_match_in_list(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        success, _observed = compare_column_type_list(
            engine, sa.types.INTEGER(), ["VARCHAR", "TEXT"]
        )
        assert success is False

    def test_observed_value_is_class_name(self):
        engine = _StubEngine("sqlite", dialect_module=sa)
        _success, observed = compare_column_type_list(engine, sa.types.INTEGER(), ["INTEGER"])
        assert observed == "INTEGER"
