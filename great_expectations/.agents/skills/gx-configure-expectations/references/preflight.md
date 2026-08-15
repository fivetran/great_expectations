# Session preflight

Before configuring anything, establish what you're operating on: a project the
user already has on disk, or a temporary in-memory session. Do this exactly
once at the start of the flow, and tell the user the outcome before you do
anything else.

## Enter with `cloud_mode=False`

Call the context factory like this, not with a bare call:

```python executable
import great_expectations as gx

context = gx.get_context(cloud_mode=False)
```

A managed cloud offering that this factory can auto-connect to has been
retired. If a machine still carries leftover configuration for it (environment
variables, or a leftover config file), a bare `gx.get_context()` — and
`cloud_mode=True` — will detect that configuration, try to honor it, and raise
immediately with an error to that effect. That failure has nothing to do with
the user's local project or data; it's a stale-environment problem, and it
would happen before you ever got to look at a local project. Passing
`cloud_mode=False` explicitly skips that detection and always resolves to a
local file-backed project if one is found, or an in-memory session otherwise.

**Check for stale cloud configuration yourself before you call it**, because
`cloud_mode=False` silently discards that configuration rather than reporting
it — there is no signal in the return value or in normal output that it was
there. Look for `GX_CLOUD_ACCESS_TOKEN`, `GX_CLOUD_ORGANIZATION_ID`, or
`GX_CLOUD_BASE_URL` in the environment. If any are set, tell the user plainly:
those variables were found but ignored, because that offering is no longer
reachable and today they should either unset them or ignore this message —
they have no effect on the session you're about to build.

## Interpret what comes back

`gx.get_context(cloud_mode=False)` returns one of two things. Branch on the
type:

```python executable
from great_expectations.data_context import FileDataContext

if isinstance(context, FileDataContext):
    context_root = context.root_directory
    # tell the user: "Using the existing project's configuration at
    # <context_root>."
else:
    # tell the user: "No project found — working in a temporary, in-memory
    # session. Nothing here is saved until it's written out to a project
    # (see write-out.md)."
    ...
```

**A discovered project is not optional to announce.** Always state
`context_root` back to the user before doing anything else, so they know
exactly which project they're about to modify — this also makes
`add_or_update_*` updates against that project legible rather than a surprise.
Name it precisely as the project's *configuration directory*, not "the
project" on its own — `context_root` is the `gx` subdirectory that holds
`great_expectations.yml` and the stores, and its **parent** is the project
directory a user would think of as "the project". That parent is what
`project_root_dir` means everywhere it's accepted (`preflight.md`'s own
one-liner below, and `write-out.md`'s `gx.get_context(mode="file",
project_root_dir=...)`). Never feed `context_root` back in as a
`project_root_dir` — doing so nests a second `gx` directory inside the first
(`<project>/gx/gx`) instead of reopening the same project.

**An in-memory (ephemeral) session is not a degraded mode to apologize for.**
It's a normal, fully supported way to work — state plainly that the session is
temporary and that everything can be written out to a real project later (see
`write-out.md`). Do not stop, and do not treat the absence of a project as an
error condition.

## Never scaffold a project yourself

Standing up a new file-backed project is the user's decision, not something
to do on their behalf or without being asked. Two things follow from this:

- Never call the file-context constructor without an explicit target
  directory. Concretely: never call `gx.get_context(mode="file")` with no
  `project_root_dir` — it does not raise or refuse when a project isn't found
  at that implicit location; it silently creates one, into the current
  working directory, with no confirmation. That is not something to do without
  the user asking for it.
- If a user wants a new project created rather than an in-memory session, give
  them the one-liner to run themselves and let them choose the location:

  ```python
  context = gx.get_context(mode="file", project_root_dir="<path>")
  ```

  Do not walk them through it interactively or pick the path for them.

This applies during preflight. It does not apply to the write-out procedure in
`write-out.md`, which also calls `gx.get_context(mode="file", ...)` — there,
the target directory has already been confirmed with the user as an explicit
step, so the call is expected and disclosed rather than a silent side effect.

## Never treat "no project" as a stop condition

An in-memory session is a supported, first-class outcome of preflight,
covered above. Do not stop, refuse, or ask the user to go create a project
first just because discovery didn't find one — proceed with the ephemeral
session instead.

## When discovery itself fails

Two failure shapes are worth knowing by name, because neither produces an
obvious, self-explanatory error, and both are easy to misread as "no project
found" when they're actually a misconfiguration worth surfacing:

**A stale `GX_HOME` environment variable.** If `GX_HOME` points at a directory
that either doesn't exist or doesn't contain a project config file, project
discovery does *not* raise — it silently falls back to the in-memory session,
exactly as if `GX_HOME` had never been set. If the user believes they have a
project and you get an in-memory session instead, this is the first thing to
check. Validate it yourself, since the factory won't:

```python executable
import os
from pathlib import Path

gx_home = os.environ.get("GX_HOME")
if gx_home is not None:
    gx_home_path = Path(gx_home).expanduser()
    if not (gx_home_path / "great_expectations.yml").is_file():
        # tell the user: "GX_HOME is set to <gx_home>, but no project config
        # was found there. If you expected an existing project to be used,
        # check the path — otherwise this variable can be ignored/unset."
        ...
```

**Stale cloud configuration**, covered above — check for it before calling
the factory, since the factory itself won't tell you it was there.

In both cases, the same shape of report applies: state what looked
misconfigured, state which value or file caused it, and give one concrete next
step (fix the path, unset the variable, or proceed with the in-memory
session). Never let a silent fallback pass as "everything's fine" when the
environment suggests the user expected otherwise.
