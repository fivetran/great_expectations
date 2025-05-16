from typing import Any

import pandas as pd
import pytest

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
from tests.integration.data_sources_and_expectations.data_sources.test_source_to_target import (
    ALL_SOURCE_TO_TARGET_SOURCES,
)
from tests.integration.test_utils.data_source_config import SqliteDatasourceTestConfig

SQLITE_ONLY = [
    MultiSourceTestConfig(
        source=SqliteDatasourceTestConfig(),
        target=SqliteDatasourceTestConfig(),
    )
]

SOURCE_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

TARGET_DATA = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [4, 5, 6]})


@pytest.mark.parametrize(
    "target_query,source_query",
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
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_success(
    multi_source_batch: MultiSourceBatch, target_query: str, source_query: str
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=source_query.replace(
                "{source_table}", multi_source_batch.source_table_name
            ),
        )
    )
    assert result.success


@pytest.mark.parametrize(
    "target_query,source_query",
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
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_failure(
    multi_source_batch: MultiSourceBatch, target_query: str, source_query: str
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=source_query.replace(
                "{source_table}", multi_source_batch.source_table_name
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
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_mostly(
    multi_source_batch: MultiSourceBatch, mostly: float, success: bool
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT a, b FROM {batch} LIMIT 2",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT a, b FROM {multi_source_batch.source_table_name}",
            mostly=mostly,
        )
    )
    assert result.success is success


MAX_LENGTH_TARGET_DATA = pd.DataFrame(
    {
        "a": list(range(100, 300)),
        "b": list(range(100, 200)) + ([None] * 100),
        "c": list(range(200, 300)) + ([None] * 100),
        "no_dups": [1, 2, 3] + ([None] * 197),
        "has_dups": [1, 1, 2, 3] + ([None] * 196),
    }
)

MAX_LENGTH_SOURCE_DATA = pd.DataFrame(
    {
        "a": list(range(0, 200)),
        "b": list(range(100, 200)) + ([None] * 100),
        "high_numbers": list(range(1000, 1200)),
        "has_dups": [1, 1, 2, 3] + ([None] * 196),
    }
)


@pytest.mark.parametrize(
    "target_query,source_query,unexpected_percent,unexpected_count",
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
    target_data=MAX_LENGTH_TARGET_DATA,
    source_data=MAX_LENGTH_SOURCE_DATA,
)
def test_expect_query_results_to_match_source_unexpected_percent(
    multi_source_batch: MultiSourceBatch,
    target_query: str,
    source_query: str,
    unexpected_percent: float,
    unexpected_count: int,
):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=source_query.replace(
                "{source_table}", multi_source_batch.source_table_name
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
    ("target_query", "missing_rows", "unexpected_rows"),
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
    target_data=MISSING_AND_UNEXPECTED_DF,
    source_data=MISSING_AND_UNEXPECTED_DF,
)
def test_expect_query_results_to_match_source_missing_and_unexpected_values(
    multi_source_batch: MultiSourceBatch,
    target_query: str,
    missing_rows: list[dict[str, Any]],
    unexpected_rows: list[dict[str, Any]],
) -> None:
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT source FROM {multi_source_batch.source_table_name}",
        )
    )

    assert result.result["details"] == {
        "unexpected_rows": unexpected_rows,
        "missing_rows": missing_rows,
    }


@pytest.mark.parametrize(
    ("target_query", "source_query", "missing_rows", "unexpected_rows"),
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
    target_data=MISSING_AND_UNEXPECTED_DF,
    source_data=MISSING_AND_UNEXPECTED_DF,
)
def test_column_ordering(
    multi_source_batch: MultiSourceBatch,
    target_query: str,
    source_query: str,
    missing_rows: list[dict[str, Any]],
    unexpected_rows: list[dict[str, Any]],
) -> None:
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query=target_query,
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=source_query.replace(
                "{source_table}", multi_source_batch.source_table_name
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
    target_data=TOO_BIG_DATA,
    source_data=TOO_BIG_DATA,
)
def test_expect_query_results_to_match_source_limit(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name} ORDER BY a",
        )
    )
    assert result.success
    assert result.result["unexpected_count"] == 0

    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT * FROM {batch} ORDER BY a",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT * FROM {multi_source_batch.source_table_name} ORDER BY a DESC",
        )
    )
    assert not result.success
    assert result.result["unexpected_count"] == MAX_RESULT_RECORDS


@multi_source_batch_setup(
    multi_source_test_configs=ALL_SOURCE_TO_TARGET_SOURCES,
    target_data=TARGET_DATA,
    source_data=SOURCE_DATA,
)
def test_expect_query_results_to_match_source_error(multi_source_batch: MultiSourceBatch):
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT b FROM {batch}",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT invalid_column FROM {multi_source_batch.source_table_name}",
        )
    )
    assert not result.success
    assert list(result.exception_info.values())[0]["raised_exception"]


DATA_WITH_MANY_COLUMNS = pd.DataFrame({ch: [1, 2, 3] for ch in "abcdefgh"})
OTHER_DATA_WITH_MANY_COLUMNS = pd.DataFrame({ch: [4, 5, 6] for ch in "abcdefgh"})


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    target_data=DATA_WITH_MANY_COLUMNS,
    source_data=DATA_WITH_MANY_COLUMNS,
)
def test_rendering_no_differences(multi_source_batch: MultiSourceBatch):
    """NOTE: the queries here use kinda weird ordering to ensure that our output table
    actually reflects the right order.
    """
    source_table = multi_source_batch.source_table_name
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT e, a, d, g, b, e FROM {batch} ORDER BY e",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT g, d, g, c, e, a  FROM {source_table} ORDER BY g",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template="Unexpected records: $row_count",
                params={
                    "row_count": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 0,
                    }
                },
            ),
            value_type="TableType",
        ),
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template="Missing records: $row_count",
                params={
                    "row_count": {
                        "schema": RendererSchema(type=RendererValueType.NUMBER),
                        "value": 0,
                    }
                },
            ),
            value_type="TableType",
        ),
    ]


@multi_source_batch_setup(
    multi_source_test_configs=SQLITE_ONLY,
    target_data=DATA_WITH_MANY_COLUMNS,
    source_data=OTHER_DATA_WITH_MANY_COLUMNS,
)
def test_rendering_with_missing_and_unexpected(multi_source_batch: MultiSourceBatch):
    """NOTE: the queries here use kinda weird ordering to ensure that our output table
    actually reflects the right order.
    """
    source_table = multi_source_batch.source_table_name
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            target_query="SELECT a, b, c, d FROM {batch} ORDER BY e",
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT e, f, g, h  FROM {source_table} ORDER BY g",
        )
    )
    result.render()

    assert result.rendered_content == [
        RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template="Unexpected records: $row_count",
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
                template="Missing records: $row_count",
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
    source_data=pd.DataFrame({"foo": [1, 2, 3, 3]}),
    target_data=pd.DataFrame({"bar": [1, 4, 5, 5]}),
)
def test_rendering_with_one_column(multi_source_batch: MultiSourceBatch):
    source_table = multi_source_batch.source_table_name
    result = multi_source_batch.target_batch.validate(
        gxe.ExpectQueryResultsToMatchSource(
            source_data_source_name=multi_source_batch.source_data_source_name,
            source_query=f"SELECT foo FROM {source_table}",
            target_query="SELECT bar FROM {batch}",
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
