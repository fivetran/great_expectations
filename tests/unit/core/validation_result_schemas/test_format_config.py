"""Unit tests for ResultFormatConfig TypedDict.

Round-trips parse_result_format() output under each ResultFormat value,
asserting required keys are present and optional keys behave correctly.
"""

from __future__ import annotations

from typing import Mapping

import pytest

from great_expectations.core.result_format import ResultFormat
from great_expectations.core.validation_result_schemas.format_config import (
    ResultFormatConfig,
    ResultFormatConfigRequired,
)
from great_expectations.expectations.expectation_configuration import parse_result_format

REQUIRED_KEYS = frozenset(
    {
        "result_format",
        "partial_unexpected_count",
        "include_unexpected_rows",
        "map_expectation_unexpected_rows_as_dict",
    }
)
OPTIONAL_KEYS = frozenset({"exclude_unexpected_values", "return_unexpected_index_query"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_required_keys_present(config: Mapping[str, object]) -> None:
    """Assert all required keys are present in the config dict."""
    missing = REQUIRED_KEYS - config.keys()
    assert not missing, f"Missing required keys: {missing}"


def _assert_optional_keys_absent(config: Mapping[str, object]) -> None:
    """Assert optional keys are NOT present (string-only parse_result_format input)."""
    present = OPTIONAL_KEYS & config.keys()
    assert not present, f"Optional keys should be absent but found: {present}"


# ---------------------------------------------------------------------------
# Tests: string-form parse_result_format produces only required keys
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_boolean_only_required_keys_present() -> None:
    raw = parse_result_format(ResultFormat.BOOLEAN_ONLY.value)
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    _assert_optional_keys_absent(config)
    assert config["result_format"] == ResultFormat.BOOLEAN_ONLY.value


@pytest.mark.unit
def test_basic_required_keys_present() -> None:
    raw = parse_result_format(ResultFormat.BASIC.value)
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    _assert_optional_keys_absent(config)
    assert config["result_format"] == ResultFormat.BASIC.value


@pytest.mark.unit
def test_summary_required_keys_present() -> None:
    raw = parse_result_format(ResultFormat.SUMMARY.value)
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    _assert_optional_keys_absent(config)
    assert config["result_format"] == ResultFormat.SUMMARY.value


@pytest.mark.unit
def test_complete_required_keys_present() -> None:
    raw = parse_result_format(ResultFormat.COMPLETE.value)
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    _assert_optional_keys_absent(config)
    assert config["result_format"] == ResultFormat.COMPLETE.value


# ---------------------------------------------------------------------------
# Tests: dict-form parse_result_format with optional keys present
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_optional_exclude_unexpected_values_present_when_supplied() -> None:
    raw = parse_result_format(
        {
            "result_format": ResultFormat.COMPLETE.value,
            "exclude_unexpected_values": True,
        }
    )
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    assert "exclude_unexpected_values" in config
    assert config["exclude_unexpected_values"] is True


@pytest.mark.unit
def test_optional_return_unexpected_index_query_present_when_supplied() -> None:
    raw = parse_result_format(
        {
            "result_format": ResultFormat.COMPLETE.value,
            "return_unexpected_index_query": False,
        }
    )
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    assert "return_unexpected_index_query" in config
    assert config["return_unexpected_index_query"] is False


@pytest.mark.unit
def test_both_optional_keys_present_when_supplied() -> None:
    raw = parse_result_format(
        {
            "result_format": ResultFormat.SUMMARY.value,
            "exclude_unexpected_values": False,
            "return_unexpected_index_query": True,
        }
    )
    config: ResultFormatConfig = raw  # type: ignore[assignment]
    _assert_required_keys_present(config)
    assert "exclude_unexpected_values" in config
    assert "return_unexpected_index_query" in config


# ---------------------------------------------------------------------------
# Tests: partial_unexpected_count default
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_partial_unexpected_count_defaults_to_20() -> None:
    raw = parse_result_format(ResultFormat.BASIC.value)
    assert raw["partial_unexpected_count"] == 20


@pytest.mark.unit
def test_partial_unexpected_count_preserved_when_supplied() -> None:
    raw = parse_result_format(
        {
            "result_format": ResultFormat.BASIC.value,
            "partial_unexpected_count": 5,
        }
    )
    assert raw["partial_unexpected_count"] == 5


# ---------------------------------------------------------------------------
# Tests: TypedDict structural constraints
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_result_format_config_required_is_typeddict() -> None:
    """Confirm ResultFormatConfigRequired is a TypedDict (not a runtime check, but importable)."""
    # Verify the class exists and has the expected annotations
    annotations = ResultFormatConfigRequired.__annotations__
    assert "result_format" in annotations
    assert "partial_unexpected_count" in annotations
    assert "include_unexpected_rows" in annotations
    assert "map_expectation_unexpected_rows_as_dict" in annotations


@pytest.mark.unit
def test_result_format_config_extends_required() -> None:
    """Confirm ResultFormatConfig inherits required keys from ResultFormatConfigRequired."""
    # TypedDict merges required keys from bases into __required_keys__; works on 3.10+.
    assert ResultFormatConfigRequired.__required_keys__ <= ResultFormatConfig.__required_keys__


@pytest.mark.unit
def test_result_format_config_has_optional_keys_in_annotations() -> None:
    """Confirm ResultFormatConfig declares optional keys."""
    # ResultFormatConfig (total=False subclass) owns the optional fields
    own_annotations = ResultFormatConfig.__annotations__
    assert "exclude_unexpected_values" in own_annotations
    assert "return_unexpected_index_query" in own_annotations
