import pytest

from great_expectations.execution_engine.sqlalchemy_dialect import (
    GXSqlDialect,
    _strip_quotes,
    quote_str,
    wrap_identifier,
)


@pytest.mark.unit
def test_dialect_instantiation_with_string():
    assert GXSqlDialect("hive") == GXSqlDialect.HIVE


@pytest.mark.unit
def test_dialect_instantiation_with_byte_string():
    assert GXSqlDialect(b"hive") == GXSqlDialect.HIVE


@pytest.mark.unit
def test_string_equivalence():
    assert GXSqlDialect.HIVE == "hive"


@pytest.mark.unit
def test_byte_string_equivalence():
    assert GXSqlDialect.HIVE == b"hive"


@pytest.mark.unit
def test_get_all_dialect_names_no_other_dialects():
    assert GXSqlDialect.OTHER.value not in GXSqlDialect.get_all_dialect_names()


@pytest.mark.unit
def test_get_all_dialects_no_other_dialects():
    assert GXSqlDialect.OTHER not in GXSqlDialect.get_all_dialects()


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect,expected",
    [
        (GXSqlDialect.DATABRICKS, "`col`"),
        (GXSqlDialect.SQL_SERVER, "[col]"),
        (GXSqlDialect.MYSQL, "`col`"),
        (GXSqlDialect.POSTGRESQL, '"col"'),
        (GXSqlDialect.SNOWFLAKE, '"col"'),
        (GXSqlDialect.SQLITE, '"col"'),
        (GXSqlDialect.TRINO, "`col`"),
        (GXSqlDialect.SINGLESTOREDB, "`col`"),
    ],
)
def test_quote_str(dialect, expected):
    assert quote_str("col", dialect) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect,quoted_input",
    [
        (GXSqlDialect.DATABRICKS, "`col`"),
        (GXSqlDialect.SQL_SERVER, "[col]"),
        (GXSqlDialect.MYSQL, "`col`"),
        (GXSqlDialect.POSTGRESQL, '"col"'),
        (GXSqlDialect.SNOWFLAKE, '"col"'),
        (GXSqlDialect.SQLITE, '"col"'),
        (GXSqlDialect.TRINO, "`col`"),
        (GXSqlDialect.SINGLESTOREDB, "`col`"),
    ],
)
def test_quote_str_already_quoted_raises(dialect, quoted_input):
    with pytest.raises(ValueError, match="already uses quote characters"):
        quote_str(quoted_input, dialect)


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect,quoted_input",
    [
        (GXSqlDialect.DATABRICKS, "`col`"),
        (GXSqlDialect.SQL_SERVER, "[col]"),
        (GXSqlDialect.SQL_SERVER, '"col"'),
        (GXSqlDialect.MYSQL, "`col`"),
        (GXSqlDialect.POSTGRESQL, '"col"'),
        (GXSqlDialect.SNOWFLAKE, '"col"'),
        (GXSqlDialect.SQLITE, '"col"'),
        (GXSqlDialect.TRINO, "`col`"),
        (GXSqlDialect.SINGLESTOREDB, "`col`"),
    ],
)
def test_strip_quotes(dialect, quoted_input):
    assert _strip_quotes(quoted_input, dialect) == "col"


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect",
    [
        GXSqlDialect.DATABRICKS,
        GXSqlDialect.SQL_SERVER,
        GXSqlDialect.MYSQL,
        GXSqlDialect.POSTGRESQL,
        GXSqlDialect.SNOWFLAKE,
        GXSqlDialect.SQLITE,
        GXSqlDialect.TRINO,
        GXSqlDialect.SINGLESTOREDB,
    ],
)
def test_strip_quotes_unquoted_noop(dialect):
    assert _strip_quotes("col", dialect) == "col"


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect,quoted_input",
    [
        (GXSqlDialect.DATABRICKS, "`col`"),
        (GXSqlDialect.SQL_SERVER, "[col]"),
        (GXSqlDialect.SQL_SERVER, '"col"'),
        (GXSqlDialect.MYSQL, "`col`"),
        (GXSqlDialect.POSTGRESQL, '"col"'),
        (GXSqlDialect.SNOWFLAKE, '"col"'),
        (GXSqlDialect.SQLITE, '"col"'),
        (GXSqlDialect.TRINO, "`col`"),
        (GXSqlDialect.SINGLESTOREDB, "`col`"),
    ],
)
def test_wrap_identifier_strips_quotes(dialect, quoted_input):
    result = wrap_identifier(quoted_input, dialect=dialect)
    assert str(result) == "col"
    assert result.quote is True
