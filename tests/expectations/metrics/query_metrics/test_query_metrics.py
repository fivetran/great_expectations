from typing import ClassVar, Optional
from unittest import mock

import pytest

from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.expectations.metrics.query_metric_provider import (
    QueryMetricProvider,
    QueryParameters,
)
from great_expectations.expectations.metrics.query_metrics import (
    QueryColumn,
    QueryColumnPair,
    QueryMultipleColumns,
    QueryRowCount,
    QueryTable,
    QueryTemplateValues,
)
from tests.expectations.metrics.conftest import MockSqlAlchemyExecutionEngine


@pytest.mark.unit
def test_query_template_get_query_function_with_int():
    """Simple test to ensure that the `get_query()` method for QueryTemplateValue can handle integer value"""  # noqa: E501 # FIXME CoP
    query: str = """
            SELECT {column_to_check}
            FROM {batch}
            WHERE {condition}
            GROUP BY {column_to_check}
            """
    selectable = sa.Table("gx_temp_aaa", sa.MetaData(), schema=None)
    template_dict: dict = {"column_to_check": 1, "condition": "is_open"}
    metric_ob: QueryTemplateValues = QueryTemplateValues()
    formatted_query: str = metric_ob.get_query(query, template_dict, selectable)
    assert (
        formatted_query
        == """
            SELECT 1
            FROM gx_temp_aaa
            WHERE is_open
            GROUP BY 1
            """
    )


@pytest.mark.unit
def test_query_template_get_query_function_with_float():
    """Simple test to ensure that the `get_query()` method for QueryTemplateValue can handle float value"""  # noqa: E501 # FIXME CoP
    query: str = """
            SELECT {column_to_check}
            FROM {batch}
            WHERE {condition}
            GROUP BY {column_to_check}
            """
    selectable = sa.Table("gx_temp_aaa", sa.MetaData(), schema=None)
    template_dict: dict = {"column_to_check": 1.0, "condition": "is_open"}
    metric_ob: QueryTemplateValues = QueryTemplateValues()
    formatted_query: str = metric_ob.get_query(query, template_dict, selectable)
    assert (
        formatted_query
        == """
            SELECT 1.0
            FROM gx_temp_aaa
            WHERE is_open
            GROUP BY 1.0
            """
    )


class MyQueryColumn(QueryColumn):
    metric_name = "my_query.column"
    value_keys = ("my_query",)

    query_param_name: ClassVar[str] = "my_query"


class MyQueryColumnPair(QueryColumnPair):
    metric_name = "my_query.column_pair"
    value_keys = ("my_query",)

    query_param_name: ClassVar[str] = "my_query"


class MyQueryMultipleColumns(QueryMultipleColumns):
    metric_name = "my_query.multiple_columns"
    value_keys = ("my_query",)

    query_param_name: ClassVar[str] = "my_query"


class MyQueryTable(QueryTable):
    metric_name = "my_query.table"
    value_keys = ("my_query",)

    query_param_name: ClassVar[str] = "my_query"


