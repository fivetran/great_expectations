---
title: Install agent skills
description: Install the agent skills bundled with GX so that your coding agent can set up Data Sources, Expectations, and Checkpoints for you.
---

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';

GX bundles a set of agent skills: packaged guidance that a coding agent reads and follows in order to operate GX through its public Python API. With the skills installed in your project, you can ask your coding agent — in your own words — to connect to your data, describe what you expect of that data, and assemble a Checkpoint you can re-run later. The agent works through the same steps a GX practitioner would, with you in the loop.

The skills are plain text files that ship inside the `great_expectations` package. Installing them copies them into the directories that your coding agent already reads, so there is nothing to configure beyond the install command. The skills work with Claude Code, Codex, and Cursor.

## Prerequisites

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>, version 1.21.0 or newer. Earlier versions do not bundle the skills.
- One of the supported coding agents: Claude Code, Codex, or Cursor.

## Install the skills

Run the install command from the root of the project you want the skills available in:

```bash title="Terminal input"
python -m great_expectations skills install
```

The command reports what it did at each destination:

```shell title="Terminal output"
Great Expectations 1.21.0 skills in /path/to/my_project

Installed (6)
  .agents/skills/gx-configure-checkpoint
  .agents/skills/gx-configure-data-source
  .agents/skills/gx-configure-expectations
  .claude/skills/gx-configure-checkpoint
  .claude/skills/gx-configure-data-source
  .claude/skills/gx-configure-expectations
```

Destinations are shown relative to your project root. GX installs each skill into two locations, because different agents read different ones:

- `.agents/skills/` is read by Codex and Cursor.
- `.claude/skills/` is read by Claude Code and Cursor.

Installing into both is the default, so a single run serves all three supported agents.

### Choose where the skills are installed

Pass `--target` to narrow the destinations:

| Value | Installs into | Read by |
| --- | --- | --- |
| `agents` | `.agents/skills/` | Codex, Cursor |
| `claude` | `.claude/skills/` | Claude Code, Cursor |
| `all` (default) | both of the above | Claude Code, Codex, Cursor |

```bash title="Terminal input"
python -m great_expectations skills install --target claude
```

To install into a project other than the current directory, pass `--project-root`:

```bash title="Terminal input"
python -m great_expectations skills install --project-root /path/to/my_project
```

To link to the skills inside the installed package instead of copying them — so that they follow the package when you upgrade it — pass `--symlink`. Not every platform permits symlinks; where they cannot be created, the skill is reported as failed and installs normally without the option.

## What the skills do

The three skills are three segments of one path: get GX reading your data, describe what you expect of that data, then bundle those checks into something you can run again without an agent involved. Each one ends where the next begins, and each one checks that its own starting point exists before it does anything — so you can work straight through, or come back weeks later and pick up where the last one left off.

You do not run a command to start a skill. Describe what you want — "connect GX to my orders table", "check that no amount is ever negative", "make these checks re-runnable" — and your coding agent selects the matching skill from the ones installed in your project. Agents discover installed skills on their own.

**The skills hand work back to you rather than take it.** Anything that reaches past the work you asked for and touches your machine starts from you: a missing database driver is reported by name along with the command to install it, rather than installed; a project directory is created only after you have agreed to write the session out and named where; a change to your project's configuration that goes beyond what you asked for — repairing a disabled Data Docs site, for instance — is explained first and made only after you say yes; and a file you did not ask for and locate is offered in the conversation instead of written to your disk.

### Connect to your data: `gx-configure-data-source`

This skill takes you from "here is my data" to a verified Batch Definition — a named, saved way of pulling a specific slice of your data, proven to work because the skill read through it. It builds three objects in order: a Data Source holding the connection (a directory, a connection string, or an in-memory handle), a Data Asset naming the collection of data within it (a table, a query, a family of files, a dataframe), and a Batch Definition selecting how much of that Asset a single operation reads — the whole thing, or one time window of it. Credentials go into the configuration as `${VARIABLE_NAME}` references, never as literal values.

**What it needs before it starts:** nothing but your data and a way to reach it. This is the first skill in the path. It works against either a GX project on disk or an in-memory session, and it tells you which one it is working on before it configures anything.

