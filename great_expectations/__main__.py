"""Command line entry point: ``python -m great_expectations``.

Great Expectations is a library, not a command line application, and this module is
deliberately the whole of its command surface: the one thing a user cannot do from
Python is put files into their own project before an agent reads them, because by then
the decision of what to trust in that project has already been made. Everything here
therefore only prints and installs -- it never touches data.

The subcommands wrap :mod:`great_expectations.agent_skills.installer`, which reports
per-skill problems rather than raising them. That shapes this envelope: a run that
installs three skills and refuses a fourth has to print all four and still exit
nonzero, so the whole outcome is visible in one screen and a script can tell it apart
from a clean run. The failures the installer *does* raise -- an unusable project
directory, a package that bundles no skills -- are answered with the message it wrote
and a nonzero exit, never a traceback: both are things the user can fix, and a
traceback would bury the sentence that says how.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Final

import great_expectations
from great_expectations.agent_skills.installer import (
    MANIFEST_NAME,
    InstallMode,
    SkillFailureKind,
    SkillInstallFailure,
    SkillInstallReport,
    SkillTarget,
    install_skills,
    iter_bundled_skills,
    read_skill_manifest,
)

#: The ``--target`` values, and the discovery directories each one selects.
_TARGETS: Final[dict[str, tuple[SkillTarget, ...]]] = {
    "agents": (SkillTarget.AGENTS,),
    "claude": (SkillTarget.CLAUDE,),
    "all": (SkillTarget.AGENTS, SkillTarget.CLAUDE),
}

#: Width the installer's reasons are wrapped to. Fixed rather than read from the
#: terminal so that the same command produces the same output everywhere, including
#: in a log or a pipe, where there is no terminal to read.
_REASON_WIDTH: Final = 88

_SKILLS_DESCRIPTION: Final = (
    "Great Expectations bundles skills that teach a coding agent to configure data "
    "sources and expectations. Agents look for skills in directories inside your "
    "project, so the skills have to be installed there before an agent can find them."
)

_INSTALL_DESCRIPTION: Final = (
    "Install the bundled skills into a project. Safe to run again at any time: skills "
    "already installed at this version are left byte-for-byte alone, and a directory "
    "that Great Expectations did not install, or that you have edited since it was "
    "installed, is reported rather than overwritten."
)

_LIST_DESCRIPTION: Final = (
    "Show the skills this package bundles and, for each agent directory, whether the "
    "skill is installed in the project and which version installed it."
)

#: Printed once below the failed destinations, whatever went wrong with them.
_FAILURE_FOOTER: Final = "Nothing was changed at the paths above."

#: Added when the run actually reported a skill as edited. The installer's reason for
#: that one says what to do; this says what "edited" means, because the answer has a
#: consequence nobody guesses: the whole directory is compared, so a file the user
#: never chose to put there counts. Its opening clause names the failures it belongs
#: to, since a run can report edited and unreadable destinations together and advice
#: meant for one would send the user hunting for the wrong thing at the other.
_LOCAL_EDIT_FOOTER: Final = (
    "Where a skill above is reported as edited: it counts as edited when anything "
    "inside its directory differs from what was installed -- including a file put "
    "there by an editor or by the operating system, such as .DS_Store -- because the "
    "whole directory is compared against what was written."
)


def _unreportable_project_root_reason(project_root: Path) -> str:
    return (
        f"Cannot report the skills installed in {project_root}: it is not an existing "
        "directory. Pass the path of the project you want the skills reported for."
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run a command and return its exit status.

    Returns:
        ``0`` if everything asked for succeeded, ``1`` otherwise. Nothing failing is a
        stricter condition than something succeeding: an install that put two skills in
        place and refused a third exits nonzero, because a script that treated it as a
        success would go on to run an agent that is missing a skill.
    """
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    run: Callable[[argparse.Namespace], int] = arguments.run
    try:
        return run(arguments)
    except OSError as error:
        # The installer's messages for these are written to be read by the person who
        # typed the command -- they name the path, say what is wrong with it, and give
        # the next step -- so the message is the whole of the output.
        print(error, file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m great_expectations",
        description="Command line utilities for Great Expectations.",
    )
    commands = parser.add_subparsers(metavar="command", required=True)
    skills = commands.add_parser(
        "skills",
        help="install and inspect the agent skills bundled with this package",
        description=_SKILLS_DESCRIPTION,
    )
    skills_commands = skills.add_subparsers(metavar="command", required=True)
    _add_install_parser(skills_commands)
    _add_list_parser(skills_commands)
    return parser


