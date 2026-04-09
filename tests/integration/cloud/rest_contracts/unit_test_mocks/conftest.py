import json
import uuid as uuid_mod
from unittest import mock

import pytest
import requests
from pact import match

import great_expectations as gx
from great_expectations.data_context import CloudDataContext
from tests.integration.cloud.rest_contracts.conftest import JsonData, PactBody
from tests.integration.cloud.rest_contracts.test_data_context_configuration import (
    GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY,
)


def _convert_matcher_to_value(matcher: match.AbstractMatcher) -> JsonData:
    """Extract the example value from a pact-python v3 matcher.

    Uses ``to_integration_json()`` which is available on all matcher types
    and returns a dict with ``"value"`` and ``"pact:matcher:type"`` keys.
    Matchers like ``match.uuid()`` called without an explicit value may
    omit ``"value"``; for those we generate a sensible default.
    """
    integration = matcher.to_integration_json()
    if "value" in integration:
        return integration["value"]
    # Matchers without a value need a sensible default
    if integration.get("pact:matcher:type") == "regex":
        # uuid() and similar regex-based matchers
        return str(uuid_mod.uuid4())
    return None


def _reify_pact_body(
    body: PactBody | JsonData,
) -> JsonData:
    if isinstance(body, match.AbstractMatcher):
        return _reify_pact_body(body=_convert_matcher_to_value(matcher=body))
    elif isinstance(body, list):
        return [_reify_pact_body(body=item) for item in body]
    elif isinstance(body, dict):
        return {key: _reify_pact_body(body=value) for key, value in body.items()}
    else:
        return body


def _get_mock_response_from_pact_response_body(
    status_code: int,
    pact_response_body: PactBody,
) -> requests.Response:
    response_body: JsonData = _reify_pact_body(
        body=pact_response_body,
    )
    mock_response = requests.Response()
    mock_response.status_code = status_code
    mock_response._content = json.dumps(response_body).encode("utf-8")
    return mock_response


@pytest.fixture
def mock_cloud_data_context() -> CloudDataContext:
    mock_response: requests.Response = _get_mock_response_from_pact_response_body(
        status_code=200,
        pact_response_body=GET_DATA_CONTEXT_CONFIGURATION_MIN_RESPONSE_BODY,
    )

    with mock.patch(
        target="requests.Session.get",
        return_value=mock_response,
    ):
        mock_cloud_data_context: CloudDataContext = gx.get_context(
            mode="cloud",
            cloud_base_url="https://fake-host.io",
            cloud_organization_id=str(uuid_mod.uuid4()),
            cloud_workspace_id=str(uuid_mod.uuid4()),
            cloud_access_token="not a real token",
        )

    assert isinstance(mock_cloud_data_context, CloudDataContext)
    return mock_cloud_data_context
