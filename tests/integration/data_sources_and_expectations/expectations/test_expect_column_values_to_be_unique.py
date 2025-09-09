from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
    NON_SQL_DATA_SOURCES,
    SQL_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config import (
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
)

UNIQUE_INTS = "unique_integers"
DUPLICATE_INTS = "duplicate_integers"
UNIQUE_STRINGS = "unique_strings"
DUPLICATE_STRINGS = "duplicate_strings"
UNIQUE_WITH_NULL = "unique_with_null"
DUPLICATE_WITH_NULL = "duplicate_with_null"

DATA = pd.DataFrame(
    {
        UNIQUE_INTS: [1, 2, 3, 4],
        DUPLICATE_INTS: [1, 2, 3, 3],
        UNIQUE_STRINGS: ["a", "b", "c", "d"],
        DUPLICATE_STRINGS: ["a", "b", "c", "c"],
        UNIQUE_WITH_NULL: [1, 2, None, None],
        DUPLICATE_WITH_NULL: [1, 1, None, None],
    },
    dtype="object",
)

SUPPORTED_SQL_DATASOURCES = [
    ds
    for ds in SQL_DATA_SOURCES
    if not isinstance(ds, MySQLDatasourceTestConfig)  # why don't we support MySQL?
]


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete_non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeUnique(
        column=UNIQUE_INTS,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SUPPORTED_SQL_DATASOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeUnique(
        column=UNIQUE_INTS,
    )
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 4,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "missing_count": 0,
        "missing_percent": 0.0,
        "unexpected_percent_total": 0.0,
        "unexpected_percent_nonmissing": 0.0,
        "unexpected_index_query": ANY,
        "partial_unexpected_counts": [],
        "unexpected_list": [],
    }


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(
                column=UNIQUE_INTS,
            ),
            id="unique_integers",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(
                column=UNIQUE_STRINGS,
            ),
            id="unique_strings",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(
                column=UNIQUE_WITH_NULL,
            ),
            id="unique_with_null",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(column=DUPLICATE_INTS, mostly=0.5),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeUnique,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(
                column=DUPLICATE_INTS,
            ),
            id="duplicate_integers",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(
                column=DUPLICATE_STRINGS,
            ),
            id="duplicate_strings",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(
                column=DUPLICATE_WITH_NULL,
            ),
            id="duplicate_nulls",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeUnique(column=DUPLICATE_INTS, mostly=0.7),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeUnique,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_include_unexpected_rows_pandas(batch_for_datasource: Batch) -> None:
    """Test include_unexpected_rows for ExpectColumnValuesToBeUnique with pandas data sources."""
    expectation = gxe.ExpectColumnValuesToBeUnique(column=DUPLICATE_INTS)
    result = batch_for_datasource.validate(
        expectation, result_format={"result_format": "BASIC", "include_unexpected_rows": True}
    )

    assert not result.success
    result_dict = result["result"]

    # Verify that unexpected_rows is present and contains the expected data
    assert "unexpected_rows" in result_dict
    assert result_dict["unexpected_rows"] is not None

    # For pandas data sources, unexpected_rows should be directly usable
    unexpected_rows_data = result_dict["unexpected_rows"]
    assert isinstance(unexpected_rows_data, pd.DataFrame)

    # Convert directly to DataFrame for pandas data sources
    unexpected_rows_df = unexpected_rows_data

    # Should contain 2 rows where DUPLICATE_INTS has duplicate value 3
    # (both occurrences are flagged)
    assert len(unexpected_rows_df) == 2

    # Both unexpected rows should have value 3 in DUPLICATE_INTS
    assert all(unexpected_rows_df[DUPLICATE_INTS] == 3)

    # Other columns should have their original values
    unexpected_strings = sorted(unexpected_rows_df[DUPLICATE_STRINGS].tolist())
    assert unexpected_strings == ["c", "c"]


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig()], data=DATA
)
def test_include_unexpected_rows_sql(batch_for_datasource: Batch) -> None:
    """Test include_unexpected_rows for ExpectColumnValuesToBeUnique with SQL data sources."""
    expectation = gxe.ExpectColumnValuesToBeUnique(column=DUPLICATE_INTS)
    result = batch_for_datasource.validate(
        expectation, result_format={"result_format": "BASIC", "include_unexpected_rows": True}
    )

    assert not result.success
    result_dict = result["result"]

    # Verify that unexpected_rows is present and contains the expected data
    assert "unexpected_rows" in result_dict
    assert result_dict["unexpected_rows"] is not None

    unexpected_rows_data = result_dict["unexpected_rows"]
    assert isinstance(unexpected_rows_data, list)

    # Should contain 2 rows where DUPLICATE_INTS has duplicate value 3
    # (both occurrences are flagged)
    assert len(unexpected_rows_data) == 2

    # Check that the duplicate values appear in the unexpected rows data
    unexpected_rows_str = str(unexpected_rows_data)
    assert "3" in unexpected_rows_str
    assert "c" in unexpected_rows_str
