import datetime as dt

import pytest

from great_expectations.checkpoint import MicrosoftTeamsNotificationAction, ValidationAction
from great_expectations.checkpoint.checkpoint import Checkpoint, CheckpointResult
from great_expectations.core.expectation_validation_result import ExpectationSuiteValidationResult
from great_expectations.core.run_identifier import RunIdentifier
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)


@pytest.fixture
def checkpoint_result(mocker) -> CheckpointResult:
    return CheckpointResult(
        run_id=RunIdentifier(run_name="e2e_test", run_time=dt.datetime.now(tz=dt.timezone.utc)),
        run_results={
            ValidationResultIdentifier(
                expectation_suite_identifier=ExpectationSuiteIdentifier(
                    name="test-suite",
                ),
                run_id=RunIdentifier(run_name="test-run"),
                batch_identifier="test-datasource-test-asset",
            ): ExpectationSuiteValidationResult(
                success=True,
                statistics={"successful_expectations": 3, "evaluated_expectations": 3},
                results=[],
                suite_name="test-suite",
            ),
            ValidationResultIdentifier(
                expectation_suite_identifier=ExpectationSuiteIdentifier(
                    name="test-suite",
                ),
                run_id=RunIdentifier(run_name="test-run"),
                batch_identifier="test-datasource-test-asset",
            ): ExpectationSuiteValidationResult(
                success=False,
                statistics={"successful_expectations": 2, "evaluated_expectations": 4},
                results=[],
                suite_name="test-suite",
            ),
        },
        checkpoint_config=Checkpoint(
            name="test-checkpoint",
            validation_definitions=[
                mocker.MagicMock(spec=ValidationDefinition),
                mocker.MagicMock(spec=ValidationDefinition),
            ],
        ),
        success=False,
    )


@pytest.mark.e2e
@pytest.mark.parametrize(
    "action_cls, action_creds, expected_action_result",
    [
        pytest.param(
            MicrosoftTeamsNotificationAction,
            {"teams_webhook": "${GX_MS_TEAMS_WEBHOOK}"},
            {"microsoft_teams_notification_result": "Microsoft Teams notification succeeded."},
            id="ms_teams",
        ),
    ],
)
def test_actions_e2e(
    action_cls: type[ValidationAction],
    action_creds: dict,
    expected_action_result: dict,
    checkpoint_result: CheckpointResult,
):
    action = action_cls(name="e2e_action", **action_creds)
    result = action.run(checkpoint_result=checkpoint_result)
    assert result == expected_action_result
