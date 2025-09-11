"""
This is an example script for how to add a Data Asset from an existing Data Source

To test, run:
pytest --docs-tests -k "cloud_docs_manage_data_assets" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/manage_data_assets.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>



# define source
data_source_name = "my_data_source"
bucket_name = "my-bucket"
boto3_options = {"aws_access_key_id": "${S3_KEY_ID}", "aws_secret_access_key": "${S3_SECRET_KEY}"}


# add source
data_source = context.data_sources.add_pandas_s3(
    name=data_source_name, bucket=bucket_name, boto3_options=boto3_options
)

# <snippet name="docs/docusaurus/docs/cloud/connect/manage_data_assets.py - fetch source">
data_source = context.data_sources.get("my_data_source")
# </snippet>


# <snippet name="docs/docusaurus/docs/cloud/connect/manage_data_assets.py - define asset">
asset_name = "s3_taxi_csv_file_asset"
s3_prefix = "data/taxi_yellow_tripdata/"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/manage_data_assets.py - add asset">
s3_file_data_asset = data_source.add_csv_asset(name=asset_name, s3_prefix=s3_prefix)
# </snippet>