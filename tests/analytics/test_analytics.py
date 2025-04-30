from typing import Optional
from unittest import mock
from uuid import UUID

import pytest

import great_expectations as gx
from great_expectations.analytics.config import (
    ENV_CONFIG,
    Config,
    get_config,
    update_config,
)
from great_expectations.analytics.events import DataContextInitializedEvent
from great_expectations.data_context.types.base import (
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)
from tests.datasource.fluent._fake_cloud_api import FAKE_USER_ID

TESTING_UUID = UUID("00000000-c000-0000-0000-000000000000")


@pytest.fixture(
    scope="function",
    params=[
        (
            Config(
                organization_id=TESTING_UUID,
                user_id=TESTING_UUID,
                data_context_id=None,
                oss_id=None,
                cloud_mode=False,
            ),
            TESTING_UUID,
            {
                "user_id": TESTING_UUID,
                "organization_id": TESTING_UUID,
                "data_context_id": None,
                "oss_id": None,
                "service": "gx-core",
            },
        ),
        (
            Config(),
            None,
            {"data_context_id": None, "oss_id": None, "service": "gx-core"},
        ),
    ],
)
def analytics_config(request):
    base_config = get_config()
    update_config(request.param[0])
    yield request.param[1], request.param[2]
    update_config(base_config)


@pytest.mark.unit
def test_event_identifiers(analytics_config):
    """Validate base event properties based on the analytics config."""
    distinct_id, base_properties = analytics_config
    event = DataContextInitializedEvent()
    properties = event.properties()
    # All base properties should be in the event properties
    assert base_properties.items() <= properties.items()
    # Service should be set to gx-core
    assert properties["service"] == "gx-core"
    # The distinct_id should be the user_id if it is set, otherwise the oss_id
    assert event.distinct_id == distinct_id
    if "user_id" in base_properties:
        assert event.distinct_id == base_properties["user_id"]
    else:
        assert event.distinct_id == base_properties["oss_id"]

    # The user_id and organization_id should only be set if they are in the config
    if "user_id" not in base_properties:
        assert "user_id" not in properties
    if "organization_id" not in base_properties:
        assert "organization_id" not in properties


@pytest.mark.xfail(
    reason="The mode is not always set on instantiation. This is a bug. The test will fail if "
    "run in isolation but may pass if another test has run first."
)
@pytest.mark.unit
def test_ephemeral_context_init(monkeypatch):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", True)  # Enable usage stats

    with (
        mock.patch(
            "great_expectations.data_context.data_context.abstract_data_context.init_analytics"
        ) as mock_init,
        mock.patch("posthog.capture") as mock_submit,
    ):
        _ = gx.get_context(mode="ephemeral")

    mock_init.assert_called_once_with(
        enable=True,
        data_context_id=mock.ANY,
        organization_id=None,
        oss_id=mock.ANY,
        user_id=None,
        user_agent_str=None,
        mode="ephemeral",
    )
    mock_submit.assert_called_once_with(
        mock.ANY,
        "data_context.initialized",
        {
            "data_context_id": mock.ANY,
            "oss_id": mock.ANY,
            "service": "gx-core",
            "gx_version": mock.ANY,
            "user_agent_str": None,
            "mode": "ephemeral",
        },
        groups={"data_context": mock.ANY},
    )


@pytest.mark.unit
def test_ephemeral_context_init_with_optional_fields(monkeypatch):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", True)  # Enable usage stats

    with mock.patch("posthog.capture") as mock_submit:
        user_agent_str = "test / x.x.x"
        _ = gx.get_context(mode="ephemeral", user_agent_str=user_agent_str)

    mock_submit.assert_called_once_with(
        mock.ANY,
        "data_context.initialized",
        {
            "data_context_id": mock.ANY,
            "oss_id": mock.ANY,
            "service": "gx-core",
            "gx_version": mock.ANY,
            "user_agent_str": user_agent_str,
            "mode": "ephemeral",
        },
        groups={"data_context": mock.ANY},
    )


@pytest.mark.parametrize("user_agent_str", [None, "test / x.x.x"])
@pytest.mark.cloud
def test_cloud_context_init(
    user_agent_str: Optional[str], cloud_api_fake, cloud_details, monkeypatch
):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", True)  # Enable usage stats

    with (
        mock.patch(
            "great_expectations.data_context.data_context.cloud_data_context.init_analytics"
        ) as mock_init,
        mock.patch("posthog.capture") as mock_submit,
    ):
        _ = gx.get_context(
            cloud_access_token=cloud_details.access_token,
            cloud_organization_id=cloud_details.org_id,
            cloud_base_url=cloud_details.base_url,
            cloud_mode=True,
            user_agent_str=user_agent_str,
        )

    mock_init.assert_called_once_with(
        enable=True,
        user_id=UUID(FAKE_USER_ID),  # Should be consistent with the fake Cloud API
        data_context_id=UUID(cloud_details.org_id),
        organization_id=UUID(cloud_details.org_id),
        oss_id=mock.ANY,
        cloud_mode=True,
        mode="cloud",
        user_agent_str=user_agent_str,
    )
    mock_submit.assert_called_once_with(
        mock.ANY,
        "data_context.initialized",
        {
            "data_context_id": mock.ANY,
            "oss_id": mock.ANY,
            "service": "gx-core",
            "gx_version": mock.ANY,
            "user_agent_str": mock.ANY,
            "mode": mock.ANY,
        },
        groups={"data_context": mock.ANY},
    )


