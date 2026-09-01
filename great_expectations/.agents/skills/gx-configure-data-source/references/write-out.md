# Writing an in-memory session out to a project

An in-memory (ephemeral) session, per `preflight.md`, holds everything only in
process memory — data sources, assets, batch definitions, and expectation
suites all disappear when the process ends. This procedure turns that session
into a real, file-backed project so the work survives and is reusable outside
this conversation.

Offer this at a natural point — after a data source and batch definition are
verified working, or after a suite has been built and run — not as an
unprompted interruption mid-task. Only do it when the user agrees.

## The gate: two things the user has to have said

<!-- consent-gate: project -->
This procedure creates a project on the user's disk.
`gx.get_context(mode="file", project_root_dir=...)` **creates** the project at
that path when one isn't already there. It does not refuse, does not prompt,
and its return value looks identical either way — there is no signal
afterwards distinguishing a project it opened from one it just brought into
existence. Whatever path you pass is where a project appears.

So before the first line of the procedure runs, two things have to be true,
and both are things the **user said**, not things you concluded:

1. They agreed to write the session out.
2. They named the directory it should go in.

Neither is satisfied by inference. A request to "add a data source", "set this
up", or "get this working" is a request about data access — it is not
agreement to create a project, and it does not name a location. If the session
is in memory and you are holding one of those requests, the correct end state
is the in-memory result, reported, with write-out **offered**. An absolute
path is safest; confirm it back before writing anything.

**If you cannot point to the user's message where they agreed, and the one
where they named the path, you are not past the gate.** Ask, and end your turn
there.

### The gate is skipped by construction, not by decision

The way this goes wrong is rarely a considered choice to skip the
confirmation. It is a script: the configure steps, the probe, and this
procedure assembled into one program and run in a single step. Batched that
way there is no moment at which the user could have answered — the gate is not
declined, it simply never occurs, and the project exists by the time anyone
reports anything.

**Write-out is its own run, and it begins after a user's reply.** If the call
below is sitting in the same program as the configure and verify calls, that
program skips the gate no matter what the surrounding prose says. Split it out.

### Why this is the only place to catch it

A project created without asking cannot be detected later. On the next turn —
and in every session after it — discovery finds the directory and truthfully
reports an existing project at that path, exactly as it would report one the
user made themselves. Nothing marks it, nothing records where it came from,
and no later step has anything to notice. Nobody downstream is going to catch
this for you.

## The procedure: public factories, not the built-in migrator

Great Expectations ships a method that converts an in-memory context to a
file-backed one in place. Do not use it here. It resolves the target directory
from the current working directory rather than from an explicit path, it has
a known store-migration ordering issue, and its merge behavior does not
reliably overwrite objects that already exist at the destination — none of
which is acceptable when the target directory and the correctness of the
result both matter. Instead, build the file-backed project explicitly and
re-create each object in it through the same update-safe public factories used
everywhere else in this skill. That gives you a small, fully disclosed
sequence of steps, each independently retryable.

**`add_or_update_<datasource>` replaces the datasource wholesale — it is not
additive.** Calling it drops every asset and batch definition already
attached to that datasource, including ones that came from outside this
session: a prior conversation, a teammate, an earlier write-out. Opening a
project that already has a datasource with the name you're about to write and
calling `add_or_update_pandas` (or any `add_or_update_<datasource>` factory)
under that same name silently destroys every other asset already on it — this
is true the very first time it's called in this project, not just on a
repeat. **Check whether the datasource already exists first, and skip adding
it if it does.** Only call `add_or_update_*` again if you specifically intend
to replace that datasource's connection configuration, and if so, warn the
user first that doing so will drop every other asset already attached to it.

Build the file-backed project and re-create each object with the pattern
below. Wrap each object in its own try rather than the whole procedure in one
try block, and keep a running record of what succeeded and what didn't. The
asset step needs the datasource handle, and the batch-definition step needs
the asset handle — a zero-arg step that doesn't reflect this can't express
the chain. Have each step **re-fetch its dependency by name** from
`file_context` instead of closing over a variable from an earlier step: that
gets you the same handle without needing an earlier step to have succeeded in
the same function scope, and it makes failures cascade correctly — if the
datasource step failed, the asset step's own fetch of it fails too, with a
reason that points back at the real cause instead of a confusing `NameError`.
The same chain extends further, past the suite step, to validation
definitions and checkpoints — covered below, once the base pattern is on the
table.

