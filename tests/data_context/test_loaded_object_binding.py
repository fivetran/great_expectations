"""A store-loaded object resolves its references through the Data Context that holds it (#12209).

A Validation Definition read back from a Data Context's store names a suite and a batch
definition. They are looked up in that same context, whatever context is current, and the object
that comes back belongs to it. An object built directly, outside any store, still resolves through
the current context.
"""

from __future__ import annotations

import logging
import pathlib
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Callable

import pytest

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.owner_resolution import owner_from_batch_definition
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context import AbstractDataContext
from great_expectations.data_context.data_context.context_factory import (
    project_manager,
    set_context,
)
from great_expectations.data_context.data_context.file_data_context import FileDataContext
from great_expectations.data_context.store import ValidationDefinitionStore
from great_expectations.exceptions import DataContextRequiredError

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# The wording a miss carries when the lookup went through the current context.
AMBIENT_NOTE = "not bound to a Data Context"
CURRENT_CONTEXT_WORDING = "current Data Context"


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
def c1(
    request: pytest.FixtureRequest, tmp_path: pathlib.Path, restore_current_context: None
) -> AbstractDataContext:
    """The first context, of the kind the test is parametrized with. It is current until C2 is."""
    if request.param == "file":
        return gx.get_context(mode="file", project_root_dir=tmp_path / "one")
    return gx.get_context(mode="ephemeral")


@pytest.fixture
def make_c2(tmp_path: pathlib.Path, c1: AbstractDataContext) -> Callable[[], AbstractDataContext]:
    """Create a second context of the same kind, which makes it the current context.

    A test calls it after building its resources in C1. Adding a validation definition
    serializes it, which resolves its batch definition's data source in the current context; so
    resources are added to C1 before C2 is created, and the assertions run with C2 current.
    """

    def _make() -> AbstractDataContext:
        c2: AbstractDataContext
        if isinstance(c1, FileDataContext):
            c2 = gx.get_context(mode="file", project_root_dir=tmp_path / "two")
        else:
            c2 = gx.get_context(mode="ephemeral")
        assert c2 is not c1
        assert project_manager.get_current_project() is c2
        return c2

    return _make


# Each test runs against an ephemeral context and a file-backed one.
both_context_kinds = pytest.mark.parametrize(
    "c1",
    [
        pytest.param("ephemeral", id="ephemeral", marks=pytest.mark.unit),
        pytest.param("file", id="file", marks=pytest.mark.filesystem),
    ],
    indirect=True,
)


def _add_validation_definition(
    context: AbstractDataContext, name: str
) -> tuple[ValidationDefinition, BatchDefinition[Any]]:
    """Add a datasource, asset, batch definition and suite to `context`, then a definition."""
    datasource = context.data_sources.add_pandas(f"{name}_datasource")
    asset = datasource.add_dataframe_asset(f"{name}_asset")
    batch_definition = asset.add_batch_definition_whole_dataframe(f"{name}_batch_definition")
    suite = context.suites.add(
        ExpectationSuite(
            name=f"{name}_suite",
            expectations=[gxe.ExpectColumnValuesToNotBeNull(column="a")],
        )
    )
    added = context.validation_definitions.add(
        ValidationDefinition(name=name, data=batch_definition, suite=suite)
    )
    return added, batch_definition


def _remove_batch_definition(
    context: AbstractDataContext, name: str, batch_definition: BatchDefinition[Any]
) -> None:
    """Make the stored definition `name` name a batch definition its context no longer has."""
    asset = context.data_sources.get(f"{name}_datasource").get_asset(f"{name}_asset")
    asset.delete_batch_definition(batch_definition.name)


def _break_reference(context: AbstractDataContext, name: str, reference: str) -> None:
    """Remove the datasource, asset or batch definition the stored definition `name` names."""
    datasource = context.data_sources.get(f"{name}_datasource")
    if reference == "datasource":
        context.data_sources.delete(datasource.name)
    elif reference == "asset":
        datasource.delete_asset(f"{name}_asset")
    else:
        datasource.get_asset(f"{name}_asset").delete_batch_definition(f"{name}_batch_definition")


