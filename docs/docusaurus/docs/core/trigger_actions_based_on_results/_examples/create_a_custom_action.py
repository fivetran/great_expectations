"""
This is an example script for how to create a custom Action.

To test, run:
pytest --docs-tests -k "docs_example_create_a_custom_action" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:

# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - full code example">

from typing import Literal
from great_expectations.checkpoint.actions import ActionContext, ValidationAction
from great_expectations.checkpoint.checkpoint import CheckpointResult

# 1. Extend the ValidationAction class.
# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - extend class">
class MyCustomAction(ValidationAction):
# </snippet>

    # 2. Set the 'type' attribute to a unique string that identifies the action.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - set type">
    type: Literal["my_custom_action"] = "my_custom_action"
    # </snippet>

    # 3. Override the run method to perform the action.
    # <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - override run">
    @override
    def run(
        self, 
        checkpoint_result: CheckpointResult, 
        action_context: ActionContext, # Contains results from prior actions in the same checkpoint run.
    ) -> dict:
        self._do_my_custom_action(...) # Domain-specific logic
        return {"some": "info"} # Return information about the action

    def _do_my_custom_action(self):
        ...
    # </snippet>
        
# </snippet>
