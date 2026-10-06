"""An object resolves through the Data Context that owns it (#12209).

With more than one Data Context in a process, an object keeps working against the context it
was created in after another context becomes current. An object that belongs to no context
resolves through the current one.
"""

from __future__ import annotations

import pathlib
from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.data_context.data_context.context_factory import (
    project_manager,
    set_context,
)
from great_expectations.exceptions import DataContextRequiredError
from great_expectations.validator.v1_validator import Validator as V1Validator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from great_expectations.data_context import AbstractDataContext

DATA_SOURCE_NAME = "shared_name"
ASSET_NAME = "shared_asset"
FILE_NAME = "data.csv"


@pytest.fixture
def restore_current_context() -> Iterator[None]:
    """Put the process-wide current Data Context back as the test found it."""
    try:
        previous: AbstractDataContext | None = project_manager.get_current_project()
    except DataContextRequiredError:
        previous = None
    yield
    set_context(previous)


def _add_csv_batch_definition(
    context: AbstractDataContext, directory: pathlib.Path, contents: str
) -> BatchDefinition:
    """Write a CSV into `directory` and add a data source, asset and batch definition over it."""
    directory.mkdir()
    (directory / FILE_NAME).write_text(contents)
    datasource = context.data_sources.add_pandas_filesystem(
        DATA_SOURCE_NAME, base_directory=directory
    )
    asset = datasource.add_csv_asset(ASSET_NAME)
    return asset.add_batch_definition_path("batch_definition", path=pathlib.Path(FILE_NAME))


@pytest.mark.filesystem
def test_batch_validates_against_its_own_context_while_another_is_current(
    tmp_path: pathlib.Path, restore_current_context: None
) -> None:
    c1 = gx.get_context(mode="ephemeral")
    c1_data = tmp_path / "c1"
    batch_definition = _add_csv_batch_definition(c1, c1_data, "a\n1\n2\n3\n")
    batch = batch_definition.get_batch()

    # C2 becomes current and holds a data source of the same name over different data.
    c2 = gx.get_context(mode="ephemeral")
    c2_data = tmp_path / "c2"
    _add_csv_batch_definition(c2, c2_data, "a\n10\n20\n30\n")
    assert project_manager.get_current_project() is c2
    assert c1.data_sources.get(DATA_SOURCE_NAME) is not c2.data_sources.get(DATA_SOURCE_NAME)

    suite = ExpectationSuite(
        name="max_is_three",
        expectations=[gxe.ExpectColumnMaxToBeBetween(column="a", min_value=3, max_value=3)],
    )
    result = batch.validate(suite)

    # The observed value tells the two contexts' data apart; the batch spec names C1's file.
    assert result.success is True
    assert result.results[0].result["observed_value"] == 3
    assert result.meta["batch_spec"]["path"] == str(c1_data / FILE_NAME)
    assert (
        result.meta["batch_markers"]["pandas_data_fingerprint"]
        == batch.batch_markers["pandas_data_fingerprint"]
    )


@pytest.mark.unit
def test_batch_definition_without_an_owner_validates_through_the_current_context(
    mocker: MockerFixture, restore_current_context: None
) -> None:
    other = gx.get_context(mode="ephemeral")
    current = gx.get_context(mode="ephemeral")
    assert project_manager.get_current_project() is current
    current_spy = mocker.patch.object(current, "get_validator")
    other_spy = mocker.patch.object(other, "get_validator")
    mocker.patch.object(BatchDefinition, "build_batch_request")

    validator = V1Validator(batch_definition=BatchDefinition(name="hand_assembled"))
    built = validator._wrapped_validator

    current_spy.assert_called_once()
    other_spy.assert_not_called()
    assert built is current_spy.return_value
