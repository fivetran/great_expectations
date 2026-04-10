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
from great_expectations.expectations.metrics.util import CaseInsensitiveString

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


_NonStringType.__name__ = "INTEGER"


# ---------------------------------------------------------------------------
# compare_column_type — generic behavior
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


# ===========================================================================
# Dialect-specific type coverage
#
# These tests exercise the actual type names each dialect returns.
# Case-insensitive dialects receive CaseInsensitiveString (as in production).
# isinstance-path dialects receive real SQLAlchemy type instances.
# ===========================================================================


def _ci(s: str) -> CaseInsensitiveString:
    """Shorthand for constructing a CaseInsensitiveString."""
    return CaseInsensitiveString(s)


# ---------------------------------------------------------------------------
# PostgreSQL (case-insensitive path)
# ---------------------------------------------------------------------------


class TestPostgreSQLTypes:
    engine = _StubEngine(GXSqlDialect.POSTGRESQL)

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("CHAR", "CHAR"),
            ("TEXT", "TEXT"),
            ("VARCHAR", "VARCHAR"),
            ("INTEGER", "INTEGER"),
            ("SMALLINT", "SMALLINT"),
            ("BIGINT", "BIGINT"),
            ("TIMESTAMP WITHOUT TIME ZONE", "TIMESTAMP WITHOUT TIME ZONE"),
            ("DATE", "DATE"),
            ("DOUBLE PRECISION", "DOUBLE PRECISION"),
            ("BOOLEAN", "BOOLEAN"),
            ("NUMERIC", "NUMERIC"),
        ],
    )
    def test_type_match(self, actual, expected):
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("integer", "INTEGER"),
            ("INTEGER", "integer"),
            ("Boolean", "boolean"),
            ("timestamp without time zone", "TIMESTAMP WITHOUT TIME ZONE"),
        ],
    )
    def test_case_insensitive(self, actual, expected):
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True

    def test_type_list_match(self):
        success, observed = compare_column_type_list(
            self.engine,
            _ci("TIMESTAMP WITHOUT TIME ZONE"),
            ["TIMESTAMP", "TIMESTAMP WITHOUT TIME ZONE"],  # noqa: E501
        )
        assert success is True
        assert observed == "TIMESTAMP WITHOUT TIME ZONE"


# ---------------------------------------------------------------------------
# Snowflake (case-insensitive path)
# ---------------------------------------------------------------------------


class TestSnowflakeTypes:
    engine = _StubEngine(GXSqlDialect.SNOWFLAKE)

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("STRING", "STRING"),
            ("TEXT", "TEXT"),
            ("CHARACTER", "CHARACTER"),
            ("VARCHAR", "VARCHAR"),
            ("BYTEINT", "BYTEINT"),
            ("TINYINT", "TINYINT"),
            ("INTEGER", "INTEGER"),
            ("BIGINT", "BIGINT"),
            ("FLOAT", "FLOAT"),
            ("DOUBLE", "DOUBLE"),
            ("DECIMAL(38, 0)", "DECIMAL(38, 0)"),
            ("DECIMAL(38,0)", "DECIMAL(38,0)"),
            ("FIXED", "FIXED"),
            ("DEC", "DEC"),
            ("NUMBER", "NUMBER"),
            ("DATE", "DATE"),
            ("TIMESTAMP_NTZ", "TIMESTAMP_NTZ"),
            ("TIMESTAMP_LTZ", "TIMESTAMP_LTZ"),
            ("TIMESTAMP_TZ", "TIMESTAMP_TZ"),
            ("TIME", "TIME"),
            ("VARIANT", "VARIANT"),
            ("VARBINARY", "VARBINARY"),
            ("GEOGRAPHY", "GEOGRAPHY"),
            ("GEOMETRY", "GEOMETRY"),
        ],
    )
    def test_type_match(self, actual, expected):
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("decimal(38, 0)", "DECIMAL(38, 0)"),
            ("timestamp_ntz", "TIMESTAMP_NTZ"),
            ("String", "STRING"),
        ],
    )
    def test_case_insensitive(self, actual, expected):
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True

    def test_type_list_integer_variants(self):
        """Snowflake INTEGER can be reported as DECIMAL(38, 0) depending on column definition."""
        success, _observed = compare_column_type_list(
            self.engine, _ci("DECIMAL(38, 0)"), ["INTEGER", "DECIMAL(38, 0)"]
        )
        assert success is True


