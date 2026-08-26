from __future__ import annotations

from pprint import pformat as pf
from typing import TYPE_CHECKING, ClassVar, Dict, List, Literal, Optional, Type

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.batch import LegacyBatchDefinition
from great_expectations.core.batch_spec import PathBatchSpec
from great_expectations.core.id_dict import IDDict
from great_expectations.datasource.fluent import BatchParameters, BatchRequest
from great_expectations.datasource.fluent.constants import _DATA_CONNECTOR_NAME
from great_expectations.datasource.fluent.interfaces import Batch, DataAsset, Datasource
from great_expectations.exceptions.exceptions import BuildBatchRequestError
from great_expectations.execution_engine.duckdb_execution_engine import DuckDBExecutionEngine

if TYPE_CHECKING:
    from great_expectations.core.partitioners import ColumnPartitioner
    from great_expectations.datasource.fluent.data_connector.batch_filter import BatchSlice
    from great_expectations.datasource.fluent.interfaces import BatchMetadata


@public_api
class _DuckDBDataAsset(DataAsset):
    """A DuckDB DataAsset is a whole-file DataAsset: each Batch is the entire file."""

    @override
    def test_connection(self) -> None: ...

    @override
    def get_batch_parameters_keys(
        self, partitioner: Optional[ColumnPartitioner] = None
    ) -> tuple[str, ...]:
        return tuple()

    @override
    def get_batch_identifiers_list(self, batch_request: BatchRequest) -> List[dict]:
        return [IDDict(batch_request.options)]

    @override
    def build_batch_request(
        self,
        options: Optional[BatchParameters] = None,
        batch_slice: Optional[BatchSlice] = None,
        partitioner: Optional[ColumnPartitioner] = None,
    ) -> BatchRequest:
        """A batch request that can be used to obtain batches for this DataAsset.

        Args:
            options: This is not currently supported and must be {}/None for this data asset.
            batch_slice: This is not currently supported and must be None for this data asset.
            partitioner: This is not currently supported and must be None for this data asset.

        Returns:
            A BatchRequest object that can be used to obtain a batch from an Asset by calling
            the get_batch method.
        """
        if options:
            raise BuildBatchRequestError(
                message="options is not currently supported for this DataAsset "
                "and must be None or {}."
            )
        if batch_slice is not None:
            raise BuildBatchRequestError(
                message="batch_slice is not currently supported for this DataAsset "
                "and must be None."
            )
        if partitioner is not None:
            raise BuildBatchRequestError(
                message="partitioner is not currently supported for this DataAsset "
                "and must be None."
            )

        return BatchRequest(
            datasource_name=self.datasource.name,
            data_asset_name=self.name,
            options={},
        )

    @override
    def _validate_batch_request(self, batch_request: BatchRequest) -> None:
        if not (
            batch_request.datasource_name == self.datasource.name
            and batch_request.data_asset_name == self.name
            and not batch_request.options
        ):
            expect_batch_request_form = BatchRequest(
                datasource_name=self.datasource.name,
                data_asset_name=self.name,
                options={},
            )
            raise BuildBatchRequestError(
                message="BatchRequest should have form:\n"
                f"{pf(expect_batch_request_form.dict())}\n"
                f"but actually has form:\n{pf(batch_request.dict())}\n"
            )

    def _build_batch_spec(self) -> PathBatchSpec:
        raise NotImplementedError

    @override
    def get_batch(self, batch_request: BatchRequest) -> Batch:
        self._validate_batch_request(batch_request)

        batch_spec = self._build_batch_spec()
        execution_engine: DuckDBExecutionEngine = self.datasource.get_execution_engine()
        data, markers = execution_engine.get_batch_data_and_markers(batch_spec=batch_spec)

        batch_definition = LegacyBatchDefinition(
            datasource_name=self.datasource.name,
            data_connector_name=_DATA_CONNECTOR_NAME,
            data_asset_name=self.name,
            batch_identifiers=IDDict(batch_request.options),
            batch_spec_passthrough=None,
        )

        batch_metadata: BatchMetadata = self._get_batch_metadata_from_batch_request(
            batch_request=batch_request
        )

        return Batch(
            datasource=self.datasource,
            data_asset=self,
            batch_request=batch_request,
            data=data,
            metadata=batch_metadata,
            batch_markers=markers,
            batch_spec=batch_spec,
            batch_definition=batch_definition,
        )


class CSVAsset(_DuckDBDataAsset):
    type: Literal["csv"] = "csv"
    path: str
    reader_options: Dict = pydantic.Field(default_factory=dict)

    @override
    def _build_batch_spec(self) -> PathBatchSpec:
        return PathBatchSpec(
            path=self.path,
            reader_method="read_csv",
            reader_options=dict(self.reader_options),
        )


class ParquetAsset(_DuckDBDataAsset):
    type: Literal["parquet"] = "parquet"
    path: str
    reader_options: Dict = pydantic.Field(default_factory=dict)

    @override
    def _build_batch_spec(self) -> PathBatchSpec:
        return PathBatchSpec(
            path=self.path,
            reader_method="read_parquet",
            reader_options=dict(self.reader_options),
        )


@public_api
class DuckDBDatasource(Datasource):
    """Adds a DuckDB datasource to the data context, backed directly by the `duckdb`
    package rather than a SQLAlchemy dialect.

    Args:
        name: The name of this DuckDB datasource.
        assets: An optional dictionary whose keys are DataAsset names and whose values are
            DataAsset objects.
    """

    asset_types: ClassVar[List[Type[DataAsset]]] = [CSVAsset, ParquetAsset]

    type: Literal["duckdb"] = "duckdb"
    assets: List[CSVAsset | ParquetAsset] = []

    @property
    @override
    def execution_engine_type(self) -> Type[DuckDBExecutionEngine]:
        return DuckDBExecutionEngine

    @override
    def test_connection(self, test_assets: bool = True) -> None:
        pass

    @public_api
    def add_csv_asset(
        self,
        name: str,
        path: str,
        reader_options: Optional[Dict] = None,
        batch_metadata: Optional[BatchMetadata] = None,
    ) -> CSVAsset:
        """Adds a CSV asset, read directly by DuckDB via `read_csv`, to this datasource.

        Args:
            name: The name of this asset.
            path: The path to the CSV file to read.
            reader_options: Additional keyword arguments passed through to DuckDB's `read_csv`.
            batch_metadata: An arbitrary dictionary for a caller to annotate the asset.

        Returns:
            The CSVAsset added.
        """
        asset = CSVAsset(
            name=name,
            path=path,
            reader_options=reader_options or {},
            batch_metadata=batch_metadata or {},
        )
        return self._add_asset(asset)

    @public_api
    def add_parquet_asset(
        self,
        name: str,
        path: str,
        reader_options: Optional[Dict] = None,
        batch_metadata: Optional[BatchMetadata] = None,
    ) -> ParquetAsset:
        """Adds a Parquet asset, read directly by DuckDB via `read_parquet`, to this datasource.

        Args:
            name: The name of this asset.
            path: The path to the Parquet file to read.
            reader_options: Additional keyword arguments passed through to DuckDB's `read_parquet`.
            batch_metadata: An arbitrary dictionary for a caller to annotate the asset.

        Returns:
            The ParquetAsset added.
        """
        asset = ParquetAsset(
            name=name,
            path=path,
            reader_options=reader_options or {},
            batch_metadata=batch_metadata or {},
        )
        return self._add_asset(asset)
