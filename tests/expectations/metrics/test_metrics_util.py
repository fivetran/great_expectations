from __future__ import annotations

import random
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Final, List, Union
from unittest.mock import create_autospec, patch

import pytest
from _pytest import monkeypatch

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility import sqlalchemy
from great_expectations.compatibility.sqlalchemy import (
    Dialect,
    Engine,
)
from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.data_context.util import file_relative_path
from great_expectations.exceptions import MetricResolutionError
from great_expectations.execution_engine import SqlAlchemyExecutionEngine
from great_expectations.expectations.metrics.util import (
    CaseInsensitiveString,
    get_dbms_compatible_metric_domain_kwargs,
    get_dialect_like_pattern_expression,
    get_unexpected_indices_for_multiple_pandas_named_indices,
    get_unexpected_indices_for_single_pandas_named_index,
    sqlalchemy_select_to_sql_string,
)
from tests.test_utils import (
    get_awsathena_connection_url,
    get_bigquery_connection_url,
    get_default_mssql_url,
    get_default_mysql_url,
    get_default_postgres_url,
    get_default_trino_url,
    get_redshift_connection_url,
    get_snowflake_connection_url,
)

if TYPE_CHECKING:
    import pandas as pd

# The following class allows for declarative instantiation of base class for SqlAlchemy. Adopted from  # noqa: E501 # FIXME CoP
# https://docs.sqlalchemy.org/en/14/faq/sqlexpressions.html#rendering-postcompile-parameters-as-bound-parameters

Base = sqlalchemy.declarative_base()


class A(Base):
    __tablename__ = "a"
    id = sa.Column(sa.Integer, primary_key=True)
    data = sa.Column(sa.String)


def select_with_post_compile_statements() -> sqlalchemy.Select:
    test_id: str = "00000000"
    return sa.select(A).where(A.data == test_id)


def _compare_select_statement_with_converted_string(engine) -> None:
    """
    Helper method used to do the call to sqlalchemy_select_to_sql_string()
    and compare with expected value.
    Args:
        engine (ExecutionEngine): SqlAlchemyExecutionEngine with connection to backend under test
    """
    select_statement: sqlalchemy.Select = select_with_post_compile_statements()
    returned_string = sqlalchemy_select_to_sql_string(
        engine=engine, select_statement=select_statement
    )
    assert returned_string == ("SELECT a.id, a.data \nFROM a \nWHERE a.data = '00000000';")


@pytest.fixture
def unexpected_index_list_one_index_column():
    return [
        {"animals": "cat", "pk_1": 0},
        {"animals": "fish", "pk_1": 1},
        {"animals": "dog", "pk_1": 2},
        {"animals": "giraffe", "pk_1": 3},
        {"animals": "lion", "pk_1": 4},
        {"animals": "zebra", "pk_1": 5},
    ]


@pytest.fixture
def unexpected_index_list_one_index_column_without_column_values():
    return [
        {"pk_1": [0, 1, 2, 3, 4, 5]},
    ]


@pytest.fixture
def unexpected_index_list_two_index_columns():
    return [
        {"animals": "cat", "pk_1": 0, "pk_2": "zero"},
        {"animals": "fish", "pk_1": 1, "pk_2": "one"},
        {"animals": "dog", "pk_1": 2, "pk_2": "two"},
        {"animals": "giraffe", "pk_1": 3, "pk_2": "three"},
        {"animals": "lion", "pk_1": 4, "pk_2": "four"},
        {"animals": "zebra", "pk_1": 5, "pk_2": "five"},
    ]


@pytest.fixture
def unexpected_index_list_two_index_columns_without_column_values():
    return [
        {
            "pk_1": [0, 1, 2, 3, 4, 5],
            "pk_2": ["zero", "one", "two", "three", "four", "five"],
        },
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "backend_name,connection_string",
    [
        (
            "sqlite",
            f"sqlite:///{file_relative_path(__file__, '../../test_sets/metrics_test.db')}",
        ),
        ("postgresql", get_default_postgres_url()),
        ("mysql", get_default_mysql_url()),
        ("mssql", get_default_mssql_url()),
        ("trino", get_default_trino_url()),
        ("redshift", get_redshift_connection_url()),
        ("snowflake", get_snowflake_connection_url()),
    ],
)
def test_sql_statement_conversion_to_string_for_backends(
    backend_name: str, connection_string: str, test_backends: List[str]
):
    if backend_name in test_backends:
        engine = SqlAlchemyExecutionEngine(connection_string=connection_string)
        _compare_select_statement_with_converted_string(engine=engine)
    else:
        pytest.skip(f"skipping sql statement conversion test for : {backend_name}")


