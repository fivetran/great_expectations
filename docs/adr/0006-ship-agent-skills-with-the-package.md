# 6. Ship agent skills with the package

Date: 2026-08-13

## Status

Accepted

## Context

Data practitioners increasingly configure and validate data through a coding
agent rather than by writing every line of Python themselves. An agent's
general programming knowledge does not tell it the current, correct sequence
of calls for a specific library: which factory method to call for a given
connection type, in what order a validation suite has to be registered before
expectations are added to it, or how to handle a secret without ever printing
it to the conversation. Left to infer this from the source or from
out-of-date training data, an agent produces plausible-looking code that is
subtly wrong at least as often as it produces working code, and a user who
does not already know the right pattern has no way to tell the two apart.

Closing that gap requires guidance that an agent can actually find and use.
That means it has to live where an agent's tooling already looks, in a form
the agent's platform already knows how to read, and it has to stay accurate
for whatever version of the library the user has installed — guidance
written against an API that has since changed is worse than no guidance,
because it is confidently wrong instead of visibly absent.

## Decision

We ship a set of "skills" — self-contained guidance documents for a coding
agent — as part of the `great_expectations` distribution, and give users a
command to place them where their agent looks for them.

**Format.** Each skill is a directory containing one entry document, plus
supporting reference material one directory level below it. This is an open
format, not something specific to Great Expectations: multiple coding-agent
tools already read directories shaped this way, so publishing skills in this
form makes them usable by every agent whose platform speaks the format,
without our writing a separate integration per agent. A proprietary or
single-vendor shape would have bought nothing for the additional maintenance
of yet another format, and would have worked with only one agent.

**Location.** The skill content lives inside the installed package itself,
not behind a URL the agent fetches at runtime and not something generated on
demand. The reason is version matching: the correct guidance for calling a
fluent factory method or registering a suite is a function of the exact
`great_expectations` release installed, and an install of the package is the
one artifact guaranteed to carry the version the guidance has to match. A
separately hosted copy can drift out of sync with any given install the
moment either one changes independently, silently handing an agent
instructions for an API surface that no longer matches what is on disk.
Shipping the content in the package ties its version to the code's version by
construction, so the normal act of installing or upgrading the package is
also what keeps the guidance current.

**Command surface.** The command to place the bundled skills into a project
is invoked as a module, `python -m great_expectations …`, rather than through
a new console-script entry point installed onto the user's `PATH`. Great
Expectations previously shipped a console-script command-line interface and
removed it. Reintroducing one — even a minimal one — brings back the
packaging-level machinery a console script requires and the platform-specific
quirks of `PATH`-installed executables (name collisions, `PATH` not being set
up in every environment a Python package is used from, different behavior
across virtual environments and editable installs), to serve what is, in
substance, an occasional local file-management step for a library that is
not a command-line application. `python -m` needs none of that: it uses the
same import machinery already required to use the library at all, so it
behaves identically in every environment where `import great_expectations`
already works.

**Install model.** The command places the bundled skills, by copying or on
request by linking, into the discovery directories a project's coding agent
reads — `.agents/skills` for Codex and Cursor, `.claude/skills` for Claude
Code and Cursor — alongside a small manifest recording what was installed and
a hash of its content. Several principles follow from treating the
destination as belonging to the user, not to the package:

- A destination that already holds exactly what would be installed is left
  completely alone. The manifest is what lets a repeat run tell "nothing to
  do" apart from "something changed" without guessing from the file contents
  alone, which is what makes the command safe to run again after every
  upgrade, or simply on the suspicion that it was never run at all.
- The tool never silently overwrites something it did not create. A
  directory with no record of having been installed by this package is left
  alone unconditionally — there is no option that overwrites it — because
  nothing in a directory it never wrote can be told apart from a user's own
  work.
- Once a directory carries that record, the tool can tell its own untouched
  copy apart from one the user has since edited, and refuses to replace the
  latter without an explicit override. A command meant to be safe to run
  again after every upgrade cannot also be a command that discards local
  edits as a side effect of checking for updates.
- An upgrade builds the replacement in full beside the destination and moves
  it into place, never rewriting files where they sit. A process that dies
  partway through therefore never leaves behind a skill with some files at the
  new version and some at the old — an agent reading a directory in that state
  would follow guidance that no single release ever actually shipped, which is
  worse than the outdated version it was replacing.

## Consequences

An agent whose platform reads this open format gets accurate, version-matched
guidance the moment the package is installed and the install command is run,
with no bespoke integration effort on our part and none required of the
agent's maintainers. The same content is available to any other tool that
scans installed packages for it, at no additional cost, because it sits at a
predictable path inside the package rather than behind custom retrieval
logic.

The guidance now has to be kept in step with the fluent API it describes, the
same way any other part of the package does, or it degrades into the exact
failure mode — instructions for an API that no longer matches what is
installed — that shipping it in-package was meant to prevent.

The install copies by default, so a package upgrade alone does not update
guidance already placed in a project; the install command has to be run again
to pick up a new version. That default exists because copying is the only
form every platform this content runs on is known to treat the same way a
real directory is treated, and the only one that survives the package being
upgraded or removed. Re-running the install command is the price of that
reliability, and it is cheap precisely because re-running it is always safe.
Linking directly to the package's own copy is available for users who want
guidance that tracks the installed version without re-running anything;
choosing it accepts, in exchange, that a project's guidance can change
without an explicit action, and that on a platform that will not create
links at all it is reported as a failure rather than falling back silently
to a copy.

There is no globally installed executable to remember; the command is only
reachable through `python -m`, which requires knowing the package is
installed in the environment being used — a smaller surface than a
console script, and one that trades a small amount of discoverability for
never depending on how a user's `PATH` happens to be configured.