@pytest.mark.parametrize(
    ("environment_variable", "constructor_variable", "expected_value", "user_agent_str"),
    [
        (False, None, False, None),
        (False, False, False, None),
        (False, True, True, None),  # enabling in config overrides environment variable
        (True, None, True, None),
        (True, False, False, None),
        (True, True, True, None),
        (True, True, True, "some user agent string"),
    ],
)
@pytest.mark.unit
def test_analytics_enabled_on_load(
    environment_variable: bool,
    constructor_variable: Optional[bool],
    expected_value: bool,
    user_agent_str: Optional[str],
    monkeypatch,
):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", environment_variable)
    project_config = DataContextConfig(
        store_backend_defaults=InMemoryStoreBackendDefaults(init_temp_docs_sites=True),
        analytics_enabled=constructor_variable,
    )

    with mock.patch(
        "great_expectations.data_context.data_context.abstract_data_context.init_analytics"
    ) as mock_init:
        gx.get_context(
            mode="ephemeral",
            project_config=project_config,
            user_agent_str=user_agent_str,
        )

    mock_init.assert_called_with(
        enable=expected_value,
        data_context_id=mock.ANY,
        organization_id=mock.ANY,
        oss_id=mock.ANY,
        user_id=mock.ANY,
        user_agent_str=user_agent_str,
        mode="ephemeral",
    )


@pytest.mark.unit
@pytest.mark.parametrize("user_agent_str", [None, "some user agent string"])
def test_analytics_enabled_on_load__filesystem(
    user_agent_str: Optional[str],
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", True)

    with mock.patch(
        "great_expectations.data_context.data_context.abstract_data_context.init_analytics"
    ) as mock_init:
        gx.get_context(
            mode="file",
            project_root_dir=tmp_path,
            user_agent_str=user_agent_str,
        )

    mock_init.assert_called_with(
        enable=True,
        data_context_id=mock.ANY,
        organization_id=mock.ANY,
        oss_id=mock.ANY,
        user_id=mock.ANY,
        user_agent_str=user_agent_str,
        mode="file",
    )


@pytest.mark.parametrize("environment_variable", [None, False, True])
@pytest.mark.parametrize("constructor_variable", [None, False, True])
@pytest.mark.parametrize("enable_analytics", [False, True])
@pytest.mark.unit
def test_analytics_enabled_after_setting_explicitly(
    environment_variable: bool,
    constructor_variable: Optional[bool],
    enable_analytics: bool,
    monkeypatch,
):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", environment_variable)
    project_config = DataContextConfig(
        store_backend_defaults=InMemoryStoreBackendDefaults(init_temp_docs_sites=True),
        analytics_enabled=constructor_variable,
    )

    with mock.patch(
        "great_expectations.data_context.data_context.abstract_data_context.init_analytics"
    ) as mock_init:
        context = gx.get_context(
            mode="ephemeral",
            project_config=project_config,
        )

        context.enable_analytics(enable_analytics)

    assert context.config.analytics_enabled == enable_analytics
    mock_init.assert_called_with(
        enable=enable_analytics,
        data_context_id=mock.ANY,
        organization_id=mock.ANY,
        oss_id=mock.ANY,
        user_id=mock.ANY,
        user_agent_str=mock.ANY,
        mode="ephemeral",
    )


@pytest.mark.parametrize("initial_user_agent_str", [None, "old user agent string"])
@pytest.mark.parametrize("new_user_agent_str", [None, "new user agent string"])
@pytest.mark.unit
def test_user_agent_str_after_setting_explicitly(
    initial_user_agent_str: Optional[str],
    new_user_agent_str: Optional[str],
    monkeypatch,
):
    monkeypatch.setattr(ENV_CONFIG, "gx_analytics_enabled", True)

    with mock.patch(
        "great_expectations.data_context.data_context.abstract_data_context.init_analytics"
    ) as mock_init:
        context = gx.get_context(
            mode="ephemeral",
            user_agent_str=initial_user_agent_str,
        )

        context.set_user_agent_str(new_user_agent_str)

    mock_init.assert_called_with(
        enable=True,
        data_context_id=mock.ANY,
        organization_id=mock.ANY,
        oss_id=mock.ANY,
        user_id=mock.ANY,
        user_agent_str=new_user_agent_str,
        mode="ephemeral",
    )
