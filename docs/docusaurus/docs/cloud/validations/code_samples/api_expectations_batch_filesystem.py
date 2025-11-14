"""
This is an example script for how to validate API-managed Expectations for a time-based subset of a filesystem Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_api_expectations_batch_filesystem" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - retrieve data asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"

import great_expectations as gx

context = gx.get_context()
ds = context.data_sources.get(data_source_name)
data_asset = ds.get_asset(data_asset_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - partition data">

# Update this regex to match the pattern of your date-based filenames
# This example matches a name like my_filename_2019-01-30.csv
batch_definition_regex = (
    r"my_filename_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\.csv"
)

batch_definition_name = "my_daily_batch_definition"

batch_definition = data_asset.add_batch_definition_daily(
    name=batch_definition_name, regex=batch_definition_regex
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - retrieve suite">
suite_name = "my_expectation_suite"
suite = context.suites.get(name=suite_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - create validation definition">
definition_name = "my_validation_definition"
validation_definition = gx.ValidationDefinition(
    data=batch_definition, suite=suite, name=definition_name
)

validation_definition = context.validation_definitions.add(validation_definition)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - run validation definition">
batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

validation_definition.run(batch_parameters=batch_parameters_daily)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - checkpoint">
# Retrieve the Validation Definition
validation_definition = context.validation_definitions.get("my_validation_definition")

# Create a Checkpoint
checkpoint_name = "my_checkpoint"
checkpoint_config = gx.Checkpoint(
    name=checkpoint_name, validation_definitions=[validation_definition]
)

# Save the Checkpoint to the data context
checkpoint = context.checkpoints.add(checkpoint_config)

# When you run the Checkpoint, pass Batch Parameters as strings
batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>
