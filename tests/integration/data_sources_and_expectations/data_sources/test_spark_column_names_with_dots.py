"""
Reproduction for community issue #11199.

Spark CSV assets fail to recognize columns whose names contain a dot (e.g.
``Data.Entrega``). Any expectation targeting such a column raises
``The column "Data.Entrega" in BatchData does not exist`` because Spark SQL
treats ``.`` as nested field access unless the identifier is backtick-quoted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

import great_expectations.expectations as gxe
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    SparkFilesystemCsvDatasourceTestConfig,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch

COLUMN_WITH_DOT = "Data.Entrega"

DATA = pd.DataFrame(
    {
        COLUMN_WITH_DOT: ["2024-01-01", "2024-02-01", "2024-03-01"],
    }
)

ID_COLUMN = "ID"

DATA_WITH_A_NULL = pd.DataFrame(
    {
        ID_COLUMN: [1, 2],
        COLUMN_WITH_DOT: ["2024-01-01", None],
    }
)


@parameterize_batch_for_data_sources(
    data_source_configs=[SparkFilesystemCsvDatasourceTestConfig()],
    data=DATA,
)
def test_spark_column_with_dot_in_name_is_recognized(batch_for_datasource: Batch) -> None:
    """Spark should recognize columns whose names contain a dot.

    Reported in community issue #11199: validating any expectation on a
    column like ``Data.Entrega`` raises ``The column "Data.Entrega" in
    BatchData does not exist`` because Spark parses the dot as nested field
    access.
    """
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToNotBeNull(column=COLUMN_WITH_DOT)
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=[SparkFilesystemCsvDatasourceTestConfig()],
    data=DATA_WITH_A_NULL,
)
def test_spark_column_with_dot_in_name_returns_unexpected_index_list(
    batch_for_datasource: Batch,
) -> None:
    """A dotted domain column must not empty the result when index columns are requested.

    Reported in community issue #12196: with a flat dotted column plus
    ``unexpected_index_column_names``, the column-name normalizer hands the
    index path the backtick-quoted name, which never matches the bare names
    in ``DataFrame.columns``, raising an error that empties the result dict.
    """
    result = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToNotBeNull(column=COLUMN_WITH_DOT),
        result_format={
            "result_format": "COMPLETE",
            "unexpected_index_column_names": [ID_COLUMN],
        },
    )
    assert result.result, result.exception_info  # empty when a metric raised
    assert result.result["unexpected_count"] == 1
    assert result.result["unexpected_index_list"] == [{ID_COLUMN: 2, COLUMN_WITH_DOT: None}]
