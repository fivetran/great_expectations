---
name: gx-configure-data-source
description: Set up Great Expectations data access end to end — connect a data source, define a data asset, add a batch definition, and verify it by actually reading data through it. Use when a user asks to connect Great Expectations to their data (files, a SQL database or warehouse, or an in-memory dataframe), to add an asset or batch definition to a project they already have, or when other Great Expectations work is blocked because no working batch definition exists yet.
license: Apache-2.0
---

# Configure a Great Expectations data source

This skill takes a user from "here is my data" to a **verified working batch
definition** — a named, saved way of pulling a specific slice of their data
that you have proven works by actually reading through it.

Three objects, in order, each built on the one before:

- A **data source** holds the connection: a directory, a connection string, or
  an in-memory handle.
- A **data asset** names the logical collection of data within it: a table, a
  query, a family of files, a dataframe.
- A **batch definition** selects how much of that asset a single operation
  reads: the whole thing, or one time window of it.

Everything here goes through Great Expectations' public configuration API and
produces ordinary project artifacts. Nothing depends on this skill being
present afterwards.

## The flow

1. **Preflight** — find out which project (or in-memory session) you are
   operating on, and tell the user. See `references/preflight.md`.
2. **Elicit** — the source type, the connection details, the asset, and the
   batching cadence.
3. **Configure** — data source, then asset, then batch definition, each with
   the reuse-first pattern below.
4. **Verify** — retrieve a batch and probe it. Retrieval alone proves nothing.
5. **Report** — say what was built and where it lives; offer write-out if the
   session is in memory.

Do not skip step 1, and do not stop before step 4. A configuration that was
never read through is not a result worth reporting.

## Step 1 — Preflight

Follow `references/preflight.md` in full before configuring anything. It
establishes whether you are working against a project on disk or an in-memory
session, tells you what to announce to the user, and covers the environment
problems that silently masquerade as "no project found".

The outcome you carry forward is a `context` object and one fact: whether the
session is file-backed or in memory. Both are fully supported paths.

## Step 2 — Elicit what you need

Four things, in this order. Ask for them together where you can; don't
interrogate the user one field at a time.

**1. Which data source type.** Read the shipped catalog rather than working
from memory — see `references/datasource-catalog.md`. It gives you the exact
factory name for each type, the arguments that type accepts, and which of them
are mandatory. It also covers how to steer the conversation when the user
describes their data rather than naming a backend.

**2. The connection details** the chosen type's schema marks as required. Read
the secrets rule below before you write any of them down.

**3. What the asset is.** A table name, a SQL query, a file-name pattern, or a
dataframe variable in the user's session. Which of these are available depends
on the type; the catalog reference enumerates them.

**4. The batching cadence.** Whole collection, or sliced by day, month, or
year. Ask what the natural unit of the user's data is — if they check data
daily, a daily batch definition matches how they work. If the data has no
usable date column, the whole collection is the right answer and there is
nothing to apologize for.

### Secrets: templates only, never values

Connection strings routinely carry passwords, tokens, and account
identifiers. Great Expectations already has a mechanism for this, and it is
the only one to use.

**Put a `${VARIABLE_NAME}` reference in the configuration; never the literal
value.** The reference is what gets stored, and it is resolved at connection
time:

```python
connection_string = "postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@warehouse.internal:5432/analytics"
```

Three rules follow from this, and none of them bend:

- **Never write a literal secret into a configuration, a file, or a message
  back to the user.** Not as a placeholder, not "just for testing", not
  inlined to get past an error. If you are holding a secret value, the only
  correct thing to do with it is tell the user which environment variable to
  put it in.
- **Never echo a resolved secret value.** Report the template
  (`${DB_PASSWORD}`), never what it resolved to.
- **If a required credential is missing, say which variable is missing and how
  to set it — then stop.** Do not guess a value, do not substitute a default,
  and do not fall back to an unauthenticated connection.

**Where the variable is read from depends on the session**, and the split
matters:

- An **in-memory session** resolves `${VARIABLE_NAME}` from process
  environment variables only. It has no project on disk, so it has no
  uncommitted config file to read from. If the user wants to supply the value,
  it has to be an environment variable.
- A **file-backed project** reads environment variables *and* an uncommitted
  config-variables file inside the project directory. Either works; the
  uncommitted file is the option for values that should be available to
  anyone opening that project.

Name whichever applies when you ask for a credential, so the user knows where
to put it. `references/write-out.md` covers what changes when an in-memory
session later becomes a project.

## Step 3 — Configure, reusing what already exists

The user may be adding to a project that already has some of this configured —
possibly from a teammate, a previous conversation, or an earlier run of this
same flow. **Fetch each object before creating it**, and create only what is
missing.

Adding a duplicate is not an option the API offers: `add_<type>_asset` and
`add_batch_definition_*` raise `ValueError: "<name>" already exists` on a
second call with the same name. There is no `add_or_update_*` variant for
assets or batch definitions.

