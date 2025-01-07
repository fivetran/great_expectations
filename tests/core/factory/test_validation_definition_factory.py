import json
import pathlib
import re
from unittest import mock
from unittest.mock import ANY as ANY_TEST_ARG

import pytest
from pytest_mock import MockerFixture

import great_expectations.expectations as gxe
from great_expectations.analytics.events import (
    DomainObjectAllDeserializationEvent,
    ValidationDefinitionCreatedEvent,
    ValidationDefinitionDeletedEvent,
)
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.factory.validation_definition_factory import (
    ValidationDefinitionFactory,
)
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.data_context.abstract_data_context import (
    AbstractDataContext,
)
from great_expectations.data_context.data_context.cloud_data_context import (
    CloudDataContext,
)
from great_expectations.data_context.data_context.ephemeral_data_context import EphemeralDataContext
from great_expectations.data_context.data_context.file_data_context import (
    FileDataContext,
)
from great_expectations.data_context.store.validation_definition_store import (
    ValidationDefinitionStore,
)
from great_expectations.exceptions import DataContextError


@pytest.fixture
def validation_definition(mocker: MockerFixture) -> ValidationDefinition:
    batch_definition = mocker.Mock(spec=BatchDefinition)
    suite = mocker.Mock(spec=ExpectationSuite)
    return ValidationDefinition(
        name="test-validation",
        data=batch_definition,
        suite=suite,
    )


@pytest.fixture
def validation_definition_json(validation_definition: ValidationDefinition) -> str:
    return json.dumps(
        {
            "name": validation_definition.name,
            "id": None,
            "data": {
                "datasource": {
                    "name": "test-datasource",
                    "id": "f4b3d8f2-7e4d-4f0b-9b90-6f711d0e3e2f",
                },
                "asset": {
                    "name": "test-asset",
                    "id": "10b7e57d-958b-4d28-aa1d-e89bc0401eea",
                },
                "batch_definition": {
                    "name": "test-batch-config",
                    "id": "bcd13e3e-3e3e-4e3e-8e3e-3e3e3e3e3e3e",
                },
            },
            "suite": {
                "name": "test-expectation-suite",
                "id": "06022df2-6699-49b2-8c03-df77678363a0",
            },
        }
    )


@pytest.mark.unit
def test_validation_definition_factory_get_uses_store_get(
    mocker: MockerFixture, validation_definition: ValidationDefinition
):
    # Arrange
    name = validation_definition.name
    store = mocker.Mock(spec=ValidationDefinitionStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    store.get.return_value = validation_definition
    factory = ValidationDefinitionFactory(store=store)

    # Act
    result = factory.get(name=name)

    # Assert
    store.get.assert_called_once_with(key=key)
    assert result == validation_definition


@pytest.mark.unit
def test_validation_definition_factory_get_raises_error_on_missing_key(
    mocker: MockerFixture,
    validation_definition: ValidationDefinition,
):
    # Arrange
    name = validation_definition.name
    store = mocker.Mock(spec=ValidationDefinitionStore)
    store.has_key.return_value = False
    store.get.return_value = validation_definition
    factory = ValidationDefinitionFactory(store=store)

    # Act
    with pytest.raises(
        DataContextError, match=f"ValidationDefinition with name {name} was not found."
    ):
        factory.get(name=name)

    # Assert
    store.get.assert_not_called()


@pytest.mark.unit
def test_validation_definition_factory_add_uses_store_add(
    mocker: MockerFixture, validation_definition: ValidationDefinition
):
    # Arrange
    store = mocker.Mock(spec=ValidationDefinitionStore)
    store.has_key.return_value = False
    key = store.get_key.return_value
    factory = ValidationDefinitionFactory(store=store)
    store.get.return_value = validation_definition

    # Act
    factory.add(validation=validation_definition)

    # Assert
    store.add.assert_called_once_with(key=key, value=validation_definition)


@pytest.mark.unit
def test_validation_definition_factory_add_raises_for_duplicate_key(
    mocker: MockerFixture,
    validation_definition: ValidationDefinition,
):
    # Arrange
    name = validation_definition.name
    store = mocker.Mock(spec=ValidationDefinitionStore)
    store.has_key.return_value = True
    factory = ValidationDefinitionFactory(store=store)

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot add ValidationDefinition with name {name} because it already exists.",
    ):
        factory.add(validation=validation_definition)

    # Assert
    store.add.assert_not_called()


