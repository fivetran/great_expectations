"""
Purpose: guard the installed package against silently dropping the bundled agent
skills or their schema catalogs.

The skills and the two catalog indexes they depend on all ship through
`package_data` glob patterns rather than through code, which means nothing enforces
that the patterns stay in sync with what actually lives in the source tree: a pattern
narrowed by an unrelated edit, or a file added under a directory the patterns do not
reach, fails silently. `pip install .` and `import great_expectations` both succeed
either way, so nothing in the ordinary import-and-run check catches it.

This script is meant to run after `pip install .`, against the resulting installed
package, and checks the properties a user actually depends on:

* both bundled skills resolve the way an installed package resolves them -- through
  the import system, not by checking that some files happen to exist;
* both schema catalog indexes are present, and each schema tree ships more than just
  its index;
* the `skills list` subcommand names both skills;
* installing from the running package produces content that matches its own
  ownership manifest;
* every file the source tree bundles for a skill actually made it into the installed
  package, not just the files that happen to make the skill resolve.

Run directly with `python ci/checks/check_installed_agent_skills.py` from the
repository root, with the package already installed in the active environment.
"""

from __future__ import annotations

import io
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Final

import great_expectations
from great_expectations import __main__ as command_line
from great_expectations.agent_skills import installer
from great_expectations.agent_skills.installer import (
    SkillTarget,
    install_skills,
    iter_bundled_skills,
    read_skill_manifest,
)

#: The skills this package currently bundles, named explicitly rather than merely
#: counted -- a rename or a dropped skill is then reported by name instead of as an
#: unexplained count mismatch.
EXPECTED_SKILLS: Final = frozenset({"gx-configure-data-source", "gx-configure-expectations"})

#: The schema trees the package ships alongside the skills, each carrying its own
#: catalog index, relative to the installed package root.
SCHEMA_TREES: Final = (
    Path("expectations", "core", "schemas"),
    Path("datasource", "fluent", "schemas"),
)

INDEX_NAME: Final = "index.json"


def check_bundled_skills_resolve() -> list[Path]:
    """Both skills must be found the way an installed package is found: through the
    import system, not by checking that some files happen to exist.

    ``iter_bundled_skills`` is what every install and list run relies on to locate the
    skills, and it is also what raises when a packaging pattern ships some of a
    skill's files and drops others -- the shape a too-narrow glob produces. Calling it
    here, rather than checking paths by hand, is what makes this a check on skill
    *resolution*.
    """
    skills = sorted(iter_bundled_skills(), key=lambda skill: skill.name)
    names = {skill.name for skill in skills}
    assert names == EXPECTED_SKILLS, (
        f"expected the installed package to bundle {sorted(EXPECTED_SKILLS)}, found {sorted(names)}"
    )
    for skill in skills:
        assert (skill / "SKILL.md").is_file(), f"{skill} has no SKILL.md"
    return skills


def check_catalog_indexes(installed_root: Path) -> None:
    """Both catalog indexes must ship at their documented location."""
    for tree in SCHEMA_TREES:
        index = installed_root / tree / INDEX_NAME
        assert index.is_file(), f"{index} was not found in the installed package"


def check_schema_counts_nonzero(installed_root: Path) -> dict[str, int]:
    """Each schema tree must ship more than just its index."""
    counts: dict[str, int] = {}
    for tree in SCHEMA_TREES:
        directory = installed_root / tree
        count = sum(1 for path in directory.rglob("*.json") if path.name != INDEX_NAME)
        assert count > 0, f"no schema JSON files were found under {directory}"
        counts[tree.as_posix()] = count
    return counts


def check_skills_list_names_both(project_root: Path) -> str:
    """The ``skills list`` subcommand must name both skills, run the way a user runs it.

    Invoked in-process through the same entry point ``python -m great_expectations``
    calls, rather than shelled out to, so the exact code path a user runs is exercised
    without depending on how the interpreter running this script happens to be found.
    """
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = command_line.main(["skills", "list", "--project-root", str(project_root)])
    output = buffer.getvalue()
    assert exit_code == 0, f"'skills list' exited {exit_code}:\n{output}"
    for name in EXPECTED_SKILLS:
        assert name in output, f"'skills list' did not mention {name}:\n{output}"
    return output


