import ast
import glob
import re
from typing import List, Pattern, Tuple

import pytest
from packaging import version

from great_expectations.data_context.util import file_relative_path

UNNEEDED_DEPRECATION_WARNINGS_THRESHOLD = 13

# module level markers
pytestmark = pytest.mark.unit


@pytest.fixture
def regex_for_deprecation_comments() -> Pattern:
    pattern: Pattern = re.compile(r"deprecated-v(.+)")
    return pattern


@pytest.fixture
def files_with_deprecation_warnings() -> List[str]:
    files: List[str] = glob.glob(  # noqa: PTH207 # FIXME CoP
        "great_expectations/**/*.py", recursive=True
    )
    files_to_exclude = [
        "great_expectations/compatibility/docstring_parser.py",
        "great_expectations/compatibility/pyspark.py",
        "great_expectations/compatibility/sqlalchemy_and_pandas.py",
        "great_expectations/compatibility/sqlalchemy_compatibility_wrappers.py",
    ]
    for file_to_exclude in files_to_exclude:
        if file_to_exclude in files:
            files.remove(file_to_exclude)
    return files


def _deprecation_emission_count(source: str) -> int:
    """Number of calls in `source` that raise a deprecation warning.

    Counts emissions rather than mentions of the name. A deprecation category that
    lives in this package has to be imported before it can be raised and may be
    named in a docstring or in the class definition itself, none of which is an
    emission a marker should be paired with. Matching on the call is also not
    sensitive to how the import happens to be formatted.
    """
    if "DeprecationWarning" not in source:
        # No emission can name a category the source never mentions. Without this the
        # parse runs over every file in the package rather than the dozen that carry a
        # deprecation, which costs enough to overrun the per-test timeout.
        return 0
    count = 0
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if func_name not in ("warn", "warn_explicit"):
            continue
        for arg in [*node.args, *(keyword.value for keyword in node.keywords)]:
            category = arg.attr if isinstance(arg, ast.Attribute) else getattr(arg, "id", None)
            if category and category.endswith("DeprecationWarning"):
                count += 1
                break
    return count


SOURCE_WITH_TWO_EMISSIONS = '''
import warnings
from great_expectations.warnings import (
    GxDeprecationWarning,
    something_else,
)


class GxDeprecationWarning(UserWarning):
    """A DeprecationWarning raised by this package."""


def emits():
    warnings.warn("gone soon", GxDeprecationWarning)
    warnings.warn("gone soon", category=DeprecationWarning)
    warnings.warn("not a deprecation", UserWarning)
'''


@pytest.mark.unit
def test_deprecation_emission_count_follows_calls_not_mentions() -> None:
    """The count must follow the emitting call, not the spelling around it.

    Each non-emission above has at some point been counted as one by a text match,
    every one of them demanding a spurious marker: an import (in any formatting
    ruff may produce), a docstring, and the category's own class definition.
    """
    assert _deprecation_emission_count(SOURCE_WITH_TWO_EMISSIONS) == 2


@pytest.mark.unit
def test_deprecation_warnings_are_accompanied_by_appropriate_comment(
    regex_for_deprecation_comments: Pattern,
    files_with_deprecation_warnings: List[str],
):
    """
    What does this test do and why?

    For every invocation of 'DeprecationWarning', there must be a corresponding
    comment with the following format: 'deprecated-v<MAJOR>.<MINOR>.<PATCH>'.

    This test is meant to capture instances where one or the other is missing.
    """
    for file in files_with_deprecation_warnings:
        with open(file) as f:
            contents = f.read()

        matches: List[str] = regex_for_deprecation_comments.findall(contents)
        warning_count: int = _deprecation_emission_count(contents)
        assert len(matches) == warning_count, (
            "Either a 'deprecated-v...' comment or "
            f"'DeprecationWarning' call is missing from {file}"
        )


@pytest.mark.unit
def test_deprecation_warnings_have_been_removed_after_two_minor_versions(
    regex_for_deprecation_comments: Pattern,
    files_with_deprecation_warnings: List[str],
):
    """
    What does this test do and why?

    To ensure that we're appropriately deprecating, we want to test that we're fully
    removing warnings (and the code they correspond to) after two minor versions have passed.
    """
    deployment_version_path: str = file_relative_path(
        __file__, "../great_expectations/deployment_version"
    )
    current_version: str
    with open(deployment_version_path) as f:
        current_version = f.read().strip()

    current_parsed_version: version.Version = version.parse(current_version)
    current_major_version: int = current_parsed_version.major
    current_minor_version: int = current_parsed_version.minor

    unneeded_deprecation_warnings: List[Tuple[str, str]] = []
    for file in files_with_deprecation_warnings:
        with open(file) as f:
            contents = f.read()

        matches: List[str] = regex_for_deprecation_comments.findall(contents)
        for match in matches:
            parsed_version: version.Version = version.parse(match)
            major_version: int = parsed_version.major
            minor_version: int = parsed_version.minor
            if (current_major_version - major_version > 0) and (
                current_minor_version - minor_version > 2
            ):
                unneeded_deprecation_warning: Tuple[str, str] = (file, match)
                unneeded_deprecation_warnings.append(unneeded_deprecation_warning)

    if unneeded_deprecation_warnings:
        print("\nThe following deprecation warnings must be cleared per the code style guide:")
        for file, version_ in unneeded_deprecation_warnings:
            print(f"{file} - v{version_}")

    # Chetan - 20220316 - Once v0.16.0 lands, this should be cleaned up and made 0.
    if len(unneeded_deprecation_warnings) > UNNEEDED_DEPRECATION_WARNINGS_THRESHOLD:
        raise ValueError(
            f"Found {len(unneeded_deprecation_warnings)} warnings but threshold is {UNNEEDED_DEPRECATION_WARNINGS_THRESHOLD}; please adjust accordingly"  # noqa: E501 # FIXME CoP
        )
