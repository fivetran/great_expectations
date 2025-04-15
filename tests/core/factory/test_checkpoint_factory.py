import re
from unittest import mock
from unittest.mock import ANY
from unittest.mock import ANY as ANY_TEST_ARG

import pytest
from pytest_mock import MockerFixture

from great_expectations.analytics.events import (
    CheckpointCreatedEvent,
    CheckpointDeletedEvent,
    DomainObjectAllDeserializationEvent,
)
from great_expectations.checkpoint.checkpoint import Checkpoint
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.factory.checkpoint_factory import CheckpointFactory
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.data_context.store.checkpoint_store import (
    CheckpointStore,
)
from great_expectations.exceptions import DataContextError


@pytest.mark.unit
def test_checkpoint_factory_get_uses_store_get(
    mocker: MockerFixture,
    arbitrary_validation_definition: ValidationDefinition,
):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    checkpoint = Checkpoint(name=name, validation_definitions=[arbitrary_validation_definition])
    store.get.return_value = checkpoint
    factory = CheckpointFactory(store=store)

    # Act
    result = factory.get(name=name)

    # Assert
    store.get.assert_called_once_with(key=key)

    assert result == checkpoint


@pytest.mark.unit
def test_checkpoint_factory_get_raises_error_on_missing_key(
    mocker: MockerFixture,
    arbitrary_validation_definition: ValidationDefinition,
):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = False
    checkpoint = Checkpoint(name=name, validation_definitions=[arbitrary_validation_definition])
    store.get.return_value = checkpoint
    factory = CheckpointFactory(store=store)

    # Act
    with pytest.raises(DataContextError, match=f"Checkpoint with name {name} was not found."):
        factory.get(name=name)

    # Assert
    store.get.assert_not_called()


@pytest.mark.unit
def test_checkpoint_factory_add_uses_store_add(
    mocker: MockerFixture, arbitrary_validation_definition: ValidationDefinition
):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = False
    key = store.get_key.return_value
    store.get.return_value = None
    factory = CheckpointFactory(store=store)
    checkpoint = Checkpoint(name=name, validation_definitions=[arbitrary_validation_definition])
    store.get.return_value = checkpoint

    # Act
    factory.add(checkpoint=checkpoint)

    # Assert
    store.add.assert_called_once_with(key=key, value=checkpoint.dict())


@pytest.mark.unit
def test_checkpoint_factory_add_raises_for_duplicate_key(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = True
    factory = CheckpointFactory(store=store)
    checkpoint = Checkpoint(
        name=name, validation_definitions=[mocker.Mock(spec=ValidationDefinition)]
    )

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot add Checkpoint with name {name} because it already exists.",
    ):
        factory.add(checkpoint=checkpoint)

    # Assert
    store.add.assert_not_called()


@pytest.mark.unit
def test_checkpoint_factory_delete_uses_store_remove_key(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.Mock(spec=CheckpointStore)
    store.has_key.return_value = True
    key = store.get_key.return_value
    checkpoint = mocker.Mock(spec=Checkpoint, id=None)
    checkpoint.name = name
    store.get.return_value = checkpoint
    factory = CheckpointFactory(store=store)

    # Act
    factory.delete(name=name)

    # Assert
    store.remove_key.assert_called_once_with(
        key=key,
    )


@pytest.mark.unit
def test_checkpoint_factory_delete_raises_for_missing_checkpoint(mocker: MockerFixture):
    # Arrange
    name = "test-checkpoint"
    store = mocker.MagicMock(spec=CheckpointStore)
    store.has_key.return_value = False
    factory = CheckpointFactory(store=store)

    # Act
    with pytest.raises(
        DataContextError,
        match=f"Cannot delete Checkpoint with name {name} because it cannot be found.",
    ):
        factory.delete(name=name)

    # Assert
    store.remove_key.assert_not_called()


@pytest.mark.filesystem
def test_checkpoint_factory_is_initialized_with_context_filesystem(empty_data_context):
    assert isinstance(empty_data_context.checkpoints, CheckpointFactory)


@pytest.mark.cloud
def test_checkpoint_factory_is_initialized_with_context_cloud(empty_cloud_data_context):
    assert isinstance(empty_cloud_data_context.checkpoints, CheckpointFactory)


@pytest.mark.filesystem
def test_checkpoint_factory_add_success_filesystem(empty_data_context):
    _test_checkpoint_factory_add_success(empty_data_context)


@pytest.mark.cloud
def test_checkpoint_factory_add_success_cloud(empty_cloud_context_fluent):
    _test_checkpoint_factory_add_success(empty_cloud_context_fluent)


def _test_checkpoint_factory_add_success(context):
    # Arrange
    name = "test-checkpoint"
    ds = context.data_sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")
    batch_def = asset.add_batch_definition("my_batch_definition")

    suite = context.suites.add(ExpectationSuite(name="my_suite"))
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(name="validation_def", data=batch_def, suite=suite)
    )

    checkpoint = Checkpoint(
        name=name,
        validation_definitions=[validation_definition],
    )
    with pytest.raises(DataContextError, match=f"Checkpoint with name {name} was not found."):
        context.checkpoints.get(name)

    # Act
    created_checkpoint = context.checkpoints.add(checkpoint=checkpoint)

    # Assert
    assert created_checkpoint == context.checkpoints.get(name=name)


