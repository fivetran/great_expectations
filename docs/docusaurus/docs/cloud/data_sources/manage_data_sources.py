"""
This is an example script for how to edit a Data Source

To test, run:
pytest --docs-tests -k "cloud_docs_manage_data_sources" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - verify context type">
print(type(context).__name__)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - pick source">
# The name identitifes which Data Source to update.
# You cannot change the Data Source name with the API.
data_source_name = "S3 Data Source"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - define source updates">
# You can change some or all connection details.
bucket_name = "my-new-bucket"
boto3_options = {
    "aws_access_key_id": "${MY_NEW_S3_KEY_ID}",
    "aws_secret_access_key": "${MY_NEW_S3_SECRET_KEY}",
}
# </snippet>


# add a source to update
data_source = context.data_sources.add_pandas_s3(
    name=data_source_name, bucket=bucket_name, boto3_options=boto3_options
)

# <snippet name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - update source">
context.data_sources.update_pandas_s3(
    name=data_source_name, bucket=bucket_name, boto3_options=boto3_options
)
# </snippet>

