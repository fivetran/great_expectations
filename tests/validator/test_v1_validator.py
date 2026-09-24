from __future__ import annotations

import threading
import time
from copy import copy
from pprint import pformat as pf
from typing import TYPE_CHECKING
from unittest import mock

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.partitioners import PartitionerColumnValue
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import DataAsset, Datasource
from great_expectations.validator.v1_validator import Validator
from great_expectations.validator.validator import Validator as OldValidator

if TYPE_CHECKING:
    from great_expectations.data_context.data_context.abstract_data_context import (
        AbstractDataContext,
    )
    from great_expectations.datasource.fluent.pandas_datasource import PandasDatasource
    from great_expectations.expectations.expectation import Expectation


_BUILD_SECONDS = 0.5
_WAIT_BUDGET_SECONDS = 1.0


@pytest.fixture
def failing_expectation() -> Expectation:
    return gxe.ExpectColumnValuesToBeInSet(
        column="event_type",
        value_set=["start", "stop"],
    )


@pytest.fixture
def passing_expectation() -> Expectation:
    return gxe.ExpectColumnValuesToBeBetween(
        column="id",
        min_value=-1,
        max_value=1000000,
    )


@pytest.fixture
def expectation_suite(
    failing_expectation: Expectation, passing_expectation: Expectation
) -> ExpectationSuite:
    suite = ExpectationSuite("test_suite")
    suite.add_expectation_configuration(failing_expectation.configuration)
    suite.add_expectation_configuration(passing_expectation.configuration)
    return suite


@pytest.fixture
def fds_data_asset(
    fds_data_context: AbstractDataContext,
    fds_data_context_datasource_name: str,
) -> DataAsset:
    datasource = fds_data_context.data_sources.get(fds_data_context_datasource_name)
    assert isinstance(datasource, Datasource)
    return datasource.get_asset("trip_asset")


@pytest.fixture
def fds_data_asset_with_event_type_partitioner(
    fds_data_context: AbstractDataContext,
    fds_data_context_datasource_name: str,
) -> DataAsset:
    datasource = fds_data_context.data_sources.get(fds_data_context_datasource_name)
    assert isinstance(datasource, Datasource)
    return datasource.get_asset("trip_asset_partition_by_event_type")


@pytest.fixture
def batch_definition(
    fds_data_asset: DataAsset,
) -> BatchDefinition:
    batch_definition = BatchDefinition[None](name="test_batch_definition")
    batch_definition.set_data_asset(fds_data_asset)
    return batch_definition


@pytest.fixture
def batch_definition_with_event_type_partitioner(
    fds_data_asset_with_event_type_partitioner: DataAsset,
) -> BatchDefinition:
    partitioner = PartitionerColumnValue(column_name="event_type")
    batch_definition = BatchDefinition(name="test_batch_definition", partitioner=partitioner)
    batch_definition.set_data_asset(fds_data_asset_with_event_type_partitioner)
    return batch_definition


@pytest.fixture
def validator(
    fds_data_context: AbstractDataContext, batch_definition: BatchDefinition
) -> Validator:
    return Validator(
        batch_definition=batch_definition,
        batch_parameters=None,
        result_format=ResultFormat.SUMMARY,
    )


@pytest.mark.unit
def test_result_format_boolean_only(validator: Validator, failing_expectation: Expectation):
    validator.result_format = ResultFormat.BOOLEAN_ONLY
    result = validator.validate_expectation(failing_expectation)

    assert not result.success
    assert result.result == {}


@pytest.mark.unit
def test_result_format_basic(validator: Validator, failing_expectation: Expectation):
    validator.result_format = ResultFormat.BASIC
    result = validator.validate_expectation(failing_expectation)

    assert not result.success

    assert "partial_unexpected_list" in result.result
    assert "partial_unexpected_counts" not in result.result
    assert "unexpected_list" not in result.result


@pytest.mark.unit
def test_result_format_summary(validator: Validator, failing_expectation: Expectation):
    validator.result_format = ResultFormat.SUMMARY
    result = validator.validate_expectation(failing_expectation)

    assert not result.success

    assert "partial_unexpected_list" in result.result
    assert "partial_unexpected_counts" in result.result
    assert "unexpected_list" not in result.result


@pytest.mark.unit
def test_result_format_complete(validator: Validator, failing_expectation: Expectation):
    validator.result_format = ResultFormat.COMPLETE
    result = validator.validate_expectation(failing_expectation)

    assert not result.success

    assert "partial_unexpected_list" in result.result
    assert "partial_unexpected_counts" in result.result
    assert "unexpected_list" in result.result


