# SQL backend onboarding backlog

This is a working backlog for maintainers, not a promise or a schedule. It records, for each SQL
backend that is not yet onboarded to the shared harness, which of the onboarding wiring surfaces
already exist in the repository, which are missing, and what is concretely known about onboarding
it. See the onboarding walkthrough in
[`tests/integration/data_sources_and_expectations/README.md`](./README.md) for what each surface
is and how to add it — this document does not restate that material, only cross-references it.

## How to read an entry

Each backend below is checked against the seven onboarding surfaces the walkthrough's step 3 and
step 4 describe, plus one further signal:

- **pytest marker** — an entry in `pyproject.toml`'s `[tool.pytest.ini_options] markers` list.
- **`REQUIRED_MARKERS` entry** — the marker name added to that set in `tests/conftest.py`.
- **dev requirements file** — `reqs/requirements-dev-<backend>.txt`.
- **task-runner entry** — a key in `tasks.py`'s `MARKER_DEPENDENCY_MAP`.
- **CI lane** — a token in the marker matrix in `.github/workflows/ci.yml`.
- **compose directory** — `assets/docker/<backend>/`, for a backend that would run as a local
  container.
- **harness declaration** — a `SqlDatasourceTestConfig` subclass under
  `tests/integration/test_utils/data_source_config/`, decorated with `@register_sql_backend`.
- **`GXSqlDialect` member** — whether `great_expectations/execution_engine/sqlalchemy_dialect.py`
  already has an enum member for this dialect. This one is not a harness onboarding surface; it
  signals how much dialect-specific behavior the core execution engine already carries, independent
  of the test harness.

None of the six backends below has a harness declaration, so none is registered, and the wiring
drift check (`pytest tests/test_sql_backend_wiring.py -m project -q`) has nothing to say about any
of them — that check only walks backends that are already registered.

## Athena

- **Existing**: pytest marker (`athena`), `REQUIRED_MARKERS` entry, dev requirements file
  (`reqs/requirements-dev-athena.txt`, pinning `pyathena[SQLAlchemy]`), a task-runner entry in
  `tasks.py`'s `MARKER_DEPENDENCY_MAP` (naming only the requirements file, no `services`), a CI
  lane (the `athena` token in the marker matrix in `.github/workflows/ci.yml`), and a
  `GXSqlDialect` member (`AWSATHENA`, already consulted by the execution engine for temp-table and
  sampling behavior).
- **Missing**: harness declaration, compose directory.
- **Known obstacle**: `pyathena` connects to the hosted AWS Athena service over its API rather than
  to a local server, the same shape as this harness's existing `EXTERNAL_CREDENTIALS` backends
  (BigQuery, Databricks, Redshift, Snowflake). Athena has no `assets/docker/athena/` directory, and
  its task-runner entry declaring no `services` is consistent with that — there is nothing local to
  start. Onboarding Athena would plausibly declare
  `provisioning=BackendProvisioning.EXTERNAL_CREDENTIALS`, the same way those four backends do, but
  that is inference from the existing pattern, not something verified against an actual connection.

## Dremio

- **Existing**: dev requirements file (`reqs/requirements-dev-dremio.txt`, pinning `pyodbc` and
  `sqlalchemy-dremio`), a `GXSqlDialect` member (`DREMIO`).
- **Missing**: pytest marker, `REQUIRED_MARKERS` entry, task-runner entry, CI lane, compose
  directory, harness declaration.
- **Known obstacle**: core marks the dialect experimental — "Dremio Support is experimental,
  functionality is not fully under test" in the execution engine. That is a stated caveat on the
  dialect support itself, not merely absent wiring.

## Hive

- **Existing**: dev requirements file (`reqs/requirements-dev-hive.txt`, pinning `PyHive`, `thrift`,
  and `thrift-sasl`), a `GXSqlDialect` member (`HIVE`).
- **Missing**: pytest marker, `REQUIRED_MARKERS` entry, task-runner entry, CI lane, compose
  directory, harness declaration.
- **Known obstacle**: none established. The surfaces are simply absent; nothing in the tree records
  why.

## Oracle

- **Existing**: a `GXSqlDialect` member (`ORACLE`), already referenced by non-harness code —
  `great_expectations/data_context/util.py`'s connection-string handling and the execution engine's
  sampling tests both know about the `oracle` and `oracle+cx_oracle` dialect strings.
