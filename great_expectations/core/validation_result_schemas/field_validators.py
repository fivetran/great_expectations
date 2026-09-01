"""Reusable pydantic v1 field validators for validation result schemas.

All validators are pure functions intended to be bound to schema classes via
``pydantic.validator`` and ``pydantic.root_validator``.  They are defined once
here and imported by every schema family so that per-format classes stay thin.

Import rules (enforced by ruff banned-api):
- Pydantic symbols come exclusively from ``great_expectations.compatibility.pydantic``.
- ``RuntimeTypeName`` comes from ``validation_result_schemas.types``.
- No direct ``import pydantic``, no PEP 604 unions.
"""

from __future__ import annotations

from typing import Any, Optional

from great_expectations.core.validation_result_schemas.types import RuntimeTypeName

# ---------------------------------------------------------------------------
# Runtime-type classifier
# ---------------------------------------------------------------------------

# Module-level type map used by classify_runtime_type.
# bool is intentionally excluded — it must be checked before int (bool is a
# subclass of int), so it gets its own explicit branch in the function.
_RUNTIME_TYPE_MAP: dict = {
    int: RuntimeTypeName.INT,
    float: RuntimeTypeName.FLOAT,
    str: RuntimeTypeName.STR,
    list: RuntimeTypeName.LIST,
    dict: RuntimeTypeName.DICT,
}

# Module-level constant for the SQL engine validation error message (TRY003).
_SQL_INDEX_QUERY_REQUIRED_MSG = (
    "unexpected_index_query is required when engine_hint='sql' and "
    "return_unexpected_index_query=True, but it was not found in the "
    "result dict.  This indicates a schema mismatch for this SQL engine "
    "and ResultFormat combination."
)


def classify_runtime_type(value: Any) -> RuntimeTypeName:
    """Classify the runtime type of a heterogeneous field (e.g., unexpected_rows).

    Returns a stable ``RuntimeTypeName`` enum value used in findings metadata.
    Never raises — all branches end in a known enum member.

    Handles pyspark and pandas DataFrames by inspecting ``type(v).__module__``
    and ``type(v).__name__`` so that neither library needs to be imported at
    module load time.
    """
    if value is None:
        return RuntimeTypeName.NONE

    # Check bool before int — bool is a subclass of int in Python
    if isinstance(value, bool):
        return RuntimeTypeName.BOOL

    for t, name in _RUNTIME_TYPE_MAP.items():
        if isinstance(value, t):
            return name

    # DataFrame detection without importing the package
    type_name = type(value).__name__
    module = type(value).__module__
    if type_name == "DataFrame" and not module.startswith("pyspark"):
        return RuntimeTypeName.DATAFRAME_PANDAS
    if "pyspark" in module:
        return RuntimeTypeName.DATAFRAME_SPARK

    return RuntimeTypeName.OTHER


# ---------------------------------------------------------------------------
# Field validators (pydantic v1 style — bound by callers via validator())
# ---------------------------------------------------------------------------


def validate_unexpected_rows_passthrough(cls: Any, v: Any) -> Any:
    """v1 validator for ``unexpected_rows``.

    Accepts any runtime type; the matrix runner records the actual type via
    ``classify_runtime_type`` for findings.  Does **not** raise on type mismatch
    — the schema accepts ``Any`` for this field because the runtime type differs
    across execution engines (pandas DataFrame, list[dict] on SQL, Spark frame).
    """
    return v


def validate_partial_unexpected_counts_fallback(cls: Any, v: Optional[list]) -> Optional[list]:
    """v1 validator for ``partial_unexpected_counts``.

    Accepts the two documented shapes:
    - Canonical: ``[{"value": x, "count": n}, ...]``
    - Error fallback: ``[{"error": "partial_exception_counts requires a hashable type"}]``
    - ``None``

    Both shapes are returned unchanged — the validator is a passthrough that
    exists so the schema explicitly acknowledges the fallback rather than
    inadvertently forbidding it.
    """
    return v


# ---------------------------------------------------------------------------
# Root validator
# ---------------------------------------------------------------------------


def root_validate_engine_required_fields(cls: Any, values: dict) -> dict:
    """v1 root_validator for SQL engine-required fields.

    If ``engine_hint`` is ``"sql"`` and ``return_unexpected_index_query`` is
    ``True``, asserts that ``unexpected_index_query`` is present (non-None) in
    the parsed values dict.  All other combinations are a no-op.

    Engine hint is read from the ``engine_hint`` key in the ``values`` dict.
    Schemas that do not declare ``engine_hint`` as a field will simply not have
    the key, and the check is skipped — ensuring the validator is safe to include
    in any schema regardless of whether the dispatcher sets the hint.

    A ``None`` hint means the engine is unknown, never "assume SQL".  The engine
    is never guessed from the result dict: ``unexpected_index_query`` is emitted
    by pandas too (as a ``df.filter(...)`` expression), so a shape-based guess
    would arm this assertion against results it does not apply to.
    """
    engine_hint = values.get("engine_hint")

    if engine_hint != "sql":
        # Unknown engine (hint is None) or a non-SQL engine: no assertion applies.
        return values

    if not values.get("return_unexpected_index_query"):
        # SQL engine, but the query was not requested: no assertion needed
        return values

    # SQL engine + query was requested: unexpected_index_query must be present
    if not values.get("unexpected_index_query"):
        raise ValueError(_SQL_INDEX_QUERY_REQUIRED_MSG)

    return values
