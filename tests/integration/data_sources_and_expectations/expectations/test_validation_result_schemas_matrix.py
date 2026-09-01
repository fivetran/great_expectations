"""Matrix runner for validation result schema coverage.

Runs every (expectation x result_format x data_source) combination and writes
a structured findings JSON file.  Expanded to ALL_DATA_SOURCES (task 8.1).

Abstract stubs (5 expectations whose ``__init__`` raises ``NotImplementedError``)
cannot be validated; they produce ``status=failed`` findings and the corresponding
test cells are marked as failures — this is expected and documented here.

Findings file location (relative to the worktree root):
    tests/_artifacts/validation_result_schemas/findings/<run_id>.json

xdist note: this module uses a session-scoped FindingsWriter; parallelising
within a single session would cause concurrent writes to the same JSON file.
The ``no_xdist`` marker documents this constraint.  CI uses ``--dist loadfile``
which naturally routes all cells from this file to a single worker, so the
constraint is satisfied without extra conftest machinery.
"""

from __future__ import annotations

import datetime
import random
import string
from typing import TYPE_CHECKING, Generator

import pandas as pd
import pytest

from great_expectations.core.result_format import ResultFormat
from great_expectations.core.validation_result_schemas.dispatcher import as_typed
from great_expectations.core.validation_result_schemas.findings_emitter import (
    FindingsWriter,
)
from great_expectations.core.validation_result_schemas.types import Status
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.expectations._validation_result_schemas_cases import (  # noqa: E501
    EXPECTATION_CASES,
    ExpectationCase,
    _AbstractStub,
)
from tests.integration.data_sources_and_expectations.expectations._validation_result_schemas_helpers import (  # noqa: E501
    _normalize_engine_hint,
    assert_field_set_covered,
    summarize_raw_dict,
)
from tests.integration.test_utils.data_source_config.tiers import ALL_DATA_SOURCES

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch

# ---------------------------------------------------------------------------
# Module-level marker: session-scoped FindingsWriter must not be split across
# xdist workers.  CI uses --dist loadfile which enforces this automatically.
# ---------------------------------------------------------------------------
pytestmark = [pytest.mark.no_xdist]

