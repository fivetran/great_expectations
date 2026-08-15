"""Filesystem tests for installing the bundled agent skills into a project.

The install command writes into a directory that belongs to the user rather than to this
package, which makes most of what it does a promise about what it will *not* touch: a
second run must not rewrite an unchanged copy, an edited copy must survive being refused,
a directory Great Expectations never created must be byte-for-byte untouched even under
``--force``, and a write that fails must leave nothing behind. None of those promises can
be checked by reading the report a run returns -- a report is what the installer *says*
it did -- so every assertion below is made against the filesystem: bytes, link targets,
ownership manifests, modification times and inode numbers.

Each check is a function returning a list of problems, and each one is paired with a test
that runs the same check against a deliberately broken build of the installer -- copying
that dereferences symlinks, an ownership check that trusts every directory, a staged
write that goes straight to the destination -- and asserts the check reports it. A
filesystem check that quietly stopped comparing anything would otherwise keep passing
forever while asserting nothing, which is the failure mode these tests exist to prevent.

Everything runs against directories built under ``tmp_path``. Nothing here installs into
the checkout, and nothing reaches the network.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import importlib.util
import itertools
import json
import pathlib
import shutil
import stat
import types
from collections.abc import Iterator, Sequence
from typing import Callable, Final

import pytest

import great_expectations
from great_expectations import __main__ as command_line
from great_expectations.agent_skills import installer
from great_expectations.agent_skills.installer import (
    MANIFEST_NAME,
    InstallMode,
    SkillFailureKind,
    SkillInstallFailure,
    SkillInstallReport,
    SkillTarget,
    install_skills,
)

pytestmark = [pytest.mark.unit]

PROJECT_ROOT: Final = pathlib.Path(__file__).parents[2]
BUNDLED_SKILLS_ROOT: Final = PROJECT_ROOT / "great_expectations" / ".agents" / "skills"

ENTRY_DOCUMENT: Final = "SKILL.md"
REFERENCE_DIR: Final = "references"
STAGING_PREFIX: Final = ".gx-tmp-"

ALL_TARGETS: Final = (SkillTarget.AGENTS, SkillTarget.CLAUDE)

#: Number of skills the package is known to bundle. Guards the checks over the real
#: bundle against a discovery bug reducing them to nothing.
MIN_BUNDLED_SKILLS: Final = 2

#: Two synthetic skills into two target directories. Every check over the synthetic
#: bundle asserts it had at least this many destinations to look at, so a scenario that
#: silently stopped installing anything cannot pass by comparing empty sets.
MIN_DESTINATIONS: Final = 4

#: Versions the synthetic package claims. Neither is a real release, so a check that
#: read the real version by accident fails rather than passes.
INSTALLED_VERSION: Final = "1.3.0.test"
EARLIER_VERSION: Final = "1.2.0.test"

FILE: Final = "file"
LINK: Final = "link"
DIRECTORY: Final = "directory"

#: How deep the synthetic bundle really goes (``references/guide.md``). A walk that
#: descended through the symlink cycles below would report paths far deeper than this.
REAL_TREE_DEPTH: Final = 2
#: Depth reached by a link-following walk before the demonstration below gives up. Well
#: past the real depth and well short of the point where the kernel refuses to resolve
#: any more symlink components.
CYCLE_DEPTH_EVIDENCE: Final = 8
#: Entries the link-following demonstration is allowed to visit before it is cut off. A
#: walk that terminates on its own never reaches this.
CYCLE_WALK_LIMIT: Final = 400


# ---------------------------------------------------------------------------
# Recording what is on disk, independently of the code under test.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Entry:
    """One path in a tree, as the filesystem holds it.

    Identity is deliberately recorded twice over: ``kind`` and ``payload`` say what the
    user would read, while ``mtime_ns`` and ``inode`` say whether it was written. A run
    that rewrote a file with identical bytes changes the second pair and not the first,
    and "already up to date" is a claim about both.
    """

    kind: str
    #: Link target for a link, a hash of the bytes for a file, empty for a directory.
    payload: str
    size: int
    mtime_ns: int
    inode: int


def walk(root: pathlib.Path) -> Iterator[pathlib.Path]:
    """Yield every path below ``root`` without following links.

    Spelled out here rather than borrowed from the installer: a test that measured the
    filesystem with the code under test would report a broken walk as an unchanged tree.
    """
    pending = [root]
    while pending:
        for entry in sorted(pending.pop().iterdir()):
            yield entry
            if entry.is_dir() and not entry.is_symlink():
                pending.append(entry)


def snapshot(root: pathlib.Path) -> dict[str, Entry]:
    """Record a whole tree, keyed by path relative to ``root``."""
    recorded: dict[str, Entry] = {}
    for path in walk(root):
        stats = path.lstat()
        if path.is_symlink():
            kind, payload, size = LINK, str(path.readlink()), 0
        elif path.is_file():
            payload_bytes = path.read_bytes()
            kind, payload, size = (
                FILE,
                hashlib.sha256(payload_bytes).hexdigest(),
                len(payload_bytes),
            )
        else:
            kind, payload, size = DIRECTORY, "", 0
        recorded[path.relative_to(root).as_posix()] = Entry(
            kind=kind, payload=payload, size=size, mtime_ns=stats.st_mtime_ns, inode=stats.st_ino
        )
    return recorded


def contents(recorded: dict[str, Entry]) -> dict[str, tuple[str, str]]:
    """Reduce a snapshot to what a reader would see, dropping when it was written."""
    return {name: (entry.kind, entry.payload) for name, entry in recorded.items()}


def describe(entry: Entry) -> str:
    if entry.kind == LINK:
        return f"a link to {entry.payload}"
    if entry.kind == FILE:
        return f"a file of {entry.size} bytes ({entry.payload[:12]})"
    return "a directory"


# ---------------------------------------------------------------------------
# The synthetic package the scenarios install from.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Bundle:
    """A stand-in for the skills directory inside an installed package."""

    root: pathlib.Path
    names: tuple[str, ...]

    @property
    def skills(self) -> list[pathlib.Path]:
        return [self.root / name for name in self.names]

    def source_for(self, destination: pathlib.Path) -> pathlib.Path:
        return self.root / destination.name


@pytest.fixture
def bundle(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> Bundle:
    """A package bundling two skills, with a directory that is not one alongside them.

    Synthetic rather than the real content because the scenarios need to change what the
    package holds -- an upgrade adds a file, a defective packaging run drops an entry
    document -- and because a check that reads the real bundle would change meaning every
    time the shipped guidance is edited. The real bundle is covered separately.
    """
    root = tmp_path / "site-packages" / "great_expectations" / ".agents" / "skills"
    names = ("gx-first-skill", "gx-second-skill")
    for index, name in enumerate(names):
        skill = root / name
        (skill / REFERENCE_DIR).mkdir(parents=True)
        (skill / ENTRY_DOCUMENT).write_text(
            f"---\nname: {name}\n---\n\n# {name}\n\nSee `{REFERENCE_DIR}/guide.md`.\n",
            encoding="utf-8",
        )
        (skill / REFERENCE_DIR / "guide.md").write_text(f"# guide {index}\n", encoding="utf-8")
    not_a_skill = root / "shared-fragments"
    not_a_skill.mkdir()
    (not_a_skill / "fragment.md").write_text("# not a skill: no entry document\n", encoding="utf-8")

    monkeypatch.setattr(installer, "_bundled_skills_root", lambda: root)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)
    return Bundle(root=root, names=names)


@pytest.fixture
def bundle_with_links(bundle: Bundle) -> Bundle:
    """The same package, with a skill holding an ordinary link and a dangling one.

    Both belong here: a link that resolves is what a build step or a packaging tool
    leaves behind, and a link that does not is what an upgrade leaves behind when the
    file it pointed at is dropped. Neither may abort an install, and neither may make an
    installed copy hash differently from the skill it was copied from.
    """
    references = bundle.root / bundle.names[0] / REFERENCE_DIR
    (references / "shared.md").symlink_to(pathlib.Path("guide.md"))
    (references / "dropped.md").symlink_to(pathlib.Path("gone.md"))
    return bundle


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "project"
    root.mkdir()
    return root


def expected_destinations(
    project: pathlib.Path, bundle: Bundle, targets: Sequence[SkillTarget] = ALL_TARGETS
) -> list[pathlib.Path]:
    return [project / target.value / name for target in targets for name in bundle.names]


def stamp_manifest_version(destination: pathlib.Path, version: str) -> None:
    """Rewrite the version an installed skill records, leaving its content alone.

    This is what an installed skill looks like after the package is upgraded: the tree
    still matches the hash its own manifest recorded, so it is unmodified, but it is no
    longer what this version of the package would install. The manifest is excluded from
    the hash, so editing it here does not make the destination look edited.
    """
    path = destination / MANIFEST_NAME
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["gx_version"] = version
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@contextlib.contextmanager
def made_unreadable(path: pathlib.Path) -> Iterator[None]:
    """Take away every permission on ``path`` for the duration, then give them back."""
    original = stat.S_IMODE(path.lstat().st_mode)
    path.chmod(0o000)
    try:
        yield
    finally:
        path.chmod(original)


def is_readable(path: pathlib.Path) -> bool:
    try:
        list(path.iterdir())
    except OSError:
        return False
    return True


# ---------------------------------------------------------------------------
# Checks. Each returns the problems it found, so the same code can be asserted
# empty against the real installer and non-empty against a broken one.
# ---------------------------------------------------------------------------


def describe_report(report: SkillInstallReport) -> str:
    failed = ", ".join(f"{failure.destination}: {failure.kind.value}" for failure in report.failed)
    return (
        f"installed={[str(path) for path in report.installed]},"
        f" up_to_date={[str(path) for path in report.up_to_date]},"
        f" replaced={[str(path) for path in report.replaced]},"
        f" failed=[{failed}]"
    )


def failure_for(
    report: SkillInstallReport, destination: pathlib.Path
) -> SkillInstallFailure | None:
    for failure in report.failed:
        if failure.destination == destination:
            return failure
    return None


def partition_problems(report: SkillInstallReport, expected: Sequence[pathlib.Path]) -> list[str]:
    """Every destination the run considered must appear in exactly one outcome.

    A caller reports the whole run by printing the four fields, so a destination in two
    of them is reported twice and one in none of them is never mentioned at all.
    """
    if not expected:
        return ["the run considered no destinations, so its partition proves nothing"]
    groups = {
        "installed": tuple(report.installed),
        "up_to_date": tuple(report.up_to_date),
        "replaced": tuple(report.replaced),
        "failed": tuple(failure.destination for failure in report.failed),
    }
    problems: list[str] = []
    for destination in sorted(set(expected).union(*(set(group) for group in groups.values()))):
        appearances = [
            name for name, group in groups.items() for path in group if path == destination
        ]
        if len(appearances) > 1:
            problems.append(f"{destination} is reported in {sorted(appearances)}, not in one.")
        elif not appearances:
            problems.append(f"{destination} is reported in no outcome; the run must place it.")
        elif destination not in expected:
            problems.append(
                f"{destination} is reported as {appearances[0]} but is not a destination"
                " this run had to consider."
            )
    return problems


def manifest_problems(
    destination: pathlib.Path, source: pathlib.Path, version: str, mode: InstallMode
) -> list[str]:
    """The ownership manifest must record who installed this, at which version and how."""
    path = destination / MANIFEST_NAME
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path}: no readable ownership manifest ({error})."]
    expected = {
        "managed_by": "great_expectations",
        "gx_version": version,
        "content_sha256": installer._tree_digest(source),
        "mode": mode.value,
    }
    return [
        f"{path}: {field} is {manifest.get(field)!r}, expected {value!r}."
        for field, value in expected.items()
        if manifest.get(field) != value
    ]


def difference_problems(
    source: pathlib.Path,
    destination: pathlib.Path,
    expected: dict[str, tuple[str, str]],
    actual: dict[str, tuple[str, str]],
) -> list[str]:
    problems: list[str] = []
    for name in sorted(set(expected) - set(actual)):
        problems.append(f"{destination}: {name} is missing; {source} holds it.")
    for name in sorted(set(actual) - set(expected)):
        problems.append(f"{destination}: {name} was installed but is not part of {source}.")
    for name in sorted(set(actual) & set(expected)):
        if actual[name] != expected[name]:
            problems.append(
                f"{destination}: {name} is {actual[name][0]} ({actual[name][1][:12]}) but"
                f" {source / name} is {expected[name][0]} ({expected[name][1][:12]})."
            )
    return problems


def installed_copy_problems(
    source: pathlib.Path, destination: pathlib.Path, version: str
) -> list[str]:
    """A copy install must reproduce the bundled skill entry for entry.

    The digests are compared as well as the trees, because the digest is what every later
    run decides on: a copy that reads the same but hashes differently is reported as
    edited for ever afterwards.
    """
    if destination.is_symlink() or not destination.is_dir():
        return [f"{destination} is not a directory; a copy install must create one."]
    expected = contents(snapshot(source))
    if not expected:
        return [f"{source} holds nothing, so comparing {destination} against it proves nothing."]
    actual = contents(snapshot(destination))
    problems: list[str] = []
    if actual.pop(MANIFEST_NAME, None) is None:
        problems.append(
            f"{destination} holds no {MANIFEST_NAME}; nothing records who installed it."
        )
    problems += difference_problems(source, destination, expected, actual)
    problems += manifest_problems(destination, source, version, InstallMode.COPY)
    installed_digest = installer._tree_digest(destination)
    if installed_digest != installer._tree_digest(source):
        problems.append(
            f"{destination} hashes to {installed_digest[:12]} but {source} hashes to"
            f" {installer._tree_digest(source)[:12]}; every later run would call this copy edited."
        )
    return problems


def linked_install_problems(
    source: pathlib.Path, destination: pathlib.Path, version: str
) -> list[str]:
    """A symlink install must be a real directory of links into the installed package.

    Not a single link to the package: the ownership manifest is written into the
    destination, and a link would put it inside the installed package instead.
    """
    if destination.is_symlink() or not destination.is_dir():
        return [f"{destination} is not a directory; a symlink install must create one."]
    expected = {entry.name for entry in source.iterdir()}
    if not expected:
        return [f"{source} holds nothing to link to."]
    actual = {entry.name: entry for entry in destination.iterdir() if entry.name != MANIFEST_NAME}
    problems: list[str] = []
    if set(actual) != expected:
        problems.append(f"{destination} links {sorted(actual)}; {source} holds {sorted(expected)}.")
    for name, entry in sorted(actual.items()):
        if not entry.is_symlink():
            problems.append(
                f"{entry} is a real file or directory rather than a link into {source}."
            )
        elif entry.readlink() != source / name:
            problems.append(f"{entry} links to {entry.readlink()}, not to {source / name}.")
    problems += entry_document_readable_problems(source, destination)
    problems += manifest_problems(destination, source, version, InstallMode.SYMLINK)
    return problems


def entry_document_readable_problems(source: pathlib.Path, destination: pathlib.Path) -> list[str]:
    """The entry document must read back through the destination, or no agent finds it."""
    try:
        installed = (destination / ENTRY_DOCUMENT).read_bytes()
    except OSError as error:
        return [f"{destination / ENTRY_DOCUMENT} cannot be read: {error}."]
    if installed != (source / ENTRY_DOCUMENT).read_bytes():
        return [f"{destination / ENTRY_DOCUMENT} does not read back as {source / ENTRY_DOCUMENT}."]
    return []


def unchanged_problems(destination: pathlib.Path, before: dict[str, Entry]) -> list[str]:
    """Nothing under ``destination`` may have been read back differently, or rewritten."""
    if not before:
        return [f"{destination} held nothing before the run, so comparing it proves nothing."]
    if destination.is_symlink() or not destination.is_dir():
        return [
            f"{destination} is no longer a directory; it held {len(before)} entries"
            " before the run and has to hold them still."
        ]
    after = snapshot(destination)
    problems: list[str] = []
    for name in sorted(set(after) - set(before)):
        problems.append(
            f"{destination}: {name} appeared ({describe(after[name])}) in an untouched run."
        )
    for name in sorted(set(before) - set(after)):
        problems.append(f"{destination}: {name} was removed ({describe(before[name])}).")
    for name in sorted(set(before) & set(after)):
        old, new = before[name], after[name]
        if (new.kind, new.payload) != (old.kind, old.payload):
            problems.append(
                f"{destination}: {name} was rewritten: {describe(old)} became {describe(new)}."
            )
        elif (new.mtime_ns, new.inode) != (old.mtime_ns, old.inode):
            problems.append(
                f"{destination}: {name} was written again with the same content"
                " (its modification time or inode changed); an untouched run writes nothing."
            )
    return problems


def staging_remnant_problems(project: pathlib.Path) -> list[str]:
    """No half-written tree may be left beside a destination once a run has returned."""
    problems: list[str] = []
    for target in ALL_TARGETS:
        parent = project / target.value
        if not parent.is_dir():
            continue
        for entry in sorted(parent.iterdir()):
            if entry.name.startswith(STAGING_PREFIX):
                problems.append(
                    f"{entry} was left behind; a run must remove what it staged before returning."
                )
    return problems


def reason_problems(failure: SkillInstallFailure, mentions: Sequence[str] = ()) -> list[str]:
    problems: list[str] = []
    if not failure.reason.strip():
        problems.append(f"{failure.destination}: the failure carries no reason to show the user.")
    problems += [
        f"{failure.destination}: the reason does not name {mention}: {failure.reason}"
        for mention in mentions
        if mention not in failure.reason
    ]
    return problems


def refusal_problems(
    report: SkillInstallReport,
    destination: pathlib.Path,
    kind: SkillFailureKind,
    mentions: Sequence[str] = (),
) -> list[str]:
    failure = failure_for(report, destination)
    if failure is None:
        return [
            f"{destination} must be reported as failed with {kind.value};"
            f" got {describe_report(report)}"
        ]
    if failure.kind is not kind:
        return [f"{destination} was refused as {failure.kind.value}, expected {kind.value}."]
    return reason_problems(failure, mentions)


# ---------------------------------------------------------------------------
# Scenarios: setup, one or two runs, and the filesystem afterwards.
# ---------------------------------------------------------------------------


def fresh_install_problems(project: pathlib.Path, bundle: Bundle) -> list[str]:
    report = install_skills(project, targets=ALL_TARGETS)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    problems += partition_problems(report, expected)
    if set(report.installed) != set(expected):
        problems.append(
            f"a first run must install every destination; got {describe_report(report)}"
        )
    for destination in expected:
        problems += installed_copy_problems(
            bundle.source_for(destination), destination, INSTALLED_VERSION
        )
    for target in ALL_TARGETS:
        stray = project / target.value / "shared-fragments"
        if stray.exists():
            problems.append(f"{stray}: a directory holding no {ENTRY_DOCUMENT} is not a skill.")
    problems += staging_remnant_problems(project)
    return problems


def non_vacuity_problems(expected: Sequence[pathlib.Path]) -> list[str]:
    if len(expected) < MIN_DESTINATIONS:
        return [
            f"expected at least {MIN_DESTINATIONS} destinations to check, got"
            f" {[str(path) for path in expected]}"
        ]
    return []


def idempotency_problems(project: pathlib.Path, bundle: Bundle, mode: InstallMode) -> list[str]:
    first = install_skills(project, targets=ALL_TARGETS, mode=mode)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    if first.failed:
        return [
            *problems,
            f"the first run must succeed before idempotency means anything;"
            f" got {describe_report(first)}",
        ]
    before = {destination: snapshot(destination) for destination in expected}

    second = install_skills(project, targets=ALL_TARGETS, mode=mode)

    problems += partition_problems(second, expected)
    if set(second.up_to_date) != set(expected):
        problems.append(
            f"a second run must leave every destination alone; got {describe_report(second)}"
        )
    for destination, recorded in before.items():
        problems += unchanged_problems(destination, recorded)
    problems += staging_remnant_problems(project)
    return problems


@dataclasses.dataclass(frozen=True)
class InstalledProject:
    """A project with every skill installed, and what everything looked like then.

    Both sides are recorded, the project and the package, because the questions a
    re-run answers are all comparisons between the two: what the destination held when
    it was installed, and what the package ships now.
    """

    project: pathlib.Path
    bundle: Bundle
    destinations: list[pathlib.Path]
    installed: dict[pathlib.Path, dict[str, Entry]]
    bundled: dict[str, dict[str, tuple[str, str]]]


def install_and_record(project: pathlib.Path, bundle: Bundle) -> InstalledProject:
    """Install every skill and record the state a later run will be measured against."""
    install_skills(project, targets=ALL_TARGETS)
    destinations = expected_destinations(project, bundle)
    return InstalledProject(
        project=project,
        bundle=bundle,
        destinations=destinations,
        installed={destination: snapshot(destination) for destination in destinations},
        bundled={skill.name: contents(snapshot(skill)) for skill in bundle.skills},
    )


def rewrite_bundled_skills(bundle: Bundle) -> None:
    """Change what the package ships, leaving its version alone.

    Kept separate from the version so that either can be moved without the other. A
    release changes both; a source checkout or an editable install changes only this,
    and that is the case in which the recorded hash is the only thing that notices.
    """
    for skill in bundle.skills:
        (skill / ENTRY_DOCUMENT).write_text(
            f"---\nname: {skill.name}\n---\n\n# {skill.name}, rewritten since the install\n",
            encoding="utf-8",
        )
        (skill / REFERENCE_DIR / "added.md").write_text(
            "# added since the install\n", encoding="utf-8"
        )


def replacement_problems(
    state: InstalledProject, report: SkillInstallReport, content_changed: bool
) -> list[str]:
    """Every destination must now hold what the package holds.

    ``content_changed`` is a dimension the caller sets, not something this decides: a
    run can reach here because the version moved, because the content moved, or because
    both did, and a check that assumed one of those would stop being able to tell the
    others apart. It is verified before it is used -- a "content moved" run in which the
    package did not actually change proves nothing, and neither does a "version only"
    run in which the content moved as well.
    """
    problems = non_vacuity_problems(state.destinations)
    problems += partition_problems(report, state.destinations)
    if set(report.replaced) != set(state.destinations):
        problems.append(f"every installed skill must be replaced; got {describe_report(report)}")
    for destination in state.destinations:
        source = state.bundle.source_for(destination)
        moved = contents(snapshot(source)) != state.bundled[source.name]
        if moved is not content_changed:
            problems.append(
                f"{source} {'changed' if moved else 'did not change'} since the install,"
                f" which is not the run this is checking (content_changed={content_changed})."
            )
        problems += installed_copy_problems(source, destination, great_expectations.__version__)
        if content_changed:
            problems += arrival_problems(destination, state.installed[destination])
    problems += staging_remnant_problems(state.project)
    return problems


def arrival_problems(destination: pathlib.Path, before: dict[str, Entry]) -> list[str]:
    """The new content has to have reached the destination, not just the manifest.

    A run that rewrote the ownership manifest and nothing else reports every destination
    as replaced and leaves the user reading the skill they had before.
    """
    was = {name: (entry.kind, entry.payload) for name, entry in before.items()}
    now = contents(snapshot(destination))
    if {name: entry for name, entry in was.items() if name != MANIFEST_NAME} == {
        name: entry for name, entry in now.items() if name != MANIFEST_NAME
    }:
        return [
            f"{destination} holds exactly what it held before the run: the changed skill"
            " never reached the project, whatever the report says."
        ]
    return []


@dataclasses.dataclass(frozen=True)
class EditedSkill:
    """An installed skill the user has since edited, and the run's other destinations."""

    project: pathlib.Path
    bundle: Bundle
    edited: pathlib.Path
    others: list[pathlib.Path]
    before: dict[str, Entry]


