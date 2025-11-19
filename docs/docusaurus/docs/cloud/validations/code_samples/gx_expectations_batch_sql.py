"""
This is an example script for how to validate GX-managed Expectations for a time-based subset of a SQL Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_batch_sql" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - define asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
column_name = "my_date_or_datetime_column"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - partition data">
import great_expectations as gx
from great_expectations.core.partitioners import ColumnPartitionerDaily

context = gx.get_context(mode="cloud")
ds = context.data_sources.get(data_source_name)
asset = ds.get_asset(data_asset_name)

for bd in asset.batch_definitions:
    if "GX-Managed" in bd.name:
        bd.partitioner = ColumnPartitionerDaily(
            method_name="partition_on_year_and_month_and_day",
            column_name=column_name,
            sort_ascending=True,
        )

context.update_datasource(ds)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - retrieve checkpoint name">
import great_expectations as gx

context = gx.get_context()

data_asset_name = "my_data_asset"

checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)
batch_parameters_daily = {"year": 2019, "month": 1, "day": 30}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>
