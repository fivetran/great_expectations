import re
from copy import copy
from typing import Dict
from unittest import mock
from unittest.mock import (
    ANY,
    Mock,  # noqa: TID251 # FIXME CoP
)
from unittest.mock import ANY as ANY_TEST_ARG

import pytest
from pytest_mock import MockerFixture

from great_expectations.alias_types import JSONValues
from great_expectations.analytics.events import (
    DomainObjectAllDeserializationEvent,
    ExpectationSuiteCreatedEvent,
    ExpectationSuiteDeletedEvent,
)
from great_expectations.core import ExpectationSuite
from great_expectations.core.factory.suite_factory import SuiteFactory
from great_expectations.data_context import AbstractDataContext
from great_expectations.data_context.data_context.context_factory import set_context
from great_expectations.data_context.store import ExpectationsStore
from great_expectations.exceptions import DataContextError
from great_expectations.expectations import (
    ExpectColumnDistinctValuesToContainSet,
    ExpectColumnSumToBeBetween,
)
from great_expectations.types import SerializableDictDot


@pytest.mark.unit
def test_suite_factory_get_uses_store_get():
    # Arrange
    name = "test-suite"
    store = Mock(spec=ExpectationsStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    suite_dict = {"name": name, "id": "3a758816-64c8-46cb-8f7e-03c12cea1d67"}
    store.get.return_value = suite_dict
    factory = SuiteFactory(store=store)
    context = Mock(spec=AbstractDataContext)
    set_context(context)

    # Act
    factory.get(name=name)

    # Assert
    store.get.assert_called_once_with(key=key)
    store.deserialize_suite_dict.assert_called_once_with(suite_dict)


@pytest.mark.unit
def test_suite_factory_get_raises_error_on_missing_key():
    # Arrange
    name = "test-suite"
    store = Mock(spec=ExpectationsStore)
    store.has_key.return_value = False
    suite_dict = {"name": name, "id": "3a758816-64c8-46cb-8f7e-03c12cea1d67"}
    store.get.return_value = suite_dict
    factory = SuiteFactory(store=store)
    context = Mock(spec=AbstractDataContext)
    set_context(context)

    # Act
    with pytest.raises(DataContextError, match=f"ExpectationSuite with name {name} was not found."):
        factory.get(name=name)

    # Assert
    store.get.assert_not_called()


@pytest.mark.unit
def test_suite_factory_add_uses_store_add():
    # Arrange
    name = "test-suite"
    store = Mock(spec=ExpectationsStore)
    store.has_key.return_value = False
    key = store.get_key.return_value
    factory = SuiteFactory(store=store)
    context = Mock(spec=AbstractDataContext)
    set_context(context)
    suite = ExpectationSuite(name=name)

    # Act
    factory.add(suite=suite)

    # Assert
    store.add.assert_called_once_with(key=key, value=suite)


@pytest.mark.unit
def test_suite_factory_add_raises_for_duplicate_key():
    # Arrange
    name = "test-suite"
    store = Mock(spec=ExpectationsStore)
    store.has_key.return_value = True
    factory = SuiteFactory(store=store)
    context = Mock(spec=AbstractDataContext)
    set_context(context)
    suite = ExpectationSuite(name=name)

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot add ExpectationSuite with name {suite.name} because it already exists.",
    ):
        factory.add(suite=suite)

    # Assert
    store.add.assert_not_called()


@pytest.mark.unit
def test_suite_factory_delete_uses_store_remove_key():
    # Arrange
    name = "test-suite"
    store = Mock(spec=ExpectationsStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    store.get.return_value = {"name": name}
    factory = SuiteFactory(store=store)
    context = Mock(spec=AbstractDataContext)
    set_context(context)

    # Act
    factory.delete(name=name)

    # Assert
    store.remove_key.assert_called_once_with(
        key=key,
    )


@pytest.mark.unit
def test_suite_factory_delete_raises_for_missing_suite():
    # Arrange
    name = "test-suite"
    store = Mock(spec=ExpectationsStore)
    store.has_key.return_value = False
    factory = SuiteFactory(store=store)
    context = Mock(spec=AbstractDataContext)
    set_context(context)

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot delete ExpectationSuite with name {name} because it cannot be found.",
    ):
        factory.delete(name=name)

    # Assert
    store.remove_key.assert_not_called()


