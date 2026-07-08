from __future__ import annotations

from typing import Any, Dict

import pytest

from great_expectations.compatibility import aws

botocore_client = pytest.importorskip("botocore.client")

pytestmark = pytest.mark.unit


@pytest.fixture
def distribution_version(monkeypatch: pytest.MonkeyPatch) -> str:
    version = "1.2.3"
    monkeypatch.setattr(aws, "_get_distribution_version", lambda: version)
    return version


def test_get_s3_boto3_options_adds_user_agent_suffix(distribution_version: str) -> None:
    options = aws.get_s3_boto3_options({})

    assert options["config"].user_agent_extra == f"great-expectations/{distribution_version}"


def test_get_s3_boto3_options_appends_user_agent_and_preserves_options(
    distribution_version: str,
) -> None:
    config = botocore_client.Config(user_agent_extra="my-app/1.0")
    boto3_options: Dict[str, Any] = {
        "config": config,
        "endpoint_url": "https://s3.example.com",
    }

    options = aws.get_s3_boto3_options(boto3_options)

    assert (
        options["config"].user_agent_extra
        == f"my-app/1.0 great-expectations/{distribution_version}"
    )
    assert options["endpoint_url"] == "https://s3.example.com"
    assert boto3_options["config"] is config