@pytest.mark.unit
def test_validation_definition_factory_delete_uses_store_remove_key(
    mocker: MockerFixture,
    validation_definition: ValidationDefinition,
):
    # Arrange
    store = mocker.Mock(spec=ValidationDefinitionStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    factory = ValidationDefinitionFactory(store=store)

    # Act
    factory.delete(name="my_validation_def")

    # Assert
    store.remove_key.assert_called_once_with(
        key=key,
    )


@pytest.mark.unit
def test_validation_definition_factory_delete_raises_for_missing_validation(
    mocker: MockerFixture,
    validation_definition: ValidationDefinition,
):
    # Arrange
    name = validation_definition.name
    store = mocker.Mock(spec=ValidationDefinitionStore)
    store.has_key.return_value = False
    factory = ValidationDefinitionFactory(store=store)

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot delete ValidationDefinition with name {name} because it cannot be found.",
    ):
        factory.delete(name=name)

    # Assert
    store.remove_key.assert_not_called()


@pytest.mark.filesystem
def test_validation_definition_factory_is_initialized_with_context_filesystem(
    empty_data_context: FileDataContext,
):
    assert isinstance(empty_data_context.validation_definitions, ValidationDefinitionFactory)


@pytest.mark.cloud
def test_validation_definition_factory_is_initialized_with_context_cloud(
    empty_cloud_data_context: CloudDataContext,
):
    assert isinstance(empty_cloud_data_context.validation_definitions, ValidationDefinitionFactory)


@pytest.mark.filesystem
def test_validation_definition_factory_add_success_filesystem(
    empty_data_context: FileDataContext,
    validation_definition: ValidationDefinition,
    validation_definition_json: str,
    mocker: MockerFixture,
):
    _test_validation_definition_factory_add_success(
        mocker=mocker,
        context=empty_data_context,
        validation_definition=validation_definition,
        validation_definition_json=validation_definition_json,
    )


@pytest.mark.cloud
def test_validation_definition_factory_add_success_cloud(
    empty_cloud_context_fluent: CloudDataContext,
    validation_definition: ValidationDefinition,
    validation_definition_json: str,
    mocker: MockerFixture,
):
    _test_validation_definition_factory_add_success(
        mocker=mocker,
        context=empty_cloud_context_fluent,
        validation_definition=validation_definition,
        validation_definition_json=validation_definition_json,
    )


def _test_validation_definition_factory_add_success(
    mocker: MockerFixture,
    context: AbstractDataContext,
    validation_definition: ValidationDefinition,
    validation_definition_json: str,
):
    # Arrange
    name = validation_definition.name
    with pytest.raises(
        DataContextError, match=f"ValidationDefinition with name {name} was not found."
    ):
        context.validation_definitions.get(name)

    # Act
    with mocker.patch.object(ValidationDefinition, "json", return_value=validation_definition_json):
        created_validation = context.validation_definitions.add(validation=validation_definition)

    # Assert
    validation_names = {
        key.to_tuple()[0] for key in context.validation_definition_store.list_keys()
    }
    assert created_validation.name in validation_names


@pytest.mark.filesystem
def test_validation_definition_factory_delete_success_filesystem(
    empty_data_context: FileDataContext,
    validation_definition: ValidationDefinition,
    validation_definition_json: str,
    mocker: MockerFixture,
):
    _test_validation_definition_factory_delete_success(
        mocker=mocker,
        context=empty_data_context,
        validation_definition=validation_definition,
        validation_definition_json=validation_definition_json,
    )


