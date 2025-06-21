import uuid
from typing import Any

import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.compatibility.postgresql as postgresql_dialect
import great_expectations.expectations as gxe
from great_expectations.expectations.metrics.util import MAX_RESULT_RECORDS
from great_expectations.render.components import (
    AtomicDiagnosticRendererType,
    RenderedAtomicContent,
    RenderedAtomicValue,
)
from great_expectations.render.renderer.observed_value_renderer import ObservedValueRenderState
from great_expectations.render.renderer_configuration import (
    MetaNotesFormat,
    RendererSchema,
    RendererTableValue,
    RendererValueType,
)
from tests.integration.conftest import (
    MultiSourceBatch,
    MultiSourceTestConfig,
    multi_source_batch_setup,
)
from tests.integration.data_sources_and_expectations.data_sources.test_comparison_to_base import (
    ALL_COMPARISON_TO_BASE_SOURCES,
)
from tests.integration.test_utils.data_source_config import SqliteDatasourceTestConfig
from tests.integration.test_utils.data_source_config.postgres import (
    PostgresBatchTestSetup,
    PostgreSQLDatasourceTestConfig,
)

SQLITE_ONLY = [
    MultiSourceTestConfig(
        comparison=SqliteDatasourceTestConfig(),
        base=SqliteDatasourceTestConfig(),
    )
]

COMPARISON_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

BASE_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [4, 5, 6]})


@pytest.mark.parametrize(
    "base_query,comparison_query",
    [
        pytest.param(
            "SELECT a, b FROM {batch} ORDER BY a, b",
            "SELECT a, b FROM {source_table} ORDER BY a, b",
            id="multiple_columns_multiple_rows",
        ),
        pytest.param(
            "SELECT a FROM {batch} ORDER BY a",
            "SELECT a FROM {source_table} ORDER BY a",
            id="one_column_multiple_rows",
        ),
        pytest.param(
            "SELECT a, b FROM {batch} ORDER BY b LIMIT 1",
            "SELECT a, b FROM {source_table} ORDER BY b LIMIT 1",
            id="multiple_columns_one_row",
        ),
        pytest.param(
            "SELECT a, b FROM {batch} LIMIT 0",
            "SELECT a, b FROM {source_table} LIMIT 0",
            id="both_results_are_empty",
        ),
        pytest.param(
            "SELECT a, c FROM {batch} ORDER BY c",
            "SELECT a, b FROM {source_table} ORDER BY b",
            id="column_names_different_values_the_same",
        ),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
    base_data=BASE_DATA,
    comparison_data=COMPARISON_DATA,
)
def test_expect_query_results_to_match_comparison_success(
    multi_source_batch: MultiSourceBatch, base_query: str, comparison_query: str
):
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query=base_query,
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=comparison_query.replace(
                "{source_table}", multi_source_batch.comparison_table_name
            ),
        )
    )
    assert result.success


@pytest.mark.parametrize(
    "base_query,comparison_query",
    [
        pytest.param(
            "SELECT * FROM {batch}",
            "SELECT * FROM {source_table}",
            id="duplicate_values_across_rows",
        ),
        pytest.param(
            "SELECT a, b FROM {batch} LIMIT 2",
            "SELECT a, b FROM {source_table}",
            id="row_count_mismatch",
        ),
        pytest.param(
            "SELECT a FROM {batch} ORDER BY a",
            "SELECT b FROM {source_table} ORDER BY a",
            id="column_value_mismatch",
        ),
        pytest.param(
            "SELECT * FROM {batch} LIMIT 0",
            "SELECT * FROM {source_table} ORDER BY a",
            id="one_result_is_empty",
        ),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
    base_data=BASE_DATA,
    comparison_data=COMPARISON_DATA,
)
def test_expect_query_results_to_match_comparison_failure(
    multi_source_batch: MultiSourceBatch, base_query: str, comparison_query: str
):
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query=base_query,
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=comparison_query.replace(
                "{source_table}", multi_source_batch.comparison_table_name
            ),
        )
    )
    assert not result.success
    assert not result.exception_info["raised_exception"]


@pytest.mark.parametrize(
    "mostly,success",
    [
        pytest.param(0.9, False, id="mostly_failure"),
        pytest.param(0.5, True, id="mostly_success"),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=BASE_DATA,
    comparison_data=COMPARISON_DATA,
)
def test_expect_query_results_to_match_comparison_mostly(
    multi_source_batch: MultiSourceBatch, mostly: float, success: bool
):
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT a, b FROM {batch} LIMIT 2",
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT a, b FROM {multi_source_batch.comparison_table_name}",
            mostly=mostly,
        )
    )
    assert result.success is success


