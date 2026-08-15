---
name: gx-configure-expectations
description: Turn the data-quality checks a user describes in their own words into Great Expectations expectations — matched against the catalog shipped with the installed package, collected into a persisted suite, run against a batch, and reported per expectation. Use when a user wants to assert something about their data ("amounts should never be negative", "the customer column must never be empty"), to add checks to an existing suite, or to re-run a suite and explain the results.
license: Apache-2.0
---

# Configure Great Expectations expectations

This skill takes a user from "here is what I want to be true about my data" to
a **saved suite of expectations that has been run against a real batch**, with
every check reported individually.

Two objects, and the relationship between them is where the traps live:

- An **expectation** is a single check with typed parameters — one column, one
  assertion, one set of bounds.
- An **expectation suite** is the named, persisted collection of them.

Everything here goes through Great Expectations' public API and produces
ordinary project artifacts. Nothing depends on this skill being present
afterwards.

## The flow

1. **Preflight** — find out which project (or in-memory session) you are
   operating on, and tell the user. See `references/preflight.md`.
2. **Check the precondition** — a working batch definition must already
   exist. If none does, hand off and stop.
3. **Match** what the user described against the shipped expectation catalog.
   Build only what they described.
4. **Register the suite first**, then add the matched expectations to it.
5. **Validate** against a batch and report each expectation's own outcome.
6. **Confirm persistence**, and offer write-out if the session is in memory.

Steps 2 and 4 are the two places this flow fails silently rather than loudly.
Do not reorder them, and do not skip step 5 — a suite that was never run is
not a result worth reporting.

## Step 1 — Preflight

Follow `references/preflight.md` in full before anything else. It establishes
whether you are working against a project on disk or an in-memory session,
tells you what to announce to the user, and covers the environment problems
that silently masquerade as "no project found".

The outcome you carry forward is a `context` object and one fact: whether the
session is file-backed or in memory. Both are fully supported paths, and the
difference matters at step 6.

## Step 2 — The precondition: a working batch definition must exist

Expectations are checks against a batch of data. Without a batch definition to
retrieve one through, there is nothing to validate against, and **there is no
acceptable way to improvise data access here**. Do not add a data source, do
not read a file directly with pandas, do not construct a batch by hand.

Enumerate what the session already has:

```python executable
def existing_batch_definitions(context):
    """(data source, asset, batch definition) name triples available in this session."""
    found = []
    for datasource in context.data_sources.all().values():
        for asset in datasource.assets:
            for batch_definition in asset.batch_definitions:
                found.append((datasource.name, asset.name, batch_definition.name))
    return found
```

**If this returns an empty list, stop.** Tell the user that expectations need
a batch definition to run against, that their project (or session) has none
yet, and that setting one up is the `gx-configure-data-source` skill's job.
Hand off to it and end this flow — do not carry on and do not offer a
workaround. This is a hard stop, not a suggestion.

If it returns more than one, name them and let the user choose; guessing which
slice of their data they meant to assert against is not a decision to make for
them. Then retrieve the batch:

```python executable
datasource_name, asset_name, batch_definition_name = existing_batch_definitions(context)[0]
batch_definition = (
    context.data_sources.get(datasource_name)
    .get_asset(asset_name)
    .get_batch_definition(batch_definition_name)
)
batch = batch_definition.get_batch()   # add batch_parameters=... for a partitioned definition
```

A dataframe asset needs its data supplied at retrieval time —
`get_batch(batch_parameters={"dataframe": df})` — so ask the user for the
dataframe rather than inventing one.

**Retrieving a batch is not proof that it works.** For SQL assets, retrieval
touches nothing. If the batch definition has not been verified in this
session, probe it first with `batch.head(n_rows=5)` inside the wrapper in
`references/robustness.md`, exactly as the data-source flow does. A broken
batch definition discovered at validation time reports as a wall of metric
errors instead of one clear configuration problem.

## Step 3 — Match what the user described, and only that

Read the shipped catalog rather than working from memory — see
`references/expectation-catalog.md`. It covers locating the index inside the
installed package, matching a described check on type, description, and
data-quality category, filtering by the backend behind the batch definition,
and reading each expectation's parameters from its schema.

