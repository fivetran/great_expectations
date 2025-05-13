import pytest

from great_expectations.checkpoint.checkpoint import CheckpointResult
from great_expectations.data_context.types.resource_identifiers import (
    ValidationResultIdentifier,
)
from great_expectations.render.renderer import EmailRenderer


@pytest.mark.big
def test_EmailRenderer_get_report_element():
    email_renderer = EmailRenderer()

    # these should all be caught
    assert email_renderer._get_report_element(docs_link=None) is None
    assert email_renderer._get_report_element(docs_link=1) is None
    assert email_renderer._get_report_element(docs_link=email_renderer) is None

    # this should work
    assert email_renderer._get_report_element(docs_link="i_should_work") is not None


@pytest.mark.unit
def test_EmailRenderer_render(v1_checkpoint_result: CheckpointResult):
    email_renderer = EmailRenderer()
    _, raw_html = email_renderer.render(checkpoint_result=v1_checkpoint_result)
    html_blocks = raw_html.split("\n")

    assert html_blocks == [
        "<p><strong><h3><u>my_bad_suite</u></h3></strong></p>",
        "<p><strong>Batch Validation Status</strong>: Failed ❌</p>",
        "<p><strong>Expectation Suite Name</strong>: my_bad_suite</p>",
        "<p><strong>Data Asset Name</strong>: my_first_asset</p>",
        "<p><strong>Run ID</strong>: __no_run_id__</p>",
        "<p><strong>Batch ID</strong>: my_batch</p>",
        "<p><strong>Summary</strong>: <strong>3</strong> of <strong>5</strong> expectations were met</p>",  # noqa: E501
        "<br><p><strong><h3><u>my_good_suite</u></h3></strong></p>",
        "<p><strong>Batch Validation Status</strong>: Success 🎉</p>",
        "<p><strong>Expectation Suite Name</strong>: my_good_suite</p>",
        "<p><strong>Data Asset Name</strong>: __no_asset_name__</p>",
        "<p><strong>Run ID</strong>: my_run_id</p>",
        "<p><strong>Batch ID</strong>: my_other_batch</p>",
        "<p><strong>Summary</strong>: <strong>1</strong> of <strong>1</strong> expectations were met</p>",  # noqa: E501 # FIXME CoP
    ]


def test_EmailRenderer_render_with_data_docs_pages(v1_checkpoint_result: CheckpointResult, mocker):
    email_renderer = EmailRenderer()
    local_path = "http://local_site"
    data_docs_pages = {
        list(v1_checkpoint_result.run_results.keys())[0]: {"local_site": local_path},
        mocker.MagicMock(ValidationResultIdentifier): {"local_site": local_path + "2"},
    }
    _, raw_html = email_renderer.render(
        checkpoint_result=v1_checkpoint_result, data_docs_pages=data_docs_pages
    )

    # data docs page with known id should be included
    assert (
        """<p><strong>DataDocs</strong> can be found here: <a href="http://local_site">http://local_site</a>.</p>"""
        in raw_html
    )
    # data docs page with unknown id should not be included
    assert (
        """<p><strong>DataDocs</strong> can be found here: <a href="http://local_site2">http://local_site2</a>.</p>"""
        not in raw_html
    )