def install_and_edit(project: pathlib.Path, bundle: Bundle) -> EditedSkill:
    """Install every skill, then add a file to one of the installed copies.

    The edit and the package version are deliberately left as two separate dimensions.
    A setup that always bumped the version alongside the edit would leave "the user
    edited this" and "this is from an older release" indistinguishable, and no test built
    on it could show which of the two a refusal -- or a repair -- was really keyed on.
    """
    install_skills(project, targets=ALL_TARGETS)
    edited = project / SkillTarget.AGENTS.value / bundle.names[0]
    (edited / REFERENCE_DIR / "notes.md").write_text("notes the user added\n", encoding="utf-8")
    expected = expected_destinations(project, bundle)
    return EditedSkill(
        project=project,
        bundle=bundle,
        edited=edited,
        others=[destination for destination in expected if destination != edited],
        before=snapshot(edited),
    )


def edited_skill_problems(
    state: EditedSkill, report: SkillInstallReport, force: bool, stale: bool
) -> list[str]:
    """What a re-run must have done to an edited copy, and to everything around it.

    ``stale`` says only whether the package moved on since the install, which changes
    what happens to the destinations that were *not* edited. The edited one's outcome is
    the same either way, and that is the contract: ownership is decided before staleness,
    so a run that compared versions first would replace an edited copy and lose the edits
    on the very command that is supposed to be safe to re-run.
    """
    expected = [state.edited, *state.others]
    problems = non_vacuity_problems(expected)
    problems += partition_problems(report, expected)
    untouched = report.replaced if stale else report.up_to_date
    if set(untouched) - {state.edited} != set(state.others):
        expectation = "brought up to the new version" if stale else "left up to date"
        problems.append(
            f"the destinations that were not edited must be {expectation};"
            f" got {describe_report(report)}"
        )
    if force:
        if state.edited not in report.replaced:
            problems.append(f"--force must replace {state.edited}; got {describe_report(report)}")
        problems += forced_repair_problems(state)
    else:
        problems += refusal_problems(report, state.edited, SkillFailureKind.LOCALLY_MODIFIED)
        problems += unchanged_problems(state.edited, state.before)
    problems += staging_remnant_problems(state.project)
    return problems


