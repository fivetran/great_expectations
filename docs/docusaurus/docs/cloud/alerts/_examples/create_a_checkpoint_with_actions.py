"""
This is an example script for how to append an Action to a Checkpoint.

To test, run:
pytest --docs-tests -k "docs_example_create_a_checkpoint" tests/integration/test_script_runner.py
"""

# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - full code example">
import great_expectations as gx
from great_expectations.checkpoint import SlackNotificationAction

context = gx.get_context(mode="cloud")

# Retrieve the Checkpoint
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - retrieve the Checkpoint">
checkpoint_name = "my_checkpoint"
checkpoint = context.checkpoints.get(checkpoint_name)
# </snippet>

# Create a SlackNotificationAction for the Checkpoint to perform
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a SlackNotificationAction">
# This Action sends a Slack Notification if an Expectation fails.
action = SlackNotificationAction(
    name="send_slack_notification_on_failed_expectations",
    slack_token="${validation_notification_slack_webhook}",
    slack_channel="${validation_notification_slack_channel}",
    notify_on="failure",
    show_failed_expectations=True,
)
# </snippet>

# Append the action to the Checkpoint and save it.
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - save the Checkpoint">
checkpoint.actions.append(action)
checkpoint.save()
# </snippet>
