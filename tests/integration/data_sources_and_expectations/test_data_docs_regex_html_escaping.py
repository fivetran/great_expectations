"""
Reproduction for community issue #11907: angle brackets in regular expressions
are not HTML-escaped when rendering Data Docs.

An ``ExpectColumnValuesToMatchRegex`` whose ``regex`` contains a negative
lookbehind such as ``(?<!\\s)`` carries a literal ``<`` character. The Data Docs
prescriptive renderer substitutes the regex into a string template and the
resulting HTML is emitted without escaping the parameter values, so the ``<!``
sequence reaches the browser raw and is interpreted as the start of an HTML
comment (the regex is then truncated / hidden).

The repro renders a minimal validation result through the same page renderer and
Jinja view used by Data Docs, then asserts the regex's HTML-significant
characters (``<``, ``>``, ``&``) are escaped in the rendered output, while
trusted renderer-generated markup (the status icon) is still emitted raw.

The same class of bug reaches a second parameter: ``ExpectColumnValuesToMatchJSONSchema``
builds a ``formatted_json`` param whose value is ``<pre>{json.dumps(schema)}</pre>`` —
renderer-generated markup wrapping user-supplied schema content. Both properties must
hold there too: the ``<pre>`` wrapper must reach the browser as raw HTML (so the schema
renders as a formatted code block) while the schema content is HTML-escaped.
"""

from __future__ import annotations

import pytest

from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
    ExpectationValidationResult,
)
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.render.renderer import ValidationResultsPageRenderer
from great_expectations.render.view import DefaultJinjaPageView
from great_expectations.render.view.view import DefaultJinjaView

# Regex carrying every HTML-significant character: the negative lookbehind
# (?<!\s) contains a literal "<", plus a literal ">" and "&".
REGEX_WITH_HTML_CHARS = r"^(?<!\s)a>b&c([A-Za-z0-9()_\- \/*]+)$"

# JSON Schema whose ``pattern`` carries every HTML-significant character: the negative
# lookbehind (?<!\s) contains a literal "<", plus a literal ">" and "&". The renderer
# wraps the dumped schema in a <pre>...</pre> block.
JSON_SCHEMA_WITH_HTML_CHARS = {"type": "string", "pattern": r"(?<!\s)a>b&c"}


def _validation_result_with_expectation(
    expectation_type: str, **kwargs: object
) -> ExpectationSuiteValidationResult:
    return ExpectationSuiteValidationResult(
        results=[
            ExpectationValidationResult(
                success=True,
                expectation_config=ExpectationConfiguration(
                    type=expectation_type,
                    kwargs={"column": "my_col", **kwargs},
                ),
                result={},
            ),
        ],
        success=True,
        statistics={
            "evaluated_expectations": 1,
            "successful_expectations": 1,
            "unsuccessful_expectations": 0,
            "success_percent": 100.0,
        },
        suite_name="test_suite",
        meta={
            "great_expectations_version": "test",
            "run_id": {
                "run_name": "test",
                "run_time": "2024-01-01T00:00:00.000000+00:00",
            },
        },
    )


def _validation_result_with_regex(regex: str) -> ExpectationSuiteValidationResult:
    return _validation_result_with_expectation("expect_column_values_to_match_regex", regex=regex)