# ---------------------------------------------------------------------------
# Databricks (case-insensitive path)
# ---------------------------------------------------------------------------


class TestDatabricksTypes:
    engine = _StubEngine(GXSqlDialect.DATABRICKS)

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("STRING", "STRING"),
            ("INT", "INT"),
            ("BIGINT", "BIGINT"),
            ("SMALLINT", "SMALLINT"),
            ("TINYINT", "TINYINT"),
            ("BOOLEAN", "BOOLEAN"),
            ("FLOAT", "FLOAT"),
            ("DOUBLE", "DOUBLE"),
            ("DECIMAL", "DECIMAL"),
            ("DECIMAL(10, 0)", "DECIMAL(10, 0)"),
            ("DATE", "DATE"),
            ("TIMESTAMP", "TIMESTAMP"),
            ("TIMESTAMP_NTZ", "TIMESTAMP_NTZ"),
        ],
    )
    def test_type_match(self, actual, expected):
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True

    def test_sqla_text_maps_to_string(self):
        """SqlA Text type gets reported as STRING on Databricks."""
        success, _observed = compare_column_type(self.engine, _ci("STRING"), "STRING")
        assert success is True

    def test_type_list_decimal_variants(self):
        success, _observed = compare_column_type_list(
            self.engine, _ci("DECIMAL(10, 0)"), ["DECIMAL", "DECIMAL(10, 0)"]
        )
        assert success is True


# ---------------------------------------------------------------------------
# SQL Server / MS SQL (case-insensitive path)
# ---------------------------------------------------------------------------


class TestSQLServerTypes:
    engine = _StubEngine(GXSqlDialect.SQL_SERVER)

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("INTEGER", "INTEGER"),
            ("BIGINT", "BIGINT"),
            ("SMALLINT", "SMALLINT"),
            ("FLOAT", "FLOAT"),
            ("REAL", "REAL"),
            ("NUMERIC", "NUMERIC"),
            ("DECIMAL", "DECIMAL"),
            ("VARCHAR", "VARCHAR"),
            ("NVARCHAR", "NVARCHAR"),
            ("CHAR", "CHAR"),
            ("BIT", "BIT"),
            ("DATE", "DATE"),
            ("DATETIME", "DATETIME"),
            ("DATETIME2", "DATETIME2"),
        ],
    )
    def test_type_match(self, actual, expected):
        """SQL Server returns type(col['type']).__name__ as CaseInsensitiveString."""
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True

    def test_case_insensitive(self):
        success, _observed = compare_column_type(self.engine, _ci("integer"), "INTEGER")
        assert success is True


# ---------------------------------------------------------------------------
# Trino (case-insensitive path)
# ---------------------------------------------------------------------------


class TestTrinoTypes:
    engine = _StubEngine(GXSqlDialect.TRINO)

    @pytest.mark.parametrize(
        "actual, expected",
        [
            ("INTEGER", "INTEGER"),
            ("BIGINT", "BIGINT"),
            ("SMALLINT", "SMALLINT"),
            ("TINYINT", "TINYINT"),
            ("DOUBLE", "DOUBLE"),
            ("DECIMAL", "DECIMAL"),
            ("VARCHAR", "VARCHAR"),
            ("CHAR", "CHAR"),
            ("BOOLEAN", "BOOLEAN"),
            ("DATE", "DATE"),
            ("TIMESTAMP", "TIMESTAMP"),
        ],
    )
    def test_type_match(self, actual, expected):
        success, _observed = compare_column_type(self.engine, _ci(actual), expected)
        assert success is True


# ---------------------------------------------------------------------------
# SQLite (isinstance path via sa.types)
# ---------------------------------------------------------------------------


