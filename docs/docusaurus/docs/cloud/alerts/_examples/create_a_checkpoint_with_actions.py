"""
This is an example script for how to create a Checkpoint with Actions.

To test, run:
pytest --docs-tests -k "docs_example_create_a_checkpoint" tests/integration/test_script_runner.py
"""

import great_expectations as gx
from great_expectations.checkpoint import (
    SlackNotificationAction,
)

context = gx.get_context(mode="cloud")

# Create a list of one or more Validation Definitions for the Checkpoint to run
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a Validation Definitions list">
validation_definitions = []
validation_definitions.append(
    context.validation_definitions.get("my_validation_definition")
)
# Find Validation Definitions based on the Data Asset
for vd in context.validation_definitions.all():
    if vd.asset.name == "my_asset_name":
        validation_definitions.append(vd)

# </snippet>

# Create a list of Actions for the Checkpoint to perform
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - define an Action list">
action_list = [
    # This Action sends a Slack Notification if an Expectation fails.
    SlackNotificationAction(
        name="send_slack_notification_on_failed_expectations",
        slack_token="${validation_notification_slack_webhook}",
        slack_channel="${validation_notification_slack_channel}",
        notify_on="failure",
        show_failed_expectations=True,
    )
]
# </snippet>

# Create the Checkpoint
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a Checkpoint">
checkpoint_name = "my_checkpoint"
checkpoint = gx.Checkpoint(
    name=checkpoint_name,
    validation_definitions=validation_definitions,
    actions=action_list,
    result_format={"result_format": "COMPLETE"},
)
# </snippet>

# Save the Checkpoint to the Data Context
# <snippet name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_checkpoint_with_actions.py - save the Checkpoint">
context.checkpoints.add(checkpoint)
# </snippet>
