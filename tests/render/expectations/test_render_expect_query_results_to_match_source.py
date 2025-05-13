import pytest

from great_expectations import expectations as gxe
from great_expectations.render import (
    RenderedAtomicContent,
    RenderedAtomicValue,
)
from great_expectations.render.renderer.inline_renderer import InlineRenderer
from great_expectations.render.renderer_configuration import CodeBlock, CodeBlockLanguage


@pytest.mark.parametrize(
    "expectation,expected_expectation_configuration_rendered_atomic_content",
    [
        pytest.param(
            gxe.ExpectQueryResultsToMatchSource(
                description="Both tables should be identical",
                target_query="SELECT * FROM {batch}",
                source_data_source_name="My Data Source",
                source_query="SELECT * FROM a_table_in_source_data_source",
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template="Both tables should be identical",
                        code_block=CodeBlock(
                            code_template_str="$target_query", language=CodeBlockLanguage.SQL
                        ),
                        params={
                            "target_query": {
                                "schema": {"type": "string"},
                                "value": "SELECT * FROM {batch}",
                            }
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template="Compare with Data Source $source_data_source_name",
                        code_block=CodeBlock(
                            code_template_str="$source_query", language=CodeBlockLanguage.SQL
                        ),
                        params={
                            "source_data_source_name": {
                                "schema": {"type": "string"},
                                "value": "My Data Source",
                            },
                            "source_query": {
                                "schema": {"type": "string"},
                                "value": "SELECT * FROM a_table_in_source_data_source",
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="with_description",
        ),
        pytest.param(
            gxe.ExpectQueryResultsToMatchSource(
                target_query="SELECT * FROM {batch}",
                source_data_source_name="My Data Source",
                source_query="SELECT * FROM a_table_in_source_data_source",
            ),
            [
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        code_block=CodeBlock(
                            code_template_str="$target_query", language=CodeBlockLanguage.SQL
                        ),
                        params={
                            "target_query": {
                                "schema": {"type": "string"},
                                "value": "SELECT * FROM {batch}",
                            }
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
                RenderedAtomicContent(
                    name="atomic.prescriptive.summary",
                    value=RenderedAtomicValue(
                        template="Compare with Data Source $source_data_source_name",
                        code_block=CodeBlock(
                            code_template_str="$source_query", language=CodeBlockLanguage.SQL
                        ),
                        params={
                            "source_data_source_name": {
                                "schema": {"type": "string"},
                                "value": "My Data Source",
                            },
                            "source_query": {
                                "schema": {"type": "string"},
                                "value": "SELECT * FROM a_table_in_source_data_source",
                            },
                        },
                        schema={"type": "com.superconductive.rendered.string"},
                    ),
                    value_type="StringValueType",
                ),
            ],
            id="no_description",
        ),
    ],
)
@pytest.mark.unit
def test_expectation_configuration_rendered_atomic_content(
    expectation: gxe.Expectation,
    expected_expectation_configuration_rendered_atomic_content: dict,
):
    inline_renderer: InlineRenderer = InlineRenderer(render_object=expectation.configuration)

    actual_expectation_configuration_rendered_atomic_content: list[RenderedAtomicContent] = (
        inline_renderer.get_rendered_content()
    )

    assert len(actual_expectation_configuration_rendered_atomic_content) == 2

    assert (
        expected_expectation_configuration_rendered_atomic_content
        == actual_expectation_configuration_rendered_atomic_content
    )