@pytest.mark.cloud
def test_validation_definition_factory_delete_success_cloud(
    empty_cloud_context_fluent: CloudDataContext,
    validation_definition: ValidationDefinition,
    validation_definition_json: str,
    mocker: MockerFixture,
):
    _test_validation_definition_factory_delete_success(
        mocker=mocker,
        context=empty_cloud_context_fluent,
        validation_definition=validation_definition,
        validation_definition_json=validation_definition_json,
    )


def _test_validation_definition_factory_delete_success(
    mocker: MockerFixture,
    context: AbstractDataContext,
    validation_definition: ValidationDefinition,
    validation_definition_json: str,
):
    # Arrange
    name = validation_definition.name

    with mocker.patch.object(ValidationDefinition, "json", return_value=validation_definition_json):
        validation_definition = context.validation_definitions.add(validation=validation_definition)

    # Act
    with mocker.patch.object(ValidationDefinition, "parse_raw", return_value=validation_definition):
        context.validation_definitions.delete(name=name)

    # Assert
    with pytest.raises(
        DataContextError,
        match=f"ValidationDefinition with name {name} was not found.",
    ):
        context.validation_definitions.get(name)


@pytest.mark.parametrize(
    "context_fixture_name",
    [
        pytest.param("empty_cloud_context_fluent", id="cloud", marks=pytest.mark.cloud),
        pytest.param("in_memory_runtime_context", id="ephemeral", marks=pytest.mark.big),
        pytest.param("empty_data_context", id="filesystem", marks=pytest.mark.filesystem),
    ],
)
def test_validation_definition_factory_all(
    context_fixture_name: str, request: pytest.FixtureRequest
):
    context: AbstractDataContext = request.getfixturevalue(context_fixture_name)

    # Arrange
    ds = context.data_sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")  # type: ignore[arg-type] # FIXME CoP
    suite = context.suites.add(ExpectationSuite(name="my_suite"))
    validation_definition_a = ValidationDefinition(
        name="validation definition a",
        data=asset.add_batch_definition("a"),
        suite=suite,
    )
    validation_definition_b = ValidationDefinition(
        name="validation definition b",
        data=asset.add_batch_definition("b"),
        suite=suite,
    )

    context.validation_definitions.add(validation=validation_definition_a)
    context.validation_definitions.add(validation=validation_definition_b)

    # Act
    result = context.validation_definitions.all()
    result = sorted(result, key=lambda x: x.name)

    # Assert
    assert [r.name for r in result] == [validation_definition_a.name, validation_definition_b.name]
    assert result == [validation_definition_a, validation_definition_b]


@pytest.mark.unit
def test_validation_definition_factory_all_with_bad_config(
    in_memory_runtime_context: AbstractDataContext,
    mocker: MockerFixture,
):
    mocker.patch(
        "great_expectations.core.validation_definition.ValidationDefinition.Config.validate_assignment",
        False,
    )
    analytics_submit_mock = mocker.patch(
        "great_expectations.data_context.store.store.submit_analytics_event"
    )
    context: AbstractDataContext = in_memory_runtime_context

    # Arrange
    ds = context.data_sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")  # type: ignore[arg-type] # FIXME CoP
    suite = context.suites.add(ExpectationSuite(name="my_suite"))

    validation_definition_1 = ValidationDefinition(
        name="validation1",
        data=asset.add_batch_definition("1"),
        suite=suite,
    )
    context.validation_definitions.add(validation=validation_definition_1)

    validation_definition_2 = ValidationDefinition(
        name="validation2",
        data=asset.add_batch_definition("2"),
        suite=suite,
    )
    context.validation_definitions.add(validation=validation_definition_2)

    # Verify our validation definitions are added
    assert sorted(context.validation_definitions.all(), key=lambda cp: cp.name) == [
        validation_definition_1,
        validation_definition_2,
    ]

    # Make validation_definition_2 invalid. Pydantic will validate the object at creation time
    # but we can invalidate via assignment because of the monkeypatch at the top of this test.
    validation_definition_2.suite = None  # type: ignore[assignment] # done intentionally for test
    validation_definition_2.save()

    # Act
    result = context.validation_definitions.all()

    # Assert
    assert result == [validation_definition_1]
    analytics_submit_mock.assert_called_once_with(
        DomainObjectAllDeserializationEvent(
            error_type=ANY_TEST_ARG,
            store_name="ValidationDefinitionStore",
        )
    )
    analytics_submit_args = analytics_submit_mock.call_args[0][0]
    assert re.match("pydantic.*ValidationError", analytics_submit_args.error_type)