@pytest.mark.filesystem
def test_checkpoint_factory_delete_success_filesystem(empty_data_context):
    _test_checkpoint_factory_delete_success(empty_data_context)


@pytest.mark.cloud
def test_checkpoint_factory_delete_success_cloud(empty_cloud_context_fluent):
    _test_checkpoint_factory_delete_success(empty_cloud_context_fluent)


def _test_checkpoint_factory_delete_success(context):
    # Arrange
    name = "test-checkpoint"
    ds = context.data_sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")
    batch_def = asset.add_batch_definition("my_batch_definition")

    suite = context.suites.add(ExpectationSuite(name="my_suite"))
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(name="validation_def", data=batch_def, suite=suite)
    )

    context.checkpoints.add(
        checkpoint=Checkpoint(
            name=name,
            validation_definitions=[validation_definition],
        )
    )

    # Act
    context.checkpoints.delete(name)

    # Assert
    with pytest.raises(
        DataContextError,
        match=f"Checkpoint with name {name} was not found.",
    ):
        context.checkpoints.get(name)


@pytest.mark.parametrize(
    "context_fixture_name",
    [
        pytest.param("empty_cloud_context_fluent", id="cloud", marks=pytest.mark.unit),
        pytest.param("in_memory_runtime_context", id="ephemeral", marks=pytest.mark.unit),
        pytest.param("empty_data_context", id="filesystem", marks=pytest.mark.filesystem),
    ],
)
def test_checkpoint_factory_all(context_fixture_name: str, request: pytest.FixtureRequest):
    context: AbstractDataContext = request.getfixturevalue(context_fixture_name)

    # Arrange
    ds = context.data_sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")  # type: ignore[arg-type] # FIXME CoP
    batch_def = asset.add_batch_definition("my_batch_definition")

    suite = context.suites.add(ExpectationSuite(name="my_suite"))
    validation_definition_a = context.validation_definitions.add(
        ValidationDefinition(name="val def a", data=batch_def, suite=suite)
    )

    checkpoint_a = context.checkpoints.add(
        Checkpoint(
            name="a",
            validation_definitions=[validation_definition_a],
        )
    )

    validation_definition_b = context.validation_definitions.add(
        ValidationDefinition(name="val def b", data=batch_def, suite=suite)
    )
    checkpoint_b = context.checkpoints.add(
        Checkpoint(
            name="b",
            validation_definitions=[validation_definition_b],
        )
    )

    # Act
    result = context.checkpoints.all()
    result = sorted(result, key=lambda x: x.name)

    # Assert
    assert [r.name for r in result] == [checkpoint_a.name, checkpoint_b.name]
    assert result == [checkpoint_a, checkpoint_b]


