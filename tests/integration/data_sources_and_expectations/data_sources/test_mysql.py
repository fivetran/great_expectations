import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import MySQLDatasourceTestConfig

pytestmark = pytest.mark.mysql


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_a(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_b(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_c(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_d(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_e(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_f(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_g(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[MySQLDatasourceTestConfig()],
    data=pd.DataFrame({"a": [1, 2, 3]}),
)
def test_h(batch_for_datasource: Batch) -> None:
    batch_for_datasource.validate(
        gxe.ExpectColumnValuesToBeBetween(column="a", min_value=0, max_value=5)
    )
