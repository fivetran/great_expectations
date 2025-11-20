"""
This is an example script for how to validate GX-managed Expectations for a time-based subset of a filesystem Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_batch_filesystem" tests/integration/test_script_runner.py
"""

# Setup code for testing (not shown in documentation)
import shutil
import tempfile
from pathlib import Path

import pandas as pd

import great_expectations as gx

context = gx.get_context(mode="cloud")


# Helper to delete entities if they exist
def safe_delete(collection, name):
    try:
        collection.delete(name=name)
    except Exception:
        pass


# Define names
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
suite_name = "my_expectation_suite"
definition_name = "my_validation_definition"
checkpoint_name = f"{data_asset_name} - GX-Managed Checkpoint"
batch_definition_name = f"{data_asset_name} - GX-Managed Batch Definition"

# Delete any existing entities from previous runs (in dependency order)
safe_delete(context.checkpoints, checkpoint_name)
safe_delete(context.validation_definitions, definition_name)
safe_delete(context.suites, suite_name)
safe_delete(context.data_sources, data_source_name)

# Create temporary directory with date-based CSV files
temp_dir = tempfile.mkdtemp()
test_df = pd.DataFrame({"column_1": [1, 2, 3], "column_2": ["a", "b", "c"]})
csv_path_1 = Path(temp_dir) / "my_filename_2019-01-30.csv"
csv_path_2 = Path(temp_dir) / "my_filename_2019-02-15.csv"
test_df.to_csv(csv_path_1, index=False)
test_df.to_csv(csv_path_2, index=False)

# Create Pandas filesystem datasource and asset
data_source = context.data_sources.add_pandas_filesystem(
    name=data_source_name, base_directory=temp_dir
)
batching_regex = r"my_filename_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\.csv"
asset = data_source.add_csv_asset(name=data_asset_name)
batch_definition = asset.add_batch_definition_daily(
    name=batch_definition_name, regex=batching_regex
)

# Create expectation suite
context.suites.add(gx.ExpectationSuite(name=suite_name))

# Create validation definition
validation_definition = context.validation_definitions.add(
    gx.ValidationDefinition(
        name=definition_name,
        data=batch_definition,
        suite=context.suites.get(suite_name),
    )
)

# Create checkpoint with GX-Managed name pattern
context.checkpoints.add(
    gx.Checkpoint(
        name=checkpoint_name,
        validation_definitions=[validation_definition],
    )
)

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - define asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - partition data">
# Update this regex to match the pattern of your date-based filenames
# This example matches a name like my_filename_2019-01-30.csv
batching_regex = r"my_filename_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\.csv"

import great_expectations as gx
from great_expectations.core.partitioners import FileNamePartitionerDaily

context = gx.get_context(mode="cloud")
ds = context.data_sources.get(data_source_name)
asset = ds.get_asset(data_asset_name)

for bd in asset.batch_definitions:
    if "GX-Managed" in bd.name:
        bd.partitioner = FileNamePartitionerDaily(
            regex=batching_regex,
            sort_ascending=True,
            param_names=("year", "month", "day"),
        )

context.update_datasource(ds)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - retrieve checkpoint name">
import great_expectations as gx

context = gx.get_context()

data_asset_name = "my_data_asset"

my_checkpoint = None
checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
        break
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)
batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>

# Cleanup test entities (outside snippet for testing)
context.checkpoints.delete(name=checkpoint_name)
context.validation_definitions.delete(name=definition_name)
context.suites.delete(name=suite_name)
context.data_sources.delete(name=data_source_name)
shutil.rmtree(temp_dir, ignore_errors=True)
