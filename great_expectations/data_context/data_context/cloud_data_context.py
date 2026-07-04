from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Literal,
    Mapping,
    Optional,
    Union,
)

import great_expectations.exceptions as gx_exceptions
from great_expectations._docs_decorators import public_api
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context.cloud_constants import (
    CLOUD_DEFAULT_BASE_URL,
    GXCloudEnvironmentVariable,
)
from great_expectations.data_context.data_context.serializable_data_context import (
    SerializableDataContext,
)

if TYPE_CHECKING:
    from great_expectations.alias_types import PathStr
    from great_expectations.checkpoint.checkpoint import Checkpoint
    from great_expectations.core.suite_parameters import SuiteParameterDict
    from great_expectations.data_context.types.base import (
        DataContextConfig,
        GXCloudConfig,
    )

SHUTDOWN_MESSAGE: str = (
    "GX Cloud has been shut down, so this no longer functions and "
    "will be removed in great_expectations 2.0."
)


OPTIONAL_CLOUD_CONFIG_KEYS = [GXCloudEnvironmentVariable.WORKSPACE_ID]


@dataclass
class Workspace:
    id: str
    role: str


@dataclass
class CloudUserInfo:
    user_id: uuid.UUID
    workspaces: list[Workspace]


@public_api
class CloudDataContext(SerializableDataContext):
    """Subclass of AbstractDataContext for working in a GX Cloud-backed environment.

    GX Cloud has been shut down. The backend this class relied on no longer exists,
    so constructing a ``CloudDataContext`` now raises immediately instead of attempting
    to connect. This class is kept importable for source compatibility and will be
    removed in great_expectations 2.0.
    """  # FIXME CoP

    def __init__(  # noqa: PLR0913 # FIXME CoP
        self,
        project_config: Optional[Union[DataContextConfig, Mapping]] = None,
        context_root_dir: Optional[PathStr] = None,
        project_root_dir: Optional[PathStr] = None,
        runtime_environment: Optional[dict] = None,
        cloud_base_url: Optional[str] = None,
        cloud_access_token: Optional[str] = None,
        cloud_organization_id: Optional[str] = None,
        cloud_workspace_id: Optional[str] = None,
        user_agent_str: Optional[str] = None,
    ) -> None:
        """
        CloudDataContext constructor

        Args:
            project_config (DataContextConfig): config for CloudDataContext
            runtime_environment (dict):  a dictionary of config variables that override both those set in
                config_variables.yml and the environment
            cloud_config (GXCloudConfig): GXCloudConfig corresponding to current CloudDataContext
        """  # noqa: E501 # FIXME CoP
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    @override
    def _init_project_config(
        self, project_config: Optional[Union[DataContextConfig, Mapping]]
    ) -> DataContextConfig:
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    @override
    def _save_project_config(self) -> None:
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    @property
    @override
    def mode(self) -> Literal["cloud"]:
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    def cloud_user_info(self, force_refresh: bool = False) -> CloudUserInfo:
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    @classmethod
    def is_cloud_config_available(
        cls,
        cloud_base_url: Optional[str] = None,
        cloud_access_token: Optional[str] = None,
        cloud_organization_id: Optional[str] = None,
        cloud_workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Helper method called by gx.get_context() method to determine whether all the information needed
        to build a cloud_config is available.

        If provided as explicit arguments, cloud_base_url, cloud_access_token and
        cloud_organization_id will use runtime values instead of environment variables or conf files.

        If any of the values are missing but workspace id, the method will return False.
        It will return True otherwise.

        Args:
            cloud_base_url: Optional, you may provide this alternatively via
                environment variable GX_CLOUD_BASE_URL or within a config file.
            cloud_access_token: Optional, you may provide this alternatively
                via environment variable GX_CLOUD_ACCESS_TOKEN or within a config file.
            cloud_organization_id: Optional, you may provide this alternatively
                via environment variable GX_CLOUD_ORGANIZATION_ID or within a config file.
            cloud_workspace_id: Optional, you may provide this alternatively
                via environment variable GX_CLOUD_WORKSPACE_ID or within a config file.

        Returns:
            bool: Is all the information needed to build a cloud_config is available?
        """  # noqa: E501 # FIXME CoP
        cloud_config_dict = cls._get_cloud_config_dict(
            cloud_base_url=cloud_base_url,
            cloud_access_token=cloud_access_token,
            cloud_organization_id=cloud_organization_id,
            cloud_workspace_id=cloud_workspace_id,
        )

        return all((v for k, v in cloud_config_dict.items() if k not in OPTIONAL_CLOUD_CONFIG_KEYS))

    @classmethod
    def _get_cloud_config_dict(
        cls,
        cloud_base_url: Optional[str] = None,
        cloud_access_token: Optional[str] = None,
        cloud_organization_id: Optional[str] = None,
        cloud_workspace_id: Optional[str] = None,
    ) -> Dict[GXCloudEnvironmentVariable, Optional[str]]:
        cloud_base_url = (
            cloud_base_url
            or cls._get_global_config_value(
                environment_variable=GXCloudEnvironmentVariable.BASE_URL,
                conf_file_section="ge_cloud_config",
                conf_file_option="base_url",
            )
            or CLOUD_DEFAULT_BASE_URL
        )
        cloud_organization_id = cloud_organization_id or cls._get_global_config_value(
            environment_variable=GXCloudEnvironmentVariable.ORGANIZATION_ID,
            conf_file_section="ge_cloud_config",
            conf_file_option="organization_id",
        )
        cloud_access_token = cloud_access_token or cls._get_global_config_value(
            environment_variable=GXCloudEnvironmentVariable.ACCESS_TOKEN,
            conf_file_section="ge_cloud_config",
            conf_file_option="access_token",
        )
        cloud_workspace_id = cloud_workspace_id or cls._get_global_config_value(
            environment_variable=GXCloudEnvironmentVariable.WORKSPACE_ID,
            conf_file_section="ge_cloud_config",
            conf_file_option="workspace_id",
        )
        return {
            GXCloudEnvironmentVariable.BASE_URL: cloud_base_url,
            GXCloudEnvironmentVariable.ORGANIZATION_ID: cloud_organization_id,
            GXCloudEnvironmentVariable.ACCESS_TOKEN: cloud_access_token,
            GXCloudEnvironmentVariable.WORKSPACE_ID: cloud_workspace_id,
        }

    def _delete_asset(self, id: str) -> bool:
        """Delete a DataAsset. Cloud will also update the corresponding Datasource."""
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    @property
    def ge_cloud_config(self) -> GXCloudConfig:
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)

    @override
    def prepare_checkpoint_run(
        self,
        checkpoint: Checkpoint,
        batch_parameters: Dict[str, Any],
        expectation_parameters: SuiteParameterDict,
    ) -> None:
        """CloudContext specific preparation for a checkpoint run.

        Actualizes windowed parameters by updating expectation_parameters in place.
        """
        raise gx_exceptions.GreatExpectationsError(SHUTDOWN_MESSAGE)