def forced_repair_problems(state: EditedSkill) -> list[str]:
    """After ``--force``, the edited copy must be the bundled skill and nothing else."""
    problems: list[str] = []
    if (state.edited / REFERENCE_DIR / "notes.md").exists():
        problems.append(f"{state.edited} still holds the edit --force was asked to overwrite.")
    problems += installed_copy_problems(
        state.bundle.source_for(state.edited), state.edited, great_expectations.__version__
    )
    return problems


#: An ownership manifest that parses, and names an owner that is not this package.
ANOTHER_OWNERS_MANIFEST: Final = json.dumps(
    {"managed_by": "some-other-tool", "gx_version": INSTALLED_VERSION, "mode": "copy"},
    indent=2,
    sort_keys=True,
)

#: Bytes that are not text at all: what a truncated write, a compressed file restored
#: under the wrong name, or an editor saving in another encoding leaves behind.
UNDECODABLE_MANIFEST: Final = b'{"managed_by": "\xff\xfegreat_expectations"}'

#: Every way a destination can fail to prove that Great Expectations installed it, one
#: per branch that decides it: absent or unreadable, bytes that will not decode, text
#: that will not parse, JSON that is not a mapping, and a mapping naming another owner.
#: Ownership that cannot be proved is ownership by someone else, so all of these have to
#: be refused identically -- and none of them may end the run, since the manifest is read
#: before the point at which a destination's problems start being caught.
UNPROVEN_OWNERSHIP: Final = [
    pytest.param(None, id="no_manifest"),
    pytest.param(UNDECODABLE_MANIFEST, id="undecodable"),
    pytest.param("{ this never parsed", id="unparseable"),
    pytest.param('["great_expectations"]', id="not_a_mapping"),
    pytest.param(ANOTHER_OWNERS_MANIFEST, id="another_owner"),
]


def undecodable_problems(manifest: bytes) -> list[str]:
    """The bytes have to be undecodable, or the case they stand for is not being tested."""
    try:
        manifest.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return [f"{manifest!r} decodes as UTF-8, so it does not stand for a manifest that cannot."]


def foreign_destination_problems(
    project: pathlib.Path, bundle: Bundle, force: bool, manifest: str | bytes | None = None
) -> list[str]:
    """A destination this package did not install is never replaced, with or without force.

    ``manifest`` is what sits at the ownership manifest's path: nothing, or a file that
    fails to prove ownership -- as text that cannot be decoded, cannot be parsed, or
    parses into something that is not this package's. A directory another tool manages is
    the case that looks most like one of ours, since it holds a manifest and that
    manifest parses, so only the recorded owner tells them apart.
    """
    foreign = project / SkillTarget.CLAUDE.value / bundle.names[0]
    foreign.mkdir(parents=True)
    (foreign / ENTRY_DOCUMENT).write_text("---\nname: mine\n---\n\n# a skill I wrote\n", "utf-8")
    (foreign / "notes.md").write_text("notes of my own\n", encoding="utf-8")
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    if isinstance(manifest, bytes):
        (foreign / MANIFEST_NAME).write_bytes(manifest)
        problems += undecodable_problems(manifest)
    elif manifest is not None:
        (foreign / MANIFEST_NAME).write_text(manifest, encoding="utf-8")
    before = snapshot(foreign)

    try:
        report = install_skills(project, targets=ALL_TARGETS, force=force)
    except Exception as error:
        # Caught rather than allowed to end the test, because "the run did not survive
        # this destination" is the finding, and the module's whole promise is that a
        # problem with one skill is reported instead of raised.
        return [
            *problems,
            "a destination that cannot be read as one of ours must cost that destination"
            f" and no more; the run raised {error!r}",
        ]

    problems += partition_problems(report, expected)
    problems += refusal_problems(report, foreign, SkillFailureKind.FOREIGN_DESTINATION)
    problems += unchanged_problems(foreign, before)
    others = [destination for destination in expected if destination != foreign]
    if set(report.installed) != set(others):
        problems.append(
            f"refusing one destination must not stop the others; got {describe_report(report)}"
        )
    for destination in others:
        problems += installed_copy_problems(
            bundle.source_for(destination), destination, INSTALLED_VERSION
        )
    problems += staging_remnant_problems(project)
    return problems


def write_failure_problems(project: pathlib.Path, bundle: Bundle) -> list[str]:
    """A failed first write must disclose itself and leave nothing at the destination."""
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)

    report = install_skills(project, targets=ALL_TARGETS)

    problems += partition_problems(report, expected)
    for destination in expected:
        problems += refusal_problems(report, destination, SkillFailureKind.WRITE_FAILED)
        if destination.exists() or destination.is_symlink():
            problems.append(
                f"{destination} exists after a write that failed; a run that could not"
                " finish must leave nothing an agent could read."
            )
    problems += staging_remnant_problems(project)
    return problems


def failed_replacement_problems(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    """A failed replacement must leave the skill that was already installed intact."""
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    install_skills(project, targets=ALL_TARGETS)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    before = {destination: snapshot(destination) for destination in expected}
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)
    break_writing(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS)

    problems += partition_problems(report, expected)
    for destination in expected:
        problems += refusal_problems(report, destination, SkillFailureKind.WRITE_FAILED)
        problems += unchanged_problems(destination, before[destination])
    problems += staging_remnant_problems(project)
    return problems


def swap_failure_problems(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch, restore: bool = True
) -> list[str]:
    """A rename that fails while the destination is briefly absent must put it back.

    Replacing an existing skill cannot be one rename, because renaming onto a non-empty
    directory is not allowed: the old tree is moved aside first, and between the two
    renames the destination does not exist. A failure in that window is the only way this
    module can lose a skill it was asked to update, so the previous contents are moved
    back and the failure is reported against that destination alone.
    """
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    install_skills(project, targets=ALL_TARGETS)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    before = {destination: snapshot(destination) for destination in expected}
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)
    break_the_swap(monkeypatch, restore=restore)

    report = install_skills(project, targets=ALL_TARGETS)

    problems += partition_problems(report, expected)
    for destination in expected:
        # The reason names the staging directory the previous contents may be sitting in,
        # which is what makes it worth reading next to a failure that never got that far.
        problems += refusal_problems(
            report, destination, SkillFailureKind.WRITE_FAILED, mentions=[STAGING_PREFIX]
        )
        problems += unchanged_problems(destination, before[destination])
    problems += staging_remnant_problems(project)
    return problems


