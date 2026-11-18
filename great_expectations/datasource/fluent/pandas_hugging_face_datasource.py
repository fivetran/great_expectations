from __future__ import annotations

import threading
import warnings
from typing import TYPE_CHECKING, Any, ClassVar, List, Literal, Optional, Sequence, Type

import pandas as pd

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility import datasets, pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.batch import LegacyBatchDefinition
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.batch_spec import RuntimeDataBatchSpec
from great_expectations.core.id_dict import IDDict
from great_expectations.datasource.fluent.batch_request import BatchParameters, BatchRequest
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.constants import _DATA_CONNECTOR_NAME
from great_expectations.datasource.fluent.interfaces import (
    Batch,
    BatchMetadata,
    DataAsset,
)
from great_expectations.datasource.fluent.pandas_datasource import _PandasDatasource

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.data_connector.batch_filter import BatchSlice

_ENDPOINT_LOCK = threading.RLock()


class HuggingFaceDatasourceError(Exception):
    """Raised when a Hugging Face dataset cannot be materialized."""


class HuggingFaceBatchDefinition(BatchDefinition):
    """A named configuration and split to load from a Hugging Face repository."""

    id: Optional[str] = None
    name: str
    config: Optional[str] = None
    split: Optional[str] = None
    whole_config: bool = False
    partitioner: None = None

    @override
    def build_batch_request(
        self, batch_parameters: Optional[BatchParameters] = None
    ) -> BatchRequest:
        invalid = set(batch_parameters or {}) - {"revision"}
        if invalid:
            message = (
                f"Only 'revision' may be provided as a batch parameter; got {sorted(invalid)}."
            )
            raise ValueError(message)
        options: BatchParameters = {
            "config": self.config,
            "split": self.split,
            "whole_config": self.whole_config,
        }
        options.update(batch_parameters or {})
        return self.data_asset.build_batch_request(options=options)

    @override
    def get_batch(self, batch_parameters: Optional[BatchParameters] = None) -> Batch:
        return self.data_asset.get_batch(self.build_batch_request(batch_parameters))