@pytest.mark.filesystem
def test_validation_definition_factory_round_trip(
    empty_data_context: FileDataContext,
    validation_definition: ValidationDefinition,
):
    # Arrange
    context = empty_data_context

    ds = context.data_sources.add_pandas("my_ds")
    csv_path = pathlib.Path(
        __file__, "..", "..", "..", "test_sets", "quickstart", "yellow_tripdata_sample_2022-01.csv"
    ).resolve()
    assert csv_path.exists()
    asset = ds.add_csv_asset("my_asset", filepath_or_buffer=csv_path)

    batch_definition = asset.add_batch_definition("my_batch_def")
    suite = context.suites.add(
        ExpectationSuite(
            name="my_suite",
            expectations=[
                gxe.ExpectColumnValuesToBeBetween(
                    column="passenger_count", min_value=0, max_value=10
                ),
                gxe.ExpectColumnMeanToBeBetween(
                    column="passenger_count",
                    min_value=0,
                    max_value=1,
                ),
            ],
        )
    )

    # Act
    validation_definition = ValidationDefinition(
        name="my_validation_def", data=batch_definition, suite=suite
    )
    persisted_validation_definition = context.validation_definitions.add(
        validation=validation_definition
    )
    retrieved_validation_definition = context.validation_definitions.get(
        name=validation_definition.name
    )

    # Assert
    # Suite equality is a bit finnicky, so we just check the JSON representation
    assert persisted_validation_definition.json() == retrieved_validation_definition.json()