def remnant_sweep_problems(project: pathlib.Path, bundle: Bundle) -> list[str]:
    """A tree left behind by an interrupted run is cleaned up by the next one.

    Staging beside the destination is what keeps a crash from producing a half-written
    skill, and it is only free of litter if the leftovers are swept: without this the
    project accumulates a directory per interrupted run, for ever.
    """
    install_skills(project, targets=ALL_TARGETS)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    remnant = project / SkillTarget.AGENTS.value / f"{STAGING_PREFIX}{bundle.names[0]}-9c1f0ae4b2d7"
    (remnant / REFERENCE_DIR).mkdir(parents=True)
    (remnant / ENTRY_DOCUMENT).write_text("half a skill, left by a crash\n", encoding="utf-8")
    if not remnant.is_dir():
        return [f"{remnant} was not created, so sweeping it proves nothing."]
    before = {destination: snapshot(destination) for destination in expected}

    report = install_skills(project, targets=ALL_TARGETS)

    problems += partition_problems(report, expected)
    if set(report.up_to_date) != set(expected):
        problems.append(
            f"a run over an unchanged project must leave it alone; got {describe_report(report)}"
        )
    problems += staging_remnant_problems(project)
    for destination in expected:
        problems += unchanged_problems(destination, before[destination])
    return problems


def unreadable_destination_problems(project: pathlib.Path, bundle: Bundle) -> list[str]:
    """One path this user cannot read must cost one destination, not the whole run."""
    install_skills(project, targets=ALL_TARGETS)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    damaged = project / SkillTarget.AGENTS.value / bundle.names[0]
    unreadable = damaged / REFERENCE_DIR
    before = {destination: snapshot(destination) for destination in expected}
    others = [destination for destination in expected if destination != damaged]

    report: SkillInstallReport | None = None
    with made_unreadable(unreadable):
        if is_readable(unreadable):
            return [
                f"{unreadable} is still readable with no permissions at all, so this check"
                " cannot mean anything; it has to run as a user the filesystem restricts."
            ]
        try:
            report = install_skills(project, targets=ALL_TARGETS)
        except OSError as error:
            problems.append(
                f"a path that cannot be read must cost one destination, not the run;"
                f" the run raised {error!r}"
            )
    if report is None:
        return problems

    problems += partition_problems(report, expected)
    problems += refusal_problems(
        report, damaged, SkillFailureKind.UNREADABLE_DESTINATION, mentions=[str(unreadable)]
    )
    if set(report.up_to_date) != set(others):
        problems.append(
            f"every other destination must still be handled; got {describe_report(report)}"
        )
    for destination in expected:
        problems += unchanged_problems(destination, before[destination])
    return problems


def empty_bundle_problems(project: pathlib.Path) -> list[str]:
    """A package that bundles nothing must be refused, not reported as a clean run."""
    try:
        report = install_skills(project, targets=ALL_TARGETS)
    except FileNotFoundError as error:
        problems = []
        if "bundles no agent skills" not in str(error):
            problems.append(f"the refusal must say the package bundles no skills; got {error}")
        if any(project.iterdir()):
            problems.append(f"{project} must be left alone when there is nothing to install.")
        return problems
    return [
        "a package bundling no skills must be refused: a run in which nothing was installed"
        f" was reported as a run in which nothing went wrong ({describe_report(report)})"
    ]


def mode_switch_problems(
    project: pathlib.Path, bundle: Bundle, installed_as: InstallMode, asked_for: InstallMode
) -> list[str]:
    """Re-running in a different mode must convert what is installed, not skip it.

    The two modes hold the same content, the same version and the same recorded hash, so
    the only thing that distinguishes an installed copy from an installed link is the
    mode the manifest records. A run that did not compare it would tell a user who asked
    for links that everything was already up to date, and leave them with copies.
    """
    install_skills(project, targets=ALL_TARGETS, mode=installed_as)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)

    report = install_skills(project, targets=ALL_TARGETS, mode=asked_for)

    problems += partition_problems(report, expected)
    if set(report.replaced) != set(expected):
        problems.append(
            f"asking for {asked_for.value} where {installed_as.value} is installed must"
            f" replace every destination; got {describe_report(report)}"
        )
    check = linked_install_problems if asked_for is InstallMode.SYMLINK else installed_copy_problems
    for destination in expected:
        problems += check(
            bundle.source_for(destination), destination, great_expectations.__version__
        )
    problems += staging_remnant_problems(project)
    return problems


def symlink_mode_problems(project: pathlib.Path, bundle: Bundle) -> list[str]:
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)

    report = install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)

    problems += partition_problems(report, expected)
    if set(report.installed) != set(expected):
        problems.append(
            f"a first run must install every destination; got {describe_report(report)}"
        )
    for destination in expected:
        problems += linked_install_problems(
            bundle.source_for(destination), destination, INSTALLED_VERSION
        )
    problems += staging_remnant_problems(project)
    return problems


# ---------------------------------------------------------------------------
# Deliberately broken builds of the installer, each modelling a defect the
# checks above exist to catch.
# ---------------------------------------------------------------------------


def stop_writing_manifests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Installs the content but records no ownership, so no later run can tell it is ours."""
    monkeypatch.setattr(installer, "_write_manifest", lambda *arguments: None)


def dereference_symlinks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Copies what a link points at instead of the link, the way a plain copytree does."""
    real = shutil.copytree

    def copytree(source, destination, symlinks=False, *arguments, **keywords):
        keywords.pop("symlinks", None)
        return real(source, destination, False, *arguments, **keywords)

    monkeypatch.setattr(shutil, "copytree", copytree)


def ignore_the_version_stamp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treats every destination as stale, so a second run rewrites what it just wrote."""
    monkeypatch.setattr(installer, "_is_current", lambda *arguments: False)


def treat_everything_as_current(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treats every destination as up to date, so an upgrade never reaches the project."""
    monkeypatch.setattr(installer, "_is_current", lambda *arguments: True)


def stop_comparing_the_recorded_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    """Compares the version and the mode, but not the content the manifest recorded.

    Two releases can ship identical skills, and a source checkout ships changed skills
    under the version it was already carrying, so the recorded hash is the only thing
    that notices content moving without the version moving. Without it, anyone
    developing against an editable install re-runs the command, is told everything is
    up to date, and never sees their change reach the project.
    """

    def is_current(destination, source, manifest, digest, context):
        if (
            manifest.get("gx_version") != context.version
            or manifest.get("mode") != context.mode.value
        ):
            return False
        if context.mode is InstallMode.SYMLINK:
            return installer._links_point_at(destination, source)
        return True

    monkeypatch.setattr(installer, "_is_current", is_current)


def ignore_local_edits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Trusts every managed destination, so the user's edits are silently overwritten."""
    monkeypatch.setattr(installer, "_is_unmodified", lambda *arguments: True)


def install_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reports every destination as written and writes nothing at all."""
    monkeypatch.setattr(installer, "_materialize", lambda *arguments: None)


def claim_every_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reads an ownership manifest out of any directory, including the user's own."""
    monkeypatch.setattr(
        installer,
        "read_skill_manifest",
        lambda directory: {"managed_by": "great_expectations", "mode": InstallMode.COPY.value},
    )


def stop_checking_the_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accepts any manifest that parses, without asking whose it is.

    The narrower slip: a manifest that is missing, unreadable or not a mapping is still
    rejected, so every destination that holds no manifest behaves exactly as before. Only
    a directory another tool manages changes hands -- and it is the case that looks most
    like one of ours.
    """

    def read_skill_manifest(directory):
        try:
            raw = (directory / MANIFEST_NAME).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        try:
            manifest = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return manifest if isinstance(manifest, dict) else None

    monkeypatch.setattr(installer, "read_skill_manifest", read_skill_manifest)


def stop_swallowing_undecodable_manifests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reads the manifest as text without allowing for bytes that are not text.

    Every other way of failing to prove ownership is answered with "not ours". This one
    escapes instead -- and it escapes from the one call made before the caller starts
    guarding, so it does not cost a destination, it ends the whole run: every other
    skill and every other target with it, under a traceback rather than a report.
    """

    def read_skill_manifest(directory):
        try:
            raw = (directory / MANIFEST_NAME).read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            manifest = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(manifest, dict) or manifest.get("managed_by") != "great_expectations":
            return None
        return manifest

    monkeypatch.setattr(installer, "read_skill_manifest", read_skill_manifest)


def ignore_edits_when_deciding_staleness(monkeypatch: pytest.MonkeyPatch) -> None:
    """Decides staleness without first asking whether the copy was edited.

    Production asks "does this already hold what the run would install?" only of copies
    that still match their own manifest. Dropping that one conjunction leaves an edited
    copy at the current version looking up to date, so ``--force`` reports success,
    writes nothing, and the edit stays where it is: a repair the command claims to have
    made and did not. Everything else about this build is production's own code.
    """

    def install_one(source, destination, digest, context):
        if not installer._lexists(destination):
            installer._materialize(source, destination, digest, context)
            return installer._Outcome.INSTALLED
        manifest = installer.read_skill_manifest(destination)
        if manifest is None:
            raise installer._SkillRefusal(
                SkillFailureKind.FOREIGN_DESTINATION, installer._FOREIGN_DESTINATION_REASON
            )
        try:
            unmodified = installer._is_unmodified(destination, manifest)
            current = installer._is_current(destination, source, manifest, digest, context)
        except OSError as error:
            raise installer._SkillRefusal(
                SkillFailureKind.UNREADABLE_DESTINATION,
                installer._unreadable_destination_reason(error),
            ) from error
        if not unmodified and not context.force:
            raise installer._SkillRefusal(
                SkillFailureKind.LOCALLY_MODIFIED, installer._LOCALLY_MODIFIED_REASON
            )
        if current:
            return installer._Outcome.UP_TO_DATE
        installer._materialize(source, destination, digest, context)
        return installer._Outcome.REPLACED

    monkeypatch.setattr(installer, "_install_one", install_one)


def break_the_swap(monkeypatch: pytest.MonkeyPatch, restore: bool = True) -> None:
    """Fails the rename that moves a staged tree into place.

    By then the previous tree has already been renamed aside, so this is the one moment
    at which the destination does not exist. ``restore`` leaves the second attempt --
    the one that puts the previous tree back -- working, which is what production
    promises; turning it off models a filesystem that fails that too, and shows what the
    check would have to notice.
    """
    real = pathlib.Path.replace
    failed: set[str] = set()

    def replace(self, target):
        target = pathlib.Path(target)
        moving_into_place = self.name.startswith(STAGING_PREFIX) and not target.name.startswith(
            STAGING_PREFIX
        )
        if moving_into_place and (not restore or str(target) not in failed):
            failed.add(str(target))
            raise OSError(16, "Device or resource busy", str(target))
        return real(self, target)

    monkeypatch.setattr(pathlib.Path, "replace", replace)