MAX_LENGTH_BASE_DATA = pd.DataFrame(
    {
        "a": list(range(100, 300)),
        "b": list(range(100, 200)) + ([None] * 100),
        "c": list(range(200, 300)) + ([None] * 100),
        "no_dups": [1, 2, 3] + ([None] * 197),
        "has_dups": [1, 1, 2, 3] + ([None] * 196),
    }
)

MAX_LENGTH_COMPARISON_DATA = pd.DataFrame(
    {
        "a": list(range(0, 200)),
        "b": list(range(100, 200)) + ([None] * 100),
        "high_numbers": list(range(1000, 1200)),
        "has_dups": [1, 1, 2, 3] + ([None] * 196),
    }
)


@pytest.mark.parametrize(
    "base_query,comparison_query,unexpected_percent,unexpected_count",
    [
        pytest.param(
            "SELECT b FROM {batch} ORDER BY b",  # 100 records
            "SELECT b FROM {source_table} ORDER BY b",  # 100 records
            0,
            0,
            id="only_match",
        ),
        pytest.param(
            "SELECT a FROM {batch}",  # 200 records (half match)
            "SELECT b FROM {source_table}",  # 100 records
            50,
            100,
            id="match_and_unexpected",
        ),
        pytest.param(
            "SELECT b FROM {batch} ORDER BY b",  # 100 records
            "SELECT a FROM {source_table}",  # 200 records (half match)
            50,
            100,
            id="match_and_missing",
        ),
        pytest.param(
            "SELECT a FROM {batch}",  # 200 low numbers
            "SELECT high_numbers FROM {source_table}",  # 200 high numbers
            100,
            200,
            id="missing_and_unexpected",
        ),
        pytest.param(
            "SELECT a FROM {batch}",  # 200 records (half match)
            "SELECT a FROM {source_table}",  # 200 records
            50,
            100,
            id="match_and_missing_and_unexpected",
        ),
        pytest.param(
            "SELECT a FROM {batch}",  # 200 records
            "SELECT b FROM {source_table}",  # 100 different records
            50,
            100,
            id="only_unexpected",
        ),
        pytest.param(
            "SELECT c FROM {batch} ORDER BY c",  # 100 records
            "SELECT * FROM {source_table} LIMIT 0",  # 0 records
            100,
            200,
            id="only_missing",
        ),
        pytest.param(
            "SELECT * FROM {batch} LIMIT 0",  # 0 records
            "SELECT * FROM {source_table} LIMIT 0",  # 0 records
            0,
            0,
            id="nothing_to_compare",
        ),
        pytest.param(
            "SELECT has_dups FROM {batch}",  # 4 records (2 are dups)
            "SELECT has_dups FROM {source_table}",  # same 4 records
            0,
            0,
            id="has_dups_success",
        ),
        pytest.param(
            "SELECT no_dups FROM {batch}",  # 3 records (no dups)
            "SELECT has_dups FROM {source_table}",  # same 3 records + 1 dup
            1 / 200 * 100,
            1,
            id="has_dups_failure",
        ),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=MAX_LENGTH_BASE_DATA,
    comparison_data=MAX_LENGTH_COMPARISON_DATA,
)
def test_expect_query_results_to_match_comparison_unexpected_percent(
    multi_source_batch: MultiSourceBatch,
    base_query: str,
    comparison_query: str,
    unexpected_percent: float,
    unexpected_count: int,
):
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query=base_query,
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=comparison_query.replace(
                "{source_table}", multi_source_batch.comparison_table_name
            ),
        )
    )
    assert result.result["unexpected_percent"] == pytest.approx(unexpected_percent)
    assert result.result["unexpected_count"] == unexpected_count


MISSING_AND_UNEXPECTED_DF = pd.DataFrame(
    {
        "id": [1, 1, 1, 2, 2, 3],
        "incorrect_id": [1, 1, 1, 2, 2, 4],
        "source": list("AAABBC"),
        "all_matches": list("CBBAAA"),
        "all_matches_reversed": list("CBBAAA"),
        "missing_and_unexpected": list("AAAAAD"),
    }
)