@pytest.mark.filesystem
def test_suite_factory_is_initialized_with_context_filesystem(empty_data_context):
    assert isinstance(empty_data_context.suites, SuiteFactory)


@pytest.mark.cloud
def test_suite_factory_is_initialized_with_context_cloud(empty_cloud_data_context):
    assert isinstance(empty_cloud_data_context.suites, SuiteFactory)


@pytest.mark.filesystem
def test_suite_factory_add_success_filesystem(empty_data_context):
    _test_suite_factory_add_success(empty_data_context)


@pytest.mark.filesystem
def test_suite_factory_add_success_cloud(empty_cloud_context_fluent):
    _test_suite_factory_add_success(empty_cloud_context_fluent)


def _test_suite_factory_add_success(context):
    # Arrange
    name = "test-suite"
    suite = ExpectationSuite(name=name)
    with pytest.raises(DataContextError, match=f"ExpectationSuite with name {name} was not found."):
        context.suites.get(name)
    # Act
    created_suite = context.suites.add(suite=suite)
    # Assert
    assert context.suites.get(name=name) == created_suite


@pytest.mark.filesystem
def test_suite_factory_delete_success_filesystem(empty_data_context):
    _test_suite_factory_delete_success(empty_data_context)


@pytest.mark.cloud
def test_suite_factory_delete_success_cloud(empty_cloud_context_fluent):
    _test_suite_factory_delete_success(empty_cloud_context_fluent)


def _test_suite_factory_delete_success(context):
    # Arrange
    name = "test-suite"
    context.suites.add(suite=ExpectationSuite(name=name))

    # Act
    context.suites.delete(name)

    # Assert
    with pytest.raises(
        DataContextError,
        match=f"ExpectationSuite with name {name} was not found.",
    ):
        context.suites.get(name)


@pytest.mark.parametrize(
    "context_fixture_name",
    [
        pytest.param("empty_cloud_context_fluent", id="cloud", marks=pytest.mark.cloud),
        pytest.param("in_memory_runtime_context", id="ephemeral", marks=pytest.mark.big),
        pytest.param("empty_data_context", id="filesystem", marks=pytest.mark.filesystem),
    ],
)
def test_suite_factory_all(context_fixture_name: str, request: pytest.FixtureRequest):
    context: AbstractDataContext = request.getfixturevalue(context_fixture_name)

    # Arrange
    suite_a = ExpectationSuite(name="a suite")
    suite_b = ExpectationSuite(name="b suite")

    context.suites.add(suite=suite_a)
    context.suites.add(suite=suite_b)

    # Act
    result = context.suites.all()
    result = sorted(result, key=lambda x: x.name)

    # Assert
    assert [r.name for r in result] == [suite_a.name, suite_b.name]
    assert result == [suite_a, suite_b]


@pytest.mark.unit
def test_suite_factory_all_with_bad_marshmallow_config(
    in_memory_runtime_context: AbstractDataContext, mocker: MockerFixture
):
    # The difficult part of writing this test was making an expectation I could save
    # in a bad state. To do that I've created this FakeExpectation.
    analytics_submit_mock = mocker.patch(
        "great_expectations.data_context.store.store.submit_analytics_event"
    )

    class BadExpectation(SerializableDictDot):
        def __init__(self, id: int):
            self.id = id
            # This type intentionally mismatches. We want a bad config.
            self.configuration: dict = {}

        def to_json_dict(self) -> Dict[str, JSONValues]:  # type: ignore[explicit-override] # FIXME
            return {"id": self.id}

    # Arrange
    context: AbstractDataContext = in_memory_runtime_context
    suite_1 = context.suites.add(suite=ExpectationSuite(name="suite1"))
    suite_2 = context.suites.add(suite=ExpectationSuite(name="suite2"))

    # Assert both suites are added
    assert sorted(context.suites.all(), key=lambda x: x.name) == [suite_1, suite_2]

    # Put suite_2 into an invalid state, These BadExpectations are real Expectations since
    # we want them to not deserialize correctly.
    suite_2.expectations = [BadExpectation(id=1), BadExpectation(id=2)]  # type: ignore[list-item] # FIXME CoP
    suite_2.save()

    # Act
    result = context.suites.all()

    # Assert
    assert result == [suite_1]
    analytics_submit_mock.assert_called_once_with(
        DomainObjectAllDeserializationEvent(
            error_type=ANY_TEST_ARG,
            store_name="ExpectationsStore",
        )
    )
    analytics_submit_args = analytics_submit_mock.call_args[0][0]
    assert re.match("marshmallow.*ValidationError", analytics_submit_args.error_type)


