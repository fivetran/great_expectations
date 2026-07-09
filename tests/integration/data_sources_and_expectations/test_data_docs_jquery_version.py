"""
Regression test for community issue #11852: Data Docs rendered with vulnerable jQuery 3.4.1.

The Data Docs page template at
``great_expectations/render/view/templates/js_script_imports.j2`` previously referenced
``https://code.jquery.com/jquery-3.4.1.min.js``. jQuery 3.4.1 is affected by
CVE-2020-11022 and CVE-2020-11023 (both 6.1 Medium), which are patched in
jQuery 3.5.0+.

The repro renders a minimal validation result via the same page renderer
and Jinja view used by Data Docs, then asserts the rendered HTML does not
include the vulnerable jQuery script reference.
"""

from __future__ import annotations

import pytest

from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)
from great_expectations.render.renderer import ValidationResultsPageRenderer
from great_expectations.render.view import DefaultJinjaPageView


@pytest.mark.integration
def test_data_docs_does_not_reference_vulnerable_jquery_3_4_1() -> None:
    """Data Docs HTML must not pull jQuery 3.4.1 (CVE-2020-11022/11023)."""
    validation_result = ExpectationSuiteValidationResult(
        results=[],
        success=True,
        statistics={
            "evaluated_expectations": 0,
            "successful_expectations": 0,
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

    assert "jquery-3.4.1" not in html, (
        "Data Docs HTML references vulnerable jQuery 3.4.1 "
        "(CVE-2020-11022 / CVE-2020-11023). jQuery should be >= 3.5.0."
    )