All three fetch calls signal absence with a `LookupError` subclass, so a
single `except LookupError` is the correct catch for each:

| Fetch | Raises when missing |
| --- | --- |
| `context.data_sources.get(name)` | `KeyError` (a `LookupError`) |
| `datasource.get_asset(name)` | `LookupError` |
| `asset.get_batch_definition(name)` | `KeyError` (a `LookupError`) |

### Never "update" a data source that already exists

**`add_or_update_<type>` replaces a data source wholesale.** It does not merge.
Calling it against a name that already exists drops every asset and batch
definition attached to that data source — including ones this session never
created. A run that "updates" a data source in order to add one asset to it
destroys the user's other assets silently: no error, no warning, and the flow
carries on and reports success.

Verified directly: a data source carrying assets `['orders', 'products']` has
`[]` assets immediately after a second `add_or_update_sqlite` under the same
name.

So:

- Call the data-source factory **at most once per flow**, before any asset
  step, and **only when the data source does not already exist**.
- If the user genuinely wants to change the connection configuration of an
  existing data source, tell them first, in plain terms, that every asset and
  batch definition on it will be dropped and have to be rebuilt — then let
  them decide.

Note also that the factory **tests the connection as part of the call**, so it
can be slow or hang on an unreachable host. Run it inside the duration-tracked
wrapper in `references/robustness.md` like any other data-touching call.

### The pattern

```python executable
DATASOURCE_NAME, ASSET_NAME, BATCH_DEFINITION_NAME = "warehouse", "orders", "by_month"

# --- data source: create only if absent; never replace an existing one ---
try:
    datasource = context.data_sources.get(DATASOURCE_NAME)
except LookupError:
    datasource = context.data_sources.add_or_update_sqlite(
        name=DATASOURCE_NAME,
        connection_string="sqlite:///${WAREHOUSE_PATH}",
    )

# --- asset: reuse, or delete and re-add when its configuration must change ---
replace_asset = False  # set True only if the user wants different asset config
try:
    asset = datasource.get_asset(ASSET_NAME)
    asset_exists = True
except LookupError:
    asset_exists = False

if asset_exists and replace_asset:
    datasource.delete_asset(ASSET_NAME)
    asset_exists = False
if not asset_exists:
    asset = datasource.add_table_asset(name=ASSET_NAME, table_name="orders")

# --- batch definition: same shape ---
replace_batch_definition = False
try:
    batch_definition = asset.get_batch_definition(BATCH_DEFINITION_NAME)
    batch_definition_exists = True
except LookupError:
    batch_definition_exists = False

if batch_definition_exists and replace_batch_definition:
    asset.delete_batch_definition(BATCH_DEFINITION_NAME)
    batch_definition_exists = False
if not batch_definition_exists:
    batch_definition = asset.add_batch_definition_monthly(
        name=BATCH_DEFINITION_NAME, column="ordered_at"
    )
```

Two things to keep intact when you adapt this:

- **The fetch and the create are separate statements, not a create inside the
  `except` of the fetch's own `try`.** Keeping them apart means a failure in
  the create is reported as a create failure rather than being swallowed by
  the same handler.
- **Deleting and re-adding an asset affects only that asset.** Its siblings on
  the same data source are untouched — this is exactly why the delete-and-add
  pattern is safe for assets and batch definitions while the data-source
  factory is not.

Set `replace_asset` / `replace_batch_definition` from what the user actually
asked for. If they want a different table, different files, or a different
partitioning column than what is already configured under that name, the
existing object has to be replaced. If they described what is already there,
reuse it and say so.

## Step 4 — Verify by reading through it

**Retrieving a batch does not prove the configuration works.** For a SQL query
or table asset, building the batch touches nothing — `get_batch()` returns a
real `Batch` object even when the table does not exist. Reporting success on
that basis means telling the user their setup works when it does not.

Always follow retrieval with a probe that actually reads data:

```python executable
batch = batch_definition.get_batch()  # add batch_parameters=... for a partitioned definition
head = batch.head(n_rows=5)           # this is the step that touches the data
```

`head` is a small object with a `.data` attribute holding a pandas DataFrame
of the sampled rows; printing it renders the rows directly.

**Run this probe inside the duration-tracked, exception-catching wrapper in
`references/robustness.md`.** Do not write your own — that reference already
handles the parts that are easy to get wrong: checking in with the user while
a slow query is still running rather than after it returns, never cancelling
work that continues to run and bill on the data platform, and recovering the
real database error out of the bare `KeyError` a broken probe raises.

Four outcomes, and three of them are not failures:

- **The probe returns rows** — the batch definition works. Proceed to step 5.
- **The probe returns zero rows**, with the expected column names — the
  configuration works and the underlying collection is empty. This is what an
  empty table or empty dataframe looks like: `head` returns a frame with the
  right columns and no rows. Say both things plainly. Do not report it as a
  configuration failure, and do not start changing the configuration to make
  rows appear.