@pytest.mark.parametrize(
    ("base_query", "missing_rows", "unexpected_rows"),
    [
        pytest.param(
            "SELECT all_matches FROM {batch}",
            [],
            [],
            id="all_match",
        ),
        pytest.param(
            "SELECT all_matches_reversed FROM {batch}",
            [],
            [],
            id="all_match_order_agnostic",
        ),
        pytest.param(
            "SELECT missing_and_unexpected FROM {batch}",
            [
                {"source": "B"},
                {"source": "B"},
                {"source": "C"},
            ],
            [
                {"missing_and_unexpected": "A"},
                {"missing_and_unexpected": "A"},
                {"missing_and_unexpected": "D"},
            ],
            id="some_matches_missing_and_unexpected",
        ),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=MISSING_AND_UNEXPECTED_DF,
    comparison_data=MISSING_AND_UNEXPECTED_DF,
)
def test_expect_query_results_to_match_comparison_missing_and_unexpected_values(
    multi_source_batch: MultiSourceBatch,
    base_query: str,
    missing_rows: list[dict[str, Any]],
    unexpected_rows: list[dict[str, Any]],
) -> None:
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query=base_query,
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT source FROM {multi_source_batch.comparison_table_name}",
        )
    )

    assert result.result["details"] == {
        "unexpected_rows": unexpected_rows,
        "missing_rows": missing_rows,
    }


@pytest.mark.parametrize(
    ("base_query", "comparison_query", "missing_rows", "unexpected_rows"),
    [
        pytest.param(
            "SELECT incorrect_id, source FROM {batch}",
            "SELECT id, source FROM {source_table}",
            [{"source": "C", "id": 3}],
            [{"source": "C", "incorrect_id": 4}],
            id="One bad row, but others match despite col names",
        ),
        pytest.param(
            "SELECT id, source FROM {batch}",
            "SELECT source, id FROM {source_table}",
            [
                {"source": "A", "id": 1},
                {"source": "A", "id": 1},
                {"source": "A", "id": 1},
                {"source": "B", "id": 2},
                {"source": "B", "id": 2},
                {"source": "C", "id": 3},
            ],
            [
                {"source": "A", "id": 1},
                {"source": "A", "id": 1},
                {"source": "A", "id": 1},
                {"source": "B", "id": 2},
                {"source": "B", "id": 2},
                {"source": "C", "id": 3},
            ],
            id="Same data, but cols in the wrong order",
        ),
    ],
)
@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=MISSING_AND_UNEXPECTED_DF,
    comparison_data=MISSING_AND_UNEXPECTED_DF,
)
def test_column_ordering(
    multi_source_batch: MultiSourceBatch,
    base_query: str,
    comparison_query: str,
    missing_rows: list[dict[str, Any]],
    unexpected_rows: list[dict[str, Any]],
) -> None:
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query=base_query,
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=comparison_query.replace(
                "{source_table}", multi_source_batch.comparison_table_name
            ),
        )
    )

    assert result.result["details"] == {
        "unexpected_rows": unexpected_rows,
        "missing_rows": missing_rows,
    }


TOO_BIG_DATA = pd.DataFrame({"a": list(range(0, 500)), "b": list(range(100, 600))})


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=TOO_BIG_DATA,
    comparison_data=TOO_BIG_DATA,
)
def test_expect_query_results_to_match_comparison_limit(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT * FROM {batch} ORDER BY a",
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT * FROM {multi_source_batch.comparison_table_name} ORDER BY a",
        )
    )
    assert result.success
    assert result.result["unexpected_count"] == 0

    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT * FROM {batch} ORDER BY a",
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT * FROM {multi_source_batch.comparison_table_name} "
            "ORDER BY a DESC",
        )
    )
    assert not result.success
    assert result.result["unexpected_count"] == MAX_RESULT_RECORDS


@multi_source_batch_setup(
    multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
    base_data=BASE_DATA,
    comparison_data=COMPARISON_DATA,
)
def test_expect_query_results_to_match_comparison_error(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT b FROM {batch}",
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query="SELECT invalid_column FROM "
            f"{multi_source_batch.comparison_table_name}",
        )
    )
    assert not result.success
    assert list(result.exception_info.values())[0]["raised_exception"]