def check_installed_digests_match_manifest(project_root: Path) -> None:
    """Installing from the running package must produce content matching its own
    ownership manifest.

    That match is what lets a later run tell an untouched install apart from one the
    user edited. Checking it here, against a genuinely packaged and installed
    distribution, covers a case the test suite cannot reach: the suite exercises a
    fixture tree or a source checkout under an editable install, neither of which is
    the artifact a user actually receives.

    Hashing is done with the installer's own ``_tree_digest`` rather than a second,
    independently written function: the manifest's ``content_sha256`` field is defined
    as that function's output, so the only way to ask "does this destination still
    match what its manifest recorded" is to recompute the same function and compare --
    a differently framed hash would disagree with the manifest even for byte-identical
    content, and this check would fail on every run rather than only on a real
    regression. That is not circular, because the two hashes are taken over different
    trees: the manifest's value is computed from the installed package's own bundled
    directory, while this recomputes over the copy placed in the project. Equality is
    therefore a real property of the install pipeline -- that ``shutil.copytree``
    reproduced the source directory byte for byte.
    """
    report = install_skills(project_root, targets=(SkillTarget.AGENTS, SkillTarget.CLAUDE))
    assert not report.failed, (
        f"installing into a scratch project reported failures: {report.failed}"
    )
    assert report.installed, "installing into a scratch project installed nothing"
    for destination in report.installed:
        manifest = read_skill_manifest(destination)
        assert manifest is not None, f"{destination} has no ownership manifest after install"
        recorded = manifest.get("content_sha256")
        actual = installer._tree_digest(destination)
        assert actual == recorded, (
            f"{destination} hashes to {actual}, but its manifest records {recorded} -- the "
            "installed content does not match what was written down for it"
        )


def check_every_bundled_file_shipped(source_root: Path, installed_root: Path) -> None:
    """Every file under the source skills tree must exist at the same relative path in
    the installed package.

    Every other check here can pass while a packaging pattern still drops a file that
    is neither a ``SKILL.md`` nor a markdown reference -- a script or an image added to
    a skill directory, say -- because nothing else compares the two trees file for
    file. ``iter_bundled_skills`` would not notice: it only requires ``SKILL.md``.
    """
    missing = [
        path.relative_to(source_root).as_posix()
        for path in sorted(source_root.rglob("*"))
        if path.is_file()
        and not path.is_symlink()
        and not (installed_root / path.relative_to(source_root)).is_file()
    ]
    assert not missing, (
        f"these files exist under {source_root} but were not found in the installed package "
        f"at {installed_root} -- check the packaging patterns for the skills tree: {missing}"
    )


def main() -> None:
    installed_root = Path(great_expectations.__file__).resolve().parent
    repo_root = Path(__file__).resolve().parents[2]
    source_skills_root = repo_root / "great_expectations" / ".agents" / "skills"

    try:
        skills = check_bundled_skills_resolve()
        check_catalog_indexes(installed_root)
        counts = check_schema_counts_nonzero(installed_root)

        with tempfile.TemporaryDirectory(prefix="gx-installed-skills-guard-") as scratch:
            project_root = Path(scratch)
            check_skills_list_names_both(project_root)
            check_installed_digests_match_manifest(project_root)

        check_every_bundled_file_shipped(source_skills_root, skills[0].parent)
    except (AssertionError, OSError) as error:
        print(f"[ERROR] {error}")
        sys.exit(1)

    schema_summary = ", ".join(f"{count} under {tree}" for tree, count in counts.items())
    print(
        f"Installed agent skills are complete: {len(skills)} skills "
        f"({', '.join(sorted(skill.name for skill in skills))}), schemas {schema_summary}."
    )


if __name__ == "__main__":
    main()
