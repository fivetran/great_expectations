"""Reproduction for community issue #11381.

Spark Execution Engine: unexpected_index_column_names does not work with
nested (struct) columns. When ``unexpected_index_column_names`` (or the
expectation's ``column``) refers to a nested path such as ``Data.evt.id``,
the Spark implementation of ``_spark_map_condition_index`` raises
``InvalidMetricAccessorDomainKwargsKeyError`` because it checks the dotted
path against the top-level ``filtered.columns`` list, which only contains
the outer struct names.
"""

from __future__ import annotations

import pytest

import great_expectations as gx
import great_expectations.expectations as gxe

pytestmark = pytest.mark.spark


def _make_nested_spark_df(spark_session):
    """Build a Spark DataFrame with a nested struct schema matching the issue.

    Schema:
        root
         |-- Data: struct
         |    |-- evt: struct
         |    |    |-- id: string
         |    |    |-- retry: string
    """
    from pyspark.sql import Row

    rows = [
        Row(Data=Row(evt=Row(id="a", retry="0"))),
        Row(Data=Row(evt=Row(id="b", retry="1"))),
        # "2" is not in the value_set {"0", "1"} -> unexpected row
        Row(Data=Row(evt=Row(id="c", retry="2"))),
    ]
    return spark_session.createDataFrame(rows)


def test_spark_unexpected_index_column_names_with_nested_columns(spark_session) -> None:
    """Reproduce issue #11381.

    Validating a nested column and requesting a nested column as the
    ``unexpected_index_column_names`` should return an ``unexpected_index_list``
    keyed by the nested path. Instead, the Spark backend raises an error
    because the dotted path is not found in ``filtered.columns``.
    """
    context = gx.get_context(mode="ephemeral")
    spark_df = _make_nested_spark_df(spark_session)

    datasource = context.data_sources.add_spark(name="issue_11381_spark")
    asset = datasource.add_dataframe_asset(name="nested_asset")
    batch_def = asset.add_batch_definition_whole_dataframe(name="nested_bd")
    batch = batch_def.get_batch(batch_parameters={"dataframe": spark_df})

    expectation = gxe.ExpectColumnValuesToBeInSet(
        column="Data.evt.retry",
        value_set=["0", "1"],
    )

    result = batch.validate(
        expectation,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["Data.evt.id"],
            "partial_unexpected_count": 0,
            "include_unexpected_rows": True,
            "return_unexpected_index_query": True,
        },
    )

    # Row with retry="2" violates the expectation, so validation should fail.
    assert not result.success

    # The unexpected row has id="c"; the result should surface that via
    # unexpected_index_list keyed by the nested path "Data.evt.id".
    # Bug: on Spark, this key is missing / the call errors out.
    result_dict = result["result"]
    assert "unexpected_index_list" in result_dict, (
        f"Spark nested column path was not honored: result={result_dict}"
    )
    unexpected_index_list = result_dict["unexpected_index_list"]
    assert unexpected_index_list, "expected at least one unexpected index row"
    # Each entry should contain the nested key "Data.evt.id" with value "c".
    ids = [entry.get("Data.evt.id") for entry in unexpected_index_list]
    assert "c" in ids, f"expected 'c' among unexpected ids, got {unexpected_index_list}"


def test_spark_unexpected_index_column_names_missing_nested_path_errors(
    spark_session,
) -> None:
    """A dotted path that is neither a top-level column nor a reachable
    struct path should surface an ``InvalidMetricAccessorDomainKwargsKeyError``.

    Guards the existence-check widening in ``_spark_map_condition_index``
    against accidentally accepting any dotted string. ``batch.validate``
    catches metric-resolution errors and reports them on the result's
    ``exception_info`` rather than raising, so we inspect that.
    """
    context = gx.get_context(mode="ephemeral")
    spark_df = _make_nested_spark_df(spark_session)

    datasource = context.data_sources.add_spark(name="issue_11381_spark_missing")
    asset = datasource.add_dataframe_asset(name="nested_asset_missing")
    batch_def = asset.add_batch_definition_whole_dataframe(name="nested_bd_missing")
    batch = batch_def.get_batch(batch_parameters={"dataframe": spark_df})

    expectation = gxe.ExpectColumnValuesToBeInSet(
        column="Data.evt.retry",
        value_set=["0", "1"],
    )

    result = batch.validate(
        expectation,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["Data.evt.nonexistent"],
            "partial_unexpected_count": 0,
            "include_unexpected_rows": True,
            "return_unexpected_index_query": True,
        },
    )

    # ``exception_info`` is a dict keyed by failed metric id, each value being
    # an ExceptionInfo dict with ``raised_exception`` / ``exception_message``.
    exception_info = result.exception_info or {}
    assert exception_info, f"expected exception_info to be populated, got {exception_info!r}"
    messages = [str(info.get("exception_message", "")) for info in exception_info.values()]
    assert any("Data.evt.nonexistent" in msg for msg in messages), (
        f"expected the bogus column name in an exception message, got: {messages!r}"
    )


def test_spark_unexpected_index_column_names_with_literal_dotted_column(
    spark_session,
) -> None:
    """A flat top-level column whose literal name contains a dot must still
    be addressable — it should not be misinterpreted as a struct path.

    Spark allows column names with dots when backtick-quoted in SQL, and
    ``F.col("a.b")`` would attempt struct navigation. The selection logic
    must prefer a literal top-level match over struct resolution.
    """
    from pyspark.sql import Row

    context = gx.get_context(mode="ephemeral")
    # A flat schema with two columns: "id.with.dots" (literal name) and "retry".
    rows = [
        Row(**{"id.with.dots": "a", "retry": "0"}),
        Row(**{"id.with.dots": "b", "retry": "1"}),
        Row(**{"id.with.dots": "c", "retry": "2"}),
    ]
    spark_df = spark_session.createDataFrame(rows)

    datasource = context.data_sources.add_spark(name="literal_dotted_col_spark")
    asset = datasource.add_dataframe_asset(name="literal_dotted_asset")
    batch_def = asset.add_batch_definition_whole_dataframe(name="literal_dotted_bd")
    batch = batch_def.get_batch(batch_parameters={"dataframe": spark_df})

    expectation = gxe.ExpectColumnValuesToBeInSet(
        column="retry",
        value_set=["0", "1"],
    )

    result = batch.validate(
        expectation,
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": ["id.with.dots"],
            "partial_unexpected_count": 0,
            "include_unexpected_rows": True,
            "return_unexpected_index_query": True,
        },
    )

    assert not result.success
    unexpected_index_list = result["result"]["unexpected_index_list"]
    assert unexpected_index_list, "expected at least one unexpected index row"
    ids = [entry.get("id.with.dots") for entry in unexpected_index_list]
    assert "c" in ids, f"expected 'c' among unexpected ids, got {unexpected_index_list}"
