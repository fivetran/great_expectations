import pytest

from great_expectations.compatibility import pyspark
from great_expectations.expectations import legacy_row_conditions
from great_expectations.expectations.legacy_row_conditions import (
    _condition_value_literal,
    parse_condition_to_spark,
    parse_condition_to_sqlalchemy,
    parse_great_expectations_condition,
)


@pytest.mark.spark
def test_condition_value_literal_numeric_column_uses_numeric_literal(monkeypatch):
    # For a numeric column, a bare string literal would force an implicit
    # string<->numeric comparison that errors under ANSI mode. The value must instead be
    # converted to a numeric literal so the comparison stays numeric-vs-numeric.
    captured: list = []
    monkeypatch.setattr(
        legacy_row_conditions.F, "lit", lambda value: captured.append(value) or value
    )
    schema = pyspark.types.StructType(
        [pyspark.types.StructField("n", pyspark.types.LongType(), True)]
    )

    _condition_value_literal("5", "n", schema)

    assert captured == [5]
    assert isinstance(captured[0], int)


@pytest.mark.spark
def test_condition_value_literal_numeric_column_non_numeric_value_falls_back(monkeypatch):
    # A value that is not parseable as a number keeps the original string literal even on
    # a numeric column, preserving the pre-existing fallback behavior.
    captured: list = []
    monkeypatch.setattr(
        legacy_row_conditions.F, "lit", lambda value: captured.append(value) or value
    )
    schema = pyspark.types.StructType(
        [pyspark.types.StructField("n", pyspark.types.LongType(), True)]
    )

    _condition_value_literal("not_a_number", "n", schema)

    assert captured == ["not_a_number"]


@pytest.mark.spark
def test_condition_value_literal_string_column_preserves_string_literal(monkeypatch):
    # A non-numeric column keeps the string literal unchanged.
    captured: list = []
    monkeypatch.setattr(
        legacy_row_conditions.F, "lit", lambda value: captured.append(value) or value
    )
    schema = pyspark.types.StructType(
        [pyspark.types.StructField("s", pyspark.types.StringType(), True)]
    )

    _condition_value_literal("hello", "s", schema)

    assert captured == ["hello"]


@pytest.mark.unit
def test_notnull_parser():
    res = parse_great_expectations_condition('col("foo").notNull()')
    assert res["column"] == "foo"
    assert res["notnull"] is True

    res = parse_great_expectations_condition('col("foo") > 5')
    assert res["column"] == "foo"
    assert "notnull" not in res


@pytest.mark.unit
def test_condition_parser():
    res = parse_great_expectations_condition('col("foo") > 5')
    assert res["column"] == "foo"
    assert res["op"] == ">"
    assert res["fnumber"] == "5"


@pytest.mark.unit
def test_condition_parser_with_underscore_in_column_name():
    res = parse_great_expectations_condition('col("pk_2") == "Two"')
    assert res["column"] == "pk_2"
    assert res["op"] == "=="
    assert res["condition_value"] == "Two"


@pytest.mark.unit
def test_condition_parser_with_dash_in_column_name():
    res = parse_great_expectations_condition('col("pk-2") == "Two"')
    assert res["column"] == "pk-2"
    assert res["op"] == "=="
    assert res["condition_value"] == "Two"


@pytest.mark.unit
def test_condition_parser_with_space_in_column_name():
    res = parse_great_expectations_condition('col("pk 2") == "Two"')
    assert res["column"] == "pk 2"
    assert res["op"] == "=="
    assert res["condition_value"] == "Two"


@pytest.mark.unit
def test_condition_parser_with_space_in_condition_value():
    res = parse_great_expectations_condition('col("pk_2") == "Two Two"')
    assert res["column"] == "pk_2"
    assert res["op"] == "=="
    assert res["condition_value"] == "Two Two"


@pytest.mark.unit
def test_condition_parser_with_tab_in_condition_value():
    res = parse_great_expectations_condition('col("pk_2") == "Two  Two"')
    assert res["column"] == "pk_2"
    assert res["op"] == "=="
    assert res["condition_value"] == "Two  Two"


@pytest.mark.unit
def test_condition_parser_with_8bit_chars_in_condition_value():
    res = parse_great_expectations_condition(
        'col("sp_chars") == "Café_über_naïve_élite_ñandú_çeviche_æther_øresund_ångström"'
    )
    assert res["column"] == "sp_chars"
    assert res["op"] == "=="
    assert res["condition_value"] == "Café_über_naïve_élite_ñandú_çeviche_æther_øresund_ångström"


@pytest.mark.spark
def test_parse_condition_to_spark(spark_session):
    res = parse_condition_to_spark('col("foo") > 5')
    # This is mostly a demonstrative test; it may be brittle. I do not know how to test
    # a condition itself.
    # Spark renders Column reprs differently across versions: older Spark uses a
    # byte-string prefix and infix operators, Spark 4 drops the prefix and renders
    # comparisons in function-prefix form (">(foo, 5)").
    assert str(res) in [
        "Column<b'(foo > 5)'>",
        "Column<'(foo > 5)'>",
        "Column<'>(foo, 5)'>",
    ]

    res = parse_condition_to_spark('col("foo").notNull()')
    # This is mostly a demonstrative test; it may be brittle. I do not know how to test
    # a condition itself.
    print(str(res))
    # Spark 4 renders the null check in function-prefix form ("isNotNull(foo)")
    # rather than the older infix "(foo IS NOT NULL)".
    assert str(res) in [
        "Column<b'(foo IS NOT NULL)'>",
        "Column<'(foo IS NOT NULL)'>",
        "Column<'isNotNull(foo)'>",
    ]


@pytest.mark.unit
def test_parse_condition_to_sqlalchemy(sa):
    res = parse_condition_to_sqlalchemy('col("foo") > 5')
    assert str(res) == "foo > :foo_1"

    res = parse_condition_to_sqlalchemy('col("foo").notNull()')
    assert str(res) == "foo IS NOT NULL"

    res = parse_condition_to_sqlalchemy('col("foo") == "a-b"')
    assert str(res) == "foo = :foo_1"

    res = parse_condition_to_sqlalchemy('col("foo") != "a-b"')
    assert str(res) == "foo != :foo_1"

    res = parse_condition_to_sqlalchemy('col("foo") <= 1.34')
    assert str(res) == "foo <= :foo_1"

    res = parse_condition_to_sqlalchemy('col("foo") <= date("2023-03-13")')
    assert str(res) == "foo <= :foo_1"
