import timeit
import unittest
from unittest.mock import PropertyMock

import pandas as pd
import pytest

from great_expectations.compatibility import aws
from great_expectations.core.expectation_validation_result import (
    ExpectationValidationResult,
)
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from great_expectations.expectations import (
    ExpectColumnValuesToBeInSet,
)
from great_expectations.self_check.util import build_sa_validator_with_data
from great_expectations.util import is_library_loadable


@pytest.mark.skipif(
    not (aws.sqlalchemy_athena and is_library_loadable(library_name="pyathena")),
    reason="pyathena is not installed",
)
@pytest.mark.athena
@pytest.mark.external_sqldialect
def test_expect_column_values_to_be_of_type_string_dialect_pyathena(sa):
    df = pd.DataFrame({"col": ["test_val1", "test_val2"]})
    validator = build_sa_validator_with_data(
        df=df,
        sa_engine_name="sqlite",
        table_name="expect_column_values_to_be_of_type_string_dialect_pyathena_1",
    )

    # Monkey-patch dialect for testing purposes.
    validator.execution_engine.dialect_module = aws.sqlalchemy_athena

    result = validator.expect_column_values_to_be_of_type("col", type_="string")

    assert result == ExpectationValidationResult(
        success=True,
        expectation_config={
            "expectation_type": "expect_column_values_to_be_of_type",
            "kwargs": {
                "column": "col",
                "type_": "string",
            },
            "meta": {},
        },
        result={
            "element_count": 2,
            "unexpected_count": 0,
            "unexpected_percent": 0.0,
            "partial_unexpected_list": [],
            "missing_count": 0,
            "missing_percent": 0.0,
            "unexpected_percent_total": 0.0,
            "unexpected_percent_nonmissing": 0.0,
        },
        exception_info={
            "raised_exception": False,
            "exception_traceback": None,
            "exception_message": None,
        },
        meta={},
    )


@pytest.mark.sqlite
@pytest.mark.external_sqldialect
def test_expect_column_values_to_be_of_type_string_dialect_sqlite(sa):
    df = pd.DataFrame({"col": ["test_val1", "test_val2"]})
    validator = build_sa_validator_with_data(
        df=df,
        sa_engine_name="sqlite",
        table_name="expect_column_values_to_be_of_type_string_dialect_sqlite_1",
    )

    result = validator.expect_column_values_to_be_of_type("col", type_="TEXT")

    assert result == ExpectationValidationResult(
        success=True,
        expectation_config={
            "expectation_type": "expect_column_values_to_be_of_type",
            "kwargs": {
                "column": "col",
                "type_": "TEXT",
            },
            "meta": {},
        },
        result={
            "element_count": 2,
            "unexpected_count": 0,
            "unexpected_percent": 0.0,
            "partial_unexpected_list": [],
            "missing_count": 0,
            "missing_percent": 0.0,
            "unexpected_percent_total": 0.0,
            "unexpected_percent_nonmissing": 0.0,
        },
        exception_info={
            "raised_exception": False,
            "exception_traceback": None,
            "exception_message": None,
        },
        meta={},
    )