def _add_install_parser(commands: argparse._SubParsersAction) -> None:
    install = commands.add_parser(
        "install",
        help="install the bundled skills into a project",
        description=_INSTALL_DESCRIPTION,
    )
    _add_project_root_argument(install, "install the skills into")
    install.add_argument(
        "--target",
        choices=tuple(_TARGETS),
        default="all",
        help=(
            "which agent directories to install into: 'agents' for .agents/skills, read "
            "by Codex and Cursor; 'claude' for .claude/skills, read by Claude Code and "
            "Cursor; 'all' for both, which is the default and serves every supported "
            "agent from one run"
        ),
    )
    install.add_argument(
        "--symlink",
        action="store_true",
        help=(
            "link to the skills in the installed package instead of copying them, so "
            "that they follow the package when it is upgraded. Not every platform "
            "permits symlinks; where they cannot be created the skill is reported as "
            "failed and installs normally without this option"
        ),
    )
    install.add_argument(
        "--force",
        action="store_true",
        help=(
            "overwrite skill directories that Great Expectations installed and that "
            "have been edited since. A directory it did not install is never "
            "overwritten, with or without this option"
        ),
    )
    install.set_defaults(run=_run_install)


def _add_list_parser(commands: argparse._SubParsersAction) -> None:
    listing = commands.add_parser(
        "list",
        help="show the bundled skills and where they are installed",
        description=_LIST_DESCRIPTION,
    )
    _add_project_root_argument(listing, "report the installed skills of")
    listing.set_defaults(run=_run_list)


def _add_project_root_argument(parser: argparse.ArgumentParser, purpose: str) -> None:
    """Declare ``--project-root``, whose default is resolved later rather than here.

    The default is the working directory, but reading the working directory is a
    filesystem call that fails outright once the directory has been deleted -- ordinary
    after a build script removes its own directory or a container mount disappears.
    Evaluating it while the arguments are merely being *defined* would make that failure
    a traceback out of every command, including ``--help`` and a mistyped subcommand,
    neither of which needs a working directory at all.
    """
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        metavar="PATH",
        help=f"the project to {purpose} (default: the current directory)",
    )


def _project_root(arguments: argparse.Namespace) -> Path:
    """Return the project to act on, reading the working directory only if asked to."""
    if arguments.project_root is not None:
        project_root: Path = arguments.project_root
        return project_root
    try:
        return Path.cwd()
    except OSError as error:
        raise OSError(_unusable_working_directory_reason(error)) from error


def _unusable_working_directory_reason(error: OSError) -> str:
    return (
        f"Cannot read the current directory: {error.strerror or error}. It has usually "
        "been deleted or unmounted since this shell started. Change to a directory that "
        "still exists, or pass --project-root with the path of the project."
    )


def _run_install(arguments: argparse.Namespace) -> int:
    """Install the bundled skills and print what happened to every destination."""
    project_root = _project_root(arguments)
    report = install_skills(
        project_root,
        targets=_TARGETS[arguments.target],
        mode=InstallMode.SYMLINK if arguments.symlink else InstallMode.COPY,
        force=arguments.force,
    )
    _print_install_report(report, project_root)
    return 1 if report.failed else 0


def _print_install_report(report: SkillInstallReport, project_root: Path) -> None:
    """Print every destination the run considered, grouped by what happened to it."""
    print(f"Great Expectations {great_expectations.__version__} skills in {project_root}")
    _print_group("Installed", report.installed, project_root)
    _print_group("Updated", report.replaced, project_root)
    _print_group("Already up to date", report.up_to_date, project_root)
    _print_failures(report.failed, project_root)
    if not report.installed and not report.replaced and not report.failed:
        # Saying so beats an empty run: the user asked for something to happen, and
        # "nothing did, and that is the right answer" is the news.
        print("\nEvery bundled skill was already installed at this version. Nothing to do.")


def _print_group(heading: str, destinations: Sequence[Path], project_root: Path) -> None:
    if not destinations:
        return
    print(f"\n{heading} ({len(destinations)})")
    for destination in destinations:
        print(f"  {_display_path(destination, project_root)}")