@pytest.mark.unit
def test_sql_statement_conversion_to_string_awsathena(test_backends):
    if "awsathena" in test_backends:
        monkeypatch.setenv("ATHENA_STAGING_S3", "s3://test-staging/")
        monkeypatch.setenv("ATHENA_DB_NAME", "test_db_name")
        monkeypatch.setenv("ATHENA_TEN_TRIPS_DB_NAME", "test_ten_trips_db_name")
        connection_string = get_awsathena_connection_url()
        engine = SqlAlchemyExecutionEngine(connection_string=connection_string)
        _compare_select_statement_with_converted_string(engine=engine)
    else:
        pytest.skip("skipping sql statement conversion test for : awsathena")


@pytest.mark.unit
def test_sql_statement_conversion_to_string_bigquery(test_backends):
    """
    Bigquery backend returns a slightly different query
    """
    if "bigquery" in test_backends:
        monkeypatch.setenv("GE_TEST_GCP_PROJECT", "ge-oss")
        connection_string = get_bigquery_connection_url()
        engine = SqlAlchemyExecutionEngine(connection_string=connection_string)
        select_statement: sqlalchemy.Select = select_with_post_compile_statements()
        returned_string = sqlalchemy_select_to_sql_string(
            engine=engine, select_statement=select_statement
        )
        assert returned_string == (
            "SELECT `a`.`id`, `a`.`data` \nFROM `a` \nWHERE `a`.`data` = '00000000';"
        )
    else:
        pytest.skip("skipping sql statement conversion test for : bigquery")


