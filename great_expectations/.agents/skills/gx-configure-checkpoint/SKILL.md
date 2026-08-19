---
name: gx-configure-checkpoint
description: Turn a working batch definition and expectation suite into a persisted, re-runnable checkpoint with post-run actions — bind them into a validation definition, group into a named checkpoint, verify it by running it once, and hand off a scheduler-agnostic run snippet. Use when a user wants their checks to survive the session ("make this re-runnable", "schedule this", "notify us when this fails", "update our Data Docs after a run"), or when validation results were printed once and never saved.
license: Apache-2.0
---

# Configure a Great Expectations checkpoint

This skill takes a user from "here is a suite that already validated my data"
to a **persisted, re-runnable checkpoint** — a named, saved grouping of one or
more validation definitions plus the actions that should fire after a run —
verified by actually running it once.

Two objects, each built on work an earlier skill already did:

- A **validation definition** binds one batch definition to one expectation
  suite: the specific slice of data, and the specific checks to run against
  it.
- A **checkpoint** is the named, persisted grouping of validation definitions
  plus the post-run actions to fire — notifications, a Data Docs update — run
  as one operation.

Everything here goes through Great Expectations' public configuration API and
produces ordinary project artifacts. Nothing depends on this skill being
present afterwards — the checkpoint this flow builds runs from a plain Python
script outside any agent session, which is the point of it.

## The flow

1. **Preflight** — find out which project (or in-memory session) you are
   operating on, and tell the user. See `references/preflight.md`.
2. **Check the precondition** — at least one expectation suite and one
   working batch definition must already exist. If either is missing, hand
   off and stop.
3. **Bind** — pair batch definitions and suites into validation definitions.
4. **Group and add** — collect validation definitions into a named checkpoint
   with post-run actions, chosen from `references/action-catalog.md`,
   persisting it explicitly as part of the same step.
5. **Never rely on the run call to persist it for you** — step 4's explicit
   add is what makes that safe; see why below.
6. **Verify** by running once, and report per-validation-definition and
   per-expectation outcomes.
7. **Confirm persistence**, and offer write-out when the session is in
   memory.
8. **Hand off** a run snippet that re-runs the checkpoint from outside this
   session — see `references/run-and-schedule.md`.

Steps 2 and 5, and the fetch-first rule below, are where this flow fails
destructively rather than loudly if skipped or reordered. Do not skip step 6
either — a checkpoint that was never run is not a verified result.

## What this skill will not do without being asked

<!-- consent-gate: install -->
- **Install, upgrade, or remove a package, or otherwise modify the
  interpreter, virtual environment, environment variables, or shell state.**
  Not in response to an error, not preemptively while checking whether
  something is present, and not by announcing an intention to install with a
  chance to decline attached — none of those is the user asking. When
  something is missing, name it and hand over the command; running it is a
  separate act that starts only from the user's own instruction, later.
<!-- consent-gate: project -->
- **Create a project directory on the user's disk.** Only after the user has
  agreed to write the session out and named where.
<!-- consent-gate: config-file -->
- **Edit an existing project's `great_expectations.yml`.** Only after telling
  the user what the edit does and getting a yes.
<!-- consent-gate: saved-file -->
- **Write a file to the user's disk that the user did not ask for and
  locate.** Offer it in the conversation first.

## Step 1 — Preflight

Follow `references/preflight.md` in full before touching anything. It
establishes whether you are working against a project on disk or an
in-memory session, tells you what to announce to the user, and covers the
environment problems that silently masquerade as "no project found".

The outcome you carry forward is a `context` object and one fact: whether the
session is file-backed or in memory. Both are fully supported paths, and the
difference matters again at step 7.

## Step 2 — The precondition: a suite and a working batch definition

A checkpoint has nothing to run without both a batch definition to read data
through and an expectation suite to check it with. **There is no acceptable
way to improvise either one here** — do not build a suite from a guess at
what the data looks like, and do not construct a batch definition by hand.

Enumerate what the session already has:

```python
def existing_suites_and_batch_definitions(context):
    suite_names = [suite.name for suite in context.suites.all()]
    batch_definitions = []
    for datasource in context.data_sources.all().values():
        for asset in datasource.assets:
            for batch_definition in asset.batch_definitions:
                batch_definitions.append((datasource.name, asset.name, batch_definition.name))
    return suite_names, batch_definitions
```

**If either list comes back empty, stop and route:**

- No batch definition → hand off to `gx-configure-data-source`.
- No expectation suite → hand off to `gx-configure-expectations`.
- Neither exists → lead with the data source, since a suite is built against
  a batch and there is nothing to build one against yet.

This is a hard stop, not a suggestion — say plainly what's missing, name the
skill that builds it, and end this flow. Do not carry on and do not
improvise a workaround.