@pytest.mark.unit
def test_suite_factory_all_with_bad_pydantic_config(
    in_memory_runtime_context: AbstractDataContext, mocker: MockerFixture
):
    # Arrange
    analytics_submit_mock = mocker.patch(
        "great_expectations.data_context.store.store.submit_analytics_event"
    )

    context: AbstractDataContext = in_memory_runtime_context
    mocker.patch.object(
        context.suites._store,
        "get_all",
        lambda: [
            {
                "name": "my_suite",
                "expectations": [
                    {
                        "type": "expect_column_max_to_be_between",
                        "kwargs": {
                            "column": "my_col",
                            # mostly makes this expectation invalid
                            "mostly": None,
                            "max_value": 265,
                            "min_value": 265,
                        },
                    }
                ],
            }
        ],
    )

    # Act
    result = context.suites.all()

    # Assert
    assert result == []
    analytics_submit_mock.assert_called_once_with(
        DomainObjectAllDeserializationEvent(
            error_type=ANY_TEST_ARG,
            store_name="ExpectationsStore",
        )
    )
    analytics_submit_args = analytics_submit_mock.call_args[0][0]
    assert re.match("pydantic.*ValidationError", analytics_submit_args.error_type)


class TestSuiteFactoryAddOrUpdate:
    def test_add_empty_new_suite(self, data_context: AbstractDataContext) -> None:
        # arrange
        suite_name = "suite A"
        suite = ExpectationSuite(name=suite_name)

        # act
        created_suite = data_context.suites.add_or_update(suite=suite)

        # assert
        assert created_suite.id
        data_context.suites.get(suite_name)

    def test_add_new_suite_with_expectations(self, data_context: AbstractDataContext) -> None:
        # arrange
        suite_name = "suite A"
        expectations = [
            ExpectColumnSumToBeBetween(
                column="col A",
                min_value=0,
                max_value=10,
            ),
            ExpectColumnDistinctValuesToContainSet(
                column="col B",
                value_set=["a", "b", "c"],
            ),
        ]
        suite = ExpectationSuite(
            name=suite_name,
            expectations=[copy(exp) for exp in expectations],
        )

        # act
        created_suite = data_context.suites.add_or_update(suite=suite)

        # assert
        assert created_suite.id
        data_context.suites.get(suite_name)
        for exp, created_exp in zip(expectations, created_suite.expectations):
            assert created_exp.id
            exp.id = ANY
            assert exp == created_exp

    def test_update_existing_suite_adds_expectations(
        self, data_context: AbstractDataContext
    ) -> None:
        # arrange
        suite_name = "suite A"
        expectations = [
            ExpectColumnSumToBeBetween(
                column="col A",
                min_value=0,
                max_value=10,
            ),
            ExpectColumnDistinctValuesToContainSet(
                column="col B",
                value_set=["a", "b", "c"],
            ),
        ]
        suite = ExpectationSuite(
            name=suite_name,
            expectations=[copy(exp) for exp in expectations],
        )
        existing_suite = data_context.suites.add(suite=ExpectationSuite(name=suite_name))

        # act
        updated_suite = data_context.suites.add_or_update(suite=suite)

        # assert
        assert updated_suite.id == existing_suite.id
        for exp, created_exp in zip(expectations, updated_suite.expectations):
            assert created_exp.id
            exp.id = ANY
            assert exp == created_exp

    def _test_update_existing_suite_updates_expectations(
        self, data_context: AbstractDataContext
    ) -> None:
        # arrange
        suite_name = "suite A"
        expectations = [
            ExpectColumnSumToBeBetween(
                column="col A",
                min_value=0,
                max_value=10,
            ),
            ExpectColumnDistinctValuesToContainSet(
                column="col B",
                value_set=["a", "b", "c"],
            ),
        ]
        existing_suite = data_context.suites.add(
            suite=ExpectationSuite(
                name=suite_name,
                expectations=[copy(exp) for exp in expectations],
            )
        )
        new_col_name = "col C"
        for exp in expectations:
            exp.column = new_col_name
        suite = ExpectationSuite(
            name=suite_name,
            expectations=[copy(exp) for exp in expectations],
        )

        # act
        updated_suite = data_context.suites.add_or_update(suite=suite)

        # assert
        assert updated_suite.id == existing_suite.id
        for exp, created_exp in zip(expectations, updated_suite.expectations):
            assert created_exp.id
            exp.id = ANY
            assert exp == created_exp
            assert created_exp.column == new_col_name  # type: ignore[attr-defined]  # column exists

        for old_exp, new_exp in zip(existing_suite.expectations, updated_suite.expectations):
            # expectations have been deleted and re added, not updated
            assert old_exp.id != new_exp.id

    def test_update_existing_suite_deletes_expectations(
        self, data_context: AbstractDataContext
    ) -> None:
        # arrange
        suite_name = "suite A"
        expectations = [
            ExpectColumnSumToBeBetween(
                column="col A",
                min_value=0,
                max_value=10,
            ),
            ExpectColumnDistinctValuesToContainSet(
                column="col B",
                value_set=["a", "b", "c"],
            ),
        ]
        existing_suite = data_context.suites.add(
            suite=ExpectationSuite(
                name=suite_name,
                expectations=[copy(exp) for exp in expectations],
            )
        )
        new_col_name = "col C"
        for exp in expectations:
            exp.column = new_col_name
        suite = ExpectationSuite(
            name=suite_name,
            expectations=[],
        )

        # act
        updated_suite = data_context.suites.add_or_update(suite=suite)

        # assert
        assert updated_suite.id == existing_suite.id
        assert updated_suite.expectations == []

    def test_add_or_update_is_idempotent(self, data_context: AbstractDataContext) -> None:
        # arrange
        suite_name = "suite A"
        expectations = [
            ExpectColumnSumToBeBetween(
                column="col A",
                min_value=0,
                max_value=10,
            ),
            ExpectColumnDistinctValuesToContainSet(
                column="col B",
                value_set=["a", "b", "c"],
            ),
        ]
        suite = ExpectationSuite(
            name=suite_name,
            expectations=[copy(exp) for exp in expectations],
        )

        # act
        suite_1 = data_context.suites.add_or_update(suite=suite)
        suite_2 = data_context.suites.add_or_update(suite=suite)
        suite_3 = data_context.suites.add_or_update(suite=suite)

        # assert
        assert suite_1 == suite_2 == suite_3


class TestSuiteFactoryAnalytics:
    def test_suite_factory_add_emits_event(self, data_context: AbstractDataContext) -> None:
        # Arrange
        name = "test-suite"
        suite = ExpectationSuite(name=name)

        # Act
        with mock.patch(
            "great_expectations.core.factory.suite_factory.submit_event", autospec=True
        ) as mock_submit:
            _ = data_context.suites.add(suite=suite)

        # Assert
        mock_submit.assert_called_once_with(
            event=ExpectationSuiteCreatedEvent(expectation_suite_id=suite.id)
        )

    def test_suite_factory_delete_emits_event(self, data_context: AbstractDataContext) -> None:
        # Arrange
        name = "test-suite"
        suite = ExpectationSuite(name=name)
        suite = data_context.suites.add(suite=suite)

        # Act
        with mock.patch(
            "great_expectations.core.factory.suite_factory.submit_event", autospec=True
        ) as mock_submit:
            data_context.suites.delete(name=name)

        # Assert
        mock_submit.assert_called_once_with(
            event=ExpectationSuiteDeletedEvent(expectation_suite_id=suite.id)
        )
