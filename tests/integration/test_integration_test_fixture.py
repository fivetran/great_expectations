import pathlib

import pytest

from tests.integration.integration_test_fixture import substitute_test_buckets


@pytest.mark.filesystem
@pytest.mark.parametrize(
    ("env_var", "field"),
    [
        ("GX_GCS_TEST_BUCKET", "bucket_or_name"),
        ("GX_S3_TEST_BUCKET", "bucket"),
    ],
)
def test_substitute_test_buckets(monkeypatch, tmp_path: pathlib.Path, env_var: str, field: str):
    monkeypatch.setenv(env_var, "bucket_from_the_environment")
    config = tmp_path / "great_expectations.yml"
    config.write_text(f"    {field}: ${{{env_var}}}\n")

    substitute_test_buckets(config)

    assert config.read_text() == f"    {field}: bucket_from_the_environment\n"


@pytest.mark.filesystem
@pytest.mark.parametrize("env_var", ["GX_GCS_TEST_BUCKET", "GX_S3_TEST_BUCKET"])
def test_substitute_test_buckets_raises_when_env_var_unset(
    monkeypatch, tmp_path: pathlib.Path, env_var: str
):
    monkeypatch.delenv(env_var, raising=False)
    config = tmp_path / "great_expectations.yml"
    config.write_text(f"    bucket: ${{{env_var}}}\n")

    with pytest.raises(RuntimeError, match=env_var):
        substitute_test_buckets(config)


@pytest.mark.filesystem
def test_substitute_test_buckets_only_requires_the_placeholder_that_is_present(
    monkeypatch, tmp_path: pathlib.Path
):
    """An S3 fixture must not require the GCS bucket, or vice versa.

    Each config names one object store. Demanding both env vars would make every
    S3 fixture fail on a machine set up only for S3.
    """
    monkeypatch.setenv("GX_S3_TEST_BUCKET", "s3_bucket")
    monkeypatch.delenv("GX_GCS_TEST_BUCKET", raising=False)
    config = tmp_path / "great_expectations.yml"
    config.write_text("    bucket: ${GX_S3_TEST_BUCKET}\n")

    substitute_test_buckets(config)

    assert config.read_text() == "    bucket: s3_bucket\n"


@pytest.mark.filesystem
def test_substitute_test_buckets_leaves_other_templates_alone(monkeypatch, tmp_path: pathlib.Path):
    """Templates GX resolves itself must survive, so those fixtures still exercise that path."""
    monkeypatch.setenv("GX_GCS_TEST_BUCKET", "bucket_from_the_environment")
    monkeypatch.setenv("GX_S3_TEST_BUCKET", "bucket_from_the_environment")
    monkeypatch.setenv("AZURE_CREDENTIAL", "should_not_be_substituted")
    original = "      credential: ${AZURE_CREDENTIAL}\n"
    config = tmp_path / "great_expectations.yml"
    config.write_text(original)

    substitute_test_buckets(config)

    assert config.read_text() == original


@pytest.mark.filesystem
def test_substitute_test_buckets_is_a_noop_without_a_config(tmp_path: pathlib.Path):
    """A fixture with no Data Context config of its own must not raise."""
    substitute_test_buckets(tmp_path / "does_not_exist.yml")