Two rules govern this step.

**Never invent an expectation type.** If nothing in the catalog matches what
the user described, say so, present the nearest candidates the catalog
actually contains, and offer the custom-expectation path. Report unmatched
checks separately as unbuilt, with the reason — never silently drop one, and
never substitute a different check that sounds similar. The catalog reference
gives the no-match procedure in full.

**Build only what the user described.** Do not profile the data to find
things worth asserting. Do not scan the schema and propose a check per column.
Do not append "you might also want" suggestions to the suite. The user decides
what is asserted about their data; a check they did not ask for is a guess of
yours that will later fail and be read as a real data-quality problem. If they
describe something vaguely ("amounts should be reasonable"), ask what bound
they mean — do not pick one from the data.

Inspecting a column to *inform a question you ask the user* is fine. Turning
what you observed into an expectation without being asked is not.

## Step 4 — Register the suite first, then add expectations

**Register the suite with the context before adding any expectation to it.**
This is the ordering rule, and getting it backwards loses work silently:

```python executable
import great_expectations as gx

SUITE_NAME = "orders_quality"

# Reuse an existing suite; create one only when the name is genuinely new.
if SUITE_NAME in {suite.name for suite in context.suites.all()}:
    suite = context.suites.get(SUITE_NAME)
else:
    suite = context.suites.add(gx.ExpectationSuite(name=SUITE_NAME))

# Now add. Each add persists immediately, because the suite is registered.
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0))
```

Three things this pattern gets right, each verified against real behavior:

- **Work on the handle the factory returns.** `context.suites.add(...)`
  re-reads the stored suite and returns a *different* object from the one you
  passed in. The returned handle is the one wired to the store, so every
  `add_expectation` on it is written through immediately, with no separate
  save call.
- **An unregistered suite persists nothing.** Building
  `gx.ExpectationSuite(name=...)`, adding expectations to it, and validating
  with it all work — `batch.validate(suite)` runs happily against a suite the
  context has never seen. Nothing raises, nothing warns, and afterwards
  `context.suites.get(name)` raises `DataContextError: ExpectationSuite with
  name <name> was not found.` The entire suite is gone. This is the failure
  mode the ordering rule exists to prevent.
- **`context.suites.add_or_update()` is destructive against an existing
  name.** It replaces the stored suite wholesale rather than merging: calling
  `context.suites.add_or_update(gx.ExpectationSuite(name=SUITE_NAME))` against
  a suite already holding three expectations leaves it holding zero — no
  error, no warning. Use the fetch-first pattern above instead. Reach for
  `add_or_update` only when the user has asked to replace a suite's whole
  contents, and tell them what is being discarded first.

Reusing a suite is safe: fetching it returns its existing expectations intact,
and adding to it appends. Adding an expectation identical to one already
present is a no-op — the collection is set-like — so re-running the flow does
not accumulate duplicates.

### Suite names: no dots

**Never put a dot in a suite name.** The store treats dots as path
separators. A suite named `orders.quality` is written to
`gx/expectations/orders/quality.json`, and `a.b.c` to
`gx/expectations/a/b/c.json` — one nested directory per segment. The suite
still loads by its full dotted name, so nothing appears broken from the API,
but the project's expectations directory fans out into a tree where nobody
looking for a suite file will find it, and a plain listing of the directory no
longer shows the suites it holds.

Use underscores or hyphens: `orders_quality`, `orders-daily`. If the user asks
for a dotted name, say why you are changing it rather than changing it
silently.

## Step 5 — Validate, and report each expectation on its own terms

```python executable
result = batch.validate(suite)
```

That is the whole validation call. It builds everything else it needs
internally.

Validation is a data-touching operation, so run it inside the duration-tracked
wrapper in `references/robustness.md` — the same one the batch probe uses. A
suite over a large table can run for a long time, and the rules there about
checking in with the user rather than abandoning a query that keeps running on
the platform apply unchanged.

### Pair results with expectations by configuration, never by position

**`result.results` does not come back in the order the expectations were
added.** Validation regroups the suite before running it, in two ways. Both
are stable across runs, so neither ever looks like a bug:

