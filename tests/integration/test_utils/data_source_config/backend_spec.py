"""Declarative facts about a SQL backend used by the integration test harness.

This module holds only data: the types a SQL backend declares to describe itself, with no
dependency on the harness that consumes them. It imports nothing from this package's other
modules, so a throwaway record can be constructed here without importing a backend, and so this
module sits to the left of everything that consumes it in the dependency graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, FrozenSet, Mapping, Optional, Sequence, Union

import pytest

if TYPE_CHECKING:
    import sqlalchemy as sa

    from great_expectations.compatibility.sqlalchemy import TypeEngine


class TransactionMode(Enum):
    """How a backend handles transaction boundaries during setup and teardown."""

    EXPLICIT_COMMIT = "explicit_commit"
    """The default: the harness calls ``conn.commit()`` after setup and before teardown."""

    AUTOCOMMIT = "autocommit"
    """The backend has no standard transactions; the harness skips explicit commits."""


class BackendProvisioning(Enum):
    """Where a test run gets an instance of this backend."""

    LOCAL_CONTAINER = "local_container"
    """Started from a compose file for the duration of the test run."""

    LOCAL_FILE = "local_file"
    """No server at all; the backend is a local file (e.g. SQLite)."""

    EXTERNAL_CREDENTIALS = "external_credentials"
    """Hosted; reached with credentials read from the environment."""


class BackendTier(Enum):
    """Named suites a backend can participate in."""

    STANDARD_SQL = "standard_sql"
    """The shared standard SQL data-source list."""

    CURATED_SQL = "curated_sql"
    """The smaller curated suite."""


@dataclass(frozen=True)
class CiLaneRef:
    """Where a backend's tests run in the CI workflow."""

    workflow_job: str
    """A key under ``jobs:`` in the CI workflow file."""

    marker_token: str
    """The marker token that job selects tests on."""


# Produces the dialect-required positional schema items for ONE table. Called once per table so
# that each table gets its own freshly constructed items; a schema item that binds to a table on
# attachment cannot be reused across tables. `sa` is imported under TYPE_CHECKING only, the
# pattern `sql.py` already uses, so this module needs no dialect and no runtime SQLAlchemy symbol
# it does not already have.
TableSchemaItemFactory = Callable[[], Sequence["sa.sql.schema.SchemaItem"]]


@dataclass(frozen=True)
class SqlBackendSpec:
    """Every dialect fact about a SQL backend that is data rather than behavior."""

    # identity
    label: str
    """Appears in the parameterized test id."""

    marker: str
    """The pytest marker name; may differ from ``label`` (e.g. SQL Server's label is ``mssql``
    while its marker is ``sql_server``)."""

    # runtime shape
    provisioning: BackendProvisioning
    ci_lane: CiLaneRef
    uses_schema: bool
    transaction_mode: TransactionMode = TransactionMode.EXPLICIT_COMMIT

    table_schema_items: Optional[TableSchemaItemFactory] = None
    """A zero-argument callable returning a sequence of positional SQLAlchemy schema items,
    or ``None`` (the default) when the backend contributes nothing.

    This is a factory, not a stored instance, for two independent reasons, plus a third that
    governs where it can be declared:

    - *Positional, not keyword.* SQLAlchemy accepts dialect-specific ``Table`` keyword arguments
      only when the dialect registers them in ``construct_arguments``; a dialect storage-engine
      construct is not one of those, so it cannot be passed as a ``Table`` keyword argument at
      all — it must arrive positionally, alongside the generated columns.
    - *A factory, not a stored instance.* Such a construct binds to the first ``Table`` it is
      attached to, so reusing one instance across tables corrupts the second table's schema.
      Each table therefore needs freshly constructed items, which only a callable invoked once
      per table can provide.
    - *Deferred construction.* Building the items requires the dialect package, and this
      declaration module is imported in lanes where that package is not installed. A
      zero-argument callable defers construction to the point where the backend has been
      selected by marker and its dialect is installed; a stored instance could not be built
      where the declaration lives.
    """

    column_type_overrides: Mapping[type, Union[type[TypeEngine], TypeEngine]] = field(
        default_factory=dict
    )
    """Python-type-to-SQLAlchemy-type overrides merged over the shared default inference
    mapping, defaulting to empty.

    This is a mapping, not a callable, because there is no per-table freshness requirement:
    the values are inert data with no construction cost, so no callable indirection is
    warranted. The consequence is that the field cannot be made lazy the way
    ``table_schema_items`` is — assigning the result of a function call still evaluates at
    declaration time, because it is the value that is stored, not the callable. A backend whose
    override values come from its dialect package therefore builds the mapping at module scope
    behind an import guard that yields an empty mapping when the package is absent. That is the
    supported shape: the declared record is populated where the dialect is installed and empty
    where it is not.
    """

    insert_parameter_limit: Optional[int] = None
    tiers: FrozenSet[BackendTier] = frozenset()
    """The named test tiers this backend participates in, e.g.
    ``tiers=frozenset({BackendTier.CURATED_SQL})``.

    Always write a ``frozenset(...)`` literal, never a bare set literal: a bare
    ``{BackendTier.CURATED_SQL}`` is a ``set``, which mypy rejects against this ``FrozenSet``
    field, and ``tests/`` is inside mypy's ``files``, so that is a hard failure rather than a
    lint note. A backend joining both tiers writes
    ``frozenset({BackendTier.STANDARD_SQL, BackendTier.CURATED_SQL})``; a backend joining
    neither tier omits this field.
    """

    tier_case_exclusions: Mapping[str, str] = field(default_factory=dict)
    """Case key to reason string, defaulting to empty. Lets a tier member sit out one named case
    within that tier's suite, with a required reason recorded next to the declaration."""

    # wiring coordinates
    dev_requirements_file: Optional[str] = None
    """Repo-relative path, e.g. ``"reqs/requirements-dev-mysql.txt"``."""

    task_runner_marker: Optional[str] = None
    """Dependency-map key; ``None`` means no entry is needed."""

    container_service: Optional[str] = None
    """Compose directory name under ``assets/docker/``."""

    @property
    def pytest_mark(self) -> pytest.MarkDecorator:
        """Resolve the declared marker name to a pytest mark decorator.

        Compares equal to the literal ``pytest.mark.<name>`` the existing configs return today.
        """
        return getattr(pytest.mark, self.marker)
