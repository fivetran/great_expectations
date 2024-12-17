"""
This is an example script for how to create a custom Action.

To test, run:
pytest --docs-tests -k "docs_example_create_a_custom_action" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:

# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - full code example">

from typing import Literal

from typing_extensions import override

from great_expectations.checkpoint.actions import ActionContext, ValidationAction
from great_expectations.checkpoint.checkpoint import CheckpointResult


# 1. Extend the `ValidationAction` class.
# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - extend class">
class MyCustomAction(ValidationAction):
    # </snippet>

    # 2. Set the `type` attribute to a unique string that identifies the Action.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - set type">
    type: Literal["my_custom_action"] = "my_custom_action"
    # </snippet>

    # 3. Override the `run()` method to perform the desired task.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - override run">
    @override
    def run(
        self,
        checkpoint_result: CheckpointResult,
        action_context: ActionContext,  # Contains results from prior Actions in the same Checkpoint run.
    ) -> dict:
        success_percentage = self._do_my_custom_action(
            checkpoint_result
        )  # Domain-specific logic
        return {
            "success_percentage": success_percentage
        }  # Return information about the Action

    def _do_my_custom_action(self, checkpoint_result: CheckpointResult) -> float:
        # Perform custom logic based on the validation results.
        # In this example, we calculate the percentage of successful expectations across all validation results.
        successful_expectations = 0
        evaluated_expectations = 0
        for validation_result in checkpoint_result.run_results.values():
            successful_expectations += validation_result.statistics[
                "successful_expectations"
            ]
            evaluated_expectations += validation_result.statistics[
                "evaluated_expectations"
            ]

        return successful_expectations / evaluated_expectations

    # </snippet>


# </snippet>

# Everything below this line is not part of the example script and is used for testing.

# isort: off
from unittest import mock
from datetime import datetime, timezone

from great_expectations.checkpoint import Checkpoint
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)
from great_expectations.core.run_identifier import RunIdentifier
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)
# isort: on

action = MyCustomAction(name="test_action")

checkpoint_result = CheckpointResult(
    run_id=RunIdentifier(
        run_time=datetime.fromisoformat("2024-04-01T20:51:18.077262").replace(
            tzinfo=timezone.utc
        )
    ),
    run_results={
        ValidationResultIdentifier(
            expectation_suite_identifier=ExpectationSuiteIdentifier(
                name="suite_a",
            ),
            run_id=RunIdentifier(run_name="prod_20240401"),
            batch_identifier="my_datasource-my_first_asset",
        ): ExpectationSuiteValidationResult(
            success=True,
            statistics={"successful_expectations": 3, "evaluated_expectations": 3},
            results=[],
            suite_name="suite_a",
        ),
        ValidationResultIdentifier(
            expectation_suite_identifier=ExpectationSuiteIdentifier(
                name="suite_b",
            ),
            run_id=RunIdentifier(run_name="prod_20240402"),
            batch_identifier="my_datasource-my_second_asset",
        ): ExpectationSuiteValidationResult(
            success=False,
            statistics={"successful_expectations": 1, "evaluated_expectations": 2},
            results=[],
            suite_name="suite_b",
        ),
    },
    checkpoint_config=Checkpoint(
        name="test-checkpoint",
        validation_definitions=[
            mock.MagicMock(spec=ValidationDefinition),
            mock.MagicMock(spec=ValidationDefinition),
        ],
    ),
)
action_context = ActionContext()

result = action.run(checkpoint_result=checkpoint_result, action_context=action_context)

assert result == {"success_percentage": 0.8}