- **Expectations are grouped by the column they address.** Every check on one
  column is evaluated together, in the order that column was first mentioned.
  A suite added as `not_be_null(customer)`, `mean_to_be_between(amount)`,
  `values_to_be_unique(customer)`, `max_to_be_between(amount)` comes back with
  the two `customer` checks first and the two `amount` checks after. Checks
  with no `column` argument at all, such as a table row count, form a group of
  their own.
- **An expectation whose metric errored is moved ahead of every expectation
  that ran**, so a broken parameter also changes the position of everything
  else.

What makes this dangerous is that plenty of suites *do* come back in the order
they were built: any suite written column by column already matches the
grouping, and so does a two- or three-expectation suite over one column.
Pairing your input list with the results by index therefore looks correct
while you are trying it out and mislabels every finding once the suite grows.

Read the identity off each result instead: `each.expectation_config.type` and
`each.expectation_config.kwargs`.

### Separate a metric error from a data failure

`success is False` means two very different things, and reporting them the
same way tells the user their data is bad when their configuration is:

```python executable
for each in result.results:
    config = each.expectation_config
    if each.success:
        print(f"PASS {config.type} {config.kwargs}")
    elif not each.result:
        # The metric never evaluated — a configuration problem, not a finding.
        for _metric_id, info in each.exception_info.items():
            print(f"ERROR {config.type} {config.kwargs}: {info['exception_message']}")
    else:
        # The data genuinely failed the check.
        print(f"FAIL {config.type} {config.kwargs}: {each.result}")
```

**Both halves of `not each.success and not each.result` are load-bearing.** A
*passing* `expect_column_to_exist` also carries an empty `result` dict, so the
emptiness test alone would misclassify it.

On the error branch, `exception_info` already names the cause exactly — do not
guess at it. It is a dict with one entry per metric that errored, keyed by the
**string** repr of a metric identifier, and each value carries an
`exception_message` holding the real cause verbatim: a mistyped column reports
`Error: The column "nope" in BatchData does not exist.` Relay that message as
the *why*, apply the length ceiling from `references/robustness.md`, and never
paste the accompanying `exception_traceback`.

**Never report an empty-`result` failure as "your data failed this check."**
It was never evaluated. Report it as an expectation that could not run, name
the cause, and offer to fix the parameter and re-run.

### Degenerate data does not raise

Empty tables and all-null columns are ordinary results, not exceptions.
Anything in your report that treats them as errors is wrong. Verified
behavior, on a SQL batch:

| Situation | Outcome |
| --- | --- |
| Empty table, `expect_column_values_to_not_be_null` | `success=True`, `element_count: 0` — vacuously true |
| Empty table, `expect_column_mean_to_be_between` | `success=False`, `{"observed_value": None}` |
| Empty table, `expect_table_row_count_to_be_between(min_value=1)` | `success=False`, `{"observed_value": 0}` |
| All-null column, `expect_column_values_to_not_be_null` | `success=False`, 100% unexpected |
| All-null column, `expect_column_values_to_be_between` | `success=True` — nulls count as missing, not as violations |
| All-null column, `expect_column_mean_to_be_between` | `success=False`, `{"observed_value": None}` |

Two of these mislead if reported literally:

- **`{"observed_value": None}` is a populated result**, so the discriminator
  above correctly classifies it as a data failure rather than a metric error.
  But it does not mean the mean was out of range — it means there were no
  non-null values to compute over. Say that, and say which column.
- **A value-level check passing over an all-null column is not reassurance.**
  Nulls are excluded from the unexpected count, so a range check over a column
  of nothing but nulls succeeds. If the user's real question was whether the
  column has usable data, pair it with a non-null check and say why.

### Summarize honestly

`result.describe()` returns a JSON string carrying overall `success`, a
`statistics` block (`evaluated_expectations`, `successful_expectations`,
`unsuccessful_expectations`, `success_percent`), and a per-expectation list of
`expectation_type` / `kwargs` / `success` / `result`. It is a good basis for a
written summary — but it does not distinguish a metric error from a data
failure. Use the loop above for that distinction and `describe()` for the
counts.