@pytest.mark.unit
def test_v1_validator_doesnt_mutate_result_format(
    validator: Validator, expectation_suite: ExpectationSuite
):
    """This test verifies a bugfix where the legacy Validator mutates a ResultFormat
    dict provided by the user.
    """
    result_format_dict = {
        "result_format": "COMPLETE",
    }
    backup_result_format_dict = copy(result_format_dict)
    validator.result_format = result_format_dict
    validator.validate_expectation_suite(expectation_suite=expectation_suite)
    assert result_format_dict == backup_result_format_dict


@pytest.mark.unit
def test_validate_expectation_success(validator: Validator, passing_expectation: Expectation):
    result = validator.validate_expectation(passing_expectation)

    assert result.success


@pytest.mark.unit
def test_validate_expectation_failure(validator: Validator, failing_expectation: Expectation):
    result = validator.validate_expectation(failing_expectation)

    assert not result.success


@pytest.mark.unit
def test_validate_expectation_with_batch_asset_options(
    fds_data_context: AbstractDataContext,
    batch_definition_with_event_type_partitioner: BatchDefinition,
):
    desired_event_type = "start"
    validator = Validator(
        batch_definition=batch_definition_with_event_type_partitioner,
        batch_parameters={"event_type": desired_event_type},
    )

    result = validator.validate_expectation(
        gxe.ExpectColumnValuesToBeInSet(
            column="event_type",
            value_set=[desired_event_type],
        )
    )
    print(f"Result dict ->\n{pf(result)}")
    assert result.success


@pytest.mark.unit
def test_validate_expectation_suite(validator: Validator, expectation_suite: ExpectationSuite):
    result = validator.validate_expectation_suite(expectation_suite)

    assert not result.success
    assert not result.results[0].success
    assert result.results[1].success
    assert result.statistics == {
        "evaluated_expectations": 2,
        "successful_expectations": 1,
        "unsuccessful_expectations": 1,
        "success_percent": 50.0,
    }


@pytest.mark.parametrize(
    ["parameter", "expected"],
    [
        (["start", "stop", "continue"], True),
        (["start", "stop"], False),
    ],
)
@pytest.mark.unit
def test_validate_expectation_suite_suite_parameters(
    validator: Validator,
    parameter: list[str],
    expected: bool,
):
    suite = ExpectationSuite("test_suite")
    expectation = gxe.ExpectColumnValuesToBeInSet(
        column="event_type",
        value_set={"$PARAMETER": "my_parameter"},
    )
    suite.add_expectation_configuration(expectation.configuration)
    result = validator.validate_expectation_suite(suite, {"my_parameter": parameter})

    assert result.success == expected


@pytest.mark.unit
def test_non_cloud_validate_does_not_render_results(
    validator: Validator,
    empty_data_context: AbstractDataContext,
):
    suite = empty_data_context.suites.add(
        ExpectationSuite(
            name="test_suite",
            expectations=[
                gxe.ExpectColumnValuesToBeInSet(
                    column="event_type",
                    value_set=["start"],
                )
            ],
        )
    )
    result = validator.validate_expectation_suite(suite)

    assert len(result.results) == 1
    assert not result.results[0].rendered_content


@mock.patch(
    "great_expectations.data_context.data_context.context_factory.project_manager.is_using_cloud",
)
@pytest.mark.unit
def test_cloud_validate_renders_results_when_appropriate(
    mock_is_using_cloud,
    validator: Validator,
    empty_data_context: AbstractDataContext,
):
    mock_is_using_cloud.return_value = True
    suite = empty_data_context.suites.add(
        ExpectationSuite(
            name="test_suite",
            expectations=[
                gxe.ExpectColumnValuesToBeInSet(
                    column="event_type",
                    value_set=["start"],
                )
            ],
        )
    )
    result = validator.validate_expectation_suite(suite)

    assert len(result.results) == 1
    assert result.results[0].rendered_content


@pytest.fixture
def pandas_datasource(empty_data_context: AbstractDataContext) -> PandasDatasource:
    return empty_data_context.data_sources.add_pandas("pandas_datasource")


def _validator_for(pandas_datasource: PandasDatasource, name: str, rows: int) -> Validator:
    batch_definition = pandas_datasource.add_dataframe_asset(
        name
    ).add_batch_definition_whole_dataframe("whole")
    return Validator(
        batch_definition=batch_definition,
        batch_parameters={"dataframe": pd.DataFrame({"x": range(rows)})},
    )


