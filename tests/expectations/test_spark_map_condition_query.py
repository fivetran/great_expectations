from great_expectations.expectations.metrics.map_metric_provider.map_condition_auxilliary_methods import (  # noqa: E501
    _spark_map_condition_query,
)


class _SparkColumn:
    def __init__(self, expression: str) -> None:
        self.expression = expression

    def __str__(self) -> str:
        return f"Column<'{self.expression}'>"


def _query(expression: str, **kwargs: object) -> str:
    return _spark_map_condition_query(
        cls=None,
        execution_engine=None,
        metric_domain_kwargs={},
        metric_value_kwargs={
            "result_format": {"result_format": "COMPLETE"},
            **kwargs,
        },
        metrics={"unexpected_condition": (_SparkColumn(expression), None, None)},
    )


def test_spark_unexpected_index_query_quotes_string_value_set() -> None:
    query = _query(
        "((in_set_str IS NOT NULL) AND (NOT (in_set_str IN (Val1, Val2))))",
        value_set=["Val1", "Val2"],
    )

    assert query == (
        "df.filter(F.expr((in_set_str IS NOT NULL) AND (NOT (in_set_str IN ('Val1', 'Val2')))))"
    )


def test_spark_unexpected_index_query_quotes_regex() -> None:
    regex = r"^[a-z]+@[a-z]+\.com$"
    query = _query(
        rf"((email IS NOT NULL) AND (NOT RLIKE(email, {regex})))",
        regex=regex,
    )

    assert f"RLIKE(email, '{regex}')" in query