DATA_WITH_MANY_COLUMNS = pd.DataFrame({ch: [1, 2, 3] for ch in "abcdefgh"})
OTHER_DATA_WITH_MANY_COLUMNS = pd.DataFrame({ch: [4, 5, 6] for ch in "abcdefgh"})


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=DATA_WITH_MANY_COLUMNS,
    comparison_data=DATA_WITH_MANY_COLUMNS,
)
def test_rendering_no_differences(multi_source_batch: MultiSourceBatch):
    """NOTE: the queries here use kinda weird ordering to ensure that our output table
    actually reflects the right order.
    """
    source_table = multi_source_batch.comparison_table_name
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT e, a, d, g, b, e FROM {batch} ORDER BY e",
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT g, d, g, c, e, a  FROM {source_table} ORDER BY g",
        )
    )
    result.render()

    assert result.rendered_content == []


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    base_data=DATA_WITH_MANY_COLUMNS,
    comparison_data=OTHER_DATA_WITH_MANY_COLUMNS,
)
def test_rendering_with_missing_and_unexpected(multi_source_batch: MultiSourceBatch):
    """NOTE: the queries here use kinda weird ordering to ensure that our output table
    actually reflects the right order.
    """
    source_table = multi_source_batch.comparison_table_name
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            base_query="SELECT a, b, c, d FROM {batch} ORDER BY e",
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT e, f, g, h  FROM {source_table} ORDER BY g",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template="Unexpected rows found in current table: $row_count",
                params={
                    "row_count": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 3,
                    }
                },
                header_row=[
                    RendererTableValue(
                        schema=RendererSchema(type=RendererValueType.STRING),
                        value=col_name,
                    )
                    for col_name in ["a", "b", "c", "d"]
                ],
                table=[
                    [
                        RendererTableValue(
                            schema=RendererSchema(type=RendererValueType.NUMBER),
                            value=value,
                        )
                        for _ in ["a", "b", "c", "d"]
                    ]
                    for value in [1, 2, 3]
                ],
            ),
            value_type="TableType",
        ),
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template="Expected rows not found in current table: $row_count",
                params={
                    "row_count": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 3,
                    }
                },
                header_row=[
                    RendererTableValue(
                        schema=RendererSchema(type=RendererValueType.STRING),
                        value=col_name,
                    )
                    for col_name in ["e", "f", "g", "h"]
                ],
                table=[
                    [
                        RendererTableValue(
                            schema=RendererSchema(type=RendererValueType.NUMBER),
                            value=value,
                        )
                        for _ in ["e", "f", "g", "h"]
                    ]
                    for value in [4, 5, 6]
                ],
            ),
            value_type="TableType",
        ),
    ]


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    comparison_data=pd.DataFrame({"foo": [1, 2, 3, 3]}),
    base_data=pd.DataFrame({"bar": [1, 4, 5, 5]}),
)
def test_rendering_with_one_column(multi_source_batch: MultiSourceBatch):
    source_table = multi_source_batch.comparison_table_name
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT foo FROM {source_table}",
            base_query="SELECT bar FROM {batch}",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value_type="StringValueType",
            value=RenderedAtomicValue(
                schema={"type": "com.superconductive.rendered.string"},
                meta_notes={"format": MetaNotesFormat.STRING, "content": []},
                template="$ov__0 $ov__1 $ov__2 $exp__0 $exp__1 $exp__2",
                params={
                    "expected_value": {
                        "schema": RendererSchema(type=RendererValueType.ARRAY),
                        "value": [2, 3, 3],
                    },
                    "observed_value": {
                        "schema": RendererSchema(type=RendererValueType.ARRAY),
                        "value": [4, 5, 5],
                    },
                    "exp__0": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.MISSING,
                        "value": 2,
                    },
                    "exp__1": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.MISSING,
                        "value": 3,
                    },
                    "exp__2": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.MISSING,
                        "value": 3,
                    },
                    "ov__0": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.UNEXPECTED,
                        "value": 4,
                    },
                    "ov__1": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.UNEXPECTED,
                        "value": 5,
                    },
                    "ov__2": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.UNEXPECTED,
                        "value": 5,
                    },
                },
            ),
        )
    ]


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    comparison_data=pd.DataFrame({"foo": [1]}),
    base_data=pd.DataFrame({"bar": [2]}),
)
def test_rendering_with_one_value(multi_source_batch: MultiSourceBatch):
    source_table = multi_source_batch.comparison_table_name
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT foo FROM {source_table}",
            base_query="SELECT bar FROM {batch}",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value_type="StringValueType",
            value=RenderedAtomicValue(
                schema={"type": "com.superconductive.rendered.string"},
                template="Observed value: $base_value",
                params={
                    "base_value": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 2,
                    },
                },
            ),
        ),
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value_type="StringValueType",
            value=RenderedAtomicValue(
                schema={"type": "com.superconductive.rendered.string"},
                template="Expected value: $comparison_value",
                params={
                    "comparison_value": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 1,
                    },
                },
            ),
        ),
    ]


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    comparison_data=pd.DataFrame({"foo": [1, 2, 3]}),
    base_data=pd.DataFrame({"bar": []}),
)
def test_rendering_only_missing_rows_single_column(multi_source_batch: MultiSourceBatch):
    """Test rendering when only missing_rows exist with single column."""
    source_table = multi_source_batch.comparison_table_name
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT foo FROM {source_table}",
            base_query="SELECT bar FROM {batch}",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value_type="StringValueType",
            value=RenderedAtomicValue(
                schema={"type": "com.superconductive.rendered.string"},
                meta_notes={"format": MetaNotesFormat.STRING, "content": []},
                template="$exp__0 $exp__1 $exp__2",
                params={
                    "expected_value": {
                        "schema": RendererSchema(type=RendererValueType.ARRAY),
                        "value": [1, 2, 3],
                    },
                    "observed_value": {
                        "schema": RendererSchema(type=RendererValueType.ARRAY),
                        "value": [],
                    },
                    "exp__0": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.MISSING,
                        "value": 1,
                    },
                    "exp__1": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.MISSING,
                        "value": 2,
                    },
                    "exp__2": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.MISSING,
                        "value": 3,
                    },
                },
            ),
        )
    ]


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    comparison_data=pd.DataFrame({"foo": []}),
    base_data=pd.DataFrame({"bar": [1, 2, 3]}),
)
def test_rendering_only_unexpected_rows_single_column(multi_source_batch: MultiSourceBatch):
    """Test rendering when only unexpected_rows exist with single column."""
    source_table = multi_source_batch.comparison_table_name
    result = multi_source_batch.base_batch.validate(
        gxe.ExpectQueryResultsToMatchComparison(
            comparison_data_source_name=multi_source_batch.comparison_data_source_name,
            comparison_query=f"SELECT foo FROM {source_table}",
            base_query="SELECT bar FROM {batch}",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value_type="StringValueType",
            value=RenderedAtomicValue(
                schema={"type": "com.superconductive.rendered.string"},
                meta_notes={"format": MetaNotesFormat.STRING, "content": []},
                template="$ov__0 $ov__1 $ov__2",
                params={
                    "expected_value": {
                        "schema": RendererSchema(type=RendererValueType.ARRAY),
                        "value": [],
                    },
                    "observed_value": {
                        "schema": RendererSchema(type=RendererValueType.ARRAY),
                        "value": [1, 2, 3],
                    },
                    "ov__0": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.UNEXPECTED,
                        "value": 1,
                    },
                    "ov__1": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.UNEXPECTED,
                        "value": 2,
                    },
                    "ov__2": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "render_state": ObservedValueRenderState.UNEXPECTED,
                        "value": 3,
                    },
                },
            ),
        )
    ]


