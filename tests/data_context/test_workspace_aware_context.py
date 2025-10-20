"""
Tests for workspace-aware context functionality.

This module tests the behavior of CloudDataContext and get_context() when handling
workspaces, including automatic workspace inference when only one workspace exists,
and proper error handling when workspace_id is not set and multiple workspaces exist.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest

import great_expectations as gx
from great_expectations.data_context.cloud_constants import GXCloudEnvironmentVariable
from great_expectations.data_context.data_context.cloud_data_context import (
    CloudDataContext,
    CloudUserInfo,
    Workspace,
    WorkspaceNotSetError,
)


@pytest.fixture
def mock_cloud_config_params() -> dict[str, Any]:
    """Standard cloud config parameters for testing.

    Note: Returns dict[str, Any] instead of dict[str, str] even though all values
    are strings. This is required for mypy compatibility when unpacking these
    parameters as **kwargs to functions that expect various parameter types
    (e.g., Optional[str], Optional[dict[Any, Any]]). Using dict[str, str] causes
    mypy to reject the unpacking since it can't verify type compatibility across
    all possible target parameters.
    """
    return {
        "cloud_base_url": "https://api.test.greatexpectations.io",
        "cloud_access_token": "test_token_123",
        "cloud_organization_id": "12345678-1234-1234-1234-123456789abc",
    }


@pytest.fixture
def mock_cloud_config_params_with_cloud_mode(
    mock_cloud_config_params: dict[str, Any],
) -> dict[str, Any]:
    mock_cloud_config_params["mode"] = "cloud"
    return {**mock_cloud_config_params}


@pytest.fixture
def mock_project_config() -> dict[str, Any]:
    """Mock project config to return from retrieve_data_context_config_from_cloud."""
    return {
        "data_context_id": "12345678-1234-1234-1234-123456789012",
        "config_version": 3.0,
        "analytics_enabled": True,
        "checkpoint_store_name": "default_checkpoint_store",
        "expectations_store_name": "default_expectations_store",
        "validation_results_store_name": "default_validation_results_store",
        "stores": {},
        "data_docs_sites": {},
    }


@pytest.fixture
def sample_user_with_no_workspaces() -> CloudUserInfo:
    """CloudUserInfo with no workspaces."""
    return CloudUserInfo(user_id=uuid.UUID("12345678-1234-1234-1234-123456789012"), workspaces=[])


@pytest.fixture
def sample_user_with_one_workspace() -> CloudUserInfo:
    """CloudUserInfo with exactly one workspace."""
    return CloudUserInfo(
        user_id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
        workspaces=[Workspace(id="workspace-1", role="admin")],
    )


@pytest.fixture
def sample_user_with_multiple_workspaces() -> CloudUserInfo:
    """CloudUserInfo with multiple workspaces."""
    return CloudUserInfo(
        user_id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
        workspaces=[
            Workspace(id="workspace-1", role="admin"),
            Workspace(id="workspace-2", role="editor"),
            Workspace(id="workspace-3", role="viewer"),
        ],
    )


@pytest.mark.filterwarnings("ignore:Workspace id is not set when instantiating a CloudDataContext")
class TestGetContextWithoutSettingWorkspaceId:
    """Test get_context() behavior when GX_CLOUD_WORKSPACE_ID is not set."""

    @pytest.mark.unit
    def test_get_context_fails_with_no_workspaces(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_no_workspaces: CloudUserInfo,
    ):
        """Test that get_context() raises WorkspaceNotSetError when user has 0 workspaces."""

        with patch(
            "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
            return_value=sample_user_with_no_workspaces,
        ):
            with pytest.raises(WorkspaceNotSetError) as exc_info:
                gx.get_context(mode="cloud", **mock_cloud_config_params)

            assert (
                "Workspace id is not set and this user does not belong to exactly 1 workspace"
                in str(exc_info.value)
            )

    @pytest.mark.unit
    def test_get_context_succeeds_with_one_workspace(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params_with_cloud_mode: dict[str, Any],
        sample_user_with_one_workspace: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that get_context() succeeds and auto-sets workspace_id when user has 1 workspace."""

        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_one_workspace,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            context = gx.get_context(**mock_cloud_config_params_with_cloud_mode)

            assert isinstance(context, CloudDataContext)
            assert context._cloud_config.workspace_id == "workspace-1"

    @pytest.mark.unit
    def test_get_context_fails_with_multiple_workspaces(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params_with_cloud_mode: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
    ):
        """Test that get_context() raises WorkspaceNotSetError when user has >1 workspaces."""

        with patch(
            "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
            return_value=sample_user_with_multiple_workspaces,
        ):
            with pytest.raises(WorkspaceNotSetError) as exc_info:
                gx.get_context(**mock_cloud_config_params_with_cloud_mode)

            assert (
                "Workspace id is not set and this user does not belong to exactly 1 workspace"
                in str(exc_info.value)
            )
            assert "GX_CLOUD_WORKSPACE_ID" in str(exc_info.value)


