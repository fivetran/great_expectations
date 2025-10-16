"""
This is an example script for how to add a Data Asset from an existing Data Source

To test, run:
pytest --docs-tests -k "cloud_docs_manage_data_assets" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - full sample">
# Create a Data Context object.
# <snippet name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>
# Hide this
data_source_name = "my_data_source"
# Hide this
bucket_name = "my-bucket"
# Hide this
boto3_options = {
    # Hide this
    "aws_access_key_id": "${S3_KEY_ID}",
    # Hide this
    "aws_secret_access_key": "${S3_SECRET_KEY}",
    # Hide this
}
# Hide this
data_source = context.data_sources.add_pandas_s3(
    # Hide this
    name=data_source_name,
    # Hide this
    bucket=bucket_name,
    # Hide this
    boto3_options=boto3_options,
    # Hide this
)

# Fetch the Data Source.
# <snippet name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - get data source">
data_source = context.data_sources.get("my_data_source")
# </snippet>

# Define your Data Asset's parameters.
# <snippet name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - define asset">
asset_name = "s3_taxi_csv_file_asset"
s3_prefix = "data/taxi_yellow_tripdata/"
# </snippet>

# Add the Data Asset to your Data Source.
# <snippet name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - add asset">
s3_file_data_asset = data_source.add_csv_asset(name=asset_name, s3_prefix=s3_prefix)
# </snippet>
# </snippet>
