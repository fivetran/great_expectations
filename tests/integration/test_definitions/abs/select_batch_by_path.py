import os

import great_expectations as gx

context = gx.get_context()

datasource_name = "ABS datasource"

# All three come from the environment, and all three raise rather than default:
# the account holding this data is not the one these tests were written against,
# and a silently empty credential or a stale hardcoded host fails later, in the
# datasource, as an authentication error that says nothing about configuration.
CREDENTIAL = os.environ["AZURE_CREDENTIAL"]
ACCOUNT_URL = os.environ["AZURE_STORAGE_ACCOUNT_URL"]
CONTAINER = os.environ["AZURE_CONTAINER"]
NAME_STARTS_WITH = "data/taxi_yellow_tripdata_samples/"


datasource = context.data_sources.add_pandas_abs(
    name=datasource_name,
    azure_options={
        "account_url": ACCOUNT_URL,
        "credential": CREDENTIAL,
    },
)

asset = datasource.add_csv_asset(
    name="taxi_yellow_tripdata_samples",
    abs_container=CONTAINER,
    abs_name_starts_with=NAME_STARTS_WITH,
)

batch_definition = asset.add_batch_definition_path(
    "abs batch definition",
    path="yellow_tripdata_sample_2019-02.csv",
)

batch_request = batch_definition.build_batch_request()
batch = asset.get_batch(batch_request)

assert batch.metadata == {
    "path": "data/taxi_yellow_tripdata_samples/yellow_tripdata_sample_2019-02.csv"
}