- **Missing**: everything else — no dev requirements file, no pytest marker, no `REQUIRED_MARKERS`
  entry, no task-runner entry, no CI lane, no compose directory, no harness declaration. Oracle is
  the sharpest gap of the six: a backend the core execution engine already has a dialect entry for,
  with no onboarding surface at all, not even the requirements file every other backend on this
  list has.
- **Known obstacle**: none established beyond the missing requirements file itself. There is no
  driver pin anywhere in `reqs/` to say which Oracle client library (for example `python-oracledb`
  or `cx_Oracle`) this harness would use.

## Teradata

- **Existing**: dev requirements file (`reqs/requirements-dev-teradata.txt`, pinning
  `teradatasqlalchemy`), a `GXSqlDialect` member (`TERADATASQL`, consulted for temp-table creation
  and for dialect-module import, but — unlike Athena's `AWSATHENA` — reaching no partitioner or
  sampler code path).
- **Missing**: pytest marker, `REQUIRED_MARKERS` entry, task-runner entry, CI lane, compose
  directory, harness declaration.
- **Known obstacle**: core marks the dialect experimental — "Teradata Support is experimental,
  functionality is not fully under test" in the execution engine, and a matching note beside the
  temp-table path. That is a stated caveat on the dialect support itself, not merely absent wiring.

## Vertica

- **Existing**: dev requirements file (`reqs/requirements-dev-vertica.txt`, pinning
  `sqlalchemy-vertica-python`), a `GXSqlDialect` member (`VERTICA`).
- **Missing**: pytest marker, `REQUIRED_MARKERS` entry, task-runner entry, CI lane, compose
  directory, harness declaration.
- **Known obstacle**: none established. The surfaces are simply absent; nothing in the tree records
  why.

## What this harness cannot currently express

Nothing about any of these six backends demands a change to `SqlBackendSpec` itself — the
declaration's existing extension points (`uses_schema`, `column_type_overrides`,
`transaction_mode`, `insert_parameter_limit`, `table_schema_items`) are dialect facts, not
provisioning facts, and provisioning is already a three-way choice
(`BackendProvisioning.LOCAL_CONTAINER`, `LOCAL_FILE`, `EXTERNAL_CREDENTIALS`). Whichever of these
six backends is onboarded next should fit the existing shape; nothing here identifies a fourth
provisioning kind or a missing declaration field.

## Adjacent gaps observed but not fixed

These were noticed while surveying the six backends above but sit outside what this document's own
effort touches, so they are recorded as backlog rather than fixed here. Each is a **class** of gap
that can recur on any backend, illustrated with one **dated instance** — not a standing claim about
the named backend, because another change may close that instance at any time without this document
being updated.

**A backend can have a compose directory that is never started, because the task-runner entry that
would start it declares no `services`.** Observed for `clickhouse` as of 2026-08-07:
`assets/docker/clickhouse/` exists, but `tasks.py`'s `"clickhouse"` entry in
`MARKER_DEPENDENCY_MAP` names only its requirements file, with no `services` tuple, so running that
marker through the task runner never brings the container up.

(`databricks`'s task-runner entry has the same shape — no `services` named — but Databricks is
credential-provisioned rather than locally containerized, so there is nothing local for its entry
to start; that is not the same gap.)

**A backend can be absent from the aggregate SQLAlchemy requirements file and from both of the
SQLAlchemy pin groups in `setup.py`, leaving its extra with no SQLAlchemy version constraint.**
Observed for `singlestore` as of 2026-08-07: SingleStore has its own
`reqs/requirements-dev-singlestore.txt`, but that file is not one of the `--requirement` includes
in `reqs/requirements-dev-sqlalchemy.txt` (which lists, among others, `athena`, `dremio`,
`teradata`, `hive`, and `vertica`), and the key `"singlestore"` appears in neither of `setup.py`'s
`sqla1x_only_keys` nor `sqla_keys` tuples.

The extra itself does exist — `setup.py` derives one per `reqs/requirements-dev-*.txt` file, so
`great_expectations[singlestore]` installs `singlestoredb` and `sqlalchemy-singlestoredb`. What the
pin groups govern is which SQLAlchemy constraint gets appended to an extra that already exists.
Belonging to neither leaves `singlestore` the only SQL backend extra shipping without one, where
`athena` carries `sqlalchemy>=1.4.0` and `teradata` carries `sqlalchemy<2.0.0`. Worth noting
plainly:
SingleStore is the backend this document's own effort registered with the harness; this gap is a
fresh instance next to that work, not one inherited from before it, and it is recorded here rather
than fixed because `reqs/` and `setup.py` are outside what this effort's boundary covers.
