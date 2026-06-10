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
Jinja view used by Data Docs, then asserts the regex's ``<`` is HTML-escaped as
``&lt;`` in the rendered output.
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

# Regex from the issue: the negative lookbehind (?<!\s) contains a literal "<".
REGEX_WITH_ANGLE_BRACKETS = r"^(?!\s)([A-Za-z0-9&()_\- \/*]+)(?<!\s)$"


@pytest.mark.integration
def test_data_docs_escapes_angle_brackets_in_regex() -> None:
    """Data Docs HTML must HTML-escape angle brackets in a rendered regex."""
    validation_result = ExpectationSuiteValidationResult(
        results=[
            ExpectationValidationResult(
                success=True,
                expectation_config=ExpectationConfiguration(
                    type="expect_column_values_to_match_regex",
                    kwargs={
                        "column": "my_col",
                        "regex": REGEX_WITH_ANGLE_BRACKETS,
                    },
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

    document = ValidationResultsPageRenderer().render(validation_result)
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