@pytest.mark.unit
def test_expect_column_values_to_be_in_set_render_performance():
    """
    This test prevents a historical bug in which rendering took ~10 seconds to render 400 items.
    """

    large_number = 150

    x = ExpectColumnValuesToBeInSet(
        column="foo_column_name", value_set=["foo" for _ in range(large_number)]
    )

    duration_s = timeit.timeit(x.render, number=1)
    assert duration_s < 1, f"Rendering took {duration_s} seconds"


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect_name",
    [
        GXSqlDialect.DATABRICKS,
        GXSqlDialect.POSTGRESQL,
        GXSqlDialect.SNOWFLAKE,
    ],
)
def test_expect_column_values_to_be_of_type_case_insensitivity(sa, dialect_name):
    df = pd.DataFrame(
        {
            "datetime_col": pd.Series(
                [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")], dtype="datetime64[ns]"
            ),
            "int_col": pd.Series([1, 2, None], dtype=pd.Int64Dtype()),
            "string_col": pd.Series(["apple", "banana", "cherry"], dtype=pd.StringDtype()),
            "bool_col": pd.Series([True, False, None], dtype=pd.BooleanDtype()),
        }
    )
    validator = build_sa_validator_with_data(
        df=df,
        sa_engine_name="sqlite",  # Using sqlite as base, will mock dialect
        table_name="type_test_table_parametrized",
    )

    # Mock the dialect_name property to test different SQL dialects
    with unittest.mock.patch.object(
        type(validator.execution_engine),
        "dialect_name",
        new_callable=PropertyMock,
        return_value=dialect_name,
    ):
        column_test_configs = [
            {"col_name": "datetime_col", "canonical_type": "DATETIME", "wrong_type": "INTEGER"},
            {"col_name": "int_col", "canonical_type": "BIGINT", "wrong_type": "STRING"},
            # For SQLite, pandas StringDtype typically maps to TEXT
            {"col_name": "string_col", "canonical_type": "TEXT", "wrong_type": "BOOLEAN"},
            {"col_name": "bool_col", "canonical_type": "BOOLEAN", "wrong_type": "DATE"},
        ]

        capitalization_variations = [
            lambda t: t.lower(),
            lambda t: t.upper(),
            lambda t: t.capitalize(),
        ]

        for config in column_test_configs:
            col_name = config["col_name"]
            canonical_type = config["canonical_type"]
            wrong_type = config["wrong_type"]

            # Test correct types with different capitalizations
            for cap_func in capitalization_variations:
                type_str = cap_func(canonical_type)
                result = validator.expect_column_values_to_be_of_type(col_name, type_=type_str)
                assert result.success is True, (
                    f"Expected success=True for type='{type_str}' on column '{col_name}' "
                    f"with dialect '{dialect_name}', "
                    f"but got success={result.success}. "
                    f"Observed value: {result.result.get('observed_value')}"
                )

            # Test incorrect type
            result = validator.expect_column_values_to_be_of_type(col_name, type_=wrong_type)
            assert result.success is False, (
                f"Expected success=False for wrong_type='{wrong_type}' on column '{col_name}' "
                f"with dialect '{dialect_name}', "
                f"but got success={result.success}. "
                f"Observed value: {result.result.get('observed_value')}"
            )


@pytest.mark.unit
def test_expect_column_values_to_be_of_type_result_contains_observed_value_for_pandas():
    """For Pandas with a non-object dtype column, _validate_pandas performs a schema-level
    type check and must return a result dict with 'observed_value', NOT the full Column Map
    format (element_count / unexpected_count / etc.).  Regression test for issue #11076."""
    import pandas as pd

    from great_expectations.core.expectation_validation_result import (
        ExpectationValidationResult,
    )
    from great_expectations.execution_engine import PandasExecutionEngine
    from great_expectations.validator.validator import Validator

    df = pd.DataFrame({"amount": pd.array([1, 2, 3], dtype="int64")})

    context = None
    try:
        from great_expectations.data_context import get_context

        context = get_context(mode="ephemeral")
    except Exception:
        pass

    engine = PandasExecutionEngine()

    # Simulate what build_pandas_engine_with_data would do.
    from great_expectations.core.batch import BatchDefinition
    from great_expectations.core.id_dict import BatchSpec

    batch_spec = BatchSpec(path="test")
    batch_definition = BatchDefinition(
        datasource_name="test",
        data_connector_name="test",
        data_asset_name="test",
        batch_identifiers={},
    )
    import pandas as pd

    engine.load_batch_data(
        batch_id="test_batch",
        batch_data=pd.DataFrame({"amount": pd.array([1, 2, 3], dtype="int64")}),
    )

    validator = Validator(execution_engine=engine)
    result: ExpectationValidationResult = validator.expect_column_values_to_be_of_type(
        "amount", type_="int64"
    )

    # The result must contain 'observed_value', not 'element_count' / 'unexpected_count'.
    assert "observed_value" in result.result, (
        f"Expected 'observed_value' key in result, got: {result.result}"
    )
    assert "element_count" not in result.result, (
        "'element_count' should not appear in aggregate-mode result (issue #11076)"
    )
    assert result.success is True
