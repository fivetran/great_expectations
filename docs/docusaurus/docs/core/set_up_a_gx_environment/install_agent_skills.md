---
title: Install agent skills
description: Install the agent skills bundled with GX so that your coding agent can set up Data Sources, Expectations, and Checkpoints for you.
---

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';

GX bundles a set of agent skills: packaged guidance that a coding agent reads and follows in order to operate GX through its public Python API. With the skills installed in your project, you can ask your coding agent — in your own words — to connect to your data, describe what you expect of that data, and assemble a Checkpoint you can re-run later. The agent works through the same steps a GX practitioner would, with you in the loop, and what it leaves behind is an ordinary GX project plus a script that re-runs your checks with no agent involved.

The skills are plain text files that ship inside the `great_expectations` package. Installing them copies them into the directories that your coding agent already reads, so there is nothing to configure beyond the install command. The skills work with Claude Code, Codex, and Cursor.

## What the skills do

The three skills are three segments of one path: get GX reading your data, describe what you expect of that data, then bundle those checks into something you can run again without an agent involved. Each one ends where the next begins, and each one checks that its own starting point exists before it does anything — so you can work straight through, or come back weeks later and pick up where the last one left off.

### Connect to your data: `gx-configure-data-source`

This skill takes you from "here is my data" to a Batch Definition — a named, saved way of pulling a specific slice of your data, with the connection verified in-session. It builds three objects in order: a Data Source holding the connection (a directory, a connection string, or an in-memory handle), a Data Asset naming the collection of data within it (a table, a query, a family of files, a dataframe), and a Batch Definition selecting how much of that Asset a single operation reads — the whole thing, or one time window of it. Credentials go into the configuration as `${VARIABLE_NAME}` references, never as literal values.

**What it needs before it starts:** nothing but your data and a way to reach it. This is the first skill in the path. It works against either a GX project on disk or an in-memory session, and it tells you which one it is working on before it configures anything.

**What it leaves behind:** the Data Source, Data Asset, and Batch Definition, as ordinary GX project artifacts built through the public Python API. Before reporting, the skill retrieves a batch and reads rows through it to verify the connection is usable — then tells you what it created, what it reused, and what the read returned.

When you want to assert something about that data, this skill hands off the Batch Definition it just verified to `gx-configure-data-source`.

### Describe what you expect: `gx-configure-expectations`

This skill takes you from "here is what I want to be true about my data" to a saved Expectation Suite that has been run against a real batch of data. Two objects are involved: an Expectation is a single check with typed parameters — one column, one assertion, one set of bounds — and an Expectation Suite is the named, persisted collection of them. The skill transforms data invariants you describe in plain language into fully configured Expectations, then validates them against the underlying data and reports the results. 

**What it needs before it starts:** a working Batch Definition. If your project or session has none, you'll be redirected to `gx-configure-data-source` first to connect to your data.

**What it leaves behind:** the Suite, saved in your project, with each Expectation written through as it was added, and a report of the validation run — every Expectation shown as passed, failed with the observed numbers, or unable to run with the cause named. The exploratory validation results created in-session are not written into your project by default.

To repeatably validate your Expectations, this skill hands off the Batch Definition and ExpectationSuite to `gx-configure-checkpoint`.

### Make the checks re-runnable: `gx-configure-checkpoint`

This skill takes you from "here is a Suite that already validated my data" to a persisted, re-runnable Checkpoint. Two objects again: a Validation Definition binds one Batch Definition to one Expectation Suite — the specific slice of data, and the specific checks to run against it — and a Checkpoint is the named, persisted grouping of Validation Definitions plus the actions that fire after a run, executed as one operation. 

**What it needs before it starts:** at least one Expectation Suite and one working Batch Definition. If either is missing, the skill stops and names the skill that builds it.

