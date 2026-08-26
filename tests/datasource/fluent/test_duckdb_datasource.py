from __future__ import annotations

import pytest

import great_expectations as gx
from great_expectations.datasource.fluent.duckdb_datasource import (
    CSVAsset,
    DuckDBDatasource,
    ParquetAsset,
)
from great_expectations.execution_engine.duckdb_batch_data import DuckDBBatchData

pytestmark = pytest.mark.unit


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,x\n2,y\n3,\n4,z\n10,w\n")
    return str(path)


@pytest.fixture
def duckdb_datasource() -> DuckDBDatasource:
    context = gx.get_context(mode="ephemeral")
    return context.data_sources.add_duckdb(name="duckdb_ds")


def test_add_duckdb_datasource_registers_factory(duckdb_datasource: DuckDBDatasource):
    assert duckdb_datasource.type == "duckdb"
    assert duckdb_datasource.execution_engine_type.__name__ == "DuckDBExecutionEngine"


def test_add_csv_asset(duckdb_datasource: DuckDBDatasource, csv_path: str):
    asset = duckdb_datasource.add_csv_asset(name="my_csv", path=csv_path)
    assert isinstance(asset, CSVAsset)
    assert asset.path == csv_path
    assert duckdb_datasource.get_asset("my_csv") is asset


def test_get_batch_reads_csv_directly(duckdb_datasource: DuckDBDatasource, csv_path: str):
    asset = duckdb_datasource.add_csv_asset(name="my_csv", path=csv_path)
    batch_request = asset.build_batch_request()
    batch = duckdb_datasource.get_batch(batch_request)

    assert isinstance(batch.data, DuckDBBatchData)
    assert batch.data.relation.fetchall() == [
        (1, "x"),
        (2, "y"),
        (3, None),
        (4, "z"),
        (10, "w"),
    ]


def test_add_parquet_asset(duckdb_datasource: DuckDBDatasource):
    asset = duckdb_datasource.add_parquet_asset(
        name="my_parquet", path="/tmp/does_not_exist.parquet"
    )
    assert isinstance(asset, ParquetAsset)
    assert asset.type == "parquet"


def test_build_batch_request_rejects_options(duckdb_datasource: DuckDBDatasource, csv_path: str):
    from great_expectations.exceptions.exceptions import BuildBatchRequestError

    asset = duckdb_datasource.add_csv_asset(name="my_csv", path=csv_path)
    with pytest.raises(BuildBatchRequestError):
        asset.build_batch_request(options={"unsupported": "value"})


class TestExpectationsAgainstDuckDBCSV:
    def test_row_count_and_mean_expectations_pass(
        self, duckdb_datasource: DuckDBDatasource, csv_path: str
    ):
        asset = duckdb_datasource.add_csv_asset(name="my_csv", path=csv_path)
        context = duckdb_datasource.data_context
        assert context is not None
        validator = context.get_validator(batch_request=asset.build_batch_request())

        row_count_result = validator.expect_table_row_count_to_equal(5)
        assert row_count_result.success

        mean_result = validator.expect_column_mean_to_be_between(
            column="a", min_value=3, max_value=5
        )
        assert mean_result.success
        assert mean_result.result["observed_value"] == 4.0

        min_result = validator.expect_column_min_to_be_between(column="a", min_value=0, max_value=1)
        assert min_result.success

        max_result = validator.expect_column_max_to_be_between(
            column="a", min_value=10, max_value=10
        )
        assert max_result.success


@pytest.fixture
def category_csv_path(tmp_path):
    path = tmp_path / "category.csv"
    path.write_text("a,b\n1,cat\n2,dog\n3,bird\n4,zzz\n10,cat\n")
    return str(path)


class TestMapExpectationsAgainstDuckDBCSV:
    """Covers the "does every row satisfy X" map-metric path, distinct from the
    table/column aggregate metrics covered above."""

    def _validator(self, duckdb_datasource: DuckDBDatasource, path: str):
        asset = duckdb_datasource.add_csv_asset(name="my_csv", path=path)
        context = duckdb_datasource.data_context
        assert context is not None
        return context.get_validator(batch_request=asset.build_batch_request())

    def test_not_be_null_and_be_null(self, duckdb_datasource: DuckDBDatasource, csv_path: str):
        validator = self._validator(duckdb_datasource, csv_path)

        not_null_result = validator.expect_column_values_to_not_be_null(column="b")
        assert not not_null_result.success
        assert not_null_result.result["unexpected_count"] == 1
        assert not_null_result.result["partial_unexpected_list"] == [None]

        all_present_result = validator.expect_column_values_to_not_be_null(column="a")
        assert all_present_result.success

        be_null_result = validator.expect_column_values_to_be_null(column="b", mostly=0.1)
        assert be_null_result.success
        assert be_null_result.result["unexpected_count"] == 4

    def test_in_set_and_not_in_set(
        self, duckdb_datasource: DuckDBDatasource, category_csv_path: str
    ):
        validator = self._validator(duckdb_datasource, category_csv_path)

        in_set_result = validator.expect_column_values_to_be_in_set(
            column="b", value_set=["cat", "dog", "bird"]
        )
        assert not in_set_result.success
        assert in_set_result.result["partial_unexpected_list"] == ["zzz"]

        not_in_set_result = validator.expect_column_values_to_not_be_in_set(
            column="b", value_set=["zzz"]
        )
        assert not not_in_set_result.success
        assert not_in_set_result.result["partial_unexpected_list"] == ["zzz"]

    def test_match_regex(self, duckdb_datasource: DuckDBDatasource, category_csv_path: str):
        validator = self._validator(duckdb_datasource, category_csv_path)

        result = validator.expect_column_values_to_match_regex(column="b", regex="^[a-z]+$")
        assert result.success

        result_fail = validator.expect_column_values_to_match_regex(column="b", regex="^cat$")
        assert not result_fail.success
        assert result_fail.result["unexpected_count"] == 3

    def test_between(self, duckdb_datasource: DuckDBDatasource, category_csv_path: str):
        validator = self._validator(duckdb_datasource, category_csv_path)

        result = validator.expect_column_values_to_be_between(column="a", min_value=1, max_value=5)
        assert not result.success
        assert result.result["partial_unexpected_list"] == [10]
