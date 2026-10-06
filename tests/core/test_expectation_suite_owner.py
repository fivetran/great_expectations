"""An ExpectationSuite belongs to the Data Context whose store built or wrote it (#12209).

A store records its context on every suite it builds or writes, so the suite resolves through
that context whatever context is current later. A suite that was never added, and any copy of one,
belongs to no context and resolves through the current one.
"""

from __future__ import annotations

import copy
import pathlib
import pickle
from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest

import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite, ExpectationSuiteSchema
from great_expectations.data_context.data_context.context_factory import (
    project_manager,
    set_context,
)
from great_expectations.data_context.store import ExpectationsStore
from great_expectations.exceptions import (
    DataContextError,
    DataContextRequiredError,
    ExpectationSuiteNotAddedError,
)

if TYPE_CHECKING:
    from great_expectations.data_context import AbstractDataContext

SCHEMA_FIELDS = set(ExpectationSuiteSchema().fields)


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
def c1_and_c2(
    restore_current_context: None,
) -> tuple[AbstractDataContext, AbstractDataContext]:
    """Two distinct ephemeral contexts, with the second (C2) current."""
    c1 = gx.get_context(mode="ephemeral")
    c2 = gx.get_context(mode="ephemeral")
    assert c1 is not c2
    assert project_manager.get_current_project() is c2
    return c1, c2


@pytest.fixture
def single_context(restore_current_context: None) -> AbstractDataContext:
    return gx.get_context(mode="ephemeral")