@pytest.mark.unit
def test_checkpoint_factory_all_with_bad_config(
    in_memory_runtime_context: AbstractDataContext, mocker: MockerFixture
):
    analytics_submit_mock = mocker.patch(
        "great_expectations.data_context.store.store.submit_analytics_event"
    )

    # Arrange
    context: AbstractDataContext = in_memory_runtime_context
    ds = context.data_sources.add_pandas("my_datasource")
    asset = ds.add_csv_asset("my_asset", "data.csv")  # type: ignore[arg-type] # FIXME CoP
    batch_def = asset.add_batch_definition("my_batch_definition")
    suite = context.suites.add(ExpectationSuite(name="my_suite"))

    checkpoint_1 = context.checkpoints.add(
        Checkpoint(
            name="1",
            validation_definitions=[
                context.validation_definitions.add(
                    ValidationDefinition(name="vd1", data=batch_def, suite=suite)
                )
            ],
        )
    )
    checkpoint_2 = context.checkpoints.add(
        Checkpoint(
            name="2",
            validation_definitions=[
                context.validation_definitions.add(
                    ValidationDefinition(name="vd2", data=batch_def, suite=suite)
                )
            ],
        )
    )
    # Verify our checkpoints are added
    assert sorted(context.checkpoints.all(), key=lambda cp: cp.name) == [checkpoint_1, checkpoint_2]

    # Make checkpoint_2 invalid. Pydantic will validate the object at creation time
    # but we can invalidate via assignment.
    checkpoint_2.id = {}  # type: ignore[assignment] # done intentionally for test
    checkpoint_2.save()

    # Act
    result = context.checkpoints.all()

    # Assert
    assert result == [checkpoint_1]
    analytics_submit_mock.assert_called_once_with(
        DomainObjectAllDeserializationEvent(
            error_type=ANY_TEST_ARG,
            store_name="CheckpointStore",
        )
    )
    analytics_submit_args = analytics_submit_mock.call_args[0][0]
    assert re.match("pydantic.*ValidationError", analytics_submit_args.error_type)


class TestCheckpointFactoryAnalytics:
    @pytest.mark.filesystem
    def test_checkpoint_factory_add_emits_event_filesystem(self, empty_data_context):
        self._test_checkpoint_factory_add_emits_event(empty_data_context)

    @pytest.mark.cloud
    def test_checkpoint_factory_add_emits_event_cloud(self, empty_cloud_context_fluent):
        self._test_checkpoint_factory_add_emits_event(empty_cloud_context_fluent)

    def _test_checkpoint_factory_add_emits_event(self, context):
        # Arrange
        name = "test-checkpoint"
        ds = context.data_sources.add_pandas("my_datasource")
        asset = ds.add_csv_asset("my_asset", "data.csv")
        batch_def = asset.add_batch_definition("my_batch_definition")

        suite = context.suites.add(ExpectationSuite(name="my_suite"))
        validation_definition = context.validation_definitions.add(
            ValidationDefinition(name="validation_def", data=batch_def, suite=suite)
        )

        checkpoint = Checkpoint(
            name=name,
            validation_definitions=[validation_definition],
        )

        # Act
        with mock.patch(
            "great_expectations.core.factory.checkpoint_factory.submit_event", autospec=True
        ) as mock_submit:
            _ = context.checkpoints.add(checkpoint=checkpoint)

        # Assert
        mock_submit.assert_called_once_with(
            event=CheckpointCreatedEvent(
                checkpoint_id=mock.ANY,
                validation_definition_ids=[mock.ANY for _ in checkpoint.validation_definitions],
            )
        )

    @pytest.mark.filesystem
    def test_checkpoint_factory_delete_emits_event_filesystem(self, empty_data_context):
        self._test_checkpoint_factory_delete_emits_event(empty_data_context)

    @pytest.mark.cloud
    def test_checkpoint_factory_delete_emits_event_cloud(self, empty_cloud_context_fluent):
        self._test_checkpoint_factory_delete_emits_event(empty_cloud_context_fluent)

    def _test_checkpoint_factory_delete_emits_event(self, context):
        # Arrange
        name = "test-checkpoint"
        ds = context.data_sources.add_pandas("my_datasource")
        asset = ds.add_csv_asset("my_asset", "data.csv")
        batch_def = asset.add_batch_definition("my_batch_definition")

        suite = context.suites.add(ExpectationSuite(name="my_suite"))
        validation_definition = context.validation_definitions.add(
            ValidationDefinition(name="validation_def", data=batch_def, suite=suite)
        )

        checkpoint = Checkpoint(
            name=name,
            validation_definitions=[validation_definition],
        )
        checkpoint = context.checkpoints.add(checkpoint=checkpoint)

        # Act
        with mock.patch(
            "great_expectations.core.factory.checkpoint_factory.submit_event", autospec=True
        ) as mock_submit:
            context.checkpoints.delete(name=name)

        # Assert
        mock_submit.assert_called_once_with(
            event=CheckpointDeletedEvent(checkpoint_id=checkpoint.id)
        )