class TestSQLiteTypes:
    engine = _StubEngine("sqlite", dialect_module=sa)

    @pytest.mark.parametrize(
        "actual_type, expected_name",
        [
            (sa.types.INTEGER(), "INTEGER"),
            (sa.types.SMALLINT(), "SMALLINT"),
            (sa.types.BIGINT(), "BIGINT"),
            (sa.types.FLOAT(), "FLOAT"),
            (sa.types.NUMERIC(), "NUMERIC"),
            (sa.types.VARCHAR(), "VARCHAR"),
            (sa.types.CHAR(), "CHAR"),
            (sa.types.TEXT(), "TEXT"),
            (sa.types.BOOLEAN(), "BOOLEAN"),
            (sa.types.DATE(), "DATE"),
            (sa.types.DATETIME(), "DATETIME"),
        ],
    )
    def test_type_match(self, actual_type, expected_name):
        success, observed = compare_column_type(self.engine, actual_type, expected_name)
        assert success is True
        assert observed == type(actual_type).__name__

    def test_type_mismatch(self):
        success, _observed = compare_column_type(self.engine, sa.types.INTEGER(), "VARCHAR")
        assert success is False

    def test_type_list_match(self):
        success, _observed = compare_column_type_list(
            self.engine, sa.types.INTEGER(), ["VARCHAR", "INTEGER"]
        )
        assert success is True

    def test_type_list_no_match(self):
        success, _observed = compare_column_type_list(
            self.engine, sa.types.INTEGER(), ["VARCHAR", "TEXT"]
        )
        assert success is False


# ---------------------------------------------------------------------------
# MySQL (isinstance path via sa.types)
# ---------------------------------------------------------------------------


class TestMySQLTypes:
    engine = _StubEngine("mysql", dialect_module=sa)

    @pytest.mark.parametrize(
        "actual_type, expected_name",
        [
            (sa.types.INTEGER(), "INTEGER"),
            (sa.types.SMALLINT(), "SMALLINT"),
            (sa.types.BIGINT(), "BIGINT"),
            (sa.types.FLOAT(), "FLOAT"),
            (sa.types.DECIMAL(), "DECIMAL"),
            (sa.types.VARCHAR(), "VARCHAR"),
            (sa.types.TEXT(), "TEXT"),
            (sa.types.BOOLEAN(), "BOOLEAN"),
            (sa.types.DATE(), "DATE"),
            (sa.types.DATETIME(), "DATETIME"),
        ],
    )
    def test_type_match(self, actual_type, expected_name):
        success, observed = compare_column_type(self.engine, actual_type, expected_name)
        assert success is True
        assert observed == type(actual_type).__name__


# ---------------------------------------------------------------------------
# CaseInsensitiveString — quoted behavior
# ---------------------------------------------------------------------------


class TestCaseInsensitiveStringQuotedBehavior:
    """Quoted CaseInsensitiveString values should require exact match."""

    engine = _StubEngine(GXSqlDialect.POSTGRESQL)

    def test_quoted_requires_exact_match(self):
        quoted = CaseInsensitiveString('"MyType"')
        success, _observed = compare_column_type(self.engine, quoted, '"MyType"')
        assert success is True

    def test_quoted_rejects_case_mismatch(self):
        quoted = CaseInsensitiveString('"MyType"')
        success, _observed = compare_column_type(self.engine, quoted, '"mytype"')
        assert success is False

    def test_unquoted_accepts_case_mismatch(self):
        unquoted = CaseInsensitiveString("MyType")
        success, _observed = compare_column_type(self.engine, unquoted, "mytype")
        assert success is True

    def test_quoted_in_type_list(self):
        quoted = CaseInsensitiveString('"MyType"')
        success, _observed = compare_column_type_list(self.engine, quoted, ['"mytype"', '"MyType"'])
        assert success is True

    def test_quoted_list_uses_lower_not_eq(self):
        """The type-list path uses .lower() comparison, so quoted semantics
        are not preserved — unlike the scalar path which uses __eq__."""
        quoted = CaseInsensitiveString('"MyType"')
        success, _observed = compare_column_type_list(self.engine, quoted, ['"mytype"', '"OTHER"'])
        # .lower() matches even though CaseInsensitiveString.__eq__ would not
        assert success is True
