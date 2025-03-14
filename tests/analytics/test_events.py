import pytest

from great_expectations.analytics.base_event import Event
from great_expectations.analytics.events import (
    ActionInfo,
    CheckpointCreatedEvent,
    DataContextInitializedEvent,
    ExpectationSuiteCreatedEvent,
    ExpectationSuiteDeletedEvent,
    ExpectationSuiteExpectationCreatedEvent,
    ExpectationSuiteExpectationDeletedEvent,
    ExpectationSuiteExpectationUpdatedEvent,
)


@pytest.mark.parametrize(
    "event, expected_properties",
    [
        pytest.param(DataContextInitializedEvent(), {}, id="DataContextInitializedEvent"),
        pytest.param(
            ExpectationSuiteExpectationCreatedEvent(
                expectation_id="157abeb6-ffa8-4520-8239-649cf6ca9489",
                expectation_suite_id="fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
                expectation_type="expect_column_values_to_be_between",
                custom_exp_type=False,
            ),
            {
                "expectation_id": "157abeb6-ffa8-4520-8239-649cf6ca9489",
                "expectation_suite_id": "fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
                "expectation_type": "expect_column_values_to_be_between",
                "custom_exp_type": False,
            },
            id="ExpectationSuiteExpectationCreatedEvent",
        ),
        pytest.param(
            ExpectationSuiteExpectationUpdatedEvent(
                expectation_id="157abeb6-ffa8-4520-8239-649cf6ca9489",
                expectation_suite_id="fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            ),
            {
                "expectation_id": "157abeb6-ffa8-4520-8239-649cf6ca9489",
                "expectation_suite_id": "fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            },
            id="ExpectationSuiteExpectationUpdatedEvent",
        ),
        pytest.param(
            ExpectationSuiteExpectationDeletedEvent(
                expectation_id="157abeb6-ffa8-4520-8239-649cf6ca9489",
                expectation_suite_id="fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            ),
            {
                "expectation_id": "157abeb6-ffa8-4520-8239-649cf6ca9489",
                "expectation_suite_id": "fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            },
            id="ExpectationSuiteExpectationDeletedEvent",
        ),
        pytest.param(
            ExpectationSuiteCreatedEvent(
                expectation_suite_id="fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            ),
            {
                "expectation_suite_id": "fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            },
            id="ExpectationSuiteCreatedEvent",
        ),
        pytest.param(
            ExpectationSuiteDeletedEvent(
                expectation_suite_id="fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            ),
            {
                "expectation_suite_id": "fbb7ada0-600d-458d-a4f7-c6c30cb759b4",
            },
            id="ExpectationSuiteDeletedEvent",
        ),
        pytest.param(
            CheckpointCreatedEvent(
                checkpoint_id="a7a0ec12-9a01-4c02-938c-975826df87d3",
                validation_definition_ids=[
                    "b60bed67-268c-413d-8ad2-77b549314a51",
                    "b217cac6-1a6d-4b3f-bd63-3fd28c11add5",
                ],
                actions=[
                    ActionInfo(type="email", notify_on="failure"),
                    ActionInfo(type="microsoft", notify_on="all"),
                ],
            ),
            {
                "checkpoint_id": "a7a0ec12-9a01-4c02-938c-975826df87d3",
                "validation_definition_ids": [
                    "b60bed67-268c-413d-8ad2-77b549314a51",
                    "b217cac6-1a6d-4b3f-bd63-3fd28c11add5",
                ],
                "actions": [
                    {"type": "email", "notify_on": "failure"},
                    {"type": "microsoft", "notify_on": "all"},
                ],
            },
            id="CheckpointCreatedEvent",
        ),
    ],
)
@pytest.mark.unit
def test_event_properties(event: Event, expected_properties: dict):
    actual_properties = event.properties()

    # Assert that base properties are present
    for base_property in (
        "data_context_id",
        "oss_id",
        "service",
        "gx_version",
        "user_agent_str",
        "mode",
    ):
        assert base_property in actual_properties
        actual_properties.pop(base_property)

    # Assert remaining event-specific properties
    assert actual_properties == expected_properties