class TestCheckpointFactoryAddOrUpdate:
    CHECKPOINT_NAME = "checkpoint A"

    def test_add_empty_new_checkpoint(self, data_context: AbstractDataContext) -> None:
        # arrange
        checkpoint = Checkpoint(name=self.CHECKPOINT_NAME, validation_definitions=[])

        # act
        created_checkpoint = data_context.checkpoints.add_or_update(checkpoint=checkpoint)

        # assert
        assert created_checkpoint.id
        data_context.checkpoints.get(self.CHECKPOINT_NAME)

    def test_add_new_checkpoint_with_validations(self, data_context: AbstractDataContext) -> None:
        # arrange
        batch_def = (
            data_context.data_sources.add_pandas("data source A")
            .add_dataframe_asset("asset A")
            .add_batch_definition_whole_dataframe("batch def A")
        )

        validation_definitions = [
            ValidationDefinition(
                name="val def A",
                data=batch_def,
                suite=ExpectationSuite(name="suite A"),
            ),
            ValidationDefinition(
                name="val def B",
                data=batch_def,
                suite=ExpectationSuite(name="suite B"),
            ),
        ]
        checkpoint = Checkpoint(
            name=self.CHECKPOINT_NAME, validation_definitions=validation_definitions
        )

        # act
        created_checkpoint = data_context.checkpoints.add_or_update(checkpoint=checkpoint)

        # assert
        assert created_checkpoint.id
        assert len(created_checkpoint.validation_definitions) == len(validation_definitions)
        for val_def, created_val_def in zip(
            validation_definitions, created_checkpoint.validation_definitions
        ):
            assert created_val_def.id
            val_def_dict = val_def.dict()
            val_def_dict["id"] = ANY
            assert val_def_dict == created_val_def.dict()

    def test_update_existing_checkpoint_adds_validations(
        self, data_context: AbstractDataContext
    ) -> None:
        # arrange
        data_context.checkpoints.add(
            checkpoint=Checkpoint(name=self.CHECKPOINT_NAME, validation_definitions=[])
        )

        batch_def = (
            data_context.data_sources.add_pandas("data source A")
            .add_dataframe_asset("asset A")
            .add_batch_definition_whole_dataframe("batch def A")
        )
        validation_definitions = [
            ValidationDefinition(
                name="val def A",
                data=batch_def,
                suite=ExpectationSuite(name="suite A"),
            ),
            ValidationDefinition(
                name="val def B",
                data=batch_def,
                suite=ExpectationSuite(name="suite B"),
            ),
        ]
        checkpoint = Checkpoint(
            name=self.CHECKPOINT_NAME, validation_definitions=validation_definitions
        )

        # act
        created_checkpoint = data_context.checkpoints.add_or_update(checkpoint=checkpoint)

        # assert
        assert created_checkpoint.id
        assert len(checkpoint.validation_definitions) == len(validation_definitions)
        for val_def, created_val_def in zip(
            validation_definitions, created_checkpoint.validation_definitions
        ):
            assert created_val_def.id
            val_def_dict = val_def.dict()
            val_def_dict["id"] = ANY
            assert val_def_dict == created_val_def.dict()

    def test_update_existing_checkpoint_updates_validations(
        self, data_context: AbstractDataContext
    ) -> None:
        # arrange
        batch_def = (
            data_context.data_sources.add_pandas("data source A")
            .add_dataframe_asset("asset A")
            .add_batch_definition_whole_dataframe("batch def A")
        )
        existing_suite = data_context.suites.add(ExpectationSuite(name="suite A"))
        existing_val_def = data_context.validation_definitions.add(
            ValidationDefinition(
                name="val def A",
                data=batch_def,
                suite=existing_suite,
            )
        )

        data_context.checkpoints.add(
            checkpoint=Checkpoint(
                name=self.CHECKPOINT_NAME, validation_definitions=[existing_val_def]
            )
        )
        new_suite_name = "suite C"

        # act
        created_checkpoint = data_context.checkpoints.add_or_update(
            checkpoint=Checkpoint(
                name=self.CHECKPOINT_NAME,
                validation_definitions=[
                    ValidationDefinition(
                        name="val def A",
                        data=batch_def,
                        suite=ExpectationSuite(name=new_suite_name),
                    ),
                ],
            )
        )
        # assert
        for val_def in created_checkpoint.validation_definitions:
            assert val_def.suite.name == new_suite_name

    def test_update_existing_checkpoint_deletes_validations(
        self, data_context: AbstractDataContext
    ) -> None:
        # arrange
        batch_def = (
            data_context.data_sources.add_pandas("data source A")
            .add_dataframe_asset("asset A")
            .add_batch_definition_whole_dataframe("batch def A")
        )
        SUITE_NAME = "suite A"
        VALIDATION_DEFINITION_NAME = "val def A"
        existing_suite_1 = data_context.suites.add(ExpectationSuite(name=SUITE_NAME))
        existing_suite_2 = data_context.suites.add(ExpectationSuite(name="suite B"))
        existing_val_def_1 = data_context.validation_definitions.add(
            ValidationDefinition(
                name=VALIDATION_DEFINITION_NAME,
                data=batch_def,
                suite=existing_suite_1,
            ),
        )
        existing_val_def_2 = data_context.validation_definitions.add(
            ValidationDefinition(
                name="val def B",
                data=batch_def,
                suite=existing_suite_2,
            )
        )

        data_context.checkpoints.add(
            checkpoint=Checkpoint(
                name=self.CHECKPOINT_NAME,
                validation_definitions=[existing_val_def_1, existing_val_def_2],
            )
        )

        # act
        created_checkpoint = data_context.checkpoints.add_or_update(
            checkpoint=Checkpoint(
                name=self.CHECKPOINT_NAME,
                validation_definitions=[
                    ValidationDefinition(
                        name="val def A",
                        data=batch_def,
                        suite=ExpectationSuite(name=SUITE_NAME),
                    ),
                ],
            )
        )

        # assert
        assert len(created_checkpoint.validation_definitions) == 1
        assert created_checkpoint.validation_definitions[0].name == VALIDATION_DEFINITION_NAME
        assert created_checkpoint.validation_definitions[0].suite.name == SUITE_NAME

    def test_add_or_update_is_idempotent(self, data_context: AbstractDataContext) -> None:
        # arrange
        batch_def = (
            data_context.data_sources.add_pandas("data source A")
            .add_dataframe_asset("asset A")
            .add_batch_definition_whole_dataframe("batch def A")
        )
        SUITE_NAME = "suite A"
        VALIDATION_DEFINITION_NAME = "val def A"

        # act
        created_checkpoint_1 = data_context.checkpoints.add_or_update(
            checkpoint=Checkpoint(
                name=self.CHECKPOINT_NAME,
                validation_definitions=[
                    ValidationDefinition(
                        name=VALIDATION_DEFINITION_NAME,
                        data=batch_def,
                        suite=ExpectationSuite(name=SUITE_NAME),
                    ),
                ],
            )
        )
        created_checkpoint_2 = data_context.checkpoints.add_or_update(
            checkpoint=Checkpoint(
                name=self.CHECKPOINT_NAME,
                validation_definitions=[
                    ValidationDefinition(
                        name=VALIDATION_DEFINITION_NAME,
                        data=batch_def,
                        suite=ExpectationSuite(name=SUITE_NAME),
                    ),
                ],
            )
        )

        # assert
        assert created_checkpoint_1 == created_checkpoint_2