If enumerating what exists, or running the checkpoint in step 6, turns up a
missing driver or client library, report it and hand over the install command
per the standing rule above. Do not install it yourself — not now, before
anything has failed, and not later without the user's own go-ahead.

If more than one suite or batch definition is available, name them and let
the user choose which pairs to bind — guessing which check should run
against which slice of their data is not a decision to make for them.

## Step 3 — Bind: one validation definition per pair

A validation definition needs its suite already persisted in the working
context. **Building one against a suite the context has never seen raises,**
not silently loses work the way an unregistered suite does elsewhere in this
skill family:

```python
from great_expectations.core import ExpectationSuite, ValidationDefinition

unsaved_suite = ExpectationSuite(name="not_saved_yet")
# ValidationDefinition(name="x", data=batch_definition, suite=unsaved_suite)
# ctx.validation_definitions.add(...) on this raises ResourceFreshnessAggregateError:
# "ExpectationSuite 'not_saved_yet' must be added to the DataContext before it
# can be updated. Please call `context.suites.add(<SUITE_OBJECT>)`..."
```

So always fetch the suite (and the batch definition) from the context rather
than closing over an object from earlier in the conversation that might not
be the one actually persisted:

```python
from great_expectations.core import ValidationDefinition

VALIDATION_DEFINITION_NAME = "orders_quality_check"

datasource = context.data_sources.get("warehouse")
asset = datasource.get_asset("orders")
batch_definition = asset.get_batch_definition("by_month")
suite = context.suites.get("orders_quality")

existing = {vd.name for vd in context.validation_definitions.all()}
if VALIDATION_DEFINITION_NAME in existing:
    validation_definition = context.validation_definitions.get(VALIDATION_DEFINITION_NAME)
else:
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(
            name=VALIDATION_DEFINITION_NAME, data=batch_definition, suite=suite
        )
    )
```

Membership is checked through `.all()` rather than a fetch-and-except, the
same reason `references/write-out.md` uses it for these two object types:
`validation_definitions.get()` on a miss raises `DataContextError`, which is
not a `LookupError` — the `except LookupError` idiom from the data-source
skill does not transfer here. Name it in prose, and never import it.

Repeat this once per (batch definition, suite) pair the user wants bound.
Reusing an already-bound pair under the same name is safe — the fetch above
returns it unchanged.

## Step 4 — Group: build the checkpoint, and add it

```python
from great_expectations.checkpoint import Checkpoint
from great_expectations.checkpoint.actions import UpdateDataDocsAction

CHECKPOINT_NAME = "orders_checkpoint"

existing_checkpoints = {c.name for c in context.checkpoints.all()}
if CHECKPOINT_NAME in existing_checkpoints:
    checkpoint = context.checkpoints.get(CHECKPOINT_NAME)
else:
    checkpoint = context.checkpoints.add(
        Checkpoint(
            name=CHECKPOINT_NAME,
            validation_definitions=[validation_definition],
            actions=[UpdateDataDocsAction(name="update_data_docs")],
        )
    )
```

**This is the explicit add step 5 below is about — the create branch calls
`context.checkpoints.add(...)` directly, so `checkpoint` is a persisted
object on both branches before anything runs.** Get the two branches from
step 3's pattern above if adapting this by hand: fetch on a name that already
exists, build-and-add on one that doesn't. Never construct a bare
`Checkpoint(...)` and hold onto it without one of these two calls — that is
exactly the unpersisted object step 5 exists to warn about.

Ask what should happen after a run — a Slack or Teams message, an email, a
Data Docs rebuild, one of the less common actions — before assuming none is
wanted. `references/action-catalog.md` covers every attachable action: its
fields, which four carry a public-API stability guarantee and which four
don't, and how to word each one's credential requirements.

<!-- consent-gate: config-file -->
**Before attaching a Data Docs update action, check whether the project has a
site to write to.** File-backed projects and in-memory sessions both carry a
working default site; `references/action-catalog.md` covers both, and one
project state that doesn't: `great_expectations.yml` can hold
`data_docs_sites: null`, under which every site-management call silently
does nothing — no error, no site, no sign anything went wrong. The reference
gives the fix, and it edits the user's `great_expectations.yml`, so **ask
before running it.** Finding `data_docs_sites: null` is not, by itself,
permission to change it — state what you found and what the fix involves,
and wait for a yes. If the user declines, name the same fix as the path
forward and build the checkpoint without the action.

## The fetch-first rule: never `add_or_update` an existing checkpoint or validation definition to change it

`context.checkpoints.add_or_update(...)` and
`context.validation_definitions.add_or_update(...)` both persist the
**incoming** object with the stored object's id transplanted onto it — a
whole-object replacement, not a merge. For a checkpoint, the replacement
**cascades**: a fresh validation-definition object passed in as part of the
incoming checkpoint is itself `add_or_update`-ed, and that in turn
`add_or_update`s its own suite. Verified directly, isolating exactly what
that cascade does and does not touch:

| | outcome |
| --- | --- |
| **Always lost** | the checkpoint's validation-definition membership **and its actions** — replaced wholesale by whatever the incoming object listed |
| **Conditionally lost** | a bound suite's *contents* — only when a **fresh** suite object is passed under an existing name; upserting with the suite you fetched from the context first leaves it untouched |
| **Never lost** | validation definitions already in the store — nothing here deletes one; a validation definition dropped from a checkpoint's membership is still fetchable afterward |

Be precise about this when you talk to a user: *"you'll lose this
checkpoint's action list and which validation definitions it groups"* is
accurate; *"your other validation definitions will be deleted"* is not, and
overstating the damage is as much a defect as understating it.

**`get` → mutate → `save` avoids the cascade entirely.** To change an
existing checkpoint's actions, or which validation definitions it groups,
fetch it, mutate the field, and save the same object back — never rebuild it
from scratch and hand it to `add_or_update`:

```python
checkpoint = context.checkpoints.get(CHECKPOINT_NAME)
checkpoint.actions = checkpoint.actions + [UpdateDataDocsAction(name="update_data_docs")]
checkpoint.save()
```

`add_or_update` is not banned outright — it is the right call the one time a
user explicitly wants a checkpoint's whole contents replaced, and only after
you have told them exactly what that discards, per the table above.

## Step 5 — Why step 4 added explicitly, before running

**Never construct a bare `Checkpoint(...)` and hand it straight to `.run()`
without going through the `context.checkpoints.add(...)` /
`context.checkpoints.get(...)` branches in step 4, even though it would
work.** `Checkpoint.run()` auto-persists an unsaved checkpoint whose
validation definitions and suites are themselves already saved — verified
directly: a `Checkpoint` object built and run without ever being added to
the context shows up in `context.checkpoints.all()` immediately afterward,
with no error and no warning that it happened implicitly. That is exactly
why step 4 is written to add explicitly rather than left to be discovered as
unnecessary: skipping it still produces a persisted checkpoint, so nothing
about the flow fails to teach you that the explicit step was needed.
Persistence is something step 4 does on purpose, not a side effect of the
verification run in step 6.

## Step 6 — Verify by one run, and report by identity

```python
result = checkpoint.run(batch_parameters={"dataframe": df})
```

Run this inside the duration-tracked wrapper in `references/robustness.md`,
exactly as the data-source and expectations skills do — a checkpoint can
touch as much data as every validation definition it groups, combined. If the
run fails because a driver or client library is missing, hand over the
install command and stop — do not install it to get the run passing.
`references/run-and-schedule.md` covers what `batch_parameters` actually
does across multiple validation definitions, including a real trap when more
than one of them is dataframe-backed, and why numeric window parameters are
integers on every datasource family.

**Pair each outcome to the validation definition it came from by identity,
never by position:**

```python
for vr_id, vr in result.run_results.items():
    print(f"validation definition: batch={vr_id.batch_identifier} suite={vr.suite_name}")
    for each in vr.results:
        config = each.expectation_config
        if each.success:
            print(f"  PASS {config.type} {config.kwargs}")
        elif not each.result:
            for _metric_id, info in each.exception_info.items():
                print(f"  ERROR {config.type} {config.kwargs}: {info['exception_message']}")
        else:
            print(f"  FAIL {config.type} {config.kwargs}: {each.result}")
```

The same infra-vs-data discriminator from the expectations skill applies at
this level too: `success is False` with an **empty** `result` is a metric
error — a broken column or query, not a finding about the data — while a
populated `result` (even one carrying `observed_value: None`, which empty
tables and all-null columns produce routinely) is a real outcome to report as
such. `references/robustness.md` has the full rules for translating either
case into something a user can act on; do not report a metric error as
"your data failed this check."

Report the overall `result.success`, then each validation definition's own
outcome, then each expectation within it — not just a total pass/fail count.
`result.describe()` (the summary method that is `@public_api`) gives the
same information as a formatted JSON string, useful for a short written
recap, but it does not label its entries by name — use the loop above, not
`describe()`, whenever the report needs to say *which* validation definition
an outcome belongs to.

## Step 7 — Confirm persistence, offer write-out

**In a file-backed project, the checkpoint and its validation definitions
are already saved** — the explicit adds in steps 3 and 4 wrote them.
Confirm this concretely: name the checkpoint, name the validation
definitions it groups, and say that a fresh session picks it up with
`context.checkpoints.get("<name>")`.