Report, per expectation: what was checked, on which column, and what happened
— passed, failed with the observed numbers, or could not run with the cause.
Then the totals. Do not present a metric error inside the failure count as
though the data had been judged.

## Step 6 — Persistence, and write-out when in memory

**In a file-backed project the suite is already saved.** Registering it in
step 4 wrote it to `<context_root>/expectations/<suite_name>.json`, and every
subsequent `add_expectation` was written through as it happened. There is no
save step to run and none to forget. Confirm it concretely: name the suite,
name the file, and say that a fresh session picks it up with
`context.suites.get("<suite_name>")`.

**Validation results are not persisted by this flow.** `batch.validate()`
returns the result to you and writes nothing to the project. The suite is the
durable artifact; the report you give the user is the record of this run. Say
so rather than letting them assume the results are filed somewhere.

**In an in-memory session, nothing survives the process.** A second in-memory
session sees no suites and no data sources at all. Say this plainly — it is a
supported way to work, not a degraded one — and **offer to write the session
out** to a real project, per `references/write-out.md`. That procedure covers
the suite along with the data source, asset, and batch definition it depends
on; writing out a suite without them leaves a project that cannot run it.
Offer it; don't do it unprompted, and don't pick the location.

## Worked example

A file-backed project that already holds a verified batch definition over an
`orders` table. The user asked for two things: customer must never be missing,
and amounts must never be negative.

```python
import great_expectations as gx

context = gx.get_context(cloud_mode=False)          # step 1, per references/preflight.md

batch_definition = (                                 # step 2, from what already exists
    context.data_sources.get("warehouse")
    .get_asset("orders")
    .get_batch_definition("all_rows")
)
batch = batch_definition.get_batch()

# step 3: both descriptions matched catalog entries; nothing else was invented
if "orders_quality" in {suite.name for suite in context.suites.all()}:
    suite = context.suites.get("orders_quality")     # step 4: register/fetch first
else:
    suite = context.suites.add(gx.ExpectationSuite(name="orders_quality"))

suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0))

result = batch.validate(suite)                       # step 5

for each in result.results:
    config = each.expectation_config
    if each.success:
        print(f"PASS  {config.type} {config.kwargs}")
    elif not each.result:
        for _metric_id, info in each.exception_info.items():
            print(f"ERROR {config.type} {config.kwargs}: {info['exception_message']}")
    else:
        print(f"FAIL  {config.type} {config.kwargs}: {each.result}")
```

Against a table of four rows where one `customer` is null and one `amount` is
`-5.0`, that prints:

```text
FAIL  expect_column_values_to_not_be_null {'batch_id': 'warehouse-orders', 'column': 'customer'}: {'element_count': 4, 'unexpected_count': 1, 'unexpected_percent': 25.0, 'partial_unexpected_list': [None], ...}
FAIL  expect_column_values_to_be_between {'batch_id': 'warehouse-orders', 'column': 'amount', 'min_value': 0.0}: {'element_count': 4, 'unexpected_count': 1, 'unexpected_percent': 25.0, 'partial_unexpected_list': [-5.0], ...}
```

This two-expectation suite happens to come back in the order it was built —
which is exactly why the loop reads each result's own
`expectation_config` rather than trusting the position. Report it to the user
as *one of four rows has no customer, and one amount is negative (-5.0)*; the
`partial_unexpected_list` is what makes a finding actionable, so relay it.

## Where this flow ends

The saved, run, reported suite is the end state. Three things sit outside it:

- **Setting up data access.** If the precondition in step 2 fails, that is
  the `gx-configure-data-source` skill's work, not something to improvise
  around.
- **Proposing expectations from the data.** The user describes; this flow
  builds. See step 3.
- **Rendering results anywhere but this conversation.** Report what the run
  found; do not build reporting surfaces the user did not ask for.

## References

- `references/preflight.md` — establishing and announcing the session context.
- `references/expectation-catalog.md` — locating the shipped catalog, matching
  a described check against it, reading parameters, and what to do when
  nothing matches.
- `references/robustness.md` — the time-budget wrapper, scope-reduction
  levers, and how to report a failure helpfully.
- `references/write-out.md` — turning an in-memory session into a real
  project.