The datasource step follows the same fetch-first-on-`LookupError` shape as
the asset and batch-definition steps below it — that's what makes it safe to
run once, unconditionally, without wiping a datasource that's already there.
List it exactly once, before any asset step, even when the session created
several assets on it:

<!-- consent-gate: project -->
```python executable
import great_expectations as gx

# 1. Create the project at the location the user named. Past this line a
#    directory exists on their disk, so do not run it until the gate above is
#    satisfied: they agreed, and the path below is the one they gave.
file_context = gx.get_context(mode="file", project_root_dir="<confirmed_path>")

def _add_datasource():
    try:
        return file_context.data_sources.get("my_datasource")
    except LookupError:
        return file_context.data_sources.add_or_update_pandas(name="my_datasource")

def _add_asset():
    datasource = file_context.data_sources.get("my_datasource")
    try:
        return datasource.get_asset("my_asset")
    except LookupError:
        return datasource.add_dataframe_asset(name="my_asset")

def _add_batch_definition():
    asset = file_context.data_sources.get("my_datasource").get_asset("my_asset")
    try:
        return asset.get_batch_definition("my_batch_definition")
    except LookupError:
        return asset.add_batch_definition_whole_dataframe(name="my_batch_definition")

def _add_suite():
    # `suite` here is the same ExpectationSuite object (or an equivalent one)
    # built against the in-memory context earlier in the flow.
    return file_context.suites.add_or_update(suite)

steps = [
    ("data source my_datasource", _add_datasource),
    ("asset my_asset", _add_asset),
    ("batch definition my_batch_definition", _add_batch_definition),
    ("suite my_suite", _add_suite),
    # ... one entry per object to re-create: repeat the asset and
    # batch-definition pattern (each its own function, closing over its own
    # name) for every asset/batch definition created in the session, and the
    # suite pattern for every suite. List the datasource step only once, even
    # when the session created several assets on it.
]

written = []
failed = []
for label, step in steps:
    try:
        step()
        written.append(label)
    except Exception as e:
        failed.append((label, str(e)))
```

Note the fetch-first pattern in all three of the datasource, asset, and
batch-definition steps. `add_or_update_pandas` (and the other
`add_or_update_<datasource>` factories) and `suites.add_or_update` are
update-safe on their own — calling either again just replaces that one
object's own content, which is harmless in isolation — but as just covered,
`add_or_update_<datasource>` is not safe for what's attached underneath a
datasource, which is why the datasource step above fetches first too. There
is no `add_or_update_*` factory at all for a dataframe asset or a batch
definition — calling `add_dataframe_asset` or
`add_batch_definition_whole_dataframe` a second time with the same name
raises instead of updating. Fetching first and only adding on a `LookupError`
is what actually makes every step in this procedure safe to run again — not
the presence of `add_or_update_*` in some of the calls.

Report both lists to the user explicitly: what was written successfully, and
what wasn't, with the reason for each failure. If an earlier step failed, a
later step that depends on it will fail too — report that as a consequence of
the earlier failure, not as a second, unrelated problem. Because every step
fetches first, re-running the whole procedure after fixing the cause of a
failure is safe — nothing already written gets duplicated, corrupted, or (per
the warning above) destroyed by running it again.

### Continuing the chain: validation definitions and checkpoints

When the session also bound suites into validation definitions and grouped
those into a checkpoint, two more steps complete the chain — validation
definitions after suites, checkpoints last, and neither before the step it
depends on has actually succeeded. The `steps`/`written`/`failed` loop above
already ran, over the four entries it had at the time it ran — appending to
`steps` afterward would define a longer list that nothing goes on to loop
over again. So this is not an append: it replaces `steps` with the complete,
six-entry list and runs the loop over it again from scratch, calling
`_add_datasource` and the rest a second time. That's safe for the same
reasons re-running the four-step version above is safe: the datasource,
asset, and batch-definition steps fetch first; the suite step's
`add_or_update` replaces that one suite's content with the same session
suite it already wrote, which is a no-op the second time, not a second
destructive replacement; and the two new steps below fetch first as well. It
produces the one, complete disclosure covering all six objects, superseding
the four-object one above:

