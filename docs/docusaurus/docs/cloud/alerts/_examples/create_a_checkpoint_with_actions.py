"""
This is an example script for how to append an Action to a Checkpoint.

To test, run:
pytest --docs-tests -k "cloud_docs_example_create_a_checkpoint" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    # Create a Batch Definition
    batch_definition = (
        context.data_sources.add_pandas_filesystem(
            name="my_data_source", base_directory="./data/folder_with_data"
        )
        .add_csv_asset(name="my_data_asset")
        .add_batch_definition_path(
            name="my_batch_definition", path="yellow_tripdata_sample_2019-01.csv"
        )
    )

    # Create an Expectation Suite
    expectation_suite = context.suites.add(
        gx.ExpectationSuite(name="my_expectation_suite")
    )
    # Add some Expectations
    expectation_suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="pickup_datetime")
    )

    vd = gx.ValidationDefinition(
        data=batch_definition,
        suite=expectation_suite,
        name="my_validation_definition",
    )

    # Create a Validation Definition
    context.validation_definitions.add(vd)

    checkpoint = gx.Checkpoint(
        name="my_checkpoint",
        validation_definitions=[vd],
        actions=[],
        result_format={"result_format": "COMPLETE"},
    )

    context.checkpoints.add(checkpoint)


# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - full code example">
# Instantiate the Context.
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - instantiate the Context">
import great_expectations as gx
from great_expectations.checkpoint import SlackNotificationAction

context = gx.get_context()
# </snippet>
# Hide this
set_up_context_for_example(context)

# Retrieve the Checkpoint.
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - retrieve the Checkpoint">
checkpoint_name = "my_checkpoint"
checkpoint = context.checkpoints.get(checkpoint_name)
# </snippet>

# Create a SlackNotificationAction for the Checkpoint to perform.
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a SlackNotificationAction">
action = SlackNotificationAction(
    name="send_slack_notification_on_failed_expectations",
    slack_token="${bot_user_oauth_token}",
    slack_channel="#my_channel",
    notify_on="failure",
    show_failed_expectations=True,
)
# </snippet>

# Append the Action to the Checkpoint and save it.
# <snippet name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - save the Checkpoint">
checkpoint.actions.append(action)
checkpoint.save()
# </snippet>
