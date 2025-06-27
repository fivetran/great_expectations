from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pandas as pd

from great_expectations import ValidationDefinition
from great_expectations.checkpoint import Checkpoint
from great_expectations.core import ExpectationSuite
from great_expectations.expectations import ExpectColumnValuesToNotBeNull
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config.snowflake import SnowflakeDatasourceTestConfig

if TYPE_CHECKING:
    from great_expectations.checkpoint.checkpoint import CheckpointResult


@parameterize_batch_for_data_sources(
    data_source_configs=[SnowflakeDatasourceTestConfig()],
    data=pd.DataFrame({"test_e2e_sf": [1, 2]}),
)
def test_checkpoint_run(batch_for_datasource):
    """Test running a Checkpoint end-to-end"""
    context = batch_for_datasource.datasource.data_context
    expectation_suite = context.suites.add(
        ExpectationSuite(
            name=f"es_{uuid.uuid4().hex}",
            expectations=[ExpectColumnValuesToNotBeNull(column="test_e2e_sf", mostly=1)],
        )
    )
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(
            name=f"val_def_{uuid.uuid4().hex}",
            data=batch_for_datasource.data_asset.batch_definitions[0],
            suite=expectation_suite,
        )
    )
    checkpoint = context.checkpoints.add(
        Checkpoint(
            name=f"E2E Test Checkpoint {uuid.uuid4().hex}",
            validation_definitions=[validation_definition],
        )
    )
    checkpoint_result: CheckpointResult = checkpoint.run()
    assert checkpoint_result.success