```python
from great_expectations.core import ValidationDefinition
from great_expectations.checkpoint import Checkpoint

# Labels of steps below that left an object already present alone, rather
# than creating it. Populated as a side effect of the two functions below,
# then used after the loop to separate "written" from "found".
found = []

def _add_validation_definition():
    # Re-fetch both dependencies from file_context — not from the in-memory
    # session — so the object being built is scoped to the target from the
    # start. `validation_definitions.add()` on an unpersisted suite is
    # exactly the ordering failure covered above.
    target_bd = (
        file_context.data_sources.get("my_datasource")
        .get_asset("my_asset")
        .get_batch_definition("my_batch_definition")
    )
    # Fetched by the session suite's own name, not by a literal: unlike the
    # datasource, asset and batch definition above -- which this procedure
    # creates under the names written here -- the suite arrives from the
    # session already named, and a literal that disagrees with it fails the
    # lookup. The loop below swallows that into `failed`, so the write-out
    # would finish silently short of a validation definition and a checkpoint.
    target_suite = file_context.suites.get(suite.name)
    # Existence is checked through all() rather than get()/except: unlike
    # LookupError on the earlier steps, a missing validation definition or
    # checkpoint surfaces as a data-context-level error that isn't part of
    # the public exception surface, so checking membership first keeps every
    # branch on add()/get()/all() instead.
    existing = {v.name for v in file_context.validation_definitions.all()}
    if "my_validation_definition" in existing:
        found.append("validation definition my_validation_definition")
        return file_context.validation_definitions.get("my_validation_definition")
    return file_context.validation_definitions.add(
        ValidationDefinition(
            name="my_validation_definition", data=target_bd, suite=target_suite
        )
    )

def _add_checkpoint():
    # `checkpoint` here is the same Checkpoint object (or an equivalent one)
    # built against the in-memory context earlier in the flow — the same
    # convention _add_suite uses for `suite` above.
    #
    # Rebuilt from the validation definition this procedure just added to
    # file_context — never from the session's original checkpoint or its
    # validation definitions. Carrying those over raises, and not for the
    # reason it looks like: the freshness check a checkpoint runs on each
    # validation definition's batch definition does not compare against the
    # handle's *origin* context. It resolves through the process-global
    # *active* context — whichever context creation, anywhere in this
    # process, made a context active most recently. Creating file_context
    # above made it that context, so every handle the original in-memory
    # session built now fails, not because it is "from a different context"
    # in some abstract sense, but because it is not the one context object
    # currently active (observed: CheckpointRelatedResourcesFreshnessError,
    # "BatchDefinition '...' has changed since it has last been saved").
    target_vd = file_context.validation_definitions.get("my_validation_definition")
    existing = {c.name for c in file_context.checkpoints.all()}
    if "my_checkpoint" in existing:
        found.append("checkpoint my_checkpoint")
        return file_context.checkpoints.get("my_checkpoint")
    return file_context.checkpoints.add(
        Checkpoint(
            name="my_checkpoint",
            validation_definitions=[target_vd],
            # Actions carry over unchanged — a plain field on the
            # Checkpoint being constructed, not something that needs
            # rebuilding like the validation definitions above.
            actions=list(checkpoint.actions),
        )
    )

steps = [
    ("data source my_datasource", _add_datasource),
    ("asset my_asset", _add_asset),
    ("batch definition my_batch_definition", _add_batch_definition),
    ("suite my_suite", _add_suite),
    ("validation definition my_validation_definition", _add_validation_definition),
    ("checkpoint my_checkpoint", _add_checkpoint),
    # ... one entry per object to re-create, following the same
    # repeat-per-object note as the four-step version above: the
    # validation-definition pattern once per (batch definition, suite) pair
    # the session bound, added only after its own suite step succeeded, and
    # the checkpoint pattern once per checkpoint, added only after every
    # validation definition it groups.
]

written = []
failed = []
for label, step in steps:
    try:
        step()
        written.append(label)
    except Exception as e:
        failed.append((label, str(e)))

# A step that found an object already present, rather than creating one, is
# not "written" by this run. Pull it out of `written` so the disclosure
# names exactly what changed and what didn't — see below.
written = [label for label in written if label not in found]
```

**Report three outcomes now, not two: written, found, and failed.** A
validation definition or checkpoint name can already be taken by an object
that has nothing to do with this session — a teammate's checkpoint, an
earlier write-out, anything already in the target project. The two functions
above refuse to overwrite it, which is the right call: it matches the
fetch-first, never-clobber shape of every other step, and an existing
checkpoint or validation definition under that name is left completely
alone. But refusing to overwrite and reporting "written" are different
things — if that were reported as written, the user would be told their
session's checkpoint landed when the object they will actually load and run
under that name is someone else's. Report `found` as its own list, distinct
from both `written` and `failed`: "already present, left as-is" is not a
failure, but it is not this run's work landing on disk either. If a name
collision on a validation definition or checkpoint is unwanted, that's a
naming conflict to resolve with the user, not something this procedure
resolves by overwriting.