@pytest.mark.filterwarnings("ignore:Workspace id is not set when instantiating a CloudDataContext")
class TestCloudDataContextDirectInstantiationWithoutWorkspaceId:
    """Test CloudDataContext direct instantiation when workspace_id is not provided."""

    @pytest.mark.unit
    def test_cloud_data_context_fails_with_no_workspaces(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_no_workspaces: CloudUserInfo,
    ):
        """Test that CloudDataContext raises WorkspaceNotSetError when user has 0 workspaces."""
        with patch(
            "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
            return_value=sample_user_with_no_workspaces,
        ):
            with pytest.raises(WorkspaceNotSetError) as exc_info:
                CloudDataContext(**mock_cloud_config_params)

            assert (
                "Workspace id is not set and this user does not belong to exactly 1 workspace"
                in str(exc_info.value)
            )

    @pytest.mark.unit
    def test_cloud_data_context_succeeds_with_one_workspace(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_one_workspace: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that CloudDataContext succeeds and auto-sets workspace_id when user has 1 workspace."""  # noqa: E501
        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_one_workspace,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            context = CloudDataContext(**mock_cloud_config_params)

            assert isinstance(context, CloudDataContext)
            assert context._cloud_config.workspace_id == "workspace-1"

    @pytest.mark.unit
    def test_cloud_data_context_fails_with_multiple_workspaces(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
    ):
        """Test that CloudDataContext raises WorkspaceNotSetError when user has >1 workspaces."""
        with patch(
            "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
            return_value=sample_user_with_multiple_workspaces,
        ):
            with pytest.raises(WorkspaceNotSetError) as exc_info:
                CloudDataContext(**mock_cloud_config_params)

            assert (
                "Workspace id is not set and this user does not belong to exactly 1 workspace"
                in str(exc_info.value)
            )
            assert "GX_CLOUD_WORKSPACE_ID" in str(exc_info.value)


class TestContextWithWorkspaceIdEnvironmentVariable:
    """Test context behavior when GX_CLOUD_WORKSPACE_ID environment variable is set."""

    @pytest.mark.unit
    def test_get_context_uses_env_workspace_id(
        self,
        unset_gx_env_variables: None,
        monkeypatch: pytest.MonkeyPatch,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that get_context() uses workspace_id from environment variable."""
        expected_workspace_id = "env-workspace-123"
        monkeypatch.setenv(GXCloudEnvironmentVariable.WORKSPACE_ID, expected_workspace_id)

        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_multiple_workspaces,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            context = gx.get_context(mode="cloud", **mock_cloud_config_params)

            assert isinstance(context, CloudDataContext)
            assert context._cloud_config.workspace_id == expected_workspace_id

    @pytest.mark.unit
    def test_cloud_data_context_uses_env_workspace_id(
        self,
        unset_gx_env_variables: None,
        monkeypatch: pytest.MonkeyPatch,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that CloudDataContext uses workspace_id from environment variable."""
        expected_workspace_id = "env-workspace-456"
        monkeypatch.setenv(GXCloudEnvironmentVariable.WORKSPACE_ID, expected_workspace_id)

        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_multiple_workspaces,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            context = CloudDataContext(**mock_cloud_config_params)

            assert isinstance(context, CloudDataContext)
            assert context._cloud_config.workspace_id == expected_workspace_id


class TestContextWithWorkspaceIdArgument:
    """Test context behavior when workspace_id is provided as an argument."""

    @pytest.mark.unit
    def test_get_context_uses_argument_workspace_id(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params_with_cloud_mode: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that get_context() uses workspace_id from argument."""

        expected_workspace_id = "arg-workspace-789"
        config_with_workspace = {
            **mock_cloud_config_params_with_cloud_mode,
            "cloud_workspace_id": expected_workspace_id,
        }

        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_multiple_workspaces,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            context = gx.get_context(**config_with_workspace)

            assert isinstance(context, CloudDataContext)
            assert context._cloud_config.workspace_id == expected_workspace_id

    @pytest.mark.unit
    def test_cloud_data_context_uses_argument_workspace_id(
        self,
        unset_gx_env_variables: None,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that CloudDataContext uses workspace_id from argument."""
        expected_workspace_id = "arg-workspace-abc"
        config_with_workspace = {
            **mock_cloud_config_params,
            "cloud_workspace_id": expected_workspace_id,
        }

        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_multiple_workspaces,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            context = CloudDataContext(**config_with_workspace)

            assert isinstance(context, CloudDataContext)
            assert context._cloud_config.workspace_id == expected_workspace_id

    @pytest.mark.unit
    def test_argument_workspace_id_overrides_env_variable(
        self,
        unset_gx_env_variables: None,
        monkeypatch: pytest.MonkeyPatch,
        mock_cloud_config_params: dict[str, Any],
        sample_user_with_multiple_workspaces: CloudUserInfo,
        mock_project_config: dict[str, Any],
    ):
        """Test that workspace_id argument takes precedence over environment variable."""
        env_workspace_id = "env-workspace-should-be-ignored"
        arg_workspace_id = "arg-workspace-takes-precedence"

        monkeypatch.setenv(GXCloudEnvironmentVariable.WORKSPACE_ID, env_workspace_id)
        config_with_workspace = {**mock_cloud_config_params, "cloud_workspace_id": arg_workspace_id}

        with (
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._get_cloud_user_info",
                return_value=sample_user_with_multiple_workspaces,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext.retrieve_data_context_config_from_cloud",
                return_value=mock_project_config,
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._save_project_config"
            ),
            patch(
                "great_expectations.data_context.data_context.cloud_data_context.CloudDataContext._check_if_latest_version"
            ),
        ):
            # Test with get_context
            context1 = gx.get_context(mode="cloud", **config_with_workspace)
            assert context1._cloud_config.workspace_id == arg_workspace_id

            # Test with CloudDataContext directly
            context2 = CloudDataContext(**config_with_workspace)
            assert context2._cloud_config.workspace_id == arg_workspace_id