# What each kind of miss in the record's own context says, with no note about another context.
PLAIN_MISS_TEXT = {
    "datasource": "Could not find datasource named 'vd_datasource'.",
    "asset": "Could not find asset named 'vd_asset' within 'vd_datasource' datasource.",
    "batch_definition": (
        "Could not find batch definition named 'vd_batch_definition' within 'vd_asset' asset "
        "and 'vd_datasource' datasource."
    ),
}
each_reference = pytest.mark.parametrize("reference", list(PLAIN_MISS_TEXT))


def _record_path(context: AbstractDataContext, folder: str, name: str) -> pathlib.Path:
    assert context.root_directory is not None
    return pathlib.Path(context.root_directory) / folder / f"{name}.json"


class TestValidationDefinitionStoreResolvesThroughItsContext:
    @both_context_kinds
    def test_get_returns_a_definition_whose_chain_reaches_its_context(
        self, c1: AbstractDataContext, make_c2: Callable[[], AbstractDataContext]
    ) -> None:
        _add_validation_definition(c1, "vd")
        make_c2()

        loaded = c1.validation_definitions.get("vd")

        assert owner_from_batch_definition(loaded.data) is c1
        assert loaded.suite._owner is c1

    @both_context_kinds
    def test_get_returns_the_record_the_context_holds(
        self, c1: AbstractDataContext, make_c2: Callable[[], AbstractDataContext]
    ) -> None:
        added, _ = _add_validation_definition(c1, "vd")
        make_c2()

        loaded = c1.validation_definitions.get("vd")

        assert loaded.name == "vd"
        assert loaded.data.name == "vd_batch_definition"
        assert loaded.suite.name == "vd_suite"
        assert loaded == added

    @both_context_kinds
    def test_all_returns_every_stored_definition(
        self, c1: AbstractDataContext, make_c2: Callable[[], AbstractDataContext]
    ) -> None:
        _add_validation_definition(c1, "first")
        _add_validation_definition(c1, "second")
        make_c2()

        definitions = list(c1.validation_definitions.all())

        assert len(definitions) == 2
        assert {vd.name for vd in definitions} == {"first", "second"}
        for definition in definitions:
            assert owner_from_batch_definition(definition.data) is c1
            assert definition.suite._owner is c1

    @both_context_kinds
    @each_reference
    def test_a_miss_in_its_context_raises_the_error_the_validator_raises(
        self,
        c1: AbstractDataContext,
        make_c2: Callable[[], AbstractDataContext],
        reference: str,
    ) -> None:
        _add_validation_definition(c1, "vd")
        _break_reference(c1, "vd", reference)
        make_c2()

        with pytest.raises(ValidationError) as exc_info:
            c1.validation_definitions.get("vd")

        assert PLAIN_MISS_TEXT[reference] in str(exc_info.value)
        assert exc_info.value.model is ValidationDefinition
        assert [error["loc"] for error in exc_info.value.errors()] == [("data",)]

    @both_context_kinds
    @each_reference
    def test_a_miss_in_its_context_carries_no_current_context_note(
        self,
        c1: AbstractDataContext,
        make_c2: Callable[[], AbstractDataContext],
        reference: str,
    ) -> None:
        # The lookup went through the context that holds the record, not the current one, so a
        # note that it did would be false.
        _add_validation_definition(c1, "vd")
        _break_reference(c1, "vd", reference)
        make_c2()

        with pytest.raises(ValidationError) as exc_info:
            c1.validation_definitions.get("vd")

        message = str(exc_info.value)
        assert message.endswith(f"{PLAIN_MISS_TEXT[reference]} (type=value_error)")
        assert AMBIENT_NOTE not in message
        assert CURRENT_CONTEXT_WORDING not in message

    @both_context_kinds
    def test_a_double_miss_reports_both_fields_as_the_validators_do(
        self, c1: AbstractDataContext, make_c2: Callable[[], AbstractDataContext]
    ) -> None:
        added, batch_definition = _add_validation_definition(c1, "vd")
        _remove_batch_definition(c1, "vd", batch_definition)
        c1.suites.delete("vd_suite")
        make_c2()

        with pytest.raises(ValidationError) as exc_info:
            c1.validation_definitions.get("vd")

        assert [error["loc"] for error in exc_info.value.errors()] == [("data",), ("suite",)]
        assert str(exc_info.value) == (
            "2 validation errors for ValidationDefinition\n"
            "data\n"
            "  " + PLAIN_MISS_TEXT["batch_definition"] + " (type=value_error)\n"
            "suite\n"
            f"  Could not find suite with name: vd_suite and id: {added.suite.id} "
            "(type=value_error)"
        )

    @both_context_kinds
    def test_a_suite_miss_in_its_context_carries_the_plain_message(
        self, c1: AbstractDataContext, make_c2: Callable[[], AbstractDataContext]
    ) -> None:
        added, _ = _add_validation_definition(c1, "vd")
        c1.suites.delete("vd_suite")
        make_c2()

        with pytest.raises(ValidationError) as exc_info:
            c1.validation_definitions.get("vd")

        message = str(exc_info.value)
        assert f"Could not find suite with name: vd_suite and id: {added.suite.id}" in message
        assert AMBIENT_NOTE not in message
        assert CURRENT_CONTEXT_WORDING not in message
        assert [error["loc"] for error in exc_info.value.errors()] == [("suite",)]

    @both_context_kinds
    def test_all_skips_an_unparseable_record_with_the_existing_warning(
        self,
        c1: AbstractDataContext,
        make_c2: Callable[[], AbstractDataContext],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        _add_validation_definition(c1, "kept")
        _, batch_definition = _add_validation_definition(c1, "dropped")
        _remove_batch_definition(c1, "dropped", batch_definition)
        make_c2()

        with caplog.at_level(logging.WARNING):
            definitions = list(c1.validation_definitions.all())

        assert [vd.name for vd in definitions] == ["kept"]
        assert "Skipping Bad Configs" in caplog.text
        assert "dropped" in caplog.text


class TestAnUnreadableRecordIsSkippedNotRaised:
    @pytest.mark.filesystem
    @pytest.mark.parametrize("content", ["[1]", "null", '"text"', "7"])
    def test_a_record_that_is_not_an_object_is_skipped(
        self,
        tmp_path: pathlib.Path,
        restore_current_context: None,
        caplog: pytest.LogCaptureFixture,
        content: str,
    ) -> None:
        c1 = gx.get_context(mode="file", project_root_dir=tmp_path / "one")
        _add_validation_definition(c1, "kept")
        _add_validation_definition(c1, "broken")
        _record_path(c1, "validation_definitions", "broken").write_text(content)
        gx.get_context(mode="file", project_root_dir=tmp_path / "two")

        with pytest.raises(ValidationError) as exc_info:
            c1.validation_definitions.get("broken")
        with caplog.at_level(logging.WARNING):
            definitions = list(c1.validation_definitions.all())

        assert exc_info.value.model is ValidationDefinition
        assert [vd.name for vd in definitions] == ["kept"]
        assert "Skipping Bad Configs" in caplog.text

    @pytest.mark.filesystem
    def test_a_record_whose_suite_file_is_empty_is_skipped(
        self,
        tmp_path: pathlib.Path,
        restore_current_context: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        c1 = gx.get_context(mode="file", project_root_dir=tmp_path / "one")
        _add_validation_definition(c1, "kept")
        _add_validation_definition(c1, "broken")
        _record_path(c1, "expectations", "broken_suite").write_text("")
        gx.get_context(mode="file", project_root_dir=tmp_path / "two")

        with pytest.raises(ValidationError) as exc_info:
            c1.validation_definitions.get("broken")
        with caplog.at_level(logging.WARNING):
            definitions = list(c1.validation_definitions.all())

        assert [error["loc"] for error in exc_info.value.errors()] == [("suite",)]
        assert [vd.name for vd in definitions] == ["kept"]
        assert "Skipping Bad Configs" in caplog.text


class TestACloudRecordThatIsNotAnObject:
    @pytest.mark.unit
    def test_it_raises_the_validation_error_pydantic_raises(
        self, restore_current_context: None, mocker: MockerFixture
    ) -> None:
        c1 = gx.get_context(mode="ephemeral")
        store = c1.validation_definition_store
        mocker.patch.object(
            type(store), "cloud_mode", new_callable=mocker.PropertyMock
        ).return_value = True
        assert store.cloud_mode is True

        with pytest.raises(ValidationError) as exc_info:
            store.deserialize([1])
        with pytest.raises(ValidationError) as expected:
            ValidationDefinition.parse_obj([1])

        assert exc_info.value.model is ValidationDefinition
        assert exc_info.value.errors() == expected.value.errors()
        assert [error["loc"] for error in exc_info.value.errors()] == [("__root__",)]


class TestObjectsBuiltOutsideAStoreResolveThroughTheCurrentContext:
    @pytest.mark.unit
    def test_a_direct_miss_names_the_current_context(self, restore_current_context: None) -> None:
        c1 = gx.get_context(mode="ephemeral")
        added, batch_definition = _add_validation_definition(c1, "vd")
        _remove_batch_definition(c1, "vd", batch_definition)
        c2 = gx.get_context(mode="ephemeral")
        assert project_manager.get_current_project() is c2
        record = {
            "name": "vd",
            "data": {
                "datasource": {"name": "vd_datasource", "id": None},
                "asset": {"name": "vd_asset", "id": None},
                "batch_definition": {"name": "vd_batch_definition", "id": None},
            },
            "suite": {"name": "vd_suite", "id": added.suite.id},
        }

        with pytest.raises(ValidationError) as exc_info:
            ValidationDefinition.parse_obj(record)

        # C2 is current and holds nothing named vd_datasource: the ambient lookup is the one
        # that misses, and it says so.
        assert "Could not find datasource named 'vd_datasource'." in str(exc_info.value)
        assert AMBIENT_NOTE in str(exc_info.value)

    @pytest.mark.unit
    def test_parse_obj_still_resolves_through_a_mock_current_context(
        self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        batch_definition = BatchDefinition(name="vd_batch_definition")
        context = mocker.Mock(spec=AbstractDataContext)
        context.expectations_store.get.return_value = {"name": "vd_suite", "id": "suite-id"}
        datasource = mocker.Mock()
        datasource.get_asset.return_value.get_batch_definition.return_value = batch_definition
        context.data_sources.all.return_value = {"vd_datasource": datasource}
        monkeypatch.setattr(project_manager, "_ProjectManager__project", context)

        loaded = ValidationDefinition.parse_obj(
            {
                "name": "vd",
                "data": {
                    "datasource": {"name": "vd_datasource", "id": None},
                    "asset": {"name": "vd_asset", "id": None},
                    "batch_definition": {"name": "vd_batch_definition", "id": None},
                },
                "suite": {"name": "vd_suite", "id": "suite-id"},
            }
        )

        assert loaded.data.name == "vd_batch_definition"
        datasource.get_asset.return_value.get_batch_definition.assert_called_once_with(
            "vd_batch_definition"
        )
        assert loaded.suite.name == "vd_suite"
        context.expectations_store.get.assert_called_once()
        context.data_sources.all.assert_called_once_with()

    @pytest.mark.unit
    def test_a_store_built_directly_has_no_context(self) -> None:
        store = ValidationDefinitionStore()

        assert store.data_context is None

    @pytest.mark.unit
    def test_a_store_built_by_a_context_has_that_context(
        self, restore_current_context: None
    ) -> None:
        c1 = gx.get_context(mode="ephemeral")

        assert c1.validation_definition_store.data_context is c1
