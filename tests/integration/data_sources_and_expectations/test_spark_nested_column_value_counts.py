"""Aggregate expectations over a nested struct column on Spark."""

from __future__ import annotations

import pytest

import great_expectations as gx
import great_expectations.expectations as gxe

pytestmark = pytest.mark.spark


def _get_batch(spark_session, rows):
    df = spark_session.createDataFrame(rows)
    context = gx.get_context(mode="ephemeral")
    asset = context.data_sources.add_spark(name="spark").add_dataframe_asset(name="people")
    return asset.add_batch_definition_whole_dataframe("bd").get_batch(
        batch_parameters={"dataframe": df}
    )


def test_most_common_value_on_nested_struct_column(spark_session) -> None:
    from pyspark.sql import Row

    batch = _get_batch(
        spark_session,
        [
            Row(address=Row(city="paris")),
            Row(address=Row(city="paris")),
            Row(address=Row(city="london")),
        ],
    )

    result = batch.validate(
        gxe.ExpectColumnMostCommonValueToBeInSet(column="address.city", value_set=["paris"])
    )

    assert result.result, result.exception_info
    assert result.result["observed_value"] == ["paris"]
    assert result.success


def test_most_common_value_on_deeply_nested_struct_column_ignores_nulls(spark_session) -> None:
    from pyspark.sql import Row

    batch = _get_batch(
        spark_session,
        [
            Row(Data=Row(evt=Row(retry="0"))),
            Row(Data=Row(evt=Row(retry="1"))),
            Row(Data=Row(evt=Row(retry="1"))),
            Row(Data=Row(evt=Row(retry=None))),
            Row(Data=Row(evt=Row(retry=None))),
            Row(Data=Row(evt=Row(retry=None))),
        ],
    )

    result = batch.validate(
        gxe.ExpectColumnMostCommonValueToBeInSet(column="Data.evt.retry", value_set=["1"])
    )

    assert result.result, result.exception_info
    assert result.result["observed_value"] == ["1"]
    assert result.success
