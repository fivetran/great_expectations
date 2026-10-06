from __future__ import annotations

import dataclasses
import pathlib
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any

import pytest

import great_expectations as gx
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite, ExpectationSuiteSchema
from great_expectations.core.owner_resolution import (
    ResolvedContext,
    owner_from_batch_definition,
    resolve_context,
    unbound_resolution_note,
)
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context import AbstractDataContext
from great_expectations.data_context.data_context.context_factory import (
    project_manager,
    set_context,
)
from great_expectations.datasource.fluent import PandasDatasource
from great_expectations.exceptions.exceptions import (
    BatchDefinitionNotFoundError,
    CheckpointNotFoundError,
    DataContextRequiredError,
    ExpectationSuiteNotFoundError,
    ValidationDefinitionNotFoundError,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

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


@pytest.fixture
def restore_current_context() -> Iterator[None]:
    """Put the process-wide current Data Context back as the test found it."""
    try:
        previous: AbstractDataContext | None = project_manager.get_current_project()
    except DataContextRequiredError:
        previous = None
    yield
    set_context(previous)


@pytest.fixture
def no_current_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty the shared project manager itself, so every module that reads it sees no context.

    monkeypatch puts the previous current context back at teardown.
    """
    monkeypatch.setattr(project_manager, "_ProjectManager__project", None)


def _bound_batch_definition(context: AbstractDataContext) -> BatchDefinition[Any]:
    datasource = context.data_sources.add_pandas("my_datasource")
    asset = datasource.add_dataframe_asset("my_asset")
    return asset.add_batch_definition_whole_dataframe("my_batch_definition")


class TestOwnerFromBatchDefinition:
    """The chain walk returns the owning context, or None, and never raises (#12209)."""

    @pytest.mark.unit
    def test_bare_batch_definition_has_no_owner(self) -> None:
        assert owner_from_batch_definition(BatchDefinition(name="bd")) is None

    @pytest.mark.unit
    def test_validation_definition_mock_has_no_owner(self, mocker: MockerFixture) -> None:
        assert owner_from_batch_definition(mocker.Mock(spec=ValidationDefinition)) is None

    @pytest.mark.unit
    def test_hand_assembled_datasource_without_context_has_no_owner(self) -> None:
        datasource = PandasDatasource(name="my_datasource")
        asset = datasource.add_dataframe_asset("my_asset")
        batch_definition = asset.add_batch_definition_whole_dataframe("bd")

        assert datasource.data_context is None
        assert owner_from_batch_definition(batch_definition) is None

    @pytest.mark.unit
    def test_batch_definition_mock_has_no_owner(self, mocker: MockerFixture) -> None:
        assert owner_from_batch_definition(mocker.Mock(spec=BatchDefinition)) is None

    @pytest.mark.unit
    def test_unspecced_mock_chain_has_no_owner(self, mocker: MockerFixture) -> None:
        assert owner_from_batch_definition(mocker.Mock()) is None

    @pytest.mark.unit
    def test_chain_ending_in_none_has_no_owner(self, mocker: MockerFixture) -> None:
        batch_definition = mocker.Mock()
        batch_definition.data_asset.datasource.data_context = None
        assert owner_from_batch_definition(batch_definition) is None

    @pytest.mark.unit
    def test_none_has_no_owner(self) -> None:
        assert owner_from_batch_definition(None) is None

    @pytest.mark.unit
    def test_real_chain_returns_the_owning_context(self, restore_current_context: None) -> None:
        context = gx.get_context(mode="ephemeral")
        batch_definition = _bound_batch_definition(context)

        assert owner_from_batch_definition(batch_definition) is context


class TestResolveContext:
    """An owner resolves as bound; otherwise the current context resolves as not bound."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "make_object",
        [
            lambda mocker: BatchDefinition(name="bd"),
            lambda mocker: mocker.Mock(spec=ValidationDefinition),
            lambda mocker: (
                PandasDatasource(name="ds")
                .add_dataframe_asset("a")
                .add_batch_definition_whole_dataframe("bd")
            ),
            lambda mocker: mocker.Mock(spec=BatchDefinition),
        ],
        ids=["bare", "validation_definition_mock", "hand_assembled", "batch_definition_mock"],
    )
    def test_ownerless_shapes_resolve_to_the_current_context_unbound(
        self,
        make_object: Callable[[MockerFixture], Any],
        mocker: MockerFixture,
        restore_current_context: None,
    ) -> None:
        current = gx.get_context(mode="ephemeral")

        resolved = resolve_context(owner_from_batch_definition(make_object(mocker)))

        assert resolved == ResolvedContext(context=current, bound=False)
        assert resolved.context is current

    @pytest.mark.unit
    def test_real_chain_resolves_to_its_owner_while_another_context_is_current(
        self, restore_current_context: None
    ) -> None:
        owner = gx.get_context(mode="ephemeral")
        batch_definition = _bound_batch_definition(owner)
        other = gx.get_context(mode="ephemeral")
        assert project_manager.get_current_project() is other

        resolved = resolve_context(owner_from_batch_definition(batch_definition))

        assert resolved.context is owner
        assert resolved.bound is True

    @pytest.mark.unit
    def test_real_chain_resolves_to_its_owner_after_set_context_selects_the_other(
        self, restore_current_context: None
    ) -> None:
        other = gx.get_context(mode="ephemeral")
        owner = gx.get_context(mode="ephemeral")
        batch_definition = _bound_batch_definition(owner)
        assert project_manager.get_current_project() is owner
        set_context(other)  # selecting the other context is the stimulus
        assert project_manager.get_current_project() is other

        resolved = resolve_context(owner_from_batch_definition(batch_definition))

        assert resolved.context is owner
        assert resolved.bound is True

    @pytest.mark.unit
    def test_no_owner_and_no_current_context_raises_the_required_error(
        self, no_current_context: None
    ) -> None:
        with pytest.raises(DataContextRequiredError) as exc_info:
            resolve_context(None)

        assert str(exc_info.value) == (
            "This action requires an active data context. "
            "Please call `great_expectations.get_context()` first, then try your action again."
        )

    @pytest.mark.unit
    def test_owner_resolves_without_any_current_context(
        self, restore_current_context: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        owner = gx.get_context(mode="ephemeral")
        monkeypatch.setattr(project_manager, "_ProjectManager__project", None)

        assert resolve_context(owner) == ResolvedContext(context=owner, bound=True)

    @pytest.mark.unit
    def test_resolved_context_is_frozen(self, mocker: MockerFixture) -> None:
        resolved = ResolvedContext(context=mocker.Mock(spec=AbstractDataContext), bound=True)

        field = "bound"
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(resolved, field, False)


class TestUnboundResolutionNote:
    """The note says the object is not bound and names the context that was consulted."""

    @pytest.mark.unit
    def test_ephemeral_context_is_named_by_mode_alone(self, restore_current_context: None) -> None:
        context = gx.get_context(mode="ephemeral")

        assert unbound_resolution_note(context) == (
            " This object is not bound to a Data Context,"
            " so the lookup went through the current ephemeral Data Context."
        )

    @pytest.mark.filesystem
    def test_file_context_is_named_by_mode_directory_and_id(
        self, tmp_path: pathlib.Path, restore_current_context: None
    ) -> None:
        context = gx.get_context(mode="file", project_root_dir=tmp_path)
        root_directory = str(tmp_path / "gx")
        context_id = str(context.data_context_id)
        assert context_id != "None"

        assert unbound_resolution_note(context) == (
            " This object is not bound to a Data Context,"
            f" so the lookup went through the current file Data Context at '{root_directory}'"
            f" (id {context_id})."
        )


class TestExpectationSuiteMiss:
    """A suite that belongs to no Data Context says which context the lookup went through."""

    @pytest.mark.unit
    def test_owner_slot_is_not_part_of_the_serialized_keys(self) -> None:
        assert sorted(ExpectationSuite(name="s").to_dict()) == sorted(
            ExpectationSuiteSchema().fields
        )

    @pytest.mark.unit
    def test_unbound_suite_miss_names_the_ephemeral_context_consulted(
        self, restore_current_context: None
    ) -> None:
        context = gx.get_context(mode="ephemeral")
        suite = ExpectationSuite(name="never_added", id="a-suite-id")

        diagnostics = suite.is_fresh()

        assert diagnostics.success is False
        assert len(diagnostics.errors) == 1
        error = diagnostics.errors[0]
        assert isinstance(error, ExpectationSuiteNotFoundError)
        assert str(error) == (
            "ExpectationSuite 'never_added' not found. Please check the name and try again."
            + unbound_resolution_note(context)
        )
        assert "This object is not bound to a Data Context" in str(error)
        assert "the current ephemeral Data Context." in str(error)

    @pytest.mark.filesystem
    def test_unbound_suite_miss_names_the_file_context_consulted(
        self, tmp_path: pathlib.Path, restore_current_context: None
    ) -> None:
        context = gx.get_context(mode="file", project_root_dir=tmp_path)
        root_directory = str(tmp_path / "gx")
        context_id = str(context.data_context_id)
        assert context_id != "None"
        suite = ExpectationSuite(name="never_added", id="a-suite-id")

        diagnostics = suite.is_fresh()

        assert len(diagnostics.errors) == 1
        error = diagnostics.errors[0]
        assert isinstance(error, ExpectationSuiteNotFoundError)
        assert str(error) == (
            "ExpectationSuite 'never_added' not found. Please check the name and try again."
            " This object is not bound to a Data Context,"
            f" so the lookup went through the current file Data Context at '{root_directory}'"
            f" (id {context_id})."
        )

    @pytest.mark.unit
    def test_unbound_suite_lookup_without_a_current_context_requires_one(
        self, no_current_context: None
    ) -> None:
        suite = ExpectationSuite(name="never_added", id="a-suite-id")

        with pytest.raises(DataContextRequiredError) as exc_info:
            suite.is_fresh()

        assert str(exc_info.value) == (
            "This action requires an active data context. "
            "Please call `great_expectations.get_context()` first, then try your action again."
        )