def break_writing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails partway through writing, the way a full disk does: some files, then an error."""

    def copytree(source, destination, *arguments, **keywords):
        source, destination = pathlib.Path(source), pathlib.Path(destination)
        destination.mkdir(parents=True)
        shutil.copy2(source / ENTRY_DOCUMENT, destination / ENTRY_DOCUMENT)
        raise OSError(28, "No space left on device", str(destination))

    monkeypatch.setattr(shutil, "copytree", copytree)


def leave_staging_behind(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never cleans up, so a failed write leaves its half-written tree in the project."""
    monkeypatch.setattr(installer, "_remove", lambda path: None)


def write_without_staging(monkeypatch: pytest.MonkeyPatch) -> None:
    """Writes straight into the destination, so a failure leaves a half-written skill."""

    def materialize(source, destination, digest, context):
        installer._remove(destination)
        installer._stage(source, destination, context.mode)
        installer._write_manifest(destination, digest, context)

    monkeypatch.setattr(installer, "_materialize", materialize)


def abort_on_read_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lets a read error end the whole run instead of costing one destination."""
    real = installer._install_one

    def install_one(source, destination, digest, context):
        try:
            return real(source, destination, digest, context)
        except installer._SkillRefusal as refusal:
            if refusal.kind is SkillFailureKind.UNREADABLE_DESTINATION:
                raise OSError(str(refusal)) from refusal
            raise

    monkeypatch.setattr(installer, "_install_one", install_one)


def treat_unreadable_as_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """Answers "has the user edited this?" with "no" when it cannot read the answer."""
    real = installer._is_unmodified

    def is_unmodified(destination, manifest):
        try:
            return real(destination, manifest)
        except OSError:
            return True

    monkeypatch.setattr(installer, "_is_unmodified", is_unmodified)


def report_an_empty_bundle_as_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns no skills where a defective installation should be refused outright."""
    monkeypatch.setattr(installer, "iter_bundled_skills", lambda: iter(()))


def ignore_the_install_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Compares the version and the content, but not how the skill was installed.

    Copies and links carry the same recorded hash -- it describes the package's content,
    which is what both of them serve -- so without the mode a project installed one way
    is reported up to date when the other way is asked for.
    """

    def is_current(destination, source, manifest, digest, context):
        return (
            manifest.get("gx_version") == context.version
            and manifest.get("content_sha256") == digest
        )

    monkeypatch.setattr(installer, "_is_current", is_current)


def trust_links_without_looking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Assumes installed links still point into the package, wherever it has got to."""
    monkeypatch.setattr(installer, "_links_point_at", lambda destination, source: True)