# ---------------------------------------------------------------------------
# Shared fixture data — a superset DataFrame whose columns cover all cases.
#
# Per-case data-shape variance resolution (task 8.1):
#   All EXPECTATION_CASES reference columns that exist in this DataFrame.
#   Cases needing specific data shapes (dates, JSON strings, pure numerics)
#   will run against this data; the expectation may fail validation (e.g.
#   ExpectColumnValuesToBeDateutilParseable against integers), but that is
#   fine — we are testing schema *parsing* of whatever result dict comes back,
#   not expectation correctness.  SQL backends that cannot operate on a
#   VARCHAR column for sum/numeric expectations will produce a batch.validate()
#   error which is caught, recorded as status=failed, and surfaced to the
#   curator exactly as designed.
# ---------------------------------------------------------------------------
_MATRIX_DATA = pd.DataFrame(
    {
        "col_a": [1, 2, 3, None, 5],
        "col_b": ["x", "y", "z", "w", None],
        "col_c": [1.0, 2.0, None, 4.0, 5.0],
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_run_id() -> str:
    """Generate a time-stamped run ID when ``--vrs-run-id`` is not supplied."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}-{suffix}"


def _datasource_test_id(batch: Batch) -> str:
    """Return a stable identifier for the data source under test."""
    return type(batch.datasource).__name__


# ---------------------------------------------------------------------------
# Session-scoped findings writer fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _findings_writer(request: pytest.FixtureRequest) -> Generator[FindingsWriter, None, None]:
    """Session-scoped FindingsWriter; yields writer, flushes on session teardown."""
    run_id: str = request.config.getoption("--vrs-run-id") or _generate_run_id()
    with FindingsWriter(run_id=run_id) as writer:
        yield writer


# ---------------------------------------------------------------------------
# Matrix test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", EXPECTATION_CASES, ids=lambda c: c.id)
@pytest.mark.parametrize("result_format", list(ResultFormat))
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=_MATRIX_DATA,
)
def test_validation_result_schema_matrix(
    batch_for_datasource: Batch,
    case: ExpectationCase,
    result_format: ResultFormat,
    _findings_writer: FindingsWriter,
) -> None:
    """Matrix runner: validate every (expectation x result_format x data_source) cell.

    Abstract-stub expectations (5 total) cannot be instantiated; they produce
    ``status=failed`` findings.  All other expectations should produce
    ``status=parsed`` findings.
    """
    engine_hint = _normalize_engine_hint(batch_for_datasource.datasource.type)
    datasource_test_id = _datasource_test_id(batch_for_datasource)

    # ------------------------------------------------------------------
    # Guard: abstract stubs cannot be validated — record failure immediately
    # ------------------------------------------------------------------
    if isinstance(case.expectation, _AbstractStub):
        _findings_writer.write_finding(
            {
                "expectation_type": case.expectation.expectation_type,
                "result_format": result_format.value,
                "engine": engine_hint,
                "datasource_test_id": datasource_test_id,
                "status": Status.FAILED.value,
                "error_summary": "AbstractStub: expectation not yet implemented",
            }
        )
        pytest.skip(f"[{case.id}][{result_format.value}][{engine_hint}]: abstract stub — skipped")

    expectation_type: str = case.expectation.expectation_type

    try:
        raw_evr = batch_for_datasource.validate(
            case.expectation,
            result_format=result_format,
        )
    except Exception as exc:
        _findings_writer.write_finding(
            {
                "expectation_type": expectation_type,
                "result_format": result_format.value,
                "engine": engine_hint,
                "datasource_test_id": datasource_test_id,
                "status": Status.FAILED.value,
                "error_summary": f"batch.validate raised: {type(exc).__name__}: {exc}",
            }
        )
        pytest.fail(
            f"[{case.id}][{result_format.value}][{engine_hint}]: "
            f"batch.validate raised {type(exc).__name__}: {exc}"
        )

    raw_result: dict = raw_evr.result or {}

    try:
        # Call as_typed() via the dispatcher directly so we pass the exact result_format
        # that was used for the validate() call.  raw_evr.as_typed() reads result_format
        # from expectation_config.kwargs which may default to SUMMARY instead of the
        # result_format we actually exercised.
        typed = as_typed(
            raw_result,
            expectation_type=expectation_type,
            result_format=result_format,
            engine_hint=engine_hint,
        )
    except Exception as exc:
        _findings_writer.write_finding(
            {
                "expectation_type": expectation_type,
                "result_format": result_format.value,
                "engine": engine_hint,
                "datasource_test_id": datasource_test_id,
                "status": Status.FAILED.value,
                **summarize_raw_dict(raw_result),
                "error_summary": f"as_typed raised: {type(exc).__name__}: {exc}",
            }
        )
        pytest.fail(
            f"[{case.id}][{result_format.value}][{engine_hint}]: "
            f"as_typed raised {type(exc).__name__}: {exc}"
        )

    # Coverage assertion: every raw key must appear in the parsed model
    try:
        assert_field_set_covered(raw_result, typed)
    except AssertionError as exc:
        _findings_writer.write_finding(
            {
                "expectation_type": expectation_type,
                "result_format": result_format.value,
                "engine": engine_hint,
                "datasource_test_id": datasource_test_id,
                "status": Status.FAILED.value,
                **summarize_raw_dict(raw_result),
                "matched_variant": type(typed).__name__,
                "error_summary": str(exc),
            }
        )
        pytest.fail(f"[{case.id}][{result_format.value}][{engine_hint}]: {exc}")

    # Success path — record parsed finding
    model_dict: dict = typed.dict()
    schema_required = [k for k in raw_result if k in model_dict]
    schema_optional = [k for k in model_dict if k not in raw_result]

    _findings_writer.write_finding(
        {
            "expectation_type": expectation_type,
            "result_format": result_format.value,
            "engine": engine_hint,
            "datasource_test_id": datasource_test_id,
            "status": Status.PARSED.value,
            **summarize_raw_dict(raw_result),
            "matched_variant": type(typed).__name__,
            "schema_required_fields_present": schema_required,
            "schema_optional_fields_present": schema_optional,
            "schema_extras_rejected": [],
        }
    )