def _print_failures(failures: Sequence[SkillInstallFailure], project_root: Path) -> None:
    """Print the failed destinations with the installer's reason for each.

    The reasons are reproduced whole. Each one already names the state the destination
    is in and one thing to do about it, and shortening them here would leave the user
    with a path and no way to act on it.
    """
    if not failures:
        return
    print(f"\nFailed ({len(failures)})")
    for failure in failures:
        print(f"  {_display_path(failure.destination, project_root)}")
        print(_wrap(failure.reason, indent="    "))
    footer = _FAILURE_FOOTER
    if any(failure.kind is SkillFailureKind.LOCALLY_MODIFIED for failure in failures):
        # Asked of the report rather than of the filesystem: what a destination looks
        # like afterwards cannot tell an edited directory from one that could not be
        # read, and both leave the destination sitting there with a valid manifest.
        footer = f"{footer} {_LOCAL_EDIT_FOOTER}"
    print()
    print(_wrap(footer))


def _wrap(text: str, indent: str = "") -> str:
    """Fill a paragraph without breaking a path across two lines.

    A wrapped path cannot be copied out of the terminal, and every message here exists
    to be acted on. An over-long path is left to overflow instead.
    """
    return textwrap.fill(
        text,
        width=_REASON_WIDTH,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    )


def _run_list(arguments: argparse.Namespace) -> int:
    """Print the bundled skills and what each agent directory of the project holds.

    Reporting only, so it succeeds even when the project is out of date: an install
    that has not been re-run since an upgrade is the state this command exists to
    make visible, not a failure of the command.
    """
    project_root = _project_root(arguments)
    if not project_root.is_dir():
        raise NotADirectoryError(_unreportable_project_root_reason(project_root))

    version = great_expectations.__version__
    skills = list(iter_bundled_skills())
    print(f"Great Expectations {version} bundles {len(skills)} agent skills.")
    print(f"Installed state in {project_root}:")

    stale = False
    for skill in skills:
        print(f"\n{skill.name}")
        for target in SkillTarget:
            state, is_stale = _installed_state(project_root / target.value / skill.name, version)
            stale = stale or is_stale
            print(f"  {target.value:<15} {state}")
    if stale:
        print(
            "\nSome skills were installed by a different version of Great Expectations.\n"
            "Run 'python -m great_expectations skills install' to bring them up to date."
        )
    return 0


def _installed_state(destination: Path, version: str) -> tuple[str, bool]:
    """Describe what is installed at one destination, and whether it is out of date.

    Ownership is read through the installer's own manifest reader, which treats a
    manifest that is missing, unreadable, or not Great Expectations' as the same
    answer. Anything else would let this command claim a directory the install command
    would refuse to touch.

    Presence is decided without following links, so a link pointing at nothing -- what a
    symlink install becomes when the package it pointed at is gone -- is reported as
    something being there rather than as an empty destination.
    """
    try:
        destination.lstat()
    except FileNotFoundError:
        return "not installed", False
    except OSError as error:
        # Usually an unreadable parent directory. Not knowing is its own answer: this
        # command is read from to decide whether to install, and "not installed" is a
        # claim about a destination whose state was never actually seen.
        return f"cannot be read: {error.strerror or error}", False
    manifest = read_skill_manifest(destination)
    if manifest is None:
        return f"present, but not installed by Great Expectations (no {MANIFEST_NAME})", False
    installed_version = _manifest_string(manifest, "gx_version") or "an unrecorded version"
    mode = _manifest_string(manifest, "mode")
    described = f"installed by {installed_version}"
    if mode:
        described = f"{described} ({mode})"
    if installed_version == version:
        return described, False
    return f"{described} -- this package is {version}", True


def _manifest_string(manifest: dict[str, Any], key: str) -> str | None:
    """Read one field of a manifest, tolerating a manifest that does not hold it.

    A manifest is a file in the user's project: it can be older than this code, or
    hand-edited. A field this command cannot use is reported as unknown rather than
    allowed to end the run.
    """
    value = manifest.get(key)
    return value if isinstance(value, str) else None


def _display_path(destination: Path, project_root: Path) -> str:
    """Show a destination relative to the project, which is how the user thinks of it."""
    try:
        return str(destination.relative_to(project_root))
    except ValueError:
        return str(destination)


if __name__ == "__main__":
    sys.exit(main())
