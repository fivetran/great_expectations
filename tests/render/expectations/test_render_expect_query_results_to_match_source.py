import pytest

from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.render import (
    RenderedAtomicContent,
)
from great_expectations.render.renderer.inline_renderer import InlineRenderer
from great_expectations.render.renderer_configuration import CodeBlockLanguage, RendererValueType


@pytest.mark.parametrize(
    "expectation_configuration,expected_expectation_configuration_rendered_atomic_content",
    [
        pytest.param(
            ExpectationConfiguration(
                type="expect_query_results_to_match_source",
                kwargs={
                    "target_query": "SELECT * FROM {batch}",
                    "source_data_source_name": "My Data Source",
                    "source_query": "SELECT * FROM a_table_in_source_data_source",
                },
            ),
            [
                {
                    "name": "atomic.prescriptive.summary",
                    "value": {
                        "code_block": {
                            "code_template_str": "$target_query",
                            "language": CodeBlockLanguage.SQL,
                        },
                        "params": {
                            "target_query": {
                                "schema": {"type": RendererValueType.STRING},
                                "value": "SELECT * FROM {batch}",
                            }
                        },
                        "schema": {"type": "com.superconductive.rendered.string"},
                    },
                    "value_type": "StringValueType",
                },
                {
                    "name": "atomic.prescriptive.summary",
                    "value": {
                        "code_block": {
                            "code_template_str": "$source_query",
                            "language": CodeBlockLanguage.SQL,
                        },
                        "params": {
                            "source_data_source_name": {
                                "schema": {"type": RendererValueType.STRING},
                                "value": "My Data Source",
                            },
                            "source_query": {
                                "schema": {"type": RendererValueType.STRING},
                                "value": "SELECT * FROM a_table_in_source_data_source",
                            },
                        },
                        "schema": {"type": "com.superconductive.rendered.string"},
                        "template": "Compare with Data Source $source_data_source_name",
                    },
                    "value_type": "StringValueType",
                },
            ],
        ),
    ],
)
@pytest.mark.unit
def test_expectation_configuration_rendered_atomic_content(
    expectation_configuration: ExpectationConfiguration,
    expected_expectation_configuration_rendered_atomic_content: dict,
):
    inline_renderer: InlineRenderer = InlineRenderer(render_object=expectation_configuration)

    expectation_configuration_rendered_atomic_content: list[RenderedAtomicContent] = (
        inline_renderer.get_rendered_content()
    )

    assert len(expectation_configuration_rendered_atomic_content) == 2

    actual_expectation_configuration_rendered_atomic_content: list[dict] = [
        rendered_atomic_content.to_json_dict()
        for rendered_atomic_content in expectation_configuration_rendered_atomic_content
    ]

    assert (
        actual_expectation_configuration_rendered_atomic_content
        == expected_expectation_configuration_rendered_atomic_content
    )