class TestStoreStampsTheSuitesItHandsOut:
    @pytest.mark.unit
    def test_add_returns_a_suite_owned_by_the_context_it_was_added_to(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2

        added = c1.suites.add(ExpectationSuite(name="my_suite"))

        assert added._owner is c1

    @pytest.mark.unit
    def test_add_stamps_the_callers_original_object(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2
        original = ExpectationSuite(name="my_suite")
        assert original._owner is None

        returned = c1.suites.add(original)

        assert original._owner is c1
        assert returned is not original

    @pytest.mark.unit
    def test_a_failed_add_leaves_the_callers_object_unstamped(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2
        c1.suites.add(ExpectationSuite(name="my_suite"))
        duplicate = ExpectationSuite(name="my_suite")

        with pytest.raises(DataContextError):
            c1.suites.add(duplicate)

        assert duplicate._owner is None

    @pytest.mark.unit
    def test_a_failed_store_write_leaves_the_callers_object_unstamped(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        # Below the factory's own existence check: the backend itself refuses the second write.
        c1, _ = c1_and_c2
        store = c1.suites._store
        key = store.get_key(name="my_suite", id=None)
        store.add(key=key, value=ExpectationSuite(name="my_suite"))
        duplicate = ExpectationSuite(name="my_suite")

        with pytest.raises(Exception, match="my_suite"):
            store.add(key=key, value=duplicate)

        assert duplicate._owner is None

    @pytest.mark.unit
    def test_get_returns_a_suite_owned_by_its_context(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2
        c1.suites.add(ExpectationSuite(name="my_suite"))

        assert c1.suites.get("my_suite")._owner is c1

    @pytest.mark.unit
    def test_add_or_update_returns_a_suite_owned_by_its_context(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2

        created = c1.suites.add_or_update(ExpectationSuite(name="my_suite"))

        assert created._owner is c1

    @pytest.mark.unit
    def test_all_returns_suites_owned_by_their_context(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2
        c1.suites.add(ExpectationSuite(name="first"))
        c1.suites.add(ExpectationSuite(name="second"))

        suites = list(c1.suites.all())

        assert len(suites) == 2
        assert all(suite._owner is c1 for suite in suites)

    @pytest.mark.unit
    def test_update_stamps_the_suite_it_writes(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, _ = c1_and_c2
        store = c1.suites._store
        persisted = c1.suites.add(ExpectationSuite(name="my_suite"))
        unowned = ExpectationSuite(name="my_suite", id=persisted.id)
        assert unowned._owner is None

        store.update(key=store.get_key(name="my_suite", id=persisted.id), value=unowned)

        assert unowned._owner is c1

    @pytest.mark.unit
    def test_a_failed_update_leaves_the_callers_object_unstamped(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        # The suite was never added, so the backend refuses to update it.
        c1, _ = c1_and_c2
        store = c1.suites._store
        never = ExpectationSuite(name="never_added")

        with pytest.raises(ExpectationSuiteNotAddedError):
            store.update(key=store.get_key(name="never_added", id=None), value=never)

        assert never._owner is None

    @pytest.mark.unit
    def test_each_context_stamps_its_own_suites(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, c2 = c1_and_c2
        c1.suites.add(ExpectationSuite(name="in_one"))
        c2.suites.add(ExpectationSuite(name="in_two"))

        assert c1.suites.get("in_one")._owner is c1
        assert c2.suites.get("in_two")._owner is c2

    @pytest.mark.unit
    def test_a_later_set_context_does_not_change_the_owner(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, c2 = c1_and_c2
        # Make C1 current for the add, so that selecting C2 afterwards is a real change.
        set_context(c1)
        assert project_manager.get_current_project() is c1
        owned = c1.suites.add(ExpectationSuite(name="my_suite"))
        unowned = copy.deepcopy(owned)

        set_context(c2)

        assert project_manager.get_current_project() is c2
        assert owned._owner is c1
        assert owned._resolve_context().context is c1
        assert owned._resolve_context().bound is True
        # A suite that belongs to no context follows the current one.
        assert unowned._resolve_context().context is c2
        assert unowned._resolve_context().bound is False


class TestStoreWithoutAContext:
    @pytest.mark.unit
    def test_a_directly_constructed_store_has_no_context(self) -> None:
        assert ExpectationsStore().data_context is None

    @pytest.mark.unit
    def test_a_directly_constructed_store_leaves_suites_unowned(
        self,
        single_context: AbstractDataContext,  # a current context, for the suite's own lookups
    ) -> None:
        store = ExpectationsStore()
        key = store.get_key(name="my_suite", id=None)
        suite = ExpectationSuite(name="my_suite")

        store.add(key=key, value=suite)
        built = store.deserialize_suite_dict(store.get(key=key))

        assert suite._owner is None
        assert built._owner is None

    @pytest.mark.unit
    def test_a_store_built_by_a_context_exposes_that_context(
        self, c1_and_c2: tuple[AbstractDataContext, AbstractDataContext]
    ) -> None:
        c1, c2 = c1_and_c2

        assert c1.suites._store.data_context is c1
        assert c2.suites._store.data_context is c2


class TestFileBackedStore:
    @pytest.mark.filesystem
    def test_file_backed_stores_stamp_their_context(
        self, restore_current_context: None, tmp_path: pathlib.Path
    ) -> None:
        c1 = gx.get_context(mode="file", project_root_dir=tmp_path / "one")
        c2 = gx.get_context(mode="file", project_root_dir=tmp_path / "two")
        assert project_manager.get_current_project() is c2
        original = ExpectationSuite(name="my_suite")

        added = c1.suites.add(original)

        assert original._owner is c1
        assert added._owner is c1
        assert c1.suites.get("my_suite")._owner is c1
        assert [suite._owner for suite in c1.suites.all()] == [c1]


class TestCopiesBelongToNoContext:
    """A suite added to a single context stays copyable, and a copy is owned by nobody."""

    @pytest.fixture
    def owned(self, single_context: AbstractDataContext) -> ExpectationSuite:
        suite = single_context.suites.add(ExpectationSuite(name="my_suite"))
        assert suite._owner is single_context
        return suite

    @pytest.mark.unit
    def test_deepcopy_is_unowned(self, owned: ExpectationSuite) -> None:
        duplicate = copy.deepcopy(owned)

        assert duplicate._owner is None
        assert set(duplicate.to_dict()) == SCHEMA_FIELDS

    @pytest.mark.unit
    def test_shallow_copy_is_unowned(self, owned: ExpectationSuite) -> None:
        duplicate = copy.copy(owned)

        assert duplicate._owner is None
        assert set(duplicate.to_dict()) == SCHEMA_FIELDS

    @pytest.mark.unit
    def test_pickle_round_trip_is_unowned(self, owned: ExpectationSuite) -> None:
        duplicate = pickle.loads(pickle.dumps(owned))

        assert duplicate._owner is None
        assert set(duplicate.to_dict()) == SCHEMA_FIELDS

    @pytest.mark.unit
    def test_copying_leaves_the_original_owned(self, owned: ExpectationSuite) -> None:
        owner = owned._owner
        copy.deepcopy(owned)
        copy.copy(owned)
        pickle.loads(pickle.dumps(owned))

        assert owned._owner is owner