class TestValidationDefinitionFactoryAddOrUpdate:
    def _build_batch_definition(self, context: AbstractDataContext):
        ds = context.data_sources.add_pandas("my_datasource")
        asset = ds.add_csv_asset("my_taxi_asset", pathlib.Path("data.csv"))
        return asset.add_batch_definition("my_batch_definition")

    def _build_suite(self, name: str = "my_suite") -> ExpectationSuite:
        return ExpectationSuite(
            name=name,
            expectations=[
                gxe.ExpectColumnValuesToBeBetween(
                    column="passenger_count", min_value=0, max_value=10
                )
            ],
        )

    @pytest.mark.filesystem
    def test_add_new_validation__filesystem(self, empty_data_context: FileDataContext):
        self._test_add_new_validation(empty_data_context)

    @pytest.mark.cloud
    def test_add_new_validation__cloud(self, empty_cloud_context_fluent: CloudDataContext):
        self._test_add_new_validation(empty_cloud_context_fluent)

    @pytest.mark.unit
    def test_add_new_validation__ephemeral(
        self, ephemeral_context_with_defaults: EphemeralDataContext
    ):
        self._test_add_new_validation(ephemeral_context_with_defaults)

    def _test_add_new_validation(self, context: AbstractDataContext):
        # arrange
        vd_name = "my_validation_definition"
        batch_def = self._build_batch_definition(context)
        suite = self._build_suite()
        vd = ValidationDefinition(
            name=vd_name,
            data=batch_def,
            suite=context.suites.add(suite),
        )

        # act
        created_vd = context.validation_definitions.add_or_update(validation=vd)

        # assert
        assert created_vd.id
        context.validation_definitions.get(vd_name)

    @pytest.mark.filesystem
    def test_add_new_validation_with_new_suite__filesystem(
        self, empty_data_context: FileDataContext
    ):
        self._test_add_new_validation_with_new_suite(empty_data_context)

    @pytest.mark.cloud
    def test_add_new_validation_with_new_suite__cloud(
        self, empty_cloud_context_fluent: CloudDataContext
    ):
        self._test_add_new_validation_with_new_suite(empty_cloud_context_fluent)

    @pytest.mark.unit
    def test_add_new_validation_with_new_suite__ephemeral(
        self, ephemeral_context_with_defaults: EphemeralDataContext
    ):
        self._test_add_new_validation_with_new_suite(ephemeral_context_with_defaults)

    def _test_add_new_validation_with_new_suite(self, context: AbstractDataContext):
        # arrange
        vd_name = "my_validation_definition"
        batch_def = self._build_batch_definition(context)
        suite = self._build_suite()
        vd = ValidationDefinition(
            name=vd_name,
            data=batch_def,
            suite=suite,
        )

        # act
        created_vd = context.validation_definitions.add_or_update(validation=vd)

        # assert
        assert created_vd.id
        context.validation_definitions.get(vd_name)

    @pytest.mark.filesystem
    def test_update_existing_validation__filesystem(self, empty_data_context: FileDataContext):
        self._test_update_existing_validation(empty_data_context)

    @pytest.mark.cloud
    def test_update_existing_validation__cloud(self, empty_cloud_context_fluent: CloudDataContext):
        self._test_update_existing_validation(empty_cloud_context_fluent)

    @pytest.mark.unit
    def test_update_existing_validation__ephemeral(
        self, ephemeral_context_with_defaults: EphemeralDataContext
    ):
        self._test_update_existing_validation(ephemeral_context_with_defaults)

    def _test_update_existing_validation(self, context: AbstractDataContext):
        # arrange
        vd_name = "my_validation_definition"
        batch_def = self._build_batch_definition(context)
        suite = self._build_suite()
        vd = ValidationDefinition(
            name=vd_name,
            data=batch_def,
            suite=context.suites.add(suite),
        )
        existing_vd = context.validation_definitions.add(validation=vd)

        # act
        vd.suite.expectations = [
            gxe.ExpectColumnMaxToBeBetween(column="passenger_count", min_value=0, max_value=5)
        ]

        updated_vd = context.validation_definitions.add_or_update(validation=vd)

        # assert
        assert updated_vd.id == existing_vd.id
        assert len(updated_vd.suite.expectations) == 1 and isinstance(
            updated_vd.suite.expectations[0], gxe.ExpectColumnMaxToBeBetween
        )
        context.validation_definitions.get(vd_name)

    @pytest.mark.filesystem
    def test_overwrite_existing_validation__filesystem(self, empty_data_context: FileDataContext):
        self._test_overwrite_existing_validation(empty_data_context)

    @pytest.mark.cloud
    def test_overwrite_existing_validation__cloud(
        self, empty_cloud_context_fluent: CloudDataContext
    ):
        self._test_overwrite_existing_validation(empty_cloud_context_fluent)

    @pytest.mark.unit
    def test_overwrite_existing_validation__ephemeral(
        self, ephemeral_context_with_defaults: EphemeralDataContext
    ):
        self._test_overwrite_existing_validation(ephemeral_context_with_defaults)

    def _test_overwrite_existing_validation(self, context: AbstractDataContext):
        # arrange
        vd_name = "my_validation_definition"
        batch_def = self._build_batch_definition(context)
        suite = context.suites.add(self._build_suite())
        vd = ValidationDefinition(
            name=vd_name,
            data=batch_def,
            suite=suite,
        )
        existing_vd = context.validation_definitions.add(validation=vd)

        # act
        new_suite = context.suites.add(self._build_suite(name="new_suite"))
        new_vd = ValidationDefinition(
            name=vd_name,
            data=batch_def,
            suite=new_suite,
        )
        updated_vd = context.validation_definitions.add_or_update(validation=new_vd)

        # assert
        assert updated_vd.suite.id != existing_vd.suite.id  # New suite should have a different ID
        assert updated_vd.data.id == existing_vd.data.id
        assert updated_vd.id == existing_vd.id
        context.validation_definitions.get(vd_name)

    @pytest.mark.filesystem
    def test_add_or_update_is_idempotent__filesystem(self, empty_data_context: FileDataContext):
        self._test_add_or_update_is_idempotent(empty_data_context)

    @pytest.mark.cloud
    def test_add_or_update_is_idempotent__cloud(self, empty_cloud_context_fluent: CloudDataContext):
        self._test_add_or_update_is_idempotent(empty_cloud_context_fluent)

    @pytest.mark.unit
    def test_add_or_update_is_idempotent__ephemeral(
        self, ephemeral_context_with_defaults: EphemeralDataContext
    ):
        self._test_add_or_update_is_idempotent(ephemeral_context_with_defaults)

    def _test_add_or_update_is_idempotent(self, context: AbstractDataContext):
        # arrange
        vd_name = "my_validation_definition"
        batch_def = self._build_batch_definition(context)
        suite = self._build_suite()
        vd = ValidationDefinition(
            name=vd_name,
            data=batch_def,
            suite=suite,
        )

        # act
        vd_1 = context.validation_definitions.add_or_update(validation=vd)
        vd_2 = context.validation_definitions.add_or_update(validation=vd)
        vd_3 = context.validation_definitions.add_or_update(validation=vd)

        # assert
        assert vd_1 == vd_2 == vd_3