**What it leaves behind:** the Data Source, Data Asset, and Batch Definition, as ordinary GX project artifacts built through the public Python API. Before reporting, the skill retrieves a batch and reads rows through it, because retrieving a batch on its own proves nothing — then tells you what it created, what it reused, and what the read returned. It stops there: it does not invent "smoke test" Expectations to demonstrate that the setup works. If the session is in memory, it offers to write the work out to a real project.

When you want to assert something about that data, this skill hands off the Batch Definition it just verified to the next one.

### Describe what you expect: `gx-configure-expectations`

This skill takes you from "here is what I want to be true about my data" to a saved Expectation Suite that has been run against a real batch, with every check reported individually. Two objects are involved: an Expectation is a single check with typed parameters — one column, one assertion, one set of bounds — and an Expectation Suite is the named, persisted collection of them. The skill matches what you describe in plain language against the Expectation catalog shipped inside the installed package, and builds only what you described. It does not profile your data looking for things worth asserting, and it does not append checks you did not ask for; if something you said is too vague to pin down, it asks you which bound you meant instead of picking one from the data.

**What it needs before it starts:** a working Batch Definition. If your project or session has none, the skill says so and points you at `gx-configure-data-source` rather than improvising data access some other way. If more than one exists, it names them and asks which slice of your data you meant.

**What it leaves behind:** the Suite, saved in your project, with each Expectation written through as it was added, and a report of the validation run — every Expectation shown as passed, failed with the observed numbers, or unable to run with the cause named. Validation results themselves are not filed anywhere by this skill: the Suite is the durable artifact, and the report you were given is the record of that run.

Turning a validated Suite into a check that survives the session is where the last skill picks up — and if you stop here instead, this skill's own job is already finished.

### Make the checks re-runnable: `gx-configure-checkpoint`

This skill takes you from "here is a Suite that already validated my data" to a persisted, re-runnable Checkpoint, verified by actually running it once. Two objects again: a Validation Definition binds one Batch Definition to one Expectation Suite — the specific slice of data, and the specific checks to run against it — and a Checkpoint is the named, persisted grouping of Validation Definitions plus the actions that fire after a run, executed as one operation. The skill asks what should happen after a run before assuming nothing should: a Slack or Teams message, an email, a Data Docs rebuild, or one of the less common actions.

**What it needs before it starts:** at least one Expectation Suite and one working Batch Definition. If either is missing, the skill stops and names the skill that builds it.

**What it leaves behind:** the Checkpoint and its Validation Definitions, saved in your project, plus the results of the one verification run, reported per Validation Definition and then per Expectation within it. You also get a small self-contained script that loads the project by an absolute path and re-runs the Checkpoint by name from outside any agent session — which is the point of the Checkpoint. Wiring that script into an actual cadence, such as a cron entry, an Airflow DAG, or a CI job, is your orchestrator's job rather than the skill's.

That script is where the path ends: from there, your checks run on your schedule, with no agent in the loop.

## What the install command will and will not overwrite

- **Re-running the install command is always safe.** A skill that is already installed at the version you are running, in the same form — copied, or linked with `--symlink` — is left byte-for-byte alone and is reported under `Already up to date`. Re-running with the other choice of `--symlink` converts it, and reports it under `Updated`.
- **A directory that GX did not install is never overwritten.** It is reported under `Failed`, left untouched, and the remaining skills still install. `--force` does not change this: if you want GX to install its skill at that path, move or delete the directory yourself first.
- **A GX-installed copy that you have edited since is left untouched too, so no edits are lost.** It is reported under `Failed` with an explanation. Re-run the install with `--force` to replace it with the bundled skill — this discards your edits, so save a copy elsewhere first if you want to keep them.

If any destination is refused, the command still installs the others, and it exits with a nonzero status.

:::note What counts as an edit

A GX-installed skill directory counts as edited when anything inside it differs from what was installed — including a file put there by an editor or by your operating system, such as `.DS_Store` — because the whole directory is compared against what was written.

:::

## Verify the installation

To see which skills this package bundles and where each one is installed, run:

```bash title="Terminal input"
python -m great_expectations skills list
```

