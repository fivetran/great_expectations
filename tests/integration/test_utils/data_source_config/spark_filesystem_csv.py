import pathlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

import pandas as pd
import pytest

from great_expectations.compatibility.pyspark import types as pyspark_types
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.data_asset.path.spark.csv_asset import CSVAsset
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.execution_engine import SparkDFExecutionEngine
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)

if TYPE_CHECKING:
    from great_expectations.compatibility import pyspark
    from great_expectations.compatibility.pyspark import types as pyspark_types


@dataclass(frozen=True)
class SparkFilesystemCsvDatasourceTestConfig(DataSourceTestConfig):
    # see "read" options: https://spark.apache.org/docs/3.5.3/sql-data-sources-csv.html#data-source-option
    read_options: dict[str, Any] = field(default_factory=dict)
    # see "write" options: https://spark.apache.org/docs/3.5.3/sql-data-sources-csv.html#data-source-option
    write_options: dict[str, Any] = field(default_factory=dict)

    @property
    @override
    def label(self) -> str:
        return "spark-filesystem-csv"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.spark

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        assert not extra_data, "extra_data is not supported for this data source yet."

        tmp_path = request.getfixturevalue("tmp_path")
        assert isinstance(tmp_path, pathlib.Path)

        return SparkFilesystemCsvBatchTestSetup(
            data=data,
            config=self,
            base_dir=tmp_path,
            context=context,
        )


class SparkFilesystemCsvBatchTestSetup(
    BatchTestSetup[SparkFilesystemCsvDatasourceTestConfig, CSVAsset]
):
    def __init__(
        self,
        config: SparkFilesystemCsvDatasourceTestConfig,
        data: pd.DataFrame,
        base_dir: pathlib.Path,
        context: AbstractDataContext,
    ) -> None:
        super().__init__(config=config, data=data, context=context)
        self._base_dir = base_dir

    @property
    def _spark_session(self) -> "pyspark.SparkSession":
        return SparkDFExecutionEngine.get_or_create_spark_session()

    @property
    def _spark_schema(self) -> Union["pyspark_types.StructType", None]:
        column_types = self.config.column_types or {}
        struct_fields = [
            pyspark_types.StructField(column_name, column_type())
            for column_name, column_type in column_types.items()
        ]
        return pyspark_types.StructType(struct_fields) if struct_fields else None

    @property
    def _spark_data(self) -> "pyspark.DataFrame":
        from pyspark.sql.types import _acceptable_types as spark_acceptable_types

        # Pandas 3's pd.NA and StringDtype inference break PySpark's
        # createDataFrame, so we extract plain-Python rows via itertuples,
        # replacing NA → None and coercing to PySpark-compatible types.
        schema = self._spark_schema

        # Per-column (target_type, acceptable_types) from PySpark's internal
        # _acceptable_types dict, e.g. IntegerType → (int, (int,)).
        # PySpark checks exact types (not isinstance), so we do the same.
        _TypeInfo = tuple[type, tuple[type, ...]]
        type_info_for_col: dict[str, _TypeInfo] = {
            f.name: (accepted[0], accepted)
            for f in (schema or [])
            if (accepted := spark_acceptable_types.get(type(f.dataType)))
        }
        column_type_info: tuple[_TypeInfo | None, ...] = tuple(
            type_info_for_col.get(c) for c in self.data.columns
        )

        def _clean(val: object, info: _TypeInfo | None) -> object:
            if pd.isna(val):  # type: ignore[call-overload]  # scalar from itertuples
                return None
            if info is not None:
                target, acceptable = info
                if type(val) not in acceptable:
                    # pd.Timestamp subclasses datetime but PySpark checks exact types
                    if isinstance(val, pd.Timestamp):
                        return val.to_pydatetime()
                    return target(val)
            return val

        rows = [
            tuple(_clean(val, info) for val, info in zip(record, column_type_info, strict=True))
            for record in self.data.itertuples(index=False, name=None)
        ]

        if schema:
            return self._spark_session.createDataFrame(rows, schema=schema)
        return self._spark_session.createDataFrame(rows, list(self.data.columns))

    @override
    def make_asset(self) -> CSVAsset:
        infer_schema = self._spark_schema is None
        return self.context.data_sources.add_spark_filesystem(
            name=self._random_resource_name(), base_directory=self._base_dir
        ).add_csv_asset(
            name=self._random_resource_name(),
            spark_schema=self._spark_schema,
            header=True,
            infer_schema=infer_schema,
            **self.config.read_options,
        )

    @override
    def make_batch(self) -> Batch:
        return (
            self.make_asset()
            .add_batch_definition_path(name=self._random_resource_name(), path=self.csv_path)
            .get_batch()
        )

    @override
    def setup(self) -> None:
        file_path = self._base_dir / self.csv_path
        self._spark_data.write.format("csv").option("header", True).options(
            **self.config.write_options
        ).save(str(file_path))

    @override
    def teardown(self) -> None: ...

    @property
    def csv_path(self) -> pathlib.Path:
        return pathlib.Path("data.csv")
