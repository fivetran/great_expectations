"""
This is an example script for how to validate GX-managed Expectations for a time-based subset of a filesystem Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_batch_filesystem" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - define asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - partition data">
# Update this regex to match the pattern of your date-based filenames
# This example matches a name like my_filename_2019-01-30.csv
batch_definition_regex = (
    r"my_filename_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\.csv"
)

import great_expectations as gx
from great_expectations.core.partitioners import FileNamePartitionerDaily

context = gx.get_context()
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

checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)
batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>
