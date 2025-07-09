from __future__ import annotations

import logging

import pytest

from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent import AlloyDatasource
from great_expectations.execution_engine import SqlAlchemyExecutionEngine


# We set a default time range that we use for testing.

LOGGER = logging.getLogger(__name__)


@pytest.mark.unit
def test_add_alloy_datasource(
    empty_data_context: AbstractDataContext,
):
    source = empty_data_context.data_sources.add_alloy(name="alloy_datasource")
    assert source.type == "alloy"
    assert source.name == "alloy_datasource"
    assert source.execution_engine_type is SqlAlchemyExecutionEngine
    assert source.assets == []
