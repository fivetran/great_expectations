import pathlib
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import pandas as pd
import pytest

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.duckdb_datasource import CSVAsset
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


@dataclass(frozen=True)
class DuckDBFilesystemCsvDatasourceTestConfig(DataSourceTestConfig):
    """DuckDB reading a CSV file straight off disk.

    Deliberately shaped after `PandasFilesystemCsvDatasourceTestConfig` rather than after the
    SQL configs: `DuckDBExecutionEngine` does not go through SQLAlchemy, has no connection
    string, and no table to create or drop, so it carries none of the coordinates a
    `SqlBackendSpec` exists to declare (marker/lane/compose service/dev-requirements for a
    containerized server). Membership in the standard suite is therefore stated the same way
    the other two file-backed data sources state it - by appearing in a hand-written list in
    `tiers.py` - and not through the SQL backend registry.
    """

    # Two different libraries touch the file, so the two option bags go to two different APIs.
    # pandas writes it, because that is the type the shared fixture data arrives as; DuckDB only
    # ever reads it back.
    #
    # Read side -- forwarded to the DuckDB connection's `read_csv`; the options it accepts are
    # listed at https://duckdb.org/docs/stable/data/csv/overview.html
    read_options: dict[str, Any] = field(default_factory=dict)
    # Write side -- forwarded to `pandas.DataFrame.to_csv`; see
    # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
    write_options: dict[str, Any] = field(default_factory=dict)

    @property
    @override
    def label(self) -> str:
        return "duckdb-filesystem-csv"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.duckdb

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        assert not extra_data, "extra_data is not supported for this data source."
        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)

        return DuckDBFilesystemCsvBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
            context=context,
        )


class DuckDBFilesystemCsvBatchTestSetup(
    BatchTestSetup[DuckDBFilesystemCsvDatasourceTestConfig, CSVAsset]
):
    def __init__(
        self,
        config: DuckDBFilesystemCsvDatasourceTestConfig,
        data: pd.DataFrame,
        base_dir: pathlib.Path,
        context: AbstractDataContext,
    ) -> None:
        super().__init__(config=config, data=data, context=context)
        self._base_dir = base_dir

    @override
    def make_asset(self) -> CSVAsset:
        return self.context.data_sources.add_duckdb(
            name=self._random_resource_name(),
        ).add_csv_asset(
            name=self._random_resource_name(),
            path=str(self.csv_path),
            reader_options=dict(self.config.read_options),
        )

    @override
    def make_batch(self) -> Batch:
        asset = self.make_asset()
        return asset.get_batch(asset.build_batch_request())

    @override
    def setup(self) -> None:
        self.data.to_csv(self.csv_path, index=False, **self.config.write_options)

    @override
    def teardown(self) -> None: ...

    @property
    def csv_path(self) -> pathlib.Path:
        return self._base_dir / "data.csv"
