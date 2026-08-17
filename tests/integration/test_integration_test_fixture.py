import pathlib

import pytest

from tests.integration.integration_test_fixture import substitute_gcs_test_bucket


@pytest.mark.filesystem
def test_substitute_gcs_test_bucket(monkeypatch, tmp_path: pathlib.Path):
    monkeypatch.setenv("GX_GCS_TEST_BUCKET", "bucket_from_the_environment")
    config = tmp_path / "great_expectations.yml"
    config.write_text("    bucket_or_name: ${GX_GCS_TEST_BUCKET}\n")

    substitute_gcs_test_bucket(config)

    assert config.read_text() == "    bucket_or_name: bucket_from_the_environment\n"


@pytest.mark.filesystem
def test_substitute_gcs_test_bucket_raises_when_env_var_unset(monkeypatch, tmp_path: pathlib.Path):
    monkeypatch.delenv("GX_GCS_TEST_BUCKET", raising=False)
    config = tmp_path / "great_expectations.yml"
    config.write_text("    bucket_or_name: ${GX_GCS_TEST_BUCKET}\n")

    with pytest.raises(RuntimeError, match="GX_GCS_TEST_BUCKET"):
        substitute_gcs_test_bucket(config)


@pytest.mark.filesystem
def test_substitute_gcs_test_bucket_leaves_other_templates_alone(
    monkeypatch, tmp_path: pathlib.Path
):
    """Templates GX resolves itself must survive, so those fixtures still exercise that path."""
    monkeypatch.setenv("GX_GCS_TEST_BUCKET", "bucket_from_the_environment")
    monkeypatch.setenv("AZURE_CREDENTIAL", "should_not_be_substituted")
    original = "      credential: ${AZURE_CREDENTIAL}\n"
    config = tmp_path / "great_expectations.yml"
    config.write_text(original)

    substitute_gcs_test_bucket(config)

    assert config.read_text() == original


@pytest.mark.filesystem
def test_substitute_gcs_test_bucket_is_a_noop_without_a_config(tmp_path: pathlib.Path):
    """A fixture with no Data Context config of its own must not raise."""
    substitute_gcs_test_bucket(tmp_path / "does_not_exist.yml")