This also reaches a checkpoint that *is* written — `_add_checkpoint` builds
it from whatever object `file_context.validation_definitions.get(...)`
returns, without regard to whether that get() came from the create branch or
the found branch just above it. So if the validation-definition step
reported `found`, the checkpoint step can still report `written`, and the
checkpoint just written groups someone else's validation definition, not the
session's. Report the two together when this happens, and resolve the name
with the user before anyone runs it — a `written` checkpoint is not
sufficient evidence that what it groups is the session's own.

Everything else about the disclosure contract carries over unchanged: a
validation definition that fails because its suite never landed is reported
as a consequence of the suite step's failure, not a second, unrelated
problem, and a checkpoint that fails because its validation definition never
landed is reported the same way.

**Why this order, restated as what actually failed above:** the observed
`ResourceFreshnessAggregateError` when a suite is not yet persisted, and the
observed `CheckpointRelatedResourcesFreshnessError` when a checkpoint is
built from a handle that belongs to a context other than the one currently
active, are two instances of the same rule — every object this procedure
adds has to be built from handles fetched from `file_context` after it
became the active context, never from a handle that belongs to the session
that started the procedure. Datasources, assets, and batch definitions come
first because nothing else can reference them without already being real;
suites come next for the same reason validation definitions need them;
validation definitions come before checkpoints because a checkpoint's
`validation_definitions` list is checked the same way.

## Report the written location

When it completes, tell the user the absolute path that was written to, and
name what landed there (data source names, asset names, batch definition
names, suite names, validation definition names, and checkpoint names).
Don't just say "done" — the point of write-out is that the user can go find
these files. If a validation definition or checkpoint name was already taken
by an unrelated object and this run left it alone (`found`, not `written`),
say that too, by name — the object under that name in the project is not the
one this session built, and the user needs to know that before they run it.

## What "usable without modification" means, and its one exception

For everything this run actually wrote, the result is a standard project
artifact: a fresh `gx.get_context(mode="file", project_root_dir=...)` against
that directory loads the same data sources, assets, batch definitions,
suites, validation definitions, and checkpoints, and
`batch_definition.get_batch()`, `batch.validate(suite)`, and
`checkpoint.run()` all work exactly as they did in the original session —
including firing every action on a rebuilt checkpoint, such as an
`UpdateDataDocsAction` updating the project's own Data Docs site. This
promise covers what was written, per the `written`/`found` distinction above
— an object reported as `found` is someone else's, and running it runs
whatever that object actually is, not the session's version. That includes a
`written` checkpoint whose validation definition came back `found`: it runs,
but against a validation definition that isn't the session's, per the
disclosure note above — resolve that name with the user before treating the
run as the session's own. One further exception applies even to what was
written:

**Dataframe assets carry no data.** An in-memory dataframe (a pandas
`DataFrame` passed as the asset's data) is never serialized to disk — only the
asset's *configuration* is written out. After write-out, and in every future
session, retrieving a batch from a dataframe asset still requires passing the
dataframe explicitly at call time:

```python executable
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
```

State this to the user when a dataframe asset is part of what got written
out — it's easy to assume the data went with the config, and it didn't. The
same caveat reaches any rebuilt checkpoint whose validation definitions run
against a dataframe asset: `checkpoint.run()` still needs
`batch_parameters={"dataframe": df}` passed at call time for that
validation definition, exactly as `get_batch()` does above — write-out
changes nothing about how that argument reaches it.

## Secrets after write-out: the environment-vs-file split

An in-memory session resolves `${ENV_VAR}`-style substitutions only from
process environment variables — it has no on-disk uncommitted config file to
read them from, because it has no disk footprint at all. A file-backed project
gains a second, additive source: an uncommitted config-variables file that
lives inside the project directory. Writing a session out to a project does
not change how any existing `${ENV_VAR}` reference resolves — it still comes
from the environment, exactly as before — but it does mean the user now has
the option to move any of those values into the project's uncommitted config
file for anyone else who works in that project without necessarily sharing
the same shell environment. Mention this as a follow-up option; do not do it
for them, and never write a resolved secret value into any file yourself —
only the `${ENV_VAR}`-style reference belongs in a persisted config.
