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
Great Expectations 1.20.0+35.g5b4e2e966 skills in /path/to/my_project

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

### What the install command will and will not overwrite

- **Re-running the install command is always safe.** A skill that is already installed at the version you are running is left byte-for-byte alone and is reported under `Already up to date`.
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
Great Expectations 1.20.0+35.g5b4e2e966 bundles 3 agent skills.
Installed state in /path/to/my_project:

gx-configure-checkpoint
  .agents/skills  installed by 1.20.0+35.g5b4e2e966 (copy)
  .claude/skills  installed by 1.20.0+35.g5b4e2e966 (copy)

gx-configure-data-source
  .agents/skills  installed by 1.20.0+35.g5b4e2e966 (copy)
  .claude/skills  installed by 1.20.0+35.g5b4e2e966 (copy)

gx-configure-expectations
  .agents/skills  installed by 1.20.0+35.g5b4e2e966 (copy)
  .claude/skills  installed by 1.20.0+35.g5b4e2e966 (copy)
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