@pytest.mark.unit
def test_validate_expectation_suite_reports_its_own_batch_when_a_sibling_validator_is_built(
    pandas_datasource: PandasDatasource,
):
    """Both Validators share the datasource's cached execution engine. Building the second
    one after the first has been built (but before it validates) must not make the first
    compute against, or label its result with, the second one's Batch."""
    small = _validator_for(pandas_datasource, "small", rows=3)
    big = _validator_for(pandas_datasource, "big", rows=10)
    assert small._wrapped_validator.execution_engine is big._wrapped_validator.execution_engine

    suite = ExpectationSuite("row_count")
    suite.add_expectation(gxe.ExpectTableRowCountToEqual(value=3))
    result = small.validate_expectation_suite(suite)

    assert result.success is True
    assert result.results[0].result["observed_value"] == 3
    assert result.batch_id == "pandas_datasource-small"
    assert small.active_batch_id == "pandas_datasource-small"
    assert result.meta["active_batch_definition"]["data_asset_name"] == "small"


@pytest.mark.unit
def test_wrapped_validator_construction_is_not_serialized_across_instances(
    pandas_datasource: PandasDatasource,
):
    """`functools.cached_property` must not come back here. On Python < 3.12 its descriptor
    holds one `RLock` shared by every instance of the class and computes inside it, so a second
    Validator's first access blocks until a first Validator's first access finishes computing --
    even though the two Validators share nothing. On 3.12+ CPython removed that lock
    (python/cpython#87634) and the two computations run independently.
    """
    small = _validator_for(pandas_datasource, "small", rows=3)
    big = _validator_for(pandas_datasource, "big", rows=10)

    original_init = OldValidator.__init__

    def slow_init(self, *args, **kwargs):
        time.sleep(_BUILD_SECONDS)
        original_init(self, *args, **kwargs)

    with mock.patch.object(OldValidator, "__init__", slow_init):
        start = time.perf_counter()
        threads = [threading.Thread(target=lambda v=v: v._wrapped_validator) for v in (small, big)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start

    assert elapsed < _BUILD_SECONDS * 1.5, (
        f"the two Validators' first-access computations took {elapsed:.2f}s combined; "
        f"each takes {_BUILD_SECONDS}s alone, so >= {_BUILD_SECONDS * 1.5}s means the second "
        "waited for the first instead of running concurrently"
    )


@pytest.mark.unit
def test_wrapped_validator_construction_does_not_deadlock_across_instances(
    pandas_datasource: PandasDatasource,
):
    """A wait inside one Validator's construction must not stop another from building.

    This is the shape that hung a CI job: two threads each building their own Validator,
    both held at a barrier until the other arrives. Sharing the class-wide lock, the thread
    that got there first waits while still holding it, so the second can never start, the
    barrier breaks, and both builds fail.
    """
    small = _validator_for(pandas_datasource, "small", rows=3)
    big = _validator_for(pandas_datasource, "big", rows=10)
    both_arrived = threading.Barrier(2)
    built: dict[str, object] = {}
    errors: dict[str, BaseException] = {}

    original_init = OldValidator.__init__

    def rendezvous_init(self, *args, **kwargs):
        # Only ever entered by whichever thread gets to build first; the point of the test is
        # that the other thread is not locked out of building while this one waits.
        both_arrived.wait(timeout=_WAIT_BUDGET_SECONDS)
        original_init(self, *args, **kwargs)

    def build(name, validator):
        try:
            built[name] = validator._wrapped_validator
        except BaseException as e:  # re-raised on the main thread below
            errors[name] = e

    with mock.patch.object(OldValidator, "__init__", rendezvous_init):
        threads = [
            threading.Thread(target=build, args=(name, v), name=name)
            for name, v in (("small", small), ("big", big))
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=_WAIT_BUDGET_SECONDS + 1)

    stuck = [t.name for t in threads if t.is_alive()]
    assert not stuck, f"threads still building after the wait budget: {stuck}"
    assert not errors, errors
    assert set(built) == {"small", "big"}


@pytest.mark.unit
def test_wrapped_validator_is_built_once_per_instance(pandas_datasource: PandasDatasource):
    """Laziness must not cost the caching: repeated access returns the same object and asks the
    project's validator factory for it exactly once."""
    validator = _validator_for(pandas_datasource, "once", rows=3)
    factory = validator._get_validator
    calls: list[int] = []

    def counting_factory(*args, **kwargs):
        calls.append(1)
        return factory(*args, **kwargs)

    validator._get_validator = counting_factory
    first = validator._wrapped_validator
    again = validator._wrapped_validator

    assert first is again
    assert len(calls) == 1, f"the factory was called {len(calls)} times"
    assert validator._wrapped_validator is first
    assert len(calls) == 1
    assert validator.active_batch_id == "pandas_datasource-once"
    assert len(calls) == 1