@pytest.mark.unit
def test_get_unexpected_indices_for_single_pandas_named_index_named_unexpected_index_columns(
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_one_index_column,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["pk_1"]

    unexpected_index_list = get_unexpected_indices_for_single_pandas_named_index(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
    )
    assert unexpected_index_list == unexpected_index_list_one_index_column


@pytest.mark.unit
def test_get_unexpected_indices_for_single_pandas_named_index_named_unexpected_index_columns_without_column_values(  # noqa: E501 # FIXME CoP
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_one_index_column_without_column_values,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["pk_1"]

    unexpected_index_list = get_unexpected_indices_for_single_pandas_named_index(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
        exclude_unexpected_values=True,  # the new argument
    )
    assert unexpected_index_list == unexpected_index_list_one_index_column_without_column_values


@pytest.mark.unit
def test_get_unexpected_indices_for_single_pandas_named_index(
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_one_index_column,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = [updated_dataframe.index.name]

    unexpected_index_list = get_unexpected_indices_for_single_pandas_named_index(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
    )
    assert unexpected_index_list == unexpected_index_list_one_index_column


@pytest.mark.unit
def test_get_unexpected_indices_for_single_pandas_named_index_without_column_values(
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_one_index_column_without_column_values,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = [updated_dataframe.index.name]

    unexpected_index_list = get_unexpected_indices_for_single_pandas_named_index(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
        exclude_unexpected_values=True,  # the new argument
    )
    assert unexpected_index_list == unexpected_index_list_one_index_column_without_column_values


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices(
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_two_index_columns,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = list(updated_dataframe.index.names)

    unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
    )
    assert unexpected_index_list == unexpected_index_list_two_index_columns


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_without_column_values(
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_two_index_columns_without_column_values,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = list(updated_dataframe.index.names)

    unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
        exclude_unexpected_values=True,  # the new argument
    )
    assert unexpected_index_list == unexpected_index_list_two_index_columns_without_column_values


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_named_unexpected_index_columns(
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_two_index_columns,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["pk_1", "pk_2"]

    unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
    )
    assert unexpected_index_list == unexpected_index_list_two_index_columns


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_named_unexpected_index_columns_without_column_values(  # noqa: E501 # FIXME CoP
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_two_index_columns_without_column_values,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["pk_1", "pk_2"]

    unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
        exclude_unexpected_values=True,  # the new argument
    )
    assert unexpected_index_list == unexpected_index_list_two_index_columns_without_column_values


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_named_unexpected_index_columns_one_column(  # noqa: E501 # FIXME CoP
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_one_index_column,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["pk_1"]

    unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
    )
    assert unexpected_index_list == unexpected_index_list_one_index_column


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_named_unexpected_index_columns_one_column_without_column_values(  # noqa: E501 # FIXME CoP
    pandas_animals_dataframe_for_unexpected_rows_and_index,
    unexpected_index_list_one_index_column_without_column_values,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["pk_1"]

    unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
        domain_records_df=updated_dataframe,
        unexpected_index_column_names=unexpected_index_column_names,
        expectation_domain_column_list=expectation_domain_column_list,
        exclude_unexpected_values=True,  # the new argument
    )
    assert unexpected_index_list == unexpected_index_list_one_index_column_without_column_values


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_named_unexpected_index_columns_wrong_column(  # noqa: E501 # FIXME CoP
    pandas_animals_dataframe_for_unexpected_rows_and_index,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list: List[str] = ["animals"]
    unexpected_index_column_names: List[str] = ["i_dont_exist"]
    with pytest.raises(MetricResolutionError) as e:
        get_unexpected_indices_for_multiple_pandas_named_indices(
            domain_records_df=updated_dataframe,
            unexpected_index_column_names=unexpected_index_column_names,
            expectation_domain_column_list=expectation_domain_column_list,
        )
    assert e.value.message == (
        "Error: The column i_dont_exist does not exist in the named indices. Please "
        "check your configuration."
    )


@pytest.mark.unit
def test_get_unexpected_indices_for_multiple_pandas_named_indices_named_unexpected_index_wrong_domain(  # noqa: E501 # FIXME CoP
    pandas_animals_dataframe_for_unexpected_rows_and_index,
):
    dataframe: pd.DataFrame = pandas_animals_dataframe_for_unexpected_rows_and_index
    updated_dataframe: pd.DataFrame = dataframe.set_index(["pk_1", "pk_2"])
    expectation_domain_column_list = []
    unexpected_index_column_names = ["pk_1"]
    with pytest.raises(MetricResolutionError) as e:
        get_unexpected_indices_for_multiple_pandas_named_indices(
            domain_records_df=updated_dataframe,
            unexpected_index_column_names=unexpected_index_column_names,
            expectation_domain_column_list=expectation_domain_column_list,
        )
    assert e.value.message == (
        "Error: The list of domain columns is currently empty. Please check your configuration."
    )


@pytest.fixture
def column_names_all_lowercase() -> list[str]:
    return [
        "artists",
        "healthcare_workers",
        "engineers",
        "lawyers",
        "scientists",
    ]


@pytest.fixture
def column_names_all_uppercase(column_names_all_lowercase: list[str]) -> list[str]:
    name: str
    return [name.upper() for name in column_names_all_lowercase]


@pytest.mark.unit
def test_get_dbms_compatible_metric_domain_column_kwargs_column_not_found(
    sa, column_names_all_lowercase: list[str]
):
    test_column_names: list[str] = column_names_all_lowercase
    with pytest.raises(gx_exceptions.InvalidMetricAccessorDomainKwargsKeyError) as eee:
        _ = get_dbms_compatible_metric_domain_kwargs(
            metric_domain_kwargs={"column": "non_existent_column"},
            batch_columns_list=test_column_names,
        )
    assert str(eee.value) == 'Error: The column "non_existent_column" in BatchData does not exist.'


@pytest.mark.unit
@pytest.mark.parametrize(
    [
        "input_column_name",
        "output_column_name",
        "confirm_not_equal_column_name",
    ],
    [
        pytest.param(
            "SHOULD_NOT_BE_QUOTED",
            "SHOULD_NOT_BE_QUOTED",
            None,
            id="column_does_not_need_to_be_quoted",
        ),
        pytest.param(
            "should_be_quoted",
            sqlalchemy.quoted_name(value="should_be_quoted", quote=True),
            "SHOULD_NOT_BE_QUOTED",
            id="column_must_be_quoted",
        ),
    ],
)
def test_get_dbms_compatible_metric_domain_column_kwargs(
    sa,
    column_names_all_uppercase: list[str],
    input_column_name: str,
    output_column_name: Union[str, sqlalchemy.quoted_name],
    confirm_not_equal_column_name: Union[str, sqlalchemy.quoted_name],
):
    not_quoted_column_name = "SHOULD_NOT_BE_QUOTED"
    quoted_column_name: sqlalchemy.quoted_name = sqlalchemy.quoted_name(
        value="should_be_quoted", quote=True
    )
    test_column_names: list[str] = column_names_all_uppercase + [
        not_quoted_column_name,
        quoted_column_name,
    ]

    metric_domain_kwargs: dict

    metric_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs={"column": input_column_name},
        batch_columns_list=test_column_names,
    )
    assert metric_domain_kwargs["column"] == output_column_name
    if confirm_not_equal_column_name:
        assert metric_domain_kwargs["column"] != confirm_not_equal_column_name


@pytest.mark.unit
@pytest.mark.parametrize(
    [
        "input_column_name_a",
        "input_column_name_b",
        "output_column_name_a",
        "output_column_name_b",
    ],
    [
        pytest.param(
            "SHOULD_NOT_BE_QUOTED",
            sqlalchemy.quoted_name(value="should_be_quoted", quote=True),
            "SHOULD_NOT_BE_QUOTED",
            sqlalchemy.quoted_name(value="should_be_quoted", quote=True),
            id="column_a_does_not_need_to_be_quoted_column_b_must_remain_as_quoted",
        ),
        pytest.param(
            "SHOULD_NOT_BE_QUOTED",
            "should_be_quoted",
            "SHOULD_NOT_BE_QUOTED",
            sqlalchemy.quoted_name(value="should_be_quoted", quote=True),
            id="column_a_does_not_need_to_be_quoted_column_b_needs_to_be_quoted",
        ),
    ],
)
def test_get_dbms_compatible_metric_domain_column_pair_kwargs(
    sa,
    column_names_all_uppercase: list[str],
    input_column_name_a: str,
    input_column_name_b: str,
    output_column_name_a: Union[str, sqlalchemy.quoted_name],
    output_column_name_b: Union[str, sqlalchemy.quoted_name],
):
    not_quoted_column_name = "SHOULD_NOT_BE_QUOTED"
    quoted_column_name: sqlalchemy.quoted_name = sqlalchemy.quoted_name(
        value="should_be_quoted", quote=True
    )
    test_column_names: list[str] = column_names_all_uppercase + [
        not_quoted_column_name,
        quoted_column_name,
    ]

    metric_domain_kwargs: dict

    metric_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs={
            "column_A": input_column_name_a,
            "column_B": input_column_name_b,
        },
        batch_columns_list=test_column_names,
    )
    assert metric_domain_kwargs["column_A"] == output_column_name_a
    assert metric_domain_kwargs["column_B"] == output_column_name_b


@pytest.mark.unit
@pytest.mark.unit
@pytest.mark.parametrize(
    [
        "input_column_list",
        "output_column_list",
    ],
    [
        pytest.param(
            [
                "SHOULD_NOT_BE_QUOTED",
                "should_be_quoted_0",
                "should_be_quoted_1",
                "should_be_quoted_2",
            ],
            [
                "SHOULD_NOT_BE_QUOTED",
                sqlalchemy.quoted_name(value="should_be_quoted_0", quote=True),
                sqlalchemy.quoted_name(value="should_be_quoted_1", quote=True),
                sqlalchemy.quoted_name(value="should_be_quoted_2", quote=True),
            ],
            id="column_list_has_three_columns_that_must_be_quoted",
        ),
    ],
)
def test_get_dbms_compatible_metric_domain_column_list_kwargs(
    sa,
    column_names_all_uppercase: list[str],
    input_column_list: list[str],
    output_column_list: list[Union[str, sqlalchemy.quoted_name]],
):
    not_quoted_column_name = "SHOULD_NOT_BE_QUOTED"
    quoted_column_name_0: sqlalchemy.quoted_name = sqlalchemy.quoted_name(
        value="should_be_quoted_0", quote=True
    )
    quoted_column_name_1: sqlalchemy.quoted_name = sqlalchemy.quoted_name(
        value="should_be_quoted_1", quote=True
    )
    quoted_column_name_2: sqlalchemy.quoted_name = sqlalchemy.quoted_name(
        value="should_be_quoted_2", quote=True
    )
    test_column_names: list[str] = column_names_all_uppercase + [
        not_quoted_column_name,
        quoted_column_name_0,
        quoted_column_name_1,
        quoted_column_name_2,
    ]
    """
    This shuffle intersperses input "column_list" so to ensure that there is no dependency on position of column names
    that must be quoted.  Sorting in assertion below ensures that types are correct, regardless of column order.
    """  # noqa: E501 # FIXME CoP
    random.shuffle(test_column_names)

    metric_domain_kwargs: dict

    metric_domain_kwargs = get_dbms_compatible_metric_domain_kwargs(
        metric_domain_kwargs={"column_list": input_column_list},
        batch_columns_list=test_column_names,
    )
    assert sorted(metric_domain_kwargs["column_list"]) == sorted(output_column_list)


_CASE_PARAMS: Final[list[str]] = [
    "mixedCase",
    "UPPERCASE",
    "lowercase",
    '"quotedMixedCase"',
    '"QUOTED_UPPERCASE"',
    '"quoted_lowercase"',
]


@pytest.mark.unit
@pytest.mark.parametrize("input_str", _CASE_PARAMS)
class TestCaseInsensitiveString:
    @pytest.mark.parametrize("other", _CASE_PARAMS)
    def test__eq__(
        self,
        input_str: str,
        other: str,
    ):
        other_case_insensitive = CaseInsensitiveString(other)
        input_case_insensitive = CaseInsensitiveString(input_str)

        # if either string is quoted, they must be exact match
        if input_case_insensitive.is_quoted() or other_case_insensitive.is_quoted():
            if input == other:
                assert input_case_insensitive == other
                assert input_case_insensitive == other_case_insensitive
            assert input_case_insensitive != CaseInsensitiveString(other.swapcase())
        elif input_str.lower() == other.lower():
            assert input_case_insensitive == other.swapcase()
            assert input_case_insensitive == CaseInsensitiveString(other.swapcase())
        else:
            assert input_case_insensitive != other_case_insensitive
            assert input_case_insensitive != other


@pytest.mark.unit
def test_get_sqlalchemy_column_metadata_includes_primary_key_field(
    sql_data_connector_test_db_execution_engine,
):
    """Test that get_sqlalchemy_column_metadata includes primary_key field for all columns."""
    from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData
    from great_expectations.expectations.metrics.util import get_sqlalchemy_column_metadata

    engine = sql_data_connector_test_db_execution_engine

    # Test table with single primary key
    batch_data = SqlAlchemyBatchData(execution_engine=engine, table_name="table_with_single_pk")
    engine.load_batch_data("__test_single_pk", batch_data)

    columns = get_sqlalchemy_column_metadata(
        execution_engine=engine,
        table_selectable=sqlalchemy.quoted_name("table_with_single_pk", quote=False),
        schema_name=None,
    )

    assert columns is not None
    assert len(columns) == 3  # id, name, value

    # All columns should have primary_key field
    assert all("primary_key" in col for col in columns)

    # Only 'id' should be marked as primary key
    pk_columns = [col["name"] for col in columns if col["primary_key"]]
    assert pk_columns == ["id"]

    # Other columns should not be primary keys
    non_pk_columns = [col["name"] for col in columns if not col["primary_key"]]
    assert set(non_pk_columns) == {"name", "value"}


@pytest.mark.unit
def test_get_sqlalchemy_column_metadata_composite_primary_key(
    sql_data_connector_test_db_execution_engine,
):
    """Test that composite primary keys are correctly identified."""
    from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData
    from great_expectations.expectations.metrics.util import get_sqlalchemy_column_metadata

    engine = sql_data_connector_test_db_execution_engine

    batch_data = SqlAlchemyBatchData(execution_engine=engine, table_name="table_with_composite_pk")
    engine.load_batch_data("__test_composite_pk", batch_data)

    columns = get_sqlalchemy_column_metadata(
        execution_engine=engine,
        table_selectable=sqlalchemy.quoted_name("table_with_composite_pk", quote=False),
        schema_name=None,
    )

    assert columns is not None
    assert len(columns) == 4  # user_id, order_id, product, quantity

    # All columns should have primary_key field
    assert all("primary_key" in col for col in columns)

    # Both user_id and order_id should be marked as primary keys
    pk_columns = sorted([col["name"] for col in columns if col["primary_key"]])
    assert pk_columns == ["order_id", "user_id"]

    # Other columns should not be primary keys
    non_pk_columns = sorted([col["name"] for col in columns if not col["primary_key"]])
    assert non_pk_columns == ["product", "quantity"]


@pytest.mark.unit
def test_get_sqlalchemy_column_metadata_no_primary_key(
    sql_data_connector_test_db_execution_engine,
):
    """Test that tables without primary keys don't break."""
    from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData
    from great_expectations.expectations.metrics.util import get_sqlalchemy_column_metadata

    engine = sql_data_connector_test_db_execution_engine

    batch_data = SqlAlchemyBatchData(execution_engine=engine, table_name="table_without_pk")
    engine.load_batch_data("__test_no_pk", batch_data)

    columns = get_sqlalchemy_column_metadata(
        execution_engine=engine,
        table_selectable=sqlalchemy.quoted_name("table_without_pk", quote=False),
        schema_name=None,
    )

    assert columns is not None
    assert len(columns) == 2  # description, amount

    # All columns should have primary_key field
    assert all("primary_key" in col for col in columns)

    # No columns should be marked as primary keys
    pk_columns = [col["name"] for col in columns if col["primary_key"]]
    assert pk_columns == []

    # All columns should have primary_key=False
    assert all(not col["primary_key"] for col in columns)


@pytest.mark.unit
def test_get_sqlalchemy_column_metadata_quoted_pk_column(
    sql_data_connector_test_db_execution_engine,
):
    """Test that quoted column names as primary keys work correctly."""
    from great_expectations.execution_engine.sqlalchemy_batch_data import SqlAlchemyBatchData
    from great_expectations.expectations.metrics.util import get_sqlalchemy_column_metadata

    engine = sql_data_connector_test_db_execution_engine

    batch_data = SqlAlchemyBatchData(execution_engine=engine, table_name="table_with_quoted_pk")
    engine.load_batch_data("__test_quoted_pk", batch_data)

    columns = get_sqlalchemy_column_metadata(
        execution_engine=engine,
        table_selectable=sqlalchemy.quoted_name("table_with_quoted_pk", quote=False),
        schema_name=None,
    )

    assert columns is not None
    assert len(columns) == 2  # UserId, UserName

    # All columns should have primary_key field
    assert all("primary_key" in col for col in columns)

    # UserId should be marked as primary key
    pk_columns = [col["name"] for col in columns if col["primary_key"]]
    assert len(pk_columns) == 1
    # Case-insensitive check
    assert pk_columns[0].lower() == "userid"


@pytest.mark.unit
@patch("great_expectations.expectations.metrics.util.sa")
def test_get_dialect_like_pattern_expression_is_resilient_to_missing_dialects(mock_sqlalchemy):
    # arrange
    # force the test to not depend on _anything_ in sqlalchemy.dialects
    mock_sqlalchemy.dialects = None
    column = create_autospec(sa.Column)

    class SomeSpecificDialect: ...

    class MockDialect(ModuleType):
        dialect = SomeSpecificDialect

    like_pattern = "foo"

    # act
    # expect this test to not raise an AttributeError
    expression = get_dialect_like_pattern_expression(
        column=column, dialect=MockDialect(name="mock dialect"), like_pattern=like_pattern
    )

    # assert
    assert expression is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect_name,select_statement_factory,expected_sql,mock_params,should_fail_substitution",
    [
        pytest.param(
            "sqlite",
            lambda: sa.select(A.id, A.data).where(A.data == "test_value"),
            "SELECT a.id, a.data FROM a WHERE a.data = 'test_value'",
            {"data_1": "test_value"},
            False,
            id="string_param-sqlite",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(A.data == "test_value"),
            "SELECT a.id, a.data FROM a WHERE a.data = 'test_value'",
            {"data_1": "test_value"},
            False,
            id="string_param-postgresql",
        ),
        pytest.param(
            "databricks",
            lambda: sa.select(A.id, A.data).where(A.data == "test_value"),
            "SELECT a.id, a.data FROM a WHERE a.data = 'test_value'",
            {"data_1": "test_value"},
            False,
            id="string_param-databricks",
        ),
        pytest.param(
            "sqlite",
            lambda: sa.select(A.id, A.data).where(A.id == 42),
            "SELECT a.id, a.data FROM a WHERE a.id = 42",
            {"id_1": 42},
            False,
            id="int_param-sqlite",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(A.id == 42),
            "SELECT a.id, a.data FROM a WHERE a.id = 42",
            {"id_1": 42},
            False,
            id="int_param-postgresql",
        ),
        pytest.param(
            "sqlite",
            lambda: sa.select(A.id, A.data).where(A.id == 3.14),
            "SELECT a.id, a.data FROM a WHERE a.id = 3.14",
            {"id_1": 3.14},
            False,
            id="float_param-sqlite",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(A.id == 3.14),
            "SELECT a.id, a.data FROM a WHERE a.id = 3.14",
            {"id_1": 3.14},
            False,
            id="float_param-postgresql",
        ),
        pytest.param(
            "sqlite",
            lambda: sa.select(A.id, A.data).where(A.id.is_(True)),
            "SELECT a.id, a.data FROM a WHERE a.id = True",
            {"id_1": True},
            False,
            id="bool_param-sqlite",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(A.id.is_(True)),
            "SELECT a.id, a.data FROM a WHERE a.id = True",
            {"id_1": True},
            False,
            id="bool_param-postgresql",
        ),
        pytest.param(
            "sqlite",
            lambda: sa.select(A.id, A.data).where(A.data.is_(None)),
            "SELECT a.id, a.data FROM a WHERE a.data = None",
            {"data_1": None},
            False,
            id="none_param-sqlite",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(A.data.is_(None)),
            "SELECT a.id, a.data FROM a WHERE a.data = None",
            {"data_1": None},
            False,
            id="none_param-postgresql",
        ),
        pytest.param(
            "databricks",
            lambda: sa.select(A.id, A.data).where(
                sa.or_(A.data == "value1", sa.and_(A.id > 10, A.data.like("%end%")))
            ),
            "SELECT a.id, a.data FROM a WHERE a.data = 'value1' "
            "OR (a.id > 10 AND a.data LIKE '%end%')",
            {"data_1": "value1", "id_1": 10, "data_2": "%end%"},
            False,
            id="multiple_params-databricks",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(
                sa.or_(A.data == "value1", sa.and_(A.id > 10, A.data.like("%end%")))
            ),
            "SELECT a.id, a.data FROM a WHERE a.data = 'value1' "
            "OR (a.id > 10 AND a.data LIKE '%end%')",
            {"data_1": "value1", "id_1": 10, "data_2": "%end%"},
            False,
            id="multiple_params-postgresql",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data).where(A.data.like("%test%")),
            "SELECT a.id, a.data FROM a WHERE a.data LIKE '%test%'",
            {"data_1": "%test%"},
            True,
            id="like_pattern-postgresql-fallback",
        ),
        pytest.param(
            "mysql",
            lambda: sa.select(A.id, A.data).where(A.data.like("%test%")),
            "SELECT a.id, a.data FROM a WHERE a.data LIKE '%test%'",
            {"data_1": "%test%"},
            True,
            id="like_pattern-mysql-fallback",
        ),
        pytest.param(
            "redshift",
            lambda: sa.select(A.id, A.data).where(A.data.like("%test%")),
            "SELECT a.id, a.data FROM a WHERE a.data LIKE '%test%'",
            {"data_1": "%test%"},
            True,
            id="like_pattern-redshift-fallback",
        ),
        pytest.param(
            "snowflake",
            lambda: sa.select(A.id, A.data).where(A.data.like("%test%")),
            "SELECT a.id, a.data FROM a WHERE a.data LIKE '%test%'",
            {"data_1": "%test%"},
            False,
            id="like_pattern-snowflake",
        ),
        pytest.param(
            "sqlite",
            lambda: sa.select(A.id, A.data),
            "SELECT a.id, a.data FROM a",
            {},
            False,
            id="no_params-sqlite",
        ),
        pytest.param(
            "postgresql",
            lambda: sa.select(A.id, A.data),
            "SELECT a.id, a.data FROM a",
            {},
            False,
            id="no_params-postgresql",
        ),
    ],
)
def test_sqlalchemy_select_to_sql_string_parameter_styles(
    dialect_name: str,
    select_statement_factory: Callable[[], sa.Select],
    expected_sql: str,
    mock_params: dict,
    should_fail_substitution: bool,
    mocker: MockerFixture,
) -> None:
    """
    Test sqlalchemy_select_to_sql_string with to verify
    different parameter styles work correctly.

    Args:
        should_fail_substitution: If True, the render_postcompile path will return
            unsubstituted placeholders, forcing fallback to literal_binds. This tests
            the dialect_name usage for %% unescaping.
    """
    # Arrange
    select_statement = select_statement_factory()

    # Track which compile call we're on
    compile_call_count = [0]

    def mock_compile(engine, compile_kwargs=None):
        """Mock compile that returns different results based on compile_kwargs."""
        compile_call_count[0] += 1

        mock_compiled = mocker.MagicMock()
        mock_compiled.params = mock_params

        if compile_kwargs and compile_kwargs.get("render_postcompile"):
            # First call with render_postcompile=True
            if should_fail_substitution and mock_params:
                # Return query with placeholder to force fallback
                placeholder_query = expected_sql
                for param_name, param_value in mock_params.items():
                    # Replace first param value with placeholder to trigger fallback
                    param_value_repr = repr(param_value)
                    if param_value_repr in placeholder_query:
                        placeholder_query = placeholder_query.replace(
                            param_value_repr, f":{param_name}", 1
                        )
                        break
                mock_compiled.__str__ = lambda self: placeholder_query
            else:
                # Successful render_postcompile - return fully substituted SQL
                mock_compiled.__str__ = lambda self: expected_sql
        # Second call with literal_binds=True (only happens on fallback)
        # For dialects that escape %, return with %% to test unescaping
        elif dialect_name in ("postgresql", "mysql", "redshift") and "%" in expected_sql:
            escaped_sql = expected_sql.replace("%", "%%")
            mock_compiled.__str__ = lambda self: escaped_sql
        else:
            mock_compiled.__str__ = lambda self: expected_sql

        return mock_compiled

    # Patch select_statement.compile
    with patch.object(select_statement, "compile", side_effect=mock_compile):
        # Create a mock engine with the specified dialect
        mock_engine = create_autospec(SqlAlchemyExecutionEngine)
        mock_engine.dialect_name = dialect_name

        # Create a mock dialect and engine
        mock_dialect = create_autospec(Dialect)
        mock_dialect.name = dialect_name
        mock_engine.dialect = mock_dialect

        mock_sqlalchemy_engine = create_autospec(Engine)
        mock_sqlalchemy_engine.dialect = mock_dialect
        mock_engine.engine = mock_sqlalchemy_engine

        # Act
        result = sqlalchemy_select_to_sql_string(mock_engine, select_statement)

        # Assert
        assert result == expected_sql + ";"

        # Verify compile call count based on whether fallback was expected
        if should_fail_substitution:
            assert compile_call_count[0] == 2, (
                f"Expected 2 compile calls (render_postcompile + literal_binds fallback) "
                f"but got {compile_call_count[0]}"
            )
        else:
            assert compile_call_count[0] == 1, (
                f"Expected 1 compile call (successful render_postcompile) "
                f"but got {compile_call_count[0]}"
            )
