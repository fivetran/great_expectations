from __future__ import annotations

from collections.abc import Callable

import pytest

from great_expectations.exceptions.exceptions import (
    BatchDefinitionNotFoundError,
    CheckpointNotFoundError,
    ExpectationSuiteNotFoundError,
    ValidationDefinitionNotFoundError,
)

# The note carries its own leading space: it is appended to the message verbatim.
NOTE = " This object is not bound to a Data Context; the current Data Context was consulted."


class TestNotFoundErrorNotes:
    """Each not-found error takes an optional note appended to its unchanged message (#12209)."""

    @pytest.mark.unit
    def test_expectation_suite_message_without_note_is_unchanged(self) -> None:
        error = ExpectationSuiteNotFoundError("my_suite")
        assert (
            str(error)
            == "ExpectationSuite 'my_suite' not found. Please check the name and try again."
        )

    @pytest.mark.unit
    def test_expectation_suite_message_with_note_appends_it(self) -> None:
        error = ExpectationSuiteNotFoundError("my_suite", note=NOTE)
        assert str(error) == (
            "ExpectationSuite 'my_suite' not found. Please check the name and try again."
            " This object is not bound to a Data Context; the current Data Context was consulted."
        )

    @pytest.mark.unit
    def test_validation_definition_message_without_note_is_unchanged(self) -> None:
        error = ValidationDefinitionNotFoundError("my_vd")
        assert (
            str(error)
            == "ValidationDefinition 'my_vd' not found. Please check the name and try again."
        )

    @pytest.mark.unit
    def test_validation_definition_message_with_note_appends_it(self) -> None:
        error = ValidationDefinitionNotFoundError("my_vd", note=NOTE)
        assert str(error) == (
            "ValidationDefinition 'my_vd' not found. Please check the name and try again."
            " This object is not bound to a Data Context; the current Data Context was consulted."
        )

    @pytest.mark.unit
    def test_checkpoint_message_without_note_is_unchanged(self) -> None:
        error = CheckpointNotFoundError("my_cp")
        assert str(error) == "Checkpoint 'my_cp' not found. Please check the name and try again."

    @pytest.mark.unit
    def test_checkpoint_message_with_note_appends_it(self) -> None:
        error = CheckpointNotFoundError("my_cp", note=NOTE)
        assert str(error) == (
            "Checkpoint 'my_cp' not found. Please check the name and try again."
            " This object is not bound to a Data Context; the current Data Context was consulted."
        )

    @pytest.mark.unit
    def test_batch_definition_message_without_note_is_unchanged(self) -> None:
        error = BatchDefinitionNotFoundError("my_bd")
        assert (
            str(error) == "BatchDefinition 'my_bd' not found. Please check the name and try again."
        )

    @pytest.mark.unit
    def test_batch_definition_message_with_note_appends_it(self) -> None:
        error = BatchDefinitionNotFoundError("my_bd", note=NOTE)
        assert str(error) == (
            "BatchDefinition 'my_bd' not found. Please check the name and try again."
            " This object is not bound to a Data Context; the current Data Context was consulted."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "make_error",
        [
            ExpectationSuiteNotFoundError,
            ValidationDefinitionNotFoundError,
            CheckpointNotFoundError,
            BatchDefinitionNotFoundError,
        ],
    )
    def test_name_keyword_and_none_note_match_positional(
        self, make_error: Callable[..., Exception]
    ) -> None:
        positional = str(make_error("x"))
        assert str(make_error(name="x")) == positional
        assert str(make_error("x", note=None)) == positional
