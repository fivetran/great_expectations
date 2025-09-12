"""
This is an example script for how to connect GX Cloud to Amazon s3.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_s3" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - verify context type">
print(type(context).__name__)
# </snippet>

# Hide this
assert type(context).__name__ == "CloudDataContext"
# Hide this

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - define source">
data_source_name = "S3 Data Source"
bucket_name = "my-bucket"
boto3_options = {
    "aws_access_key_id": "${S3_KEY_ID}",
    "aws_secret_access_key": "${S3_SECRET_KEY}",
}
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - add source">
data_source = context.data_sources.add_pandas_s3(
    name=data_source_name, bucket=bucket_name, boto3_options=boto3_options
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - define asset">
asset_name = "s3_taxi_csv_file_asset"
s3_prefix = "data/taxi_yellow_tripdata/"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - add asset">
s3_file_data_asset = data_source.add_csv_asset(name=asset_name, s3_prefix=s3_prefix)
# </snippet>

# </snippet>
