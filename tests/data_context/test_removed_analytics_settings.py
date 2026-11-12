"""Analytics settings that GX Core no longer acts on.

Usage analytics were removed from GX Core, but configuration files and code written against
earlier versions can still carry the settings that used to control them. These tests pin down
that such configuration keeps loading, and that the remaining public entry points are inert.
"""

from __future__ import annotations

import pathlib

import pytest

import great_expectations as gx
from great_expectations.data_context.types.base import (
    DataContextConfig,
    dataContextConfigSchema,
)


def _write_legacy_analytics_key(context_root_dir: pathlib.Path) -> pathlib.Path:
    config_file = context_root_dir / "gx" / "great_expectations.yml"
    config_file.write_text(config_file.read_text() + "\nanalytics_enabled: true\n")
    return config_file


@pytest.mark.unit
def test_schema_load_drops_analytics_enabled():
    loaded = dataContextConfigSchema.load(
        {"config_version": 4.0, "stores": {}, "analytics_enabled": True}
    )

    assert "analytics_enabled" not in loaded


@pytest.mark.unit
def test_schema_load_still_rejects_other_unknown_keys():
    with pytest.raises(gx.exceptions.InvalidDataContextConfigError):
        dataContextConfigSchema.load({"config_version": 4.0, "stores": {}, "not_a_setting": True})


@pytest.mark.unit
def test_schema_load_does_not_mutate_its_input():
    data = {"config_version": 4.0, "stores": {}, "analytics_enabled": False}

    dataContextConfigSchema.load(data)

    assert data["analytics_enabled"] is False


@pytest.mark.filesystem
def test_file_context_with_analytics_enabled_in_config_loads(tmp_path: pathlib.Path):
    gx.get_context(mode="file", project_root_dir=tmp_path)
    _write_legacy_analytics_key(tmp_path)

    context = gx.get_context(mode="file", project_root_dir=tmp_path)

    assert "analytics_enabled" not in context.config.to_yaml_str()


@pytest.mark.filesystem
def test_saving_a_file_context_drops_analytics_enabled_from_config(tmp_path: pathlib.Path):
    gx.get_context(mode="file", project_root_dir=tmp_path)
    config_file = _write_legacy_analytics_key(tmp_path)

    context = gx.get_context(mode="file", project_root_dir=tmp_path)
    context.variables.save()

    assert "analytics_enabled" not in config_file.read_text()


@pytest.mark.unit
def test_data_context_config_analytics_enabled_argument_is_deprecated():
    with pytest.deprecated_call():
        config = DataContextConfig(analytics_enabled=True)

    assert "analytics_enabled" not in config.to_json_dict()


@pytest.mark.unit
def test_data_context_config_without_analytics_enabled_does_not_warn(recwarn):
    DataContextConfig()

    assert not [w for w in recwarn if issubclass(w.category, DeprecationWarning)]


@pytest.mark.unit
def test_enable_analytics_is_a_deprecated_no_op():
    context = gx.get_context(mode="ephemeral")
    before = context.config.to_json_dict()

    with pytest.deprecated_call():
        context.enable_analytics(True)

    assert context.config.to_json_dict() == before


@pytest.mark.unit
def test_analytics_enabled_variable_is_a_deprecated_no_op():
    context = gx.get_context(mode="ephemeral")

    with pytest.deprecated_call():
        context.variables.analytics_enabled = True
    with pytest.deprecated_call():
        value = context.variables.analytics_enabled

    assert value is None
    assert "analytics_enabled" not in context.config.to_json_dict()


@pytest.mark.unit
def test_user_agent_str_argument_is_deprecated():
    with pytest.deprecated_call():
        gx.get_context(mode="ephemeral", user_agent_str="some-product/1.0")