@pytest.mark.integration
def test_data_docs_escapes_html_significant_chars_in_regex() -> None:
    """Data Docs HTML must HTML-escape ``<``, ``>`` and ``&`` in a rendered regex."""
    document = ValidationResultsPageRenderer().render(
        _validation_result_with_regex(REGEX_WITH_HTML_CHARS)
    )
    html = DefaultJinjaPageView().render(document)

    # The raw "<" from the negative lookbehind must not reach the browser:
    # if it does, "<!" is interpreted as the start of an HTML comment.
    assert "(?<!" not in html, (
        "Data Docs HTML contains an unescaped '<' from the regex negative "
        "lookbehind; angle brackets in regular expressions should be "
        "HTML-escaped so the browser renders them literally."
    )
    assert "(?&lt;!" in html, (
        "Expected the regex angle bracket to be HTML-escaped as '&lt;' in the "
        "rendered Data Docs output."
    )
    # The literal ">" and "&" from the regex must be escaped too.
    assert "a>b&c" not in html, "Regex '>' and '&' should be HTML-escaped in Data Docs."
    assert "a&gt;b&amp;c" in html, (
        "Expected the regex's '>' and '&' to be escaped as '&gt;' and '&amp;'."
    )

    # Trusted renderer-generated markup (the validation status icon) must still be
    # emitted as raw HTML, not escaped into literal text.
    assert '<i class="fas fa-check-circle' in html, (
        "Expected the success status icon to be emitted as raw HTML."
    )
    assert "&lt;i class=" not in html, (
        "Trusted renderer-generated icon markup must not be HTML-escaped."
    )


@pytest.mark.unit
def test_render_string_template_escapes_user_params_but_not_trusted_icon() -> None:
    """The unstyled ``render_string_template`` path escapes user params but not the icon.

    Exercises the branch with no ``styling`` key directly, covering both that
    user-supplied content is escaped and that ``html_success_icon`` is left raw.
    """
    icon = '<i class="fas fa-check-circle text-success" aria-hidden="true"></i>'
    template = {
        "template": "${status} ${html_success_icon} ${pattern}",
        "params": {
            "status": "Status:",
            "html_success_icon": icon,
            "pattern": "a<b>c&d",
        },
    }

    rendered = DefaultJinjaView().render_string_template(template)

    assert "a&lt;b&gt;c&amp;d" in rendered, "User param must be HTML-escaped."
    assert "a<b>c&d" not in rendered, "Raw user param must not reach the browser."
    assert icon in rendered, "Trusted icon markup must be emitted raw."


@pytest.mark.integration
def test_data_docs_renders_json_schema_pre_block_but_escapes_its_content() -> None:
    """JSON-schema ``<pre>`` wrapper must render as raw HTML while its content is escaped.

    ``ExpectColumnValuesToMatchJSONSchema`` builds a ``formatted_json`` param whose value
    is ``<pre>{json.dumps(schema)}</pre>``. Escaping the whole value turns the ``<pre>``
    wrapper into literal ``&lt;pre&gt;`` text (the schema no longer renders as a code
    block); leaving it fully raw re-introduces the issue #11907 bug for schema content
    containing ``<`` / ``>`` / ``&``. The wrapper must reach the browser raw while the
    schema content is escaped at its source.
    """
    document = ValidationResultsPageRenderer().render(
        _validation_result_with_expectation(
            "expect_column_values_to_match_json_schema",
            json_schema=JSON_SCHEMA_WITH_HTML_CHARS,
        )
    )
    html = DefaultJinjaPageView().render(document)

    # The <pre> wrapper is trusted renderer-generated markup: it must render as real
    # HTML, not be escaped into literal "&lt;pre&gt;" text.
    assert "<pre>" in html, (
        "Expected the JSON-schema '<pre>' wrapper to be emitted as raw HTML so the "
        "schema renders as a formatted code block in Data Docs."
    )
    assert "&lt;pre&gt;" not in html, (
        "The JSON-schema '<pre>' wrapper was HTML-escaped into literal text; trusted "
        "renderer-generated markup must not be escaped."
    )

    # The schema *content* is user-supplied: its HTML-significant characters must be
    # escaped, exactly as for the regex case (issue #11907). The negative lookbehind's
    # "<" must not reach the browser raw.
    assert "(?<!" not in html, (
        "Data Docs HTML contains an unescaped '<' from the JSON-schema pattern's "
        "negative lookbehind; schema content must be HTML-escaped."
    )
    assert "(?&lt;!" in html, "Expected the JSON-schema pattern's '<' to be escaped as '&lt;'."
    assert "a>b&c" not in html, "Schema content '>' and '&' should be HTML-escaped."
    assert "a&gt;b&amp;c" in html, (
        "Expected the schema pattern's '>' and '&' to be escaped as '&gt;' and '&amp;'."
    )