@pytest.mark.postgresql
def test_unhashable_data_types():
    df = pd.DataFrame({"json_data": [{"foo": "bar"}]})
    context = gx.get_context(mode="ephemeral")
    batch_setup_a = PostgresBatchTestSetup(
        config=PostgreSQLDatasourceTestConfig(
            column_types={"json_data": postgresql_dialect.postgresqltypes.JSONB}
        ),
        data=df,
        extra_data={},
        context=context,
    )
    batch_setup_b = PostgresBatchTestSetup(
        config=PostgreSQLDatasourceTestConfig(
            column_types={"json_data": postgresql_dialect.postgresqltypes.JSONB}
        ),
        data=df,
        extra_data={},
        context=context,
    )

    with (
        batch_setup_a.batch_test_context() as batch_a,
        batch_setup_b.asset_test_context() as asset_b,
    ):
        data_source_name = asset_b.datasource.name
        source_table = asset_b.table_name
        expectation = gxe.ExpectQueryResultsToMatchComparison(
            comparison_data_source_name=data_source_name,
            comparison_query=f"SELECT * FROM {source_table}",
            base_query="SELECT * FROM {batch}",
        )

        result = batch_a.validate(expectation)

        assert result.exception_info["exception_message"] == "Unhashable column: json_data"


uuid_a = uuid.uuid4()
uuid_b = uuid.uuid4()
uuid_c = uuid.uuid4()
uuid_d = uuid.uuid4()


