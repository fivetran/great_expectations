"""Process-global registry of SQL backend declarations.

A `SqlBackendSpec` (see `backend_spec.py`) is free to construct; nothing about building one has
any side effect. Registration is the separate, deliberate act that enrols a config class's spec
into the set the harness treats as "the SQL backends that exist" — the set completeness checks,
derived suite membership, and CI wiring checks all walk. That split is what lets a test build a
throwaway spec, or even a throwaway registered class, without polluting the set that gates CI.

This module imports only `backend_spec`. It does not import the SQL config base, `sql.py`, or any
backend module — those sit to this module's right in the dependency direction
(`backend_spec` -> `registry` -> `sql_config` -> `sql` -> backend modules -> `tiers`), and a
module is only ever allowed to import from modules to its own left.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import ClassVar, Dict, Iterator, Protocol, Tuple, Type, TypeVar

from tests.integration.test_utils.data_source_config.backend_spec import (
    BackendProvisioning,
    BackendTier,
    SqlBackendSpec,
)

# The ceiling on tier_case_exclusions per backend. See _validate_tier_case_exclusion_ceiling: a
# reason makes one exclusion answerable, but only a count makes the whole set answerable, so the
# count is enforced here rather than left to per-exclusion review.
_MAX_TIER_CASE_EXCLUSIONS = 2


class _DeclaresBackendSpec(Protocol):
    """Structural shape a config class must have to be enrolled.

    Registration only needs one class attribute. Describing that as a `Protocol` here, rather than
    importing the concrete SQL config base, is what lets this module stay to the left of that base
    in the dependency direction while still type-checking the decorator's argument.
    """

    BACKEND_SPEC: ClassVar[SqlBackendSpec]


_C = TypeVar("_C", bound=_DeclaresBackendSpec)

_by_label: Dict[str, Type[_DeclaresBackendSpec]] = {}
_by_marker: Dict[str, Type[_DeclaresBackendSpec]] = {}


def _validate_identity(config_class: type, spec: SqlBackendSpec) -> None:
    if not spec.label:
        raise ValueError(
            f"{config_class.__name__} declares an empty SQL backend label; it must be a "
            f"non-empty string, since it appears in the parameterized test id used to select "
            f"this backend's cases"
        )
    if not spec.marker:
        raise ValueError(
            f"{config_class.__name__} declares an empty SQL backend marker; it must be a "
            f"non-empty string naming the pytest mark used to select this backend's tests"
        )
    if not spec.ci_lane.workflow_job:
        raise ValueError(
            f"{config_class.__name__} declares an empty CI lane workflow job; it must be a "
            f"non-empty string naming the workflow job that runs this backend's lane. A lane "
            f"naming no job cannot be located in the workflow file, so its wiring cannot be "
            f"checked at all"
        )
    if not spec.ci_lane.marker_token:
        raise ValueError(
            f"{config_class.__name__} declares an empty CI lane marker token; it must be a "
            f"non-empty string identifying which CI lane runs this backend's marker-selected tests"
        )


def _validate_insert_parameter_limit(config_class: type, spec: SqlBackendSpec) -> None:
    if spec.insert_parameter_limit is not None and spec.insert_parameter_limit <= 0:
        raise ValueError(
            f"{config_class.__name__} declares a non-positive insert_parameter_limit "
            f"({spec.insert_parameter_limit!r}); it must be a positive integer, or omitted "
            f"entirely when the backend has no chunking limit"
        )


def _validate_container_provisioning(config_class: type, spec: SqlBackendSpec) -> None:
    has_container_service = spec.container_service is not None
    is_local_container = spec.provisioning is BackendProvisioning.LOCAL_CONTAINER

    if is_local_container and not has_container_service:
        raise ValueError(
            f"{config_class.__name__} declares LOCAL_CONTAINER provisioning without a "
            f"container_service; a locally containerized backend must name the compose service "
            f"that starts it"
        )
    if has_container_service and not is_local_container:
        raise ValueError(
            f"{config_class.__name__} declares a container_service "
            f"({spec.container_service!r}) without LOCAL_CONTAINER provisioning; a container "
            f"service is only meaningful for a backend the harness starts locally"
        )


def _validate_table_schema_items(config_class: type, spec: SqlBackendSpec) -> None:
    # Checked for callability only, never invoked: calling it would require the backend's dialect
    # package, and registration must never assume that package is installed (this module is
    # imported in lanes that install no SQL dialect at all).
    if spec.table_schema_items is not None and not callable(spec.table_schema_items):
        raise ValueError(
            f"{config_class.__name__} declares table_schema_items "
            f"({spec.table_schema_items!r}) that is not callable; it must be a zero-argument "
            f"factory, or omitted entirely"
        )


def _validate_tier_case_exclusion_reasons(config_class: type, spec: SqlBackendSpec) -> None:
    for key, reason in spec.tier_case_exclusions.items():
        if not key:
            raise ValueError(
                f"{config_class.__name__} declares a tier case exclusion with an empty case key; "
                f"every excluded case must be named"
            )
        if not reason or not reason.strip():
            raise ValueError(
                f"{config_class.__name__} declares a tier case exclusion for case {key!r} with no "
                f"reason (or a whitespace-only one); an unexplained exclusion is exactly the "
                f"silent narrowing this mechanism exists to prevent, so every exclusion must "
                f"record why it exists"
            )


def _validate_tier_case_exclusion_ceiling(config_class: type, spec: SqlBackendSpec) -> None:
    count = len(spec.tier_case_exclusions)
    if count <= _MAX_TIER_CASE_EXCLUSIONS:
        return
    keys = sorted(spec.tier_case_exclusions)
    raise ValueError(
        f"{config_class.__name__} declares {count} tier case exclusions {keys!r}, exceeding the "
        f"ceiling of {_MAX_TIER_CASE_EXCLUSIONS}. The count is taken over the whole mapping "
        f"regardless of what each individual reason records — an exclusion for observed "
        f"non-determinism subtracts exactly as much coverage as one for a dialect gap. A reason "
        f"makes one exclusion answerable; only a count makes the set of exclusions answerable, "
        f"which is why this check exists on top of the per-exclusion reason requirement. The "
        f"remedy is to escalate this backend's tier participation, not to raise the ceiling"
    )


def _validate_tier_case_exclusions(config_class: type, spec: SqlBackendSpec) -> None:
    _validate_tier_case_exclusion_reasons(config_class, spec)
    _validate_tier_case_exclusion_ceiling(config_class, spec)


def _validate_spec(config_class: type, spec: SqlBackendSpec) -> None:
    _validate_identity(config_class, spec)
    _validate_insert_parameter_limit(config_class, spec)
    _validate_container_provisioning(config_class, spec)
    _validate_table_schema_items(config_class, spec)
    _validate_tier_case_exclusions(config_class, spec)


def register_sql_backend(config_class: type[_C]) -> type[_C]:
    """Enrol a SQL config class. Raises `ValueError` at decoration time on a duplicate label,
    duplicate marker, or any invariant violation in its declared spec.
    """
    spec = config_class.BACKEND_SPEC
    _validate_spec(config_class, spec)

    duplicate_label = _by_label.get(spec.label)
    if duplicate_label is not None:
        raise ValueError(
            f"duplicate SQL backend label {spec.label!r} declared by "
            f"{duplicate_label.__name__} and {config_class.__name__}"
        )
    duplicate_marker = _by_marker.get(spec.marker)
    if duplicate_marker is not None:
        raise ValueError(
            f"duplicate SQL backend marker {spec.marker!r} declared by "
            f"{duplicate_marker.__name__} and {config_class.__name__}"
        )

    _by_label[spec.label] = config_class
    _by_marker[spec.marker] = config_class
    return config_class


def iter_sql_backends() -> Tuple[Type[_DeclaresBackendSpec], ...]:
    """Registered config classes, ordered by spec label."""
    return tuple(_by_label[label] for label in sorted(_by_label))


def sql_backends_for_tier(tier: BackendTier) -> Tuple[Type[_DeclaresBackendSpec], ...]:
    """Registered config classes declaring membership in `tier`, ordered by spec label."""
    return tuple(
        config_class
        for config_class in iter_sql_backends()
        if tier in config_class.BACKEND_SPEC.tiers
    )


@contextmanager
def isolated_registry() -> Iterator[None]:
    """Snapshot the registry, clear it, yield an isolated empty registry, then restore the
    snapshot verbatim regardless of what happens inside.

    The registry is process-global module state, so a test that registers a throwaway backend —
    including every duplicate-rejection test, which needs one successful registration before the
    conflicting one — must not leave that backend behind for later tests or for the real registry
    consumers (the wiring drift check and the registered-set pin) to trip over. Clearing before
    yielding, rather than only restoring after, is what makes the empty registry inside the seam
    genuinely isolated rather than merely a live view onto whatever the real registry happens to
    hold at the time — which in turn is what lets a test assert whole-registry equality exactly,
    without that assertion depending on how many real backends happen to be registered elsewhere.
    """
    saved_by_label = dict(_by_label)
    saved_by_marker = dict(_by_marker)
    _by_label.clear()
    _by_marker.clear()
    try:
        yield
    finally:
        _by_label.clear()
        _by_label.update(saved_by_label)
        _by_marker.clear()
        _by_marker.update(saved_by_marker)