- **`get_batch()` raises `NoAvailableBatchesError: No available batches
  found.`** — the configuration works, but the *window you asked for* holds no
  data. Both partitioned SQL assets and file-based assets fail this way when
  the requested year/month matches nothing, and it is the normal answer for a
  window outside the data's range. Report it as an empty window, name the
  batch parameters you used, and offer to try a window that exists — not as a
  broken setup.
- **The probe raises anything else** — the configuration does not work. Report
  it per `references/robustness.md`'s rules: what failed, why as far as it is
  known, one concrete next step. A broken table or query surfaces here as a
  bare `KeyError` with no readable message; that reference explains how to
  recover the real database error behind it. Do not report success, and do not
  retry with different parameters hoping something sticks.

## Step 5 — Report, and offer write-out when in memory

Tell the user, concretely:

- The names of the data source, asset, and batch definition, and which of them
  you created versus reused.
- Where the configuration lives: the project's configuration directory for a
  file-backed session, or a plain statement that the session is in memory and
  nothing is saved yet.
- That the batch definition is verified, and what the probe returned — a row
  count and the columns is usually enough. Never paste a secret or a resolved
  credential into this report.
- How to retrieve a batch again, including the `batch_parameters` the batch
  definition needs.

**If the session is in memory, offer to write it out** to a real project so
the work survives — see `references/write-out.md` for the procedure and for
what the user needs to know about dataframe assets, which carry configuration
but no data. Offer it; don't do it unprompted, and don't pick the location.

## Where this flow ends

**The verified batch definition is the end state.** Do not build a suite of
"smoke test" expectations to prove the setup works — the probe in step 4 has
already proven it, an invented expectation asserts something the user never
asked for, and a failing one would report a data-quality problem that is
really just a guess of yours.

When the user wants to assert things about their data, that is expectation
work: hand off to the `gx-configure-expectations` skill with the batch
definition you just verified. If they ask for both in one breath, finish this
flow, report it, and then move on.

## Worked examples

Each of these shows the object chain — data source, asset, batch definition,
verified batch — for a **fresh** setup where none of these names exist yet.
Preflight comes first in all three, and step 3's fetch-first pattern still
applies: the moment there is any chance the project already holds a data
source by that name, wrap these calls in it rather than copying them as they
stand, or the data-source call will drop assets that are already there.

Take the factory names and arguments for the user's actual backend from
`references/datasource-catalog.md`.

### A file-based source: monthly CSV files

The date lives in the file name, so the monthly batch definition takes a
`regex` with named groups. **Batch parameters for file-based definitions must
be strings** — passing `2024` instead of `"2024"` raises
`InvalidBatchRequestError`.

```python
datasource = context.data_sources.add_or_update_pandas_filesystem(
    name="sales_files",
    base_directory="/data/sales",
)
asset = datasource.add_csv_asset(name="monthly_sales")
batch_definition = asset.add_batch_definition_monthly(
    name="by_month",
    regex=r"sales_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
)

batch = batch_definition.get_batch(batch_parameters={"year": "2024", "month": "02"})
print(batch.head(n_rows=5))
```

### A SQL source: a table partitioned by month

The date lives in a column, so the monthly batch definition takes `column`.
**Batch parameters here are integers**, unlike the file-based case above. The
credential-bearing part of the connection string is a `${VARIABLE_NAME}`
reference, never a literal.

```python
datasource = context.data_sources.add_or_update_postgres(
    name="warehouse",
    connection_string="postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@warehouse.internal:5432/analytics",
)
asset = datasource.add_table_asset(name="orders", table_name="orders")
batch_definition = asset.add_batch_definition_monthly(name="by_month", column="ordered_at")

batch = batch_definition.get_batch(batch_parameters={"year": 2024, "month": 3})
print(batch.head(n_rows=5))
```

A query asset is the alternative when the logical collection is not a whole
table — `datasource.add_query_asset(name=..., query=...)`. Use it to express
what the data *is*, not to bolt a `LIMIT` onto a slow table; see
`references/robustness.md` for why row-limited query assets are a last-resort
exploration tool rather than a batching mechanism.

### An in-memory dataframe

A dataframe asset stores configuration only — the data itself is handed over
at retrieval time, every time, in this session and in every future one:

```python executable
datasource = context.data_sources.add_or_update_pandas(name="in_memory")
asset = datasource.add_dataframe_asset(name="customers")
batch_definition = asset.add_batch_definition_whole_dataframe(name="all_rows")

batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
print(batch.head(n_rows=5))
```

Say this out loud to the user when you configure one: the dataframe is not
saved, and anything reading this asset later must supply a dataframe itself.

## References

- `references/preflight.md` — establishing and announcing the session context.
- `references/datasource-catalog.md` — every configurable type, its factory,
  its arguments, and its asset and batch-definition surface, read from the
  shipped catalog.
- `references/robustness.md` — the time-budget wrapper, scope-reduction
  levers, and how to report a failure helpfully.
- `references/write-out.md` — turning an in-memory session into a real
  project.
