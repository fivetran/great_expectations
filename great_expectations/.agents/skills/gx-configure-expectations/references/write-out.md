# Writing an in-memory session out to a project

An in-memory (ephemeral) session, per `preflight.md`, holds everything only in
process memory — data sources, assets, batch definitions, and expectation
suites all disappear when the process ends. This procedure turns that session
into a real, file-backed project so the work survives and is reusable outside
this conversation.

Offer this at a natural point — after a data source and batch definition are
verified working, or after a suite has been built and run — not as an
unprompted interruption mid-task. Only do it when the user agrees.

## Confirm a target directory first

Never guess a location. Ask the user where the project should live (an
absolute path is safest), and confirm it back before writing anything.

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

The datasource step follows the same fetch-first-on-`LookupError` shape as
the asset and batch-definition steps below it — that's what makes it safe to
run once, unconditionally, without wiping a datasource that's already there.
List it exactly once, before any asset step, even when the session created
several assets on it:

```python executable
import great_expectations as gx

# 1. Open (or create) the file-backed project at the confirmed location.
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

## Report the written location

When it completes, tell the user the absolute path that was written to, and
name what landed there (data source names, asset names, batch definition
names, suite names). Don't just say "done" — the point of write-out is that
the user can go find these files.

## What "usable without modification" means, and its one exception

Everything written out this way is a standard project artifact: a fresh
`gx.get_context(mode="file", project_root_dir=...)` against that directory
loads the same data sources, assets, batch definitions, and suites, and
`batch_definition.get_batch()` and `batch.validate(suite)` work exactly as
they did in the original session — with one exception.

**Dataframe assets carry no data.** An in-memory dataframe (a pandas
`DataFrame` passed as the asset's data) is never serialized to disk — only the
asset's *configuration* is written out. After write-out, and in every future
session, retrieving a batch from a dataframe asset still requires passing the
dataframe explicitly at call time:

```python executable
batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
```

State this to the user when a dataframe asset is part of what got written
out — it's easy to assume the data went with the config, and it didn't.

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