class HuggingFaceDatasetAsset(DataAsset):
    """A tabular dataset from a Hugging Face repository."""

    type: Literal["hugging_face_dataset"] = "hugging_face_dataset"
    columns: Optional[List[str]] = None
    batch_definitions: List[HuggingFaceBatchDefinition] = pydantic.Field(default_factory=list)

    @override
    def test_connection(self) -> None:
        if not self.batch_definitions:
            return
        self.batch_definitions[0].get_batch()

    @override
    def get_batch_parameters_keys(self, partitioner: None = None) -> tuple[str, ...]:
        return ("config", "split", "whole_config", "revision")

    @override
    def get_batch_identifiers_list(self, batch_request: BatchRequest) -> List[dict]:
        return [IDDict(batch_request.options)]

    @override
    def build_batch_request(
        self,
        options: Optional[BatchParameters] = None,
        batch_slice: Optional[BatchSlice] = None,
        partitioner: None = None,
    ) -> BatchRequest:
        if batch_slice is not None or partitioner is not None:
            message = "Hugging Face dataset assets do not support batch slices or partitioners."
            raise gx_exceptions.InvalidBatchRequestError(message)
        options = dict(options or {})
        if not {"config", "split", "whole_config"}.issubset(options):
            message = "Use a HuggingFaceBatchDefinition to select a configuration and split."
            raise gx_exceptions.InvalidBatchRequestError(message)
        invalid = set(options) - set(self.get_batch_parameters_keys())
        if invalid:
            message = (
                f"Unsupported Hugging Face batch parameter(s): {sorted(invalid)}. "
                "Supported parameters are config, split, whole_config, and revision."
            )
            raise gx_exceptions.InvalidBatchRequestError(message)
        return BatchRequest(
            datasource_name=self.datasource.name,
            data_asset_name=self.name,
            options=options,
        )

    @override
    def _validate_batch_request(self, batch_request: BatchRequest) -> None:
        if (
            batch_request.datasource_name != self.datasource.name
            or batch_request.data_asset_name != self.name
            or not {"config", "split", "whole_config"}.issubset(batch_request.options)
        ):
            message = (
                "Batch request must identify this Hugging Face asset and include its "
                "configuration and split selection."
            )
            raise gx_exceptions.InvalidBatchRequestError(message)

    @override
    def get_batch(self, batch_request: BatchRequest) -> Batch:
        self._validate_batch_request(batch_request)
        source: PandasHuggingFaceDatasource = self.datasource
        opts = batch_request.options
        dataset = source._load_dataset(
            config=opts["config"],
            split=opts["split"],
            whole_config=opts["whole_config"],
            revision=opts.get("revision"),
        )
        try:
            dataframe = dataset if isinstance(dataset, pd.DataFrame) else dataset.to_pandas()
        except Exception:
            message = (
                "The selected Hugging Face dataset could not be converted to a Pandas "
                "DataFrame. Use a map-style dataset with scalar tabular features."
            )
            raise HuggingFaceDatasourceError(message) from None
        if self.columns is not None:
            missing = [column for column in self.columns if column not in dataframe.columns]
            if missing:
                message = (
                    f"Requested Hugging Face column(s) are missing: {missing}. "
                    f"Available columns: {list(dataframe.columns)}."
                )
                raise HuggingFaceDatasourceError(message)
            dataframe = dataframe.loc[:, self.columns]
        complex_columns = [
            column
            for column in dataframe.columns
            if dataframe[column].map(lambda value: not pd.api.types.is_scalar(value)).any()
        ]
        if complex_columns:
            message = (
                "Hugging Face features containing nested or non-scalar values are not supported "
                f"by this datasource. Unsupported columns: {complex_columns}."
            )
            raise HuggingFaceDatasourceError(message)

        spec = RuntimeDataBatchSpec(batch_data=dataframe)
        data, markers = source.get_execution_engine().get_batch_data_and_markers(spec)
        metadata: BatchMetadata = self._get_batch_metadata_from_batch_request(batch_request)
        legacy_definition = LegacyBatchDefinition(
            datasource_name=source.name,
            data_connector_name=_DATA_CONNECTOR_NAME,
            data_asset_name=self.name,
            batch_identifiers=IDDict(batch_request.options),
            batch_spec_passthrough=None,
        )
        return Batch(
            datasource=source,
            data_asset=self,
            batch_request=batch_request,
            data=data,
            metadata=metadata,
            batch_markers=markers,
            batch_spec=spec,
            batch_definition=legacy_definition,
        )

    def add_batch_definition_split(
        self, name: str, config: Optional[str], split: str
    ) -> HuggingFaceBatchDefinition:
        """Add a batch definition for one Hugging Face dataset split.

        Args:
            name: Name of the batch definition.
            config: Dataset configuration or subset. Use ``None`` for the default.
            split: Hugging Face split expression, such as ``"train[:10%]"``.

        Returns:
            The added batch definition.
        """
        return self._add_hf_batch_definition(
            name=name, config=config, split=split, whole_config=False
        )

    def add_batch_definition_whole_config(
        self, name: str, config: Optional[str]
    ) -> HuggingFaceBatchDefinition:
        """Add a batch definition that loads and combines all splits in a configuration.

        Args:
            name: Name of the batch definition.
            config: Dataset configuration or subset. Use ``None`` for the default.

        Returns:
            The added batch definition.
        """
        return self._add_hf_batch_definition(
            name=name, config=config, split=None, whole_config=True
        )

    def _add_hf_batch_definition(
        self, name: str, config: Optional[str], split: Optional[str], whole_config: bool
    ) -> HuggingFaceBatchDefinition:
        if any(definition.name == name for definition in self.batch_definitions):
            message = f'BatchDefinition "{name}" already exists on asset "{self.name}".'
            raise ValueError(message)
        definition = HuggingFaceBatchDefinition(
            name=name, config=config, split=split, whole_config=whole_config
        )
        definition.set_data_asset(self)
        self.batch_definitions.append(definition)
        self.update_batch_definition_field_set()
        if self.datasource.data_context:
            try:
                self.datasource.add_batch_definition(definition)
            except Exception:
                self.batch_definitions.remove(definition)
                self.update_batch_definition_field_set()
                raise
        return definition