@pytest.mark.postgresql
def test_rendering_table_with_multiple_uuid():
    context = gx.get_context(mode="ephemeral")
    batch_setup_a = PostgresBatchTestSetup(
        config=PostgreSQLDatasourceTestConfig(
            column_types={"id": postgresql_dialect.postgresqltypes.UUID}
        ),
        data=pd.DataFrame({"name": ["a", "b"], "id": [uuid_a, uuid_b]}),
        extra_data={},
        context=context,
    )
    batch_setup_b = PostgresBatchTestSetup(
        config=PostgreSQLDatasourceTestConfig(
            column_types={"id": postgresql_dialect.postgresqltypes.UUID}
        ),
        data=pd.DataFrame({"name": ["a", "b"], "id": [uuid_c, uuid_d]}),
        extra_data={},
        context=context,
    )

    with (
        batch_setup_a.batch_test_context() as batch_a,
        batch_setup_b.asset_test_context() as asset_b,
    ):
        data_source_name = asset_b.datasource.name
        source_table = asset_b.table_name

        result = batch_a.validate(
            gxe.ExpectQueryResultsToMatchComparison(
                comparison_data_source_name=data_source_name,
                comparison_query=f"SELECT name, id FROM {source_table}",
                base_query="SELECT name, id FROM {batch}",
            )
        )
        result.render()

        assert result.rendered_content == [
            _create_table_rendered_atomic_content(
                template="Unexpected rows found in current table: $row_count",
                params={
                    "row_count": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 2,
                    }
                },
                col_names=["name", "id"],
                col_types=[RendererValueType.STRING, RendererValueType.STRING],
                rows=[
                    ["a", uuid_a],
                    ["b", uuid_b],
                ],
            ),
            _create_table_rendered_atomic_content(
                template="Expected rows not found in current table: $row_count",
                params={
                    "row_count": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 2,
                    }
                },
                col_names=["name", "id"],
                col_types=[RendererValueType.STRING, RendererValueType.STRING],
                rows=[
                    ["a", uuid_c],
                    ["b", uuid_d],
                ],
            ),
        ]


def _create_table_rendered_atomic_content(
    template: str,
    params: dict[str, Any],
    col_names: list[str],
    col_types: list[RendererValueType],
    rows: list[list[str]],
) -> RenderedAtomicContent:
    return RenderedAtomicContent(
        name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
        value=RenderedAtomicValue(
            template=template,
            params=params,
            header_row=[
                RendererTableValue(
                    schema=RendererSchema(type=RendererValueType.STRING),
                    value=col_name,
                )
                for col_name in col_names
            ],
            table=[
                [
                    RendererTableValue(
                        schema=RendererSchema(type=col_type),
                        value=cell_value,
                    )
                    for cell_value, col_type in zip(row, col_types)
                ]
                for row in rows
            ],
        ),
        value_type="TableType",
    )


@multi_source_batch_setup(
    multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
    base_data=BASE_DATA,
    comparison_data=COMPARISON_DATA,
)
def test_success_with_suite_param_base_query_(
    multi_source_batch: MultiSourceBatch,
) -> None:
    suite_param_key = "test_expect_query_results_to_match_comparison"

    expectation = gxe.ExpectQueryResultsToMatchComparison(
        base_query={"$PARAMETER": suite_param_key},
        comparison_data_source_name=multi_source_batch.comparison_data_source_name,
        comparison_query=f"SELECT a, b FROM {multi_source_batch.comparison_table_name} ORDER BY a, b",  # noqa: E501
    )

    result = multi_source_batch.base_batch.validate(
        expectation,
        expectation_parameters={suite_param_key: "SELECT a, b FROM {batch} ORDER BY a, b"},
    )
    assert result.success


@multi_source_batch_setup(
    multi_source_test_configs=ALL_COMPARISON_TO_BASE_SOURCES,
    base_data=BASE_DATA,
    comparison_data=COMPARISON_DATA,
)
def test_success_with_suite_param_comparison_query_(
    multi_source_batch: MultiSourceBatch,
) -> None:
    suite_param_key = "test_expect_query_results_to_match_comparison"

    expectation = gxe.ExpectQueryResultsToMatchComparison(
        base_query="SELECT a, b FROM {batch} ORDER BY a, b",
        comparison_data_source_name=multi_source_batch.comparison_data_source_name,
        comparison_query={"$PARAMETER": suite_param_key},
    )

    result = multi_source_batch.base_batch.validate(
        expectation,
        expectation_parameters={
            suite_param_key: f"SELECT a, b FROM {multi_source_batch.comparison_table_name} ORDER BY a, b"  # noqa: E501
        },
    )
    assert result.success
