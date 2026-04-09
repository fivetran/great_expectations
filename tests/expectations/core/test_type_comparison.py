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
# Helpers for mocking execution engines
# ---------------------------------------------------------------------------


def _mock_engine(mocker, dialect_name):
    """Create a mock SqlAlchemyExecutionEngine with the given dialect_name."""
    engine = mocker.MagicMock()
    type(engine).dialect_name = mocker.PropertyMock(return_value=dialect_name)
    return engine


# ---------------------------------------------------------------------------
# compare_column_type — case-insensitive path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeCaseInsensitive:
    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_string_match(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        success, observed = compare_column_type(engine, "INTEGER", "INTEGER")
        assert success is True
        assert observed == "INTEGER"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_case_insensitive_match(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        success, _observed = compare_column_type(engine, "integer", "integer")
        assert success is True

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_mismatch(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        success, observed = compare_column_type(engine, "INTEGER", "VARCHAR")
        assert success is False
        assert observed == "INTEGER"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_non_string_fallback(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        mock_type = mocker.MagicMock()
        mock_type.__str__ = lambda self: "INTEGER"
        type(mock_type).__name__ = "INTEGER"
        success, _observed = compare_column_type(engine, mock_type, "integer")
        assert success is True


# ---------------------------------------------------------------------------
# compare_column_type — isinstance path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeByClass:
    def test_match(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        success, observed = compare_column_type(engine, sa.types.INTEGER(), "INTEGER")
        assert success is True
        assert observed == "INTEGER"

    def test_mismatch(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        success, _observed = compare_column_type(engine, sa.types.INTEGER(), "VARCHAR")
        assert success is False

    def test_unrecognized_type(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        success, _observed = compare_column_type(engine, sa.types.INTEGER(), "NONEXISTENT_TYPE")
        assert success is False

    def test_observed_value_is_class_name(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        _success, observed = compare_column_type(engine, sa.types.INTEGER(), "INTEGER")
        assert observed == "INTEGER"


# ---------------------------------------------------------------------------
# compare_column_type_list — case-insensitive path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeListCaseInsensitive:
    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_match_in_list(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        success, observed = compare_column_type_list(engine, "INTEGER", ["VARCHAR", "INTEGER"])
        assert success is True
        assert observed == "INTEGER"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_no_match_in_list(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        success, observed = compare_column_type_list(engine, "BOOLEAN", ["VARCHAR", "INTEGER"])
        assert success is False
        assert observed == "BOOLEAN"

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_case_insensitive_list_match(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        success, _observed = compare_column_type_list(engine, "integer", ["VARCHAR", "INTEGER"])
        assert success is True

    @pytest.mark.parametrize("dialect", list(CASE_INSENSITIVE_DIALECTS))
    def test_non_string_type(self, mocker, dialect):
        engine = _mock_engine(mocker, dialect)
        mock_type = mocker.MagicMock()
        type(mock_type).__name__ = "INTEGER"
        success, observed = compare_column_type_list(engine, mock_type, ["VARCHAR", "INTEGER"])
        assert success is True
        assert observed == "INTEGER"


# ---------------------------------------------------------------------------
# compare_column_type_list — isinstance path
# ---------------------------------------------------------------------------


class TestCompareColumnTypeListByClass:
    def test_match_in_list(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        success, _observed = compare_column_type_list(
            engine, sa.types.INTEGER(), ["VARCHAR", "INTEGER"]
        )
        assert success is True

    def test_no_match_in_list(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        success, _observed = compare_column_type_list(
            engine, sa.types.INTEGER(), ["VARCHAR", "TEXT"]
        )
        assert success is False

    def test_observed_value_is_class_name(self, mocker):
        engine = _mock_engine(mocker, "sqlite")
        engine.dialect_module = sa
        _success, observed = compare_column_type_list(engine, sa.types.INTEGER(), ["INTEGER"])
        assert observed == "INTEGER"
