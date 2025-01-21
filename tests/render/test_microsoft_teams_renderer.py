from unittest import mock

import pytest

from great_expectations.checkpoint.checkpoint import CheckpointResult
from great_expectations.data_context.types.resource_identifiers import ValidationResultIdentifier
from great_expectations.render.renderer import MicrosoftTeamsRenderer


@pytest.mark.unit
def test_MicrosoftTeamsRenderer_render(v1_checkpoint_result: CheckpointResult):
    rendered_output = MicrosoftTeamsRenderer().render(v1_checkpoint_result)
    body = rendered_output["attachments"][0]["content"]["body"]

    # Assert header
    assert "Failure" in body[0]["columns"][1]["items"][0]["text"]

    # Assert first validation result
    assert body[1]["text"] == "Validation Result (1 of 2) ❌"
    assert body[2]["facts"] == [
        {"title": "Data Asset name: ", "value": "my_first_asset"},
        {"title": "Suite name: ", "value": "my_bad_suite"},
        {"title": "Run name: ", "value": mock.ANY},
        {"title": "Summary:", "value": "*3* of *5* Expectations were met"},
    ]

    # Assert second validation result
    assert body[3]["text"] == "Validation Result (2 of 2) ✅"
    assert body[4]["facts"] == [
        {"title": "Data Asset name: ", "value": "--"},
        {"title": "Suite name: ", "value": "my_good_suite"},
        {"title": "Run name: ", "value": mock.ANY},
        {"title": "Summary:", "value": "*1* of *1* Expectations were met"},
    ]


@pytest.mark.unit
def test_MicrosoftTeamsRender_render_with_data_docs_pages(
    v1_checkpoint_result: CheckpointResult, mocker
):
    renderer = MicrosoftTeamsRenderer()
    local_path = "http://local_site"
    data_docs_pages = {
        mocker.MagicMock(spec=ValidationResultIdentifier): {"local_site": local_path}
    }
    rendered_output = renderer.render(
        checkpoint_result=v1_checkpoint_result, data_docs_pages=data_docs_pages
    )

    assert (
        rendered_output["attachments"][0]["content"]["actions"][0]["card"]["body"][0]["text"]
        == local_path
    )
