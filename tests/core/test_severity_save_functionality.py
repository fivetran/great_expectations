"""
Unit test for severity save/update functionality.

This test verifies that severity values are properly handled in the core
Great Expectations objects without requiring a cloud backend.
"""

import pytest

from great_expectations import get_context
from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
from great_expectations.expectations.metadata_types import FailureSeverity


@pytest.mark.unit
def test_severity_preservation_in_memory():
    """
    Test that severity values are preserved when working with expectation suites in memory.
    """
    # Get in-memory context
    context = get_context()

    # Create expectation configuration with non-default severity
    config = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.WARNING,
    )

    # Verify initial severity
    assert config.severity == FailureSeverity.WARNING

    # Create expectation suite
    suite = context.suites.add(name="test_severity_suite", expectations=[config])

    # Verify severity is preserved in the suite
    assert len(suite.expectations) == 1
    assert suite.expectations[0].severity == FailureSeverity.WARNING

    # Test updating severity
    suite.expectations[0].severity = FailureSeverity.INFO
    assert suite.expectations[0].severity == FailureSeverity.INFO

    # Test that the configuration property preserves severity
    expectation_config = suite.expectations[0].configuration
    assert expectation_config.severity == FailureSeverity.INFO


@pytest.mark.unit
def test_severity_string_assignment_in_memory():
    """
    Test that severity can be set using string values in memory.
    """
    # Get in-memory context
    context = get_context()

    # Create expectation configuration with default severity
    config = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.CRITICAL,
    )

    # Verify initial severity
    assert config.severity == FailureSeverity.CRITICAL

    # Change severity using string (like in the user's snippet)
    config.severity = "info"
    assert config.severity == FailureSeverity.INFO

    # Create suite and verify
    suite = context.suites.add(name="test_string_severity_suite", expectations=[config])

    assert suite.expectations[0].severity == FailureSeverity.INFO


@pytest.mark.unit
def test_severity_serialization_roundtrip():
    """
    Test that severity is preserved through serialization/deserialization.
    """
    # Create expectation configuration with custom severity
    config = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.WARNING,
    )

    # Serialize to JSON
    json_dict = config.to_json_dict()
    assert json_dict["severity"] == "warning"

    # Create new config from JSON
    new_config = ExpectationConfiguration(**json_dict)
    assert new_config.severity == FailureSeverity.WARNING

    # Test with different severity
    config.severity = FailureSeverity.INFO
    json_dict = config.to_json_dict()
    assert json_dict["severity"] == "info"

    new_config = ExpectationConfiguration(**json_dict)
    assert new_config.severity == FailureSeverity.INFO


@pytest.mark.unit
def test_severity_in_to_domain_obj():
    """
    Test that severity is preserved when converting to domain object.
    """
    # Create expectation configuration with custom severity
    config = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.WARNING,
    )

    # Convert to domain object
    expectation = config.to_domain_obj()

    # Verify severity is preserved
    assert expectation.severity == FailureSeverity.WARNING

    # Test that configuration property preserves severity
    expectation_config = expectation.configuration
    assert expectation_config.severity == FailureSeverity.WARNING


@pytest.mark.unit
def test_severity_equality_and_hash():
    """
    Test that severity is NOT considered in equality and hash operations (current implementation).
    """
    # Create two configs with different severities
    config1 = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.CRITICAL,
    )

    config2 = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.WARNING,
    )

    config3 = ExpectationConfiguration(
        type="expect_column_values_to_not_be_null",
        kwargs={"column": "test_column"},
        severity=FailureSeverity.CRITICAL,
    )

    # Test equality (current implementation doesn't include severity)
    assert config1 == config2  # Same type/kwargs, different severity
    assert config1 == config3  # Same type/kwargs, same severity

    # Test hash (current implementation doesn't include severity)
    assert hash(config1) == hash(config2)  # Same hash
    assert hash(config1) == hash(config3)  # Same hash
