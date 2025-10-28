from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pandas as pd
import pytest
import sqlalchemy as sa

from great_expectations.expectations.metrics.map_metric_provider.multicolumn_map_condition_auxilliary_methods import (  # noqa: E501
    _pandas_multicolumn_map_condition_filtered_row_count,
    _pandas_multicolumn_map_condition_values,
    _spark_multicolumn_map_condition_filtered_row_count,
    _spark_multicolumn_map_condition_values,
    _sqlalchemy_multicolumn_map_condition_filtered_row_count,
    _sqlalchemy_multicolumn_map_condition_values,
)

pytestmark = pytest.mark.unit


class _PandasEngine:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def get_domain_records(self, domain_kwargs: Dict[str, Any]) -> pd.DataFrame:
        return self._df


def test_pandas_values_missing_column_list_returns_empty() -> None:
    engine = _PandasEngine(pd.DataFrame({"a": [1, 2]}))  # type: ignore[arg-type]

    metrics: Dict[str, Any] = {
        "unexpected_condition": (
            pd.Series([True, False]),
            {},
            {},  # missing column_list
        ),
        "table.columns": ["a"],
    }

    res = _pandas_multicolumn_map_condition_values(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 5}
        },
        metrics=metrics,
    )
    assert res == []


def test_pandas_filtered_row_count_missing_column_list_returns_total_rows() -> None:
    engine = _PandasEngine(pd.DataFrame({"a": [1, 2, 3]}))  # type: ignore[arg-type]

    metrics: Dict[str, Any] = {
        "unexpected_condition": (
            pd.Series([True, False, True]),
            {},
            {},  # missing column_list
        ),
        "table.columns": ["a"],
    }

    count = _pandas_multicolumn_map_condition_filtered_row_count(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 5}
        },
        metrics=metrics,
    )
    assert count == 3


class _FakeSqlAlchemyEngine:
    def get_domain_records(self, domain_kwargs: Dict[str, Any]) -> Any:
        # Return a selectable
        return sa.select(sa.text("1")).subquery()

    def execute_query(self, query: Any):
        class _R:
            def scalar(self):
                return 42

            def fetchmany(self, n: int):
                return [SimpleNamespace(_asdict=lambda: {"A": 1})]

        return _R()


def test_sqlalchemy_values_missing_column_list_returns_empty() -> None:
    engine = _FakeSqlAlchemyEngine()  # type: ignore[arg-type]

    metrics: Dict[str, Any] = {
        "unexpected_condition": (
            sa.text("1=1"),
            {},
            {},  # missing column_list
        ),
        "table.columns": ["A"],
    }

    res = _sqlalchemy_multicolumn_map_condition_values(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 5}
        },
        metrics=metrics,
    )
    assert res == []


def test_sqlalchemy_filtered_row_count_missing_column_list_counts_all() -> None:
    engine = _FakeSqlAlchemyEngine()  # type: ignore[arg-type]

    metrics: Dict[str, Any] = {
        "unexpected_condition": (
            sa.text("1=1"),
            {},
            {},  # missing column_list
        ),
        "table.columns": ["A"],
    }

    count = _sqlalchemy_multicolumn_map_condition_filtered_row_count(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={
            "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 5}
        },
        metrics=metrics,
    )
    assert count == 42


@pytest.mark.unit
def test_spark_values_missing_column_list_returns_empty() -> None:
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession  # type: ignore[import-not-found]

    from great_expectations.compatibility.pyspark import (
        functions as F,  # type: ignore[import-not-found]
    )

    spark = SparkSession.builder.master("local[1]").appName("gx-test").getOrCreate()
    try:
        df = spark.createDataFrame([(1,), (2,)], ["A"])  # type: ignore[call-arg]

        class _SparkEngine:
            def get_domain_records(self, domain_kwargs: Dict[str, Any]):
                return df

        engine = _SparkEngine()  # type: ignore[arg-type]
        metrics: Dict[str, Any] = {
            "unexpected_condition": (
                F.lit(True),
                {},
                {},  # missing column_list
            ),
            "table.columns": ["A"],
        }

        res = _spark_multicolumn_map_condition_values(
            cls=SimpleNamespace(),  # type: ignore[arg-type]
            execution_engine=engine,  # type: ignore[arg-type]
            metric_domain_kwargs={},
            metric_value_kwargs={
                "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 5}
            },
            metrics=metrics,
        )
        assert res == []
    finally:
        spark.stop()


@pytest.mark.unit
def test_spark_filtered_row_count_missing_column_list_counts_all() -> None:
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession  # type: ignore[import-not-found]

    from great_expectations.compatibility.pyspark import (
        functions as F,  # type: ignore[import-not-found]
    )

    spark = SparkSession.builder.master("local[1]").appName("gx-test").getOrCreate()
    try:
        df = spark.createDataFrame([(1,), (2,), (3,)], ["A"])  # type: ignore[call-arg]

        class _SparkEngine:
            def get_domain_records(self, domain_kwargs: Dict[str, Any]):
                return df

        engine = _SparkEngine()  # type: ignore[arg-type]
        metrics: Dict[str, Any] = {
            "unexpected_condition": (
                F.lit(True),
                {},
                {},  # missing column_list
            ),
            "table.columns": ["A"],
        }

        count = _spark_multicolumn_map_condition_filtered_row_count(
            cls=SimpleNamespace(),  # type: ignore[arg-type]
            execution_engine=engine,  # type: ignore[arg-type]
            metric_domain_kwargs={},
            metric_value_kwargs={
                "result_format": {"result_format": "SUMMARY", "partial_unexpected_count": 5}
            },
            metrics=metrics,
        )
        assert count == df.count()
    finally:
        spark.stop()