@pytest.mark.unit
@mock.patch.object(sa, "text")
@mock.patch.object(
    QueryMetricProvider, "_get_substituted_batch_subquery_from_query_and_batch_selectable"
)
@mock.patch.object(QueryMetricProvider, "_get_sqlalchemy_records_from_substituted_batch_subquery")
@pytest.mark.parametrize(
    "metric_class, class_metric_value_kwargs, query_parameters",
    [
        (
            MyQueryColumn,
            {"column": "my_column"},
            QueryParameters(column="my_column"),
        ),
        (
            MyQueryColumnPair,
            {"column_A": "my_column_A", "column_B": "my_column_B"},
            QueryParameters(column_A="my_column_A", column_B="my_column_B"),
        ),
        (
            MyQueryMultipleColumns,
            {"columns": ["my_column_1", "my_column_2", "my_column_3"]},
            QueryParameters(columns=["my_column_1", "my_column_2", "my_column_3"]),
        ),
        (
            MyQueryTable,
            {},
            None,
        ),
    ],
)
def test_sqlalchemy_query_metrics_that_return_records(
    mock_get_sqlalchemy_records_from_substituted_batch_subquery,
    mock_get_substituted_batch_subquery_from_query_and_batch_selectable,
    mock_sqlalchemy_text,
    mock_sqlalchemy_execution_engine: MockSqlAlchemyExecutionEngine,
    metric_class: QueryMetricProvider,
    class_metric_value_kwargs: dict,
    query_parameters: Optional[QueryParameters],
    batch_selectable: sa.Table,
):
    metric_value_kwargs = {
        "query_param": "my_query",
        "my_query": "SELECT * FROM {batch} WHERE passenger_count > 7",
    }
    metric_value_kwargs.update(class_metric_value_kwargs)

    mock_substituted_batch_subquery = "SELECT * FROM (my_table) WHERE passenger_count > 7"
    mock_get_substituted_batch_subquery_from_query_and_batch_selectable.return_value = (
        mock_substituted_batch_subquery
    )
    mock_sqlalchemy_text.return_value = "*"
    with mock.patch.object(mock_sqlalchemy_execution_engine, "execute_query"):
        metric_class._sqlalchemy(
            cls=metric_class,
            execution_engine=mock_sqlalchemy_execution_engine,
            metric_domain_kwargs={},
            metric_value_kwargs=metric_value_kwargs,
            metrics={},
            runtime_configuration={},
        )
    if query_parameters:
        mock_get_substituted_batch_subquery_from_query_and_batch_selectable.assert_called_once_with(
            query=metric_value_kwargs["my_query"],
            batch_selectable=batch_selectable,
            execution_engine=mock_sqlalchemy_execution_engine,
            query_parameters=query_parameters,
        )
    else:
        mock_get_substituted_batch_subquery_from_query_and_batch_selectable.assert_called_once_with(
            query=metric_value_kwargs["my_query"],
            batch_selectable=batch_selectable,
            execution_engine=mock_sqlalchemy_execution_engine,
        )
    mock_get_sqlalchemy_records_from_substituted_batch_subquery.assert_called_once_with(
        substituted_batch_subquery=mock_substituted_batch_subquery,
        execution_engine=mock_sqlalchemy_execution_engine,
    )


class MyQueryRowCount(QueryRowCount):
    metric_name = "my_query.row_count"
    value_keys = ("my_query",)

    query_param_name: ClassVar[str] = "my_query"


@pytest.mark.unit
@mock.patch.object(sa, "text")
@mock.patch.object(
    QueryMetricProvider, "_get_substituted_batch_subquery_from_query_and_batch_selectable"
)
def test_sqlalchemy_query_row_count(
    mock_get_substituted_batch_subquery_from_query_and_batch_selectable,
    mock_sqlalchemy_text,
    mock_sqlalchemy_execution_engine: MockSqlAlchemyExecutionEngine,
    batch_selectable: sa.Table,
):
    metric_value_kwargs = {
        "query_param": "my_query",
        "my_query": "SELECT * FROM {batch} WHERE passenger_count > 7",
    }

    mock_substituted_batch_subquery = "SELECT * FROM (my_table) WHERE passenger_count > 7"
    mock_get_substituted_batch_subquery_from_query_and_batch_selectable.return_value = (
        mock_substituted_batch_subquery
    )
    mock_sqlalchemy_text.return_value = "*"
    with mock.patch.object(mock_sqlalchemy_execution_engine, "execute_query"):
        MyQueryRowCount._sqlalchemy(
            cls=MyQueryRowCount,
            execution_engine=mock_sqlalchemy_execution_engine,
            metric_domain_kwargs={},
            metric_value_kwargs=metric_value_kwargs,
            metrics={},
            runtime_configuration={},
        )
    mock_get_substituted_batch_subquery_from_query_and_batch_selectable.assert_called_once_with(
        query=metric_value_kwargs["my_query"],
        batch_selectable=batch_selectable,
        execution_engine=mock_sqlalchemy_execution_engine,
    )