def copy_where_links_were_asked_for(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ignores symlink mode and copies, so the install stops tracking the package."""

    def stage(source, staging, mode):
        shutil.copytree(source, staging, symlinks=True)

    monkeypatch.setattr(installer, "_stage", stage)


def refuse_to_make_links(monkeypatch: pytest.MonkeyPatch) -> None:
    """A platform that permits symlinks only for privileged accounts."""

    def symlink_to(self, target, target_is_directory=False):
        raise OSError(1, "Operation not permitted", str(self))

    monkeypatch.setattr(pathlib.Path, "symlink_to", symlink_to)


def hide_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drops the refusals from the report the command exits on."""
    real = command_line.install_skills

    def install(*arguments, **keywords):
        return dataclasses.replace(real(*arguments, **keywords), failed=())

    monkeypatch.setattr(command_line, "install_skills", install)


def hide_the_outcome_group(monkeypatch: pytest.MonkeyPatch, group: str) -> None:
    """Empties one whole outcome out of the report the command prints.

    Indistinguishable, from the printing code's side, from a build that stopped printing
    that group: the destinations are installed correctly either way, the command still
    exits 0, and the only thing lost is the user being told.
    """
    real = command_line.install_skills

    def install(*arguments, **keywords):
        return dataclasses.replace(real(*arguments, **keywords), **{group: ()})

    monkeypatch.setattr(command_line, "install_skills", install)


def label_failures_by_appearance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Derives the failure kind from the destination afterwards instead of recording it.

    This is the heuristic the typed failure kind replaced: a destination that exists and
    holds an ownership manifest is called edited. A destination whose subdirectory could
    not be read satisfies both conditions, which is exactly why the kind cannot be
    recovered after the fact.
    """
    real = command_line.install_skills

    def install(*arguments, **keywords):
        report = real(*arguments, **keywords)
        return dataclasses.replace(
            report,
            failed=tuple(
                dataclasses.replace(failure, kind=SkillFailureKind.LOCALLY_MODIFIED)
                if failure.destination.exists()
                and installer.read_skill_manifest(failure.destination) is not None
                else failure
                for failure in report.failed
            ),
        )

    monkeypatch.setattr(command_line, "install_skills", install)


# ---------------------------------------------------------------------------
# A first run.
# ---------------------------------------------------------------------------


def test_a_first_run_installs_every_skill_into_every_target(project: pathlib.Path, bundle: Bundle):
    assert not fresh_install_problems(project, bundle)


def test_a_first_run_without_ownership_manifests_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    stop_writing_manifests(monkeypatch)

    problems = fresh_install_problems(project, bundle)

    assert [problem for problem in problems if MANIFEST_NAME in problem]


def test_the_skills_this_package_bundles_install_as_exact_copies(project: pathlib.Path):
    """The real bundle, found the way an installed package is: through the import system.

    The digest comparison inside is the claim the rest of the installer rests on. If a
    bundled skill does not hash to the same value once installed -- which is what happens
    the moment a copy stops preserving something the hash describes -- then no run after
    the first can tell an untouched install from one the user edited.
    """
    skills = list(installer.iter_bundled_skills())
    assert len(skills) >= MIN_BUNDLED_SKILLS, f"found {[skill.name for skill in skills]}"
    assert {skill.parent for skill in skills} == {BUNDLED_SKILLS_ROOT}, (
        f"the package resolved its skills to {sorted({str(skill.parent) for skill in skills})},"
        f" not to {BUNDLED_SKILLS_ROOT}"
    )

    report = install_skills(project, targets=ALL_TARGETS)

    expected = [project / target.value / skill.name for target in ALL_TARGETS for skill in skills]
    assert not partition_problems(report, expected)
    assert set(report.installed) == set(expected), describe_report(report)
    problems = [
        problem
        for destination in expected
        for problem in installed_copy_problems(
            BUNDLED_SKILLS_ROOT / destination.name,
            destination,
            great_expectations.__version__,
        )
    ]
    assert not problems, "\n".join(problems)


def test_a_copy_that_dereferenced_a_link_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """Dereferencing is the one copying defect a report cannot show: every file arrives.

    What arrives is a real file where the package holds a link, so the copy hashes
    differently from the skill it was copied from and every later run calls it edited.
    """
    (bundle.root / bundle.names[0] / REFERENCE_DIR / "shared.md").symlink_to(
        pathlib.Path("guide.md")
    )
    dereference_symlinks(monkeypatch)

    problems = fresh_install_problems(project, bundle)

    assert [problem for problem in problems if "hashes to" in problem]
    assert [problem for problem in problems if "shared.md" in problem]


def test_a_copy_that_dereferenced_a_dangling_link_is_reported(
    project: pathlib.Path, bundle_with_links: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """The same defect meeting a link to a file the package no longer ships: it cannot
    copy at all, and the skill never reaches the project.
    """
    dereference_symlinks(monkeypatch)

    problems = fresh_install_problems(project, bundle_with_links)

    assert [problem for problem in problems if "is not a directory" in problem]


# ---------------------------------------------------------------------------
# The report accounts for every destination exactly once.
# ---------------------------------------------------------------------------


def test_every_destination_lands_in_exactly_one_outcome(project: pathlib.Path, bundle: Bundle):
    """One run producing all four outcomes at once, which is when a partition can slip."""
    install_skills(project, targets=ALL_TARGETS)
    first, second = bundle.names
    edited = project / SkillTarget.AGENTS.value / first
    (edited / REFERENCE_DIR / "notes.md").write_text("notes the user added\n", encoding="utf-8")
    removed = project / SkillTarget.CLAUDE.value / first
    shutil.rmtree(removed)
    stale = project / SkillTarget.CLAUDE.value / second
    stamp_manifest_version(stale, EARLIER_VERSION)
    untouched = project / SkillTarget.AGENTS.value / second

    report = install_skills(project, targets=ALL_TARGETS)

    expected = expected_destinations(project, bundle)
    assert not non_vacuity_problems(expected)
    assert not partition_problems(report, expected)
    assert report.installed == (removed,), describe_report(report)
    assert report.up_to_date == (untouched,), describe_report(report)
    assert report.replaced == (stale,), describe_report(report)
    assert [failure.destination for failure in report.failed] == [edited], describe_report(report)
    problems = [
        problem
        for destination in (removed, stale, untouched)
        for problem in installed_copy_problems(
            bundle.source_for(destination), destination, INSTALLED_VERSION
        )
    ]
    assert not problems, "\n".join(problems)


def test_a_destination_reported_twice_is_caught(tmp_path: pathlib.Path):
    destination = tmp_path / SkillTarget.AGENTS.value / "gx-first-skill"
    report = SkillInstallReport(
        installed=(destination,), up_to_date=(destination,), replaced=(), failed=()
    )

    problems = partition_problems(report, [destination])

    assert [problem for problem in problems if "installed" in problem and "up_to_date" in problem]


def test_a_destination_reported_nowhere_is_caught(tmp_path: pathlib.Path):
    destination = tmp_path / SkillTarget.AGENTS.value / "gx-first-skill"
    report = SkillInstallReport(installed=(), up_to_date=(), replaced=(), failed=())

    problems = partition_problems(report, [destination])

    assert [problem for problem in problems if "no outcome" in problem]


# ---------------------------------------------------------------------------
# Running it again.
# ---------------------------------------------------------------------------


def test_a_second_run_leaves_every_installed_skill_untouched(project: pathlib.Path, bundle: Bundle):
    assert not idempotency_problems(project, bundle, InstallMode.COPY)


def test_a_second_run_that_rewrote_the_same_content_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """A rewrite with identical bytes is invisible in the content and in the report."""
    ignore_the_version_stamp(monkeypatch)

    problems = idempotency_problems(project, bundle, InstallMode.COPY)

    assert [problem for problem in problems if "leave every destination alone" in problem]
    assert [problem for problem in problems if "written again with the same content" in problem]


def test_a_skill_holding_links_installs_and_stays_up_to_date(
    project: pathlib.Path, bundle_with_links: Bundle
):
    """Ordinary and dangling links alike: copied as links, and a no-op on the next run."""
    assert not fresh_install_problems(project, bundle_with_links)
    assert not idempotency_problems(project, bundle_with_links, InstallMode.COPY)


# ---------------------------------------------------------------------------
# Running it after an upgrade.
# ---------------------------------------------------------------------------


def test_a_new_version_alone_replaces_the_installed_skills(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """Two releases can ship byte-identical skills, and the install still has to say so:
    what the destination records is which version put it there.
    """
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    state = install_and_record(project, bundle)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)

    report = install_skills(project, targets=ALL_TARGETS)

    assert not replacement_problems(state, report, content_changed=False)


def test_changed_content_alone_replaces_the_installed_skills(project: pathlib.Path, bundle: Bundle):
    """The everyday case for anyone working on the skills themselves: an editable
    install or a source checkout ships changed content under an unchanged version, so
    the version stamp cannot be what decides whether the project is out of date.
    """
    state = install_and_record(project, bundle)
    rewrite_bundled_skills(bundle)

    report = install_skills(project, targets=ALL_TARGETS)

    assert not replacement_problems(state, report, content_changed=True)


def test_content_that_never_reached_the_project_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """The check must fail against a build that compares everything but the content."""
    state = install_and_record(project, bundle)
    rewrite_bundled_skills(bundle)
    stop_comparing_the_recorded_hash(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS)

    problems = replacement_problems(state, report, content_changed=True)
    assert [problem for problem in problems if "must be replaced" in problem]
    assert [problem for problem in problems if "added.md is missing" in problem]
    assert [problem for problem in problems if "never reached the project" in problem]


def test_an_upgrade_that_moves_both_replaces_the_installed_skills(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """A real release moves both at once, which must behave as either one alone does."""
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    state = install_and_record(project, bundle)
    rewrite_bundled_skills(bundle)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)

    report = install_skills(project, targets=ALL_TARGETS)

    assert not replacement_problems(state, report, content_changed=True)


def test_an_upgrade_left_unapplied_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    state = install_and_record(project, bundle)
    rewrite_bundled_skills(bundle)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)
    treat_everything_as_current(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS)

    problems = replacement_problems(state, report, content_changed=True)
    assert [problem for problem in problems if "added.md is missing" in problem]


# ---------------------------------------------------------------------------
# Destinations the run must not overwrite.
# ---------------------------------------------------------------------------


def test_a_skill_edited_after_it_was_installed_is_refused(project: pathlib.Path, bundle: Bundle):
    """The package has not moved on, so nothing but the edit can explain the refusal."""
    state = install_and_edit(project, bundle)

    report = install_skills(project, targets=ALL_TARGETS)

    assert not edited_skill_problems(state, report, force=False, stale=False)


def test_an_edited_skill_survives_an_upgrade(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """The dangerous case: the version moved on, so replacing would look justified."""
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    state = install_and_edit(project, bundle)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)

    report = install_skills(project, targets=ALL_TARGETS)

    assert not edited_skill_problems(state, report, force=False, stale=True)


def test_an_overwritten_local_edit_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    state = install_and_edit(project, bundle)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)
    ignore_local_edits(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS)

    problems = edited_skill_problems(state, report, force=False, stale=True)
    assert [problem for problem in problems if "LOCALLY_MODIFIED" in problem.upper()]
    assert [problem for problem in problems if "notes.md was removed" in problem]


def test_force_repairs_an_edited_skill_at_the_same_version(project: pathlib.Path, bundle: Bundle):
    """``--force`` is a repair as much as an upgrade path.

    The edited copy is the version this package would install anyway, so nothing about it
    is stale: the only thing to fix is the edit. A run that decided what to write by
    comparing versions alone would find nothing to do here and say so, leaving the edit
    in place under a command that reported success.
    """
    state = install_and_edit(project, bundle)

    report = install_skills(project, targets=ALL_TARGETS, force=True)

    assert not edited_skill_problems(state, report, force=True, stale=False)


def test_a_forced_repair_that_wrote_nothing_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """The check must fail against a build that decides staleness before ownership."""
    state = install_and_edit(project, bundle)
    ignore_edits_when_deciding_staleness(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS, force=True)

    problems = edited_skill_problems(state, report, force=True, stale=False)
    assert [problem for problem in problems if "--force must replace" in problem]
    assert [problem for problem in problems if "still holds the edit" in problem]


def test_force_replaces_an_edited_skill_across_an_upgrade(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(great_expectations, "__version__", EARLIER_VERSION)
    state = install_and_edit(project, bundle)
    monkeypatch.setattr(great_expectations, "__version__", INSTALLED_VERSION)

    report = install_skills(project, targets=ALL_TARGETS, force=True)

    assert not edited_skill_problems(state, report, force=True, stale=True)


def test_a_forced_replacement_that_wrote_nothing_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """The report says replaced either way; only the destination shows which is true."""
    state = install_and_edit(project, bundle)
    install_nothing(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS, force=True)

    problems = edited_skill_problems(state, report, force=True, stale=False)
    assert [problem for problem in problems if "still holds the edit" in problem]


@pytest.mark.parametrize("manifest", UNPROVEN_OWNERSHIP)
@pytest.mark.parametrize("force", [False, True], ids=["without_force", "with_force"])
def test_a_directory_great_expectations_did_not_install_is_never_overwritten(
    project: pathlib.Path, bundle: Bundle, force: bool, manifest: str | bytes | None
):
    assert not foreign_destination_problems(project, bundle, force=force, manifest=manifest)


def test_an_overwritten_foreign_directory_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    claim_every_directory(monkeypatch)

    problems = foreign_destination_problems(project, bundle, force=True)

    assert [problem for problem in problems if "notes.md was removed" in problem]


def test_a_manifest_that_ends_the_run_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """The check must fail against a build where one unreadable manifest ends everything.

    The ownership manifest is read before the point at which a destination's problems
    start being caught, so a way of failing that raises instead of answering does not
    cost one destination: it costs the run, and every skill that would have been
    installed after it, under a traceback rather than a report.
    """
    stop_swallowing_undecodable_manifests(monkeypatch)

    problems = foreign_destination_problems(
        project, bundle, force=True, manifest=UNDECODABLE_MANIFEST
    )

    assert [problem for problem in problems if "cost that destination and no more" in problem]


def test_a_directory_managed_by_another_tool_being_adopted_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """A manifest that parses is not a manifest that belongs to this package.

    The check must fail against a build that accepts any well-formed manifest, because
    such a directory is indistinguishable from one of ours by everything except the owner
    it records -- and adopting it overwrites whatever the other tool put there.
    """
    stop_checking_the_owner(monkeypatch)

    problems = foreign_destination_problems(
        project, bundle, force=True, manifest=ANOTHER_OWNERS_MANIFEST
    )

    assert [problem for problem in problems if "FOREIGN_DESTINATION" in problem.upper()]
    assert [problem for problem in problems if "notes.md was removed" in problem]


# ---------------------------------------------------------------------------
# Writes that fail.
# ---------------------------------------------------------------------------


def test_a_failed_write_leaves_nothing_at_the_destination(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    break_writing(monkeypatch)

    assert not write_failure_problems(project, bundle)


def test_a_half_written_tree_left_in_the_project_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    break_writing(monkeypatch)
    leave_staging_behind(monkeypatch)

    problems = write_failure_problems(project, bundle)

    assert [problem for problem in problems if STAGING_PREFIX in problem]


def test_a_failed_replacement_leaves_the_installed_skill_intact(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    assert not failed_replacement_problems(project, bundle, monkeypatch)


def test_a_replacement_written_without_staging_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """Writing in place is what makes a failure visible to an agent as a truncated skill."""
    write_without_staging(monkeypatch)

    problems = failed_replacement_problems(project, bundle, monkeypatch)

    assert [problem for problem in problems if "was removed" in problem]


def test_a_failed_swap_puts_the_previous_skill_back(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    assert not swap_failure_problems(project, bundle, monkeypatch)


def test_a_failed_swap_that_lost_the_previous_skill_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """Without the restore the destination simply stops existing, which is the whole
    reason the previous tree is moved aside rather than deleted.
    """
    problems = swap_failure_problems(project, bundle, monkeypatch, restore=False)

    assert [problem for problem in problems if "no longer a directory" in problem]


def test_a_remnant_of_an_interrupted_run_is_swept(project: pathlib.Path, bundle: Bundle):
    assert not remnant_sweep_problems(project, bundle)


def test_a_remnant_left_in_the_project_for_ever_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    leave_staging_behind(monkeypatch)

    problems = remnant_sweep_problems(project, bundle)

    assert [problem for problem in problems if STAGING_PREFIX in problem]


# ---------------------------------------------------------------------------
# Destinations that cannot be read.
# ---------------------------------------------------------------------------


def test_an_unreadable_destination_costs_one_destination_not_the_run(
    project: pathlib.Path, bundle: Bundle
):
    assert not unreadable_destination_problems(project, bundle)


def test_a_read_failure_that_ended_the_run_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    abort_on_read_failure(monkeypatch)

    problems = unreadable_destination_problems(project, bundle)

    assert [problem for problem in problems if "cost one destination, not the run" in problem]


def test_a_read_failure_reported_as_up_to_date_is_caught(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """Answering an unanswerable question is worse than failing: nothing tells the user."""
    treat_unreadable_as_unchanged(monkeypatch)

    problems = unreadable_destination_problems(project, bundle)

    assert [problem for problem in problems if "UNREADABLE_DESTINATION" in problem.upper()]


# ---------------------------------------------------------------------------
# A package with nothing to install.
# ---------------------------------------------------------------------------


def test_a_package_without_a_bundle_directory_is_refused(
    project: pathlib.Path, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    location = tmp_path / "site-packages" / "great_expectations"
    location.mkdir(parents=True)
    assert not (location / ".agents").exists()
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: types.SimpleNamespace(submodule_search_locations=[str(location)]),
    )

    assert not empty_bundle_problems(project)


def test_a_package_whose_bundle_holds_no_skills_is_refused(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    """A partly packaged installation: the reference files shipped, the entry documents
    did not. Every directory is still there, so only the entry document tells them apart.
    """
    for skill in bundle.skills:
        (skill / ENTRY_DOCUMENT).unlink()
    assert list(bundle.root.iterdir()), f"{bundle.root} must still hold directories"

    assert not empty_bundle_problems(project)


def test_an_empty_bundle_reported_as_a_clean_run_is_caught(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    report_an_empty_bundle_as_success(monkeypatch)

    problems = empty_bundle_problems(project)

    assert [problem for problem in problems if "nothing went wrong" in problem]


def test_a_project_root_that_is_not_a_directory_is_refused(tmp_path: pathlib.Path, bundle: Bundle):
    missing = tmp_path / "no-such-project"
    with pytest.raises(NotADirectoryError, match="not an existing directory"):
        install_skills(missing)
    assert not missing.exists()

    a_file = tmp_path / "a-file"
    a_file.write_text("the user pointed at a file\n", encoding="utf-8")
    with pytest.raises(NotADirectoryError, match="not an existing directory"):
        install_skills(a_file)
    assert a_file.read_text(encoding="utf-8") == "the user pointed at a file\n"


# ---------------------------------------------------------------------------
# Walking a tree that points at itself.
# ---------------------------------------------------------------------------


@pytest.fixture
def bundle_with_cycles(bundle: Bundle) -> Bundle:
    """A skill linking to its own directory, to its parent, and to itself."""
    skill = bundle.root / bundle.names[0]
    (skill / "itself").symlink_to(skill, target_is_directory=True)
    (skill / REFERENCE_DIR / "upwards").symlink_to(skill, target_is_directory=True)
    (skill / REFERENCE_DIR / "here").symlink_to(skill / REFERENCE_DIR, target_is_directory=True)
    return bundle


def walk_following_links(root: pathlib.Path) -> Iterator[str]:
    """The same walk, following symlinked directories: the defect, kept as evidence."""
    pending = [root]
    while pending:
        for entry in sorted(pending.pop().iterdir()):
            yield entry.relative_to(root).as_posix()
            if entry.is_dir():
                pending.append(entry)


def deepest(paths: Sequence[str]) -> int:
    return max(len(pathlib.PurePosixPath(path).parts) for path in paths)


def test_the_walk_behind_the_digest_terminates_on_symlink_cycles(bundle_with_cycles: Bundle):
    # Capped rather than drained: a walk that started following links would otherwise be
    # detected by this test hanging, and a hang is a much worse signal than a failure.
    skill = bundle_with_cycles.root / bundle_with_cycles.names[0]

    walked = sorted(
        relpath for relpath, _ in itertools.islice(installer._walk(skill), CYCLE_WALK_LIMIT)
    )

    assert len(walked) < CYCLE_WALK_LIMIT, "the walk was still going when it was cut off"
    assert {"itself", f"{REFERENCE_DIR}/upwards", f"{REFERENCE_DIR}/here"} <= set(walked)
    assert len(walked) == len(set(walked)), f"the walk visited a path twice: {walked}"
    assert deepest(walked) <= REAL_TREE_DEPTH, walked


def test_a_walk_that_followed_links_would_not_terminate(bundle_with_cycles: Bundle):
    """Why the walk above is written out rather than delegated to a recursive glob."""
    skill = bundle_with_cycles.root / bundle_with_cycles.names[0]

    walked: list[str] = []
    with contextlib.suppress(OSError):  # the kernel gives up on the link chain eventually
        for relpath in walk_following_links(skill):
            walked.append(relpath)
            if len(walked) >= CYCLE_WALK_LIMIT or deepest(walked) > CYCLE_DEPTH_EVIDENCE:
                break

    assert deepest(walked) > CYCLE_DEPTH_EVIDENCE, (
        f"the following walk stopped at depth {deepest(walked)}, so it proves nothing"
    )


def test_a_skill_with_symlink_cycles_installs_and_stays_up_to_date(
    project: pathlib.Path, bundle_with_cycles: Bundle
):
    assert not fresh_install_problems(project, bundle_with_cycles)
    assert not idempotency_problems(project, bundle_with_cycles, InstallMode.COPY)


# ---------------------------------------------------------------------------
# Symlink mode.
# ---------------------------------------------------------------------------


def test_symlink_mode_creates_a_directory_of_working_links(project: pathlib.Path, bundle: Bundle):
    assert not symlink_mode_problems(project, bundle)
    assert not idempotency_problems(project, bundle, InstallMode.SYMLINK)


def test_copies_where_links_were_asked_for_are_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    copy_where_links_were_asked_for(monkeypatch)

    problems = symlink_mode_problems(project, bundle)

    assert [problem for problem in problems if "rather than a link" in problem]


@pytest.mark.parametrize(
    ["installed_as", "asked_for"],
    [
        pytest.param(InstallMode.COPY, InstallMode.SYMLINK, id="copies_to_links"),
        pytest.param(InstallMode.SYMLINK, InstallMode.COPY, id="links_to_copies"),
    ],
)
def test_asking_for_the_other_mode_converts_the_installed_skills(
    project: pathlib.Path, bundle: Bundle, installed_as: InstallMode, asked_for: InstallMode
):
    # Keep both directions. Only ``links_to_copies`` rests on the recorded mode: going
    # the other way, the freshness check calls ``readlink()`` on a real file, gets an
    # OSError and reports the destination stale anyway, so that direction would still
    # pass if the mode were never compared at all.
    assert not mode_switch_problems(project, bundle, installed_as, asked_for)


def test_an_install_left_in_the_mode_it_was_not_asked_for_is_reported(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    ignore_the_install_mode(monkeypatch)

    problems = mode_switch_problems(project, bundle, InstallMode.COPY, InstallMode.SYMLINK)

    assert [problem for problem in problems if "must replace every destination" in problem]
    assert [problem for problem in problems if "rather than a link" in problem]


def test_a_symlink_install_is_refreshed_when_the_package_moves(
    project: pathlib.Path,
    bundle: Bundle,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Same version, same content, same mode -- and every link points at nothing.

    Moving the environment is the one way an installed symlink goes wrong that no hash
    can see: the content it describes has not changed, only the path it lives at, so the
    links themselves are the only thing left to compare.
    """
    install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)
    moved = tmp_path / "relocated-environment" / ".agents" / "skills"
    moved.parent.mkdir(parents=True)
    shutil.move(str(bundle.root), str(moved))
    relocated = Bundle(root=moved, names=bundle.names)
    monkeypatch.setattr(installer, "_bundled_skills_root", lambda: moved)
    expected = expected_destinations(project, relocated)
    assert not [
        destination for destination in expected if (destination / ENTRY_DOCUMENT).exists()
    ], "the installed links must be dangling before the re-run, or nothing is being fixed"

    report = install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)

    assert not partition_problems(report, expected)
    assert set(report.replaced) == set(expected), describe_report(report)
    problems = [
        problem
        for destination in expected
        for problem in linked_install_problems(
            relocated.source_for(destination), destination, INSTALLED_VERSION
        )
    ]
    assert not problems, "\n".join(problems)


