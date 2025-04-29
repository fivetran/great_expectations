import pandas as pd

from tests.integration.conftest import multi_source_batch_setup
from tests.integration.test_utils.data_source_config import PostgreSQLDatasourceTestConfig

DATA_FRAME = pd.DataFrame({"a": [1, 2, 3]})


@multi_source_batch_setup(
    primary_data_sources=[PostgreSQLDatasourceTestConfig()],
    primary_data=DATA_FRAME,
    secondary_data_sources=[PostgreSQLDatasourceTestConfig()],
    secondary_data=DATA_FRAME,
)
def test_source_to_target_example_one(batch_for_datasource): ...
