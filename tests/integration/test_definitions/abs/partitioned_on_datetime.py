import os
import re

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

data_asset_name = "data/taxi_yellow_tripdata_samples"
asset = datasource.add_csv_asset(
    name=data_asset_name,
    abs_container=CONTAINER,
    abs_name_starts_with=NAME_STARTS_WITH,
)

batch_definition = asset.add_batch_definition_monthly(
    "abs batch definition",
    regex=re.compile(r"yellow_tripdata_sample_(?P<year>.*)-(?P<month>.*)\.csv"),
)

# first check: getting all identifiers
batch_request = batch_definition.build_batch_request()
batch_identifiers_list = asset.get_batch_identifiers_list(batch_request)
assert len(batch_identifiers_list) == 3
assert batch_identifiers_list[0] == {
    "year": "2019",
    "month": "01",
    "path": "data/taxi_yellow_tripdata_samples/yellow_tripdata_sample_2019-01.csv",
}

# second batch request: getting the batch
second_batch_request = batch_definition.build_batch_request(
    batch_parameters={"year": "2019", "month": "02"}
)
second_batch_list = asset.get_batch(second_batch_request)
assert second_batch_list.metadata == {
    "year": "2019",
    "month": "02",
    "path": "data/taxi_yellow_tripdata_samples/yellow_tripdata_sample_2019-02.csv",
}