def test_links_left_pointing_at_a_package_that_moved_are_reported(
    project: pathlib.Path,
    bundle: Bundle,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)
    moved = tmp_path / "relocated-environment" / ".agents" / "skills"
    moved.parent.mkdir(parents=True)
    shutil.move(str(bundle.root), str(moved))
    relocated = Bundle(root=moved, names=bundle.names)
    monkeypatch.setattr(installer, "_bundled_skills_root", lambda: moved)
    trust_links_without_looking(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)

    expected = expected_destinations(project, relocated)
    problems = [
        problem
        for destination in expected
        for problem in linked_install_problems(
            relocated.source_for(destination), destination, INSTALLED_VERSION
        )
    ]
    assert set(report.up_to_date) == set(expected), describe_report(report)
    assert [problem for problem in problems if "links to" in problem]


def replace_a_link_with_a_file(destination: pathlib.Path) -> None:
    """What an editor that "saves through" a symlink leaves behind."""
    entry = destination / ENTRY_DOCUMENT
    content = entry.read_bytes()
    entry.unlink()
    entry.write_bytes(content)


def remove_every_link(destination: pathlib.Path) -> None:
    """What a user clearing out a skill by hand leaves behind: the manifest, alone."""
    for entry in destination.iterdir():
        if entry.name != MANIFEST_NAME:
            entry.unlink()


DAMAGED_LINKS: Final = [
    pytest.param(replace_a_link_with_a_file, id="link_replaced_by_a_file"),
    pytest.param(remove_every_link, id="links_removed"),
]


def damaged_links_problems(
    project: pathlib.Path,
    bundle: Bundle,
    monkeypatch: pytest.MonkeyPatch,
    damage: Callable[[pathlib.Path], None],
    defect: Callable[[pytest.MonkeyPatch], None] | None = None,
) -> list[str]:
    """A symlink install the user has interfered with is refused, not quietly rebuilt.

    Symlink installs are judged structurally rather than by content -- the content lives
    in the package and changes legitimately on every upgrade -- so the link set is the
    whole of the record. ``damage`` is a parameter rather than a fixed step because that
    record has more than one way to stop being true, and a single one of them stands in
    for the others only until someone changes the code.
    """
    install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)
    destination = project / SkillTarget.AGENTS.value / bundle.names[0]
    intact = snapshot(destination)
    damage(destination)
    before = snapshot(destination)
    problems = []
    if before == intact:
        problems.append(f"{destination} was not changed, so refusing it proves nothing.")
    if not (destination / MANIFEST_NAME).is_file():
        problems.append(
            f"{destination} lost its {MANIFEST_NAME}, so it would be refused as a"
            " directory this package never installed rather than as an edited one."
        )
    if defect is not None:
        defect(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)

    problems += refusal_problems(report, destination, SkillFailureKind.LOCALLY_MODIFIED)
    problems += unchanged_problems(destination, before)
    return problems


@pytest.mark.parametrize("damage", DAMAGED_LINKS)
def test_a_damaged_symlink_install_counts_as_a_local_edit(
    project: pathlib.Path,
    bundle: Bundle,
    monkeypatch: pytest.MonkeyPatch,
    damage: Callable[[pathlib.Path], None],
):
    assert not damaged_links_problems(project, bundle, monkeypatch, damage)


@pytest.mark.parametrize("damage", DAMAGED_LINKS)
def test_a_damaged_symlink_install_treated_as_intact_is_reported(
    project: pathlib.Path,
    bundle: Bundle,
    monkeypatch: pytest.MonkeyPatch,
    damage: Callable[[pathlib.Path], None],
):
    problems = damaged_links_problems(
        project, bundle, monkeypatch, damage, defect=ignore_local_edits
    )

    assert [problem for problem in problems if "LOCALLY_MODIFIED" in problem.upper()]


def test_a_platform_that_refuses_links_is_reported_per_skill(
    project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch
):
    refuse_to_make_links(monkeypatch)

    report = install_skills(project, targets=ALL_TARGETS, mode=InstallMode.SYMLINK)

    expected = expected_destinations(project, bundle)
    assert not non_vacuity_problems(expected)
    assert not partition_problems(report, expected)
    problems = [
        problem
        for destination in expected
        for problem in refusal_problems(report, destination, SkillFailureKind.SYMLINKS_UNSUPPORTED)
    ]
    assert not problems, "\n".join(problems)
    assert [destination for destination in expected if destination.exists()] == []
    assert not staging_remnant_problems(project)


# ---------------------------------------------------------------------------
# The command around the installer.
# ---------------------------------------------------------------------------


def unwrapped(text: str) -> str:
    """Collapse the command's line wrapping so a sentence can be looked for whole."""
    return " ".join(text.split())


def displayed(destination: pathlib.Path, project: pathlib.Path) -> str:
    return str(destination.relative_to(project))


def test_the_command_installs_and_exits_zero(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str]
):
    status = command_line.main(["skills", "install", "--project-root", str(project)])

    output = capsys.readouterr().out
    assert status == 0
    expected = expected_destinations(project, bundle)
    assert not non_vacuity_problems(expected)
    problems = [
        problem
        for destination in expected
        for problem in installed_copy_problems(
            bundle.source_for(destination), destination, INSTALLED_VERSION
        )
    ]
    assert not problems, "\n".join(problems)
    for destination in expected:
        assert displayed(destination, project) in output


