"""
This is an example script for how to create a custom Action.

To test, run:
pytest --docs-tests -k "docs_example_create_a_custom_action" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:

# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - full code example">

from typing import Literal, Union

from typing_extensions import override

from great_expectations.checkpoint import (
    ActionContext,
    CheckpointResult,
    ValidationAction,
)


# 1. Extend the `ValidationAction` class.
# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - extend class">
class MyCustomAction(ValidationAction):
    # </snippet>

    # 2. Set the `type` attribute to a unique string that identifies the Action.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - set type">
    type: Literal["my_custom_action"] = "my_custom_action"
    # </snippet>

    # 3. Optional. Add any additional fields your Action requires at runtime.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - add custom fields">
    my_custom_str_field: str
    # </snippet>

    # 4. Override the `run()` method to perform the desired task.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - override run">
    @override
    def run(
        self,
        checkpoint_result: CheckpointResult,
        action_context: Union[
            ActionContext, None
        ],  # Contains results from prior Actions in the same Checkpoint run.
    ) -> dict:
        # Domain-specific logic
        self._do_my_custom_action(checkpoint_result)
        # Optional. Access custom fields you provide the Action at runtime.
        extra_context = self.my_custom_str_field
        # Return information about the Action
        return {"some": "info", "extra_context": extra_context}

    def _do_my_custom_action(self, checkpoint_result: CheckpointResult):
        # Perform custom logic based on the validation results.
        ...

    # </snippet>


# </snippet>