<!-- consent-gate: project -->
**In an in-memory session, none of it survives the process.** Say this
plainly, and **offer to write the session out** — data sources through
checkpoints — to a real project, per `references/write-out.md`. That
procedure extends past suites to validation definitions and checkpoints,
re-created in the target project only after everything they reference is
already there. Offer it; don't do it unprompted, and don't pick the
location. The offer ends this flow the same way it does in the earlier
skills: write-out is a separate run, starting only after the user has agreed
and named a directory — never in the same program as the steps above.

## Step 8 — Hand off the run snippet

The checkpoint is only re-runnable outside this conversation if there is a
concrete way to re-run it. Give the user a small, self-contained script that
loads the project by an absolute path and re-runs the checkpoint by name —
see `references/run-and-schedule.md` for the exact template, why each of its
choices is deliberate, and the one case (a dataframe-backed validation
definition) where it doesn't apply as written.

<!-- consent-gate: saved-file -->
**Offer to save it to a file at a path the user confirms; never write it
unasked.**
Present it in the conversation first. Wiring it into an actual schedule — a
cron entry, an Airflow DAG, a CI job — is the user's orchestrator's job, not
this skill's; say that plainly if asked, and hand over the snippet as the
piece their scheduler needs to call.

## Worked example

A file-backed project already holds a verified `orders` batch definition,
partitioned monthly, and an `orders_quality` suite built and run earlier by
the other two skills.

```python
import great_expectations as gx
from great_expectations.core import ValidationDefinition
from great_expectations.checkpoint import Checkpoint
from great_expectations.checkpoint.actions import UpdateDataDocsAction

context = gx.get_context(cloud_mode=False)                    # step 1

# step 2: both preconditions already exist -- proceed
datasource = context.data_sources.get("warehouse")
asset = datasource.get_asset("orders")
batch_definition = asset.get_batch_definition("by_month")
suite = context.suites.get("orders_quality")

VALIDATION_DEFINITION_NAME = "orders_quality_check"           # step 3
existing_vds = {vd.name for vd in context.validation_definitions.all()}
if VALIDATION_DEFINITION_NAME in existing_vds:
    validation_definition = context.validation_definitions.get(VALIDATION_DEFINITION_NAME)
else:
    validation_definition = context.validation_definitions.add(
        ValidationDefinition(
            name=VALIDATION_DEFINITION_NAME, data=batch_definition, suite=suite
        )
    )

CHECKPOINT_NAME = "orders_checkpoint"                          # step 4
existing_checkpoints = {c.name for c in context.checkpoints.all()}
if CHECKPOINT_NAME in existing_checkpoints:
    checkpoint = context.checkpoints.get(CHECKPOINT_NAME)
else:
    checkpoint = context.checkpoints.add(                       # step 4: explicit add
        Checkpoint(
            name=CHECKPOINT_NAME,
            validation_definitions=[validation_definition],
            actions=[UpdateDataDocsAction(name="update_data_docs")],
        )
    )

result = checkpoint.run(batch_parameters={"year": 2024, "month": 3})  # step 6

for vr_id, vr in result.run_results.items():
    print(f"{vr_id.batch_identifier} / {vr.suite_name}: success={vr.success}")
    for each in vr.results:
        config = each.expectation_config
        status = "PASS" if each.success else ("ERROR" if not each.result else "FAIL")
        print(f"  {status} {config.type} {config.kwargs}")
```

Against a month where one order has no customer, that prints:

```text
warehouse-orders-year_2024-month_3 / orders_quality: success=False
  FAIL expect_column_values_to_not_be_null {'batch_id': 'warehouse-orders-year_2024-month_3', 'column': 'customer'}
```

Report to the user: the checkpoint `orders_checkpoint` is saved, groups one
validation definition (`orders_quality_check`, over the March 2024 window),
ran once, and found one failure — a missing customer on one row. Then move
to step 7's persistence confirmation and step 8's run-snippet handoff.

## Where this flow ends

The persisted, run, reported checkpoint — with its run snippet handed off —
is the end state. Two things sit outside it:

- **Building the suite or batch definition it groups.** If step 2's
  precondition fails, that is `gx-configure-expectations` or
  `gx-configure-data-source`'s work, not something to improvise around.
- **Wiring the run snippet into an actual cadence.** That's the user's
  orchestrator's job — see `references/run-and-schedule.md`.

## References

- `references/preflight.md` — establishing and announcing the session
  context.
- `references/action-catalog.md` — every attachable post-run action, its
  fields, the public-API stability split, and enabling Data Docs.
- `references/run-and-schedule.md` — `batch_parameters` semantics across
  multiple validation definitions, integer window parameters and the
  deprecation of digit strings, the run snippet, and where scheduling
  guidance stops.
- `references/robustness.md` — the time-budget wrapper, scope-reduction
  levers, and how to report a failure helpfully.
- `references/write-out.md` — turning an in-memory session into a real
  project, extended through validation definitions and checkpoints.