```shell title="Terminal output"
Great Expectations 1.21.0 bundles 3 agent skills.
Installed state in /path/to/my_project:

gx-configure-checkpoint
  .agents/skills  installed by 1.21.0 (copy)
  .claude/skills  installed by 1.21.0 (copy)

gx-configure-data-source
  .agents/skills  installed by 1.21.0 (copy)
  .claude/skills  installed by 1.21.0 (copy)

gx-configure-expectations
  .agents/skills  installed by 1.21.0 (copy)
  .claude/skills  installed by 1.21.0 (copy)
```

The command only reports state; it never changes it, and it exits successfully even when skills are missing or out of date.

Each skill is listed with one line per destination. Those lines read as follows:

| State line | What it means |
| --- | --- |
| `not installed` | Nothing is at that destination. Run the install command. |
| `installed by <version> (copy)` | GX installed the skill there, at that version, by copying the files in. |
| `installed by <version> (symlink)` | The same, installed with `--symlink`, so the destination links to the skills inside the package. |
| `installed by <version> (<mode>) -- this package is <version>` | The skill was installed by a different version of GX than the one you are running. Re-run the install command to bring it up to date. |
| `present, but not installed by Great Expectations (no .gx-skill.json)` | Something that GX does not manage occupies that directory. GX will not overwrite it; move or delete it yourself if you want GX to install its skill there. |
| `cannot be read: <reason>` | GX could not determine what is at that destination — usually because a directory above it, such as `.claude/skills`, cannot be read. Fix the permissions on that path and run the command again. |

If a destination's record of what was installed is incomplete, its line degrades rather than failing: a missing mode drops the parentheses, and a missing version reads `installed by an unrecorded version`. GX treats an unrecorded version as differing from the version you are running, so such a destination is also reported as out of date by the notice below.

When any destination is out of date, the command adds a notice after the listing:

```shell title="Terminal output"
Some skills were installed by a different version of Great Expectations.
Run 'python -m great_expectations skills install' to bring them up to date.
```

`skills list` reads each destination's record of what was installed, not the files themselves, so a GX-installed skill that you have edited locally is reported exactly like an untouched one. The install command is what detects local edits.

## Keep the skills up to date

Installing copies the skills as they shipped in the version of GX you ran the command from. Upgrading GX does not reach back into your projects, so the copies already there stay as they are until you install again. After you upgrade, re-run the install command from the project root:

```bash title="Terminal input"
python -m great_expectations skills install
```

Skills installed by an earlier version are replaced and reported under `Updated`; skills already at the version you are running are reported under `Already up to date`. Both groups can appear in the same run: the re-run brings whatever is behind up to date and leaves the rest alone.

`skills list` is what tells you a project has fallen behind. A destination installed by a different version than the package you are running has `-- this package is <version>` appended to its state line, and the listing ends with a notice naming the install command.

Skills installed with `--symlink` follow the package on their own, but the version recorded at each destination stays the one that installed them, so `skills list` reports them as out of date until you re-run. Pass `--symlink` again when you do: a re-run without it replaces the links with copies.

An upgrade does not replace a GX-installed copy that you have edited yourself. It is refused for the same reason as on a first install — see [What the install command will and will not overwrite](#what-the-install-command-will-and-will-not-overwrite) — and every other skill in the run updates around it.

## Remove the skills

There is no uninstall command. Removing the skills is the manual procedure below: delete the directories the install command created. Each skill's record of what GX installed lives inside that skill's own directory, and the install command writes nothing outside these paths, so there is no other state to clean up.

Run this from your project root:

```bash title="Terminal input"
rm -rf .agents/skills/gx-configure-data-source \
  .agents/skills/gx-configure-expectations \
  .agents/skills/gx-configure-checkpoint \
  .claude/skills/gx-configure-data-source \
  .claude/skills/gx-configure-expectations \
  .claude/skills/gx-configure-checkpoint
```

If you installed with `--target agents` or `--target claude`, only the three directories under that one location exist, and those are the ones to delete. If you installed with `--symlink`, deleting these directories removes the links only — the skills inside the installed package are untouched.

The `.agents/skills` and `.claude/skills` directories are left in place afterwards, as are `.agents` and `.claude` themselves, holding nothing that GX installed. Removing them is your call rather than part of this procedure: they are shared with anything else your coding agents keep there.

Running `skills list` afterwards reports `not installed` at every destination.