class PandasHuggingFaceDatasource(_PandasDatasource):
    """Pandas backed datasource for datasets hosted on Hugging Face Hub.

    Args:
        name: Name of this datasource.
        repository: Hugging Face dataset repository identifier.
        token: Optional Hub token, either a secret value or a GX config-variable template.
        hf_endpoint: Hugging Face Hub endpoint URL.
        assets: Optional dataset assets to attach to this datasource.
    """

    asset_types: ClassVar[List[Type[DataAsset]]] = [HuggingFaceDatasetAsset]
    type: Literal["pandas_hugging_face"] = "pandas_hugging_face"
    assets: List[HuggingFaceDatasetAsset] = pydantic.Field(default_factory=list)
    _EXTRA_EXCLUDED_EXEC_ENG_ARGS: ClassVar[set[str]] = {
        "repository",
        "token",
        "hf_endpoint",
    }

    repository: str
    token: Optional[ConfigStr | pydantic.SecretStr] = None
    hf_endpoint: str = "https://huggingface.co"

    @override
    def test_connection(self, test_assets: bool = True) -> None:
        if test_assets:
            for asset in self.assets:
                asset.test_connection()

    def add_dataset_asset(
        self,
        name: str,
        columns: Optional[Sequence[str]] = None,
        batch_metadata: Optional[BatchMetadata] = None,
    ) -> HuggingFaceDatasetAsset:
        """Add a Hugging Face dataset asset.

        Args:
            name: Name of the GX asset.
            columns: Optional columns to retain when materializing a batch.
            batch_metadata: User metadata inherited by batches from this asset.

        Returns:
            The added Hugging Face dataset asset.
        """
        return self._add_asset(
            HuggingFaceDatasetAsset(
                name=name,
                columns=list(columns) if columns is not None else None,
                batch_metadata=batch_metadata or {},
            )
        )

    def _load_dataset(
        self,
        config: Optional[str],
        split: Optional[str],
        whole_config: bool,
        revision: Optional[str],
    ) -> Any:
        if self.token is None:
            warnings.warn(
                "No Hugging Face token is configured for this datasource. The Hugging Face "
                "Datasets client may use credentials saved with `hf auth login`; run that "
                "command to authentication and improved rate limits.",
                UserWarning,
                stacklevel=2,
            )
        try:
            package = datasets.get_datasets_module()
            result = self._request_dataset(package, config, split, whole_config, revision)
        except ModuleNotFoundError as err:
            if "optional 'datasets' package" in str(err):
                raise
            message = (
                f"Could not load Hugging Face repository '{self.repository}'. Check that the "
                "repository, configuration, split, revision, and credentials are valid."
            )
            raise HuggingFaceDatasourceError(message) from None
        except Exception:
            # Do not include exception text: library errors can contain request URLs or tokens.
            message = (
                f"Could not load Hugging Face repository '{self.repository}'. Check access, "
                "the configuration, split, revision, and Hub endpoint."
            )
            raise HuggingFaceDatasourceError(message) from None
        return self._materialize_dataset(package, result, whole_config)

    def _request_dataset(
        self,
        package: Any,
        config: Optional[str],
        split: Optional[str],
        whole_config: bool,
        revision: Optional[str],
    ) -> Any:
        kwargs: dict[str, Any] = {
            "split": None if whole_config else split,
            "revision": revision,
            "token": self._resolved_token(),
        }
        if config is not None:
            kwargs["name"] = config
        if not package:
            return datasets.load_dataset(self.repository, **kwargs)
        # Serialize the temporary endpoint override to avoid cross-thread contamination.
        with _ENDPOINT_LOCK:
            old_endpoint = package.config.HF_ENDPOINT
            package.config.HF_ENDPOINT = self.hf_endpoint.rstrip("/")
            try:
                return datasets.load_dataset(self.repository, **kwargs)
            finally:
                package.config.HF_ENDPOINT = old_endpoint

    @staticmethod
    def _materialize_dataset(package: Any, result: Any, whole_config: bool) -> Any:
        if whole_config:
            if not hasattr(result, "values"):
                message = "Loading the whole configuration did not return a DatasetDict."
                raise HuggingFaceDatasourceError(message)
            pieces = list(result.values())
            if not pieces:
                return pd.DataFrame()
            concatenate = getattr(package, "concatenate_datasets", None)
            if concatenate is None:
                message = "The installed datasets package cannot combine configuration splits."
                raise HuggingFaceDatasourceError(message)
            result = concatenate(pieces)
        if not hasattr(result, "to_pandas"):
            message = (
                "Streaming Hugging Face datasets are not supported. Disable streaming and "
                "use a map-style Dataset."
            )
            raise HuggingFaceDatasourceError(message)
        return result

    def _resolved_token(self) -> Optional[str]:
        if self.token is None:
            return None
        if isinstance(self.token, ConfigStr) and self._config_provider:
            return self.token.get_config_value(self._config_provider)
        return self.token.get_secret_value()