**What it leaves behind:** the Checkpoint and its Validation Definitions, saved in your project, plus the results of the one verification run, reported per Validation Definition and then per Expectation within it. You also get a small self-contained script that loads the project by an absolute path and re-runs the Checkpoint by name from outside any agent session — which is the point of the Checkpoint. Wiring that script into an actual cadence, such as a cron entry, an Airflow DAG, or a CI job, is your orchestrator's job rather than the skill's.

That script is where the path ends: from there, deploy your checks to run on your schedule, with no agent in the loop.


## Install the skills

**Prerequisites**

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>, version 1.21.0 or newer. Earlier versions do not bundle the skills.
- One of the supported coding agents: Claude Code, Codex, or Cursor.

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

Re-running the install command is always safe: a skill that is already installed is left alone, and anything at a destination that GX did not put there is never overwritten. The full rules are under [What the install command will and will not overwrite](#what-the-install-command-will-and-will-not-overwrite).

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

To link to the skills inside the installed package instead of copying them — so that they follow the package when you upgrade it — pass `--symlink`. Not every platform permits symlinks: where they cannot be created, the destination is left as it was and the skill is reported as failed; re-run without `--symlink` to install file copies instead.

### Verify the installation

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

The command only reports state; it never changes it, and it exits successfully even when skills are missing or out of date. Every other line the report can show — a missing skill, an out-of-date one, a directory GX does not manage — is covered in [Read the skills list report](#read-the-skills-list-report).

## Use the skills

You do not run a command to start a skill, and there is nothing to register: agents discover installed skills on their own. Open your coding agent in the project you installed into and describe what you want — "connect GX to my orders table", "check that no amount is ever negative", "make these checks re-runnable" — and the agent selects the matching skill.

Start wherever your project actually is. Each skill checks that its own starting point exists before it does anything, and if what it needs is missing, it names the skill that builds it — so asking for the end of the path from an empty project walks you back to the beginning rather than failing.

## Keep the skills up to date

Installing copies the skills as they shipped in the version of GX you ran the command from. Upgrading GX does not reach back into your projects, so the copies already there stay as they are until you install again. After you upgrade, re-run the install command from the project root:

```bash title="Terminal input"
python -m great_expectations skills install
```

Skills installed by an earlier version are replaced and reported under `Updated`; skills already at the version you are running are reported under `Already up to date`. Both groups can appear in the same run: the re-run brings whatever is behind up to date and leaves the rest alone.

`skills list` is what tells you a project has fallen behind. A destination installed by a different version than the package you are running has `-- this package is <version>` appended to its state line, and the listing ends with a notice naming the install command.

Skills installed with `--symlink` follow the package on their own, but the version recorded at each destination stays the one that installed them, so `skills list` reports them as out of date until you re-run. Pass `--symlink` again when you do: a re-run without it replaces the links with copies.

An upgrade does not replace a GX-installed copy that you have edited yourself. It is refused for the same reason as on a first install — see the rules below — and every other skill in the run updates around it.

### What the install command will and will not overwrite

- **Re-running the install command is always safe.** A skill that is already installed at the version you are running, in the same form — copied, or linked with `--symlink` — is left byte-for-byte alone and is reported under `Already up to date`. Re-running with the other choice of `--symlink` converts it, and reports it under `Updated`.
- **A directory that GX did not install is never overwritten.** It is reported under `Failed`, left untouched, and the remaining skills still install. `--force` does not change this: if you want GX to install its skill at that path, move or delete the directory yourself first.
- **A GX-installed copy that you have edited since is left untouched too, so no edits are lost.** It is reported under `Failed` with an explanation. Re-run the install with `--force` to replace it with the bundled skill — this discards your edits, so save a copy elsewhere first if you want to keep them.

If any destination is refused, the command still installs the others, and it exits with a nonzero status.

:::note What counts as an edit

A GX-installed skill directory counts as edited when anything inside it differs from what was installed — including a file put there by an editor or by your operating system, such as `.DS_Store` — because the whole directory is compared against what was written.

:::

### Read the skills list report

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