class TestValidationDefinitionFactoryAnalytics:
    @pytest.mark.filesystem
    def test_validation_definition_factory_add_emits_event_filesystem(self, empty_data_context):
        self._test_validation_definition_factory_add_emits_event(empty_data_context)

    @pytest.mark.cloud
    def test_validation_definition_factory_add_emits_event_cloud(self, empty_cloud_context_fluent):
        self._test_validation_definition_factory_add_emits_event(empty_cloud_context_fluent)

    def _test_validation_definition_factory_add_emits_event(self, context):
        # Arrange
        ds = context.data_sources.add_pandas("my_datasource")
        asset = ds.add_csv_asset("my_asset", "data.csv")
        batch_def = asset.add_batch_definition("my_batch_definition")
        suite = context.suites.add(ExpectationSuite(name="my_suite"))

        validation_definition = ValidationDefinition(
            name="validation_def", data=batch_def, suite=suite
        )

        # Act
        with mock.patch(
            "great_expectations.core.factory.validation_definition_factory.submit_event",
            autospec=True,
        ) as mock_submit:
            _ = context.validation_definitions.add(validation=validation_definition)

        # Assert
        mock_submit.assert_called_once_with(
            event=ValidationDefinitionCreatedEvent(
                validation_definition_id=validation_definition.id
            )
        )

    @pytest.mark.filesystem
    def test_validation_definition_factory_delete_emits_event_filesystem(self, empty_data_context):
        self._test_validation_definition_factory_delete_emits_event(empty_data_context)

    @pytest.mark.cloud
    def test_validation_definition_factory_delete_emits_event_cloud(
        self, empty_cloud_context_fluent
    ):
        self._test_validation_definition_factory_delete_emits_event(empty_cloud_context_fluent)

    def _test_validation_definition_factory_delete_emits_event(self, context):
        # Arrange
        ds = context.data_sources.add_pandas("my_datasource")
        asset = ds.add_csv_asset("my_asset", "data.csv")
        batch_def = asset.add_batch_definition("my_batch_definition")
        suite = context.suites.add(ExpectationSuite(name="my_suite"))

        name = "validation_def"
        validation_definition = context.validation_definitions.add(
            validation=ValidationDefinition(name=name, data=batch_def, suite=suite)
        )

        # Act
        with mock.patch(
            "great_expectations.core.factory.validation_definition_factory.submit_event",
            autospec=True,
        ) as mock_submit:
            context.validation_definitions.delete(name=name)

        # Assert
        mock_submit.assert_called_once_with(
            event=ValidationDefinitionDeletedEvent(
                validation_definition_id=validation_definition.id
            )
        )
