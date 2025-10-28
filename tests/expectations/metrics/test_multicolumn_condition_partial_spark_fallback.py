from __future__ import annotations

from typing import Any, Dict

import pytest


@pytest.mark.unit
def test_spark_map_condition_raises_then_fallbacks() -> None:
    pytest.importorskip("pyspark")
    from pyspark.errors.exceptions.base import (  # type: ignore[import-not-found]
        PySparkRuntimeError,
    )
    from pyspark.sql import SparkSession  # type: ignore[import-not-found]

    try:
        from py4j.protocol import Py4JJavaError  # type: ignore[import-not-found]
    except Exception:  # pragma: no cover - py4j may not be available
        Py4JJavaError = Exception  # type: ignore[assignment]

    from great_expectations.execution_engine.sparkdf_execution_engine import (
        SparkDFExecutionEngine,
    )
    from great_expectations.expectations.metrics.map_metric_provider.multicolumn_condition_partial import (  # noqa: E501
        multicolumn_condition_partial,
    )

    try:
        spark = SparkSession.builder.master("local[1]").appName("gx-test").getOrCreate()
    except (
        PySparkRuntimeError,
        Py4JJavaError,
        Exception,
    ) as e:  # Java not available or gateway failed
        pytest.skip(f"Skipping Spark test; SparkSession failed to start: {e}")
    try:
        df = spark.createDataFrame([(1, 10), (2, 20)], ["a", "b"])  # type: ignore[call-arg]

        class _SparkEngine:
            def get_compute_domain(self, domain_kwargs: Dict[str, Any], domain_type: Any):
                # Return data, compute_domain_kwargs, accessor_domain_kwargs
                return df, {}, {"column_list": ["a"]}

        class Dummy:
            @multicolumn_condition_partial(engine=SparkDFExecutionEngine)
            def _spark(self, data, **kwargs):
                # Force error to trigger fallback path
                raise RuntimeError("boom")

        engine = _SparkEngine()  # type: ignore[arg-type]

        inner = Dummy._spark  # type: ignore[attr-defined]
        unexpected_condition, _compute, accessor = inner(
            Dummy(),
            execution_engine=engine,  # type: ignore[arg-type]
            metric_domain_kwargs={},
            metric_value_kwargs={},
            metrics={"table.columns": ["a"]},
            runtime_configuration={},
        )

        # Fallback path should produce unconditional True condition and empty column_list
        flags = [r[0] for r in df.select(unexpected_condition.alias("flag")).collect()]
        assert flags == [True, True]
        assert accessor == {"column_list": []}
    finally:
        spark.stop()
