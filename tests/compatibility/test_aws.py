from __future__ import annotations

from typing import Any, Dict

import pytest

import great_expectations as gx
from great_expectations.compatibility import aws

botocore_client = pytest.importorskip("botocore.client")

pytestmark = pytest.mark.unit


@pytest.fixture
def great_expectations_version(monkeypatch: pytest.MonkeyPatch) -> str:
    version = "1.2.3"
    monkeypatch.setattr(aws, "get_great_expectations_version", lambda: version)
    return version


def test_get_great_expectations_version_returns_package_version() -> None:
    assert aws.get_great_expectations_version() == gx.__version__


def test_get_s3_boto3_options_adds_user_agent_suffix(great_expectations_version: str) -> None:
    options = aws.get_s3_boto3_options({})

    assert options["config"].user_agent_extra == f"great-expectations/{great_expectations_version}"


def test_get_s3_boto3_options_appends_user_agent_and_preserves_options(
    great_expectations_version: str,
) -> None:
    config = botocore_client.Config(user_agent_extra="my-app/1.0")
    boto3_options: Dict[str, Any] = {
        "config": config,
        "endpoint_url": "https://s3.example.com",
    }

    options = aws.get_s3_boto3_options(boto3_options)

    assert (
        options["config"].user_agent_extra
        == f"my-app/1.0 great-expectations/{great_expectations_version}"
    )
    assert options["endpoint_url"] == "https://s3.example.com"
    assert boto3_options["config"] is config


def test_get_s3_boto3_options_is_idempotent(great_expectations_version: str) -> None:
    config = botocore_client.Config(user_agent_extra="my-app/1.0")
    boto3_options: Dict[str, Any] = {
        "config": config,
        "endpoint_url": "https://s3.example.com",
    }

    once = aws.get_s3_boto3_options(boto3_options)
    twice = aws.get_s3_boto3_options(once)

    assert (
        twice["config"].user_agent_extra
        == f"my-app/1.0 great-expectations/{great_expectations_version}"
    )
    assert twice["config"] is once["config"]
    assert twice["endpoint_url"] == "https://s3.example.com"


def test_get_s3_boto3_options_preserves_invalid_config() -> None:
    boto3_options: Dict[str, Any] = {
        "config": {"user_agent_extra": "invalid"},
        "endpoint_url": "https://s3.example.com",
    }

    options = aws.get_s3_boto3_options(boto3_options)

    assert options == boto3_options