def refused_destination_problems(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str]
) -> list[str]:
    """One destination refused, the rest installed: the run a script must not read as clean."""
    foreign = project / SkillTarget.CLAUDE.value / bundle.names[0]
    foreign.mkdir(parents=True)
    (foreign / "notes.md").write_text("a directory the user made\n", encoding="utf-8")
    before = snapshot(foreign)
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)

    status = command_line.main(["skills", "install", "--project-root", str(project)])

    output = capsys.readouterr().out
    if status == 0:
        problems.append(
            "a run that refused a destination must exit nonzero, or a script goes on to"
            " run an agent that is missing a skill"
        )
    problems += unchanged_problems(foreign, before)
    if displayed(foreign, project) not in output:
        problems.append(f"{foreign} is missing from the report the command printed.")
    for destination in expected:
        if destination == foreign:
            continue
        problems += installed_copy_problems(
            bundle.source_for(destination), destination, INSTALLED_VERSION
        )
        if displayed(destination, project) not in output:
            problems.append(f"{destination} is missing from the report the command printed.")
    return problems


def test_the_command_exits_nonzero_when_any_destination_was_refused(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str]
):
    assert not refused_destination_problems(project, bundle, capsys)


def test_a_command_that_hid_a_refusal_is_caught(
    project: pathlib.Path,
    bundle: Bundle,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
):
    hide_failures(monkeypatch)

    problems = refused_destination_problems(project, bundle, capsys)

    assert [problem for problem in problems if "exit nonzero" in problem]


def reported_destination_problems(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str], outcome: str
) -> list[str]:
    """A run must name every destination it considered, whatever became of it.

    ``outcome`` is what this run does to the destinations, and it is the caller's to set:
    the two runs that change nothing visible at the destination -- leaving a skill alone
    and bringing it up to a new version -- are the two whose output is the only evidence
    the user gets. A first install is not a substitute for either, because it is the one
    case where the destination appearing on disk says what happened by itself.
    """
    version = EARLIER_VERSION if outcome == "updated" else INSTALLED_VERSION
    with expected_package_version(version):
        command_line.main(["skills", "install", "--project-root", str(project)])
    capsys.readouterr()
    expected = expected_destinations(project, bundle)
    problems = non_vacuity_problems(expected)
    # Anchored on the filesystem rather than on the previous run's output: the manifests
    # decide what the second run must do, so this is what makes the run under test the
    # run this is named for.
    for destination in expected:
        problems += manifest_problems(
            destination, bundle.source_for(destination), version, InstallMode.COPY
        )

    status = command_line.main(["skills", "install", "--project-root", str(project)])

    output = capsys.readouterr().out
    if status != 0:
        problems.append(f"a run that {outcome} every skill must exit 0; got {status}")
    for destination in expected:
        if displayed(destination, project) not in output:
            problems.append(
                f"{destination} was {outcome} and the command's report does not name it,"
                f" so nothing tells the user it happened. Printed:\n{output}"
            )
    return problems


@contextlib.contextmanager
def expected_package_version(version: str) -> Iterator[None]:
    """Run a block with the package claiming ``version``, then put it back."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(great_expectations, "__version__", version)
        yield


@pytest.mark.parametrize(
    "outcome",
    ["left alone", "updated"],
    ids=["already_up_to_date", "updated_by_an_upgrade"],
)
def test_the_command_names_every_destination_it_considered(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str], outcome: str
):
    assert not reported_destination_problems(project, bundle, capsys, outcome)


@pytest.mark.parametrize(
    ["outcome", "group"],
    [
        pytest.param("left alone", "up_to_date", id="already_up_to_date"),
        pytest.param("updated", "replaced", id="updated_by_an_upgrade"),
    ],
)
def test_an_outcome_group_missing_from_the_report_is_caught(
    project: pathlib.Path,
    bundle: Bundle,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
    group: str,
):
    """A group that stopped being printed is invisible: the command still exits 0 and
    the destinations are still correct on disk, and the user is simply not told.
    """
    hide_the_outcome_group(monkeypatch, group)

    problems = reported_destination_problems(project, bundle, capsys, outcome)

    assert [problem for problem in problems if "does not name it" in problem]


@contextlib.contextmanager
def an_edited_skill(project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch):
    install_skills(project, targets=ALL_TARGETS)
    edited = project / SkillTarget.AGENTS.value / bundle.names[0]
    (edited / REFERENCE_DIR / "notes.md").write_text("notes the user added\n", encoding="utf-8")
    yield


@contextlib.contextmanager
def a_foreign_directory(project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch):
    foreign = project / SkillTarget.AGENTS.value / bundle.names[0]
    foreign.mkdir(parents=True)
    (foreign / "notes.md").write_text("a directory the user made\n", encoding="utf-8")
    yield


@contextlib.contextmanager
def an_unreadable_skill(project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch):
    install_skills(project, targets=ALL_TARGETS)
    unreadable = project / SkillTarget.AGENTS.value / bundle.names[0] / REFERENCE_DIR
    with made_unreadable(unreadable):
        if is_readable(unreadable):
            pytest.fail(f"{unreadable} is readable with no permissions at all; check the user")
        yield


@contextlib.contextmanager
def a_write_that_fails(project: pathlib.Path, bundle: Bundle, monkeypatch: pytest.MonkeyPatch):
    break_writing(monkeypatch)
    yield


@pytest.mark.parametrize(
    ["prepare", "kind", "explains_edits"],
    [
        pytest.param(an_edited_skill, SkillFailureKind.LOCALLY_MODIFIED, True, id="edited"),
        pytest.param(
            a_foreign_directory, SkillFailureKind.FOREIGN_DESTINATION, False, id="foreign"
        ),
        pytest.param(
            an_unreadable_skill, SkillFailureKind.UNREADABLE_DESTINATION, False, id="unreadable"
        ),
        pytest.param(a_write_that_fails, SkillFailureKind.WRITE_FAILED, False, id="write_failed"),
    ],
)
def test_the_command_explains_local_edits_only_where_a_skill_was_edited(
    project: pathlib.Path,
    bundle: Bundle,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    prepare: Callable[..., contextlib.AbstractContextManager[None]],
    kind: SkillFailureKind,
    explains_edits: bool,
):
    """Advice meant for one kind of failure sends the user hunting at the others.

    The explanation of what counts as an edit is keyed on the recorded failure kind, and
    it has to be: an edited destination and one whose subdirectory could not be read both
    still exist and both still hold a valid ownership manifest.
    """
    with prepare(project, bundle, monkeypatch):
        report = install_skills(project, targets=ALL_TARGETS)
        assert report.failed, "this scenario must produce a failure to explain"
        assert {failure.kind for failure in report.failed} == {kind}, describe_report(report)
        capsys.readouterr()

        status = command_line.main(["skills", "install", "--project-root", str(project)])

    output = unwrapped(capsys.readouterr().out)
    assert status == 1
    assert unwrapped(command_line._FAILURE_FOOTER) in output
    assert unwrapped(command_line._LOCAL_EDIT_FOOTER)
    assert (unwrapped(command_line._LOCAL_EDIT_FOOTER) in output) is explains_edits


def test_a_failure_kind_derived_after_the_fact_is_caught(
    project: pathlib.Path,
    bundle: Bundle,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
):
    """The disproved heuristic, kept executable: it calls a permission error an edit."""
    install_skills(project, targets=ALL_TARGETS)
    label_failures_by_appearance(monkeypatch)
    unreadable = project / SkillTarget.AGENTS.value / bundle.names[0] / REFERENCE_DIR

    with made_unreadable(unreadable):
        assert not is_readable(unreadable)
        capsys.readouterr()
        status = command_line.main(["skills", "install", "--project-root", str(project)])

    assert status == 1
    assert unwrapped(command_line._LOCAL_EDIT_FOOTER) in unwrapped(capsys.readouterr().out)


def raise_no_working_directory() -> pathlib.Path:
    raise FileNotFoundError(2, "No such file or directory")


@pytest.mark.parametrize(
    "arguments",
    [[], ["skills"], ["skills", "install"], ["skills", "list"]],
    ids=["root", "skills", "install", "list"],
)
def test_help_never_reads_the_working_directory(
    arguments: list[str], capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    """Help has to work from a directory that no longer exists, which is where a user
    who has just deleted a build directory reaches for it.
    """
    monkeypatch.setattr(pathlib.Path, "cwd", staticmethod(raise_no_working_directory))

    with pytest.raises(SystemExit) as exit_status:
        command_line.main([*arguments, "--help"])

    assert exit_status.value.code == 0
    assert "usage:" in capsys.readouterr().out


def test_a_working_directory_resolved_while_defining_the_arguments_is_caught(
    monkeypatch: pytest.MonkeyPatch,
):
    """Why the default is resolved when it is used and not when it is declared."""
    monkeypatch.setattr(pathlib.Path, "cwd", staticmethod(raise_no_working_directory))
    parser = argparse.ArgumentParser()

    with pytest.raises(FileNotFoundError):
        parser.add_argument("--project-root", type=pathlib.Path, default=pathlib.Path.cwd())


def test_a_deleted_working_directory_is_reported_rather_than_raised(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(pathlib.Path, "cwd", staticmethod(raise_no_working_directory))

    status = command_line.main(["skills", "install"])

    assert status == 1
    error = unwrapped(capsys.readouterr().err)
    assert "current directory" in error
    assert "--project-root" in error


def test_the_listing_reports_each_skill_against_the_given_project(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str]
):
    """A listing that could only ever describe the working directory would contradict an
    install aimed somewhere else.
    """
    assert command_line.main(["skills", "install", "--project-root", str(project)]) == 0
    capsys.readouterr()

    assert command_line.main(["skills", "list", "--project-root", str(project)]) == 0

    output = capsys.readouterr().out
    for name in bundle.names:
        assert name in output
    for target in ALL_TARGETS:
        assert target.value in output
    assert INSTALLED_VERSION in output


def test_the_listing_shows_skills_installed_by_another_version(
    project: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str]
):
    install_skills(project, targets=ALL_TARGETS)
    for destination in expected_destinations(project, bundle):
        stamp_manifest_version(destination, EARLIER_VERSION)
    capsys.readouterr()

    assert command_line.main(["skills", "list", "--project-root", str(project)]) == 0

    output = capsys.readouterr().out
    assert EARLIER_VERSION in output
    assert INSTALLED_VERSION in output


def test_the_listing_refuses_a_project_that_is_not_a_directory(
    tmp_path: pathlib.Path, bundle: Bundle, capsys: pytest.CaptureFixture[str]
):
    status = command_line.main(["skills", "list", "--project-root", str(tmp_path / "nowhere")])

    assert status == 1
    assert "not an existing directory" in unwrapped(capsys.readouterr().err)
