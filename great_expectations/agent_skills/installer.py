"""Install the skills bundled in this package into a project's agent directories.

Coding agents discover skills by reading well-known directories inside the project they
are working in, so guidance that ships inside an installed Python package is invisible
to them until it is copied (or linked) into one of those directories. This module is
that bridge, and the whole of its difficulty is that the destination belongs to the
user, not to Great Expectations:

*   **The install command has to be safe to re-run.** Users run it again after every
    upgrade, and often just because they are not sure whether they ran it. A second run
    must therefore be a no-op rather than a rewrite.
*   **Great Expectations must only ever replace its own files.** A directory that this
    package did not create, or one it created and the user has since edited, is not
    the installer's to overwrite. Each installed skill directory therefore carries an ownership
    manifest recording the version and a content hash, which is what lets a later run
    tell "unchanged copy of an older version" (safe to replace) apart from "the user
    edited this" (refuse) and "someone else's directory" (refuse, always).
*   **A crash must not leave a half-written skill.** A skill directory whose entry
    document survived but whose references did not is worse than no skill at all,
    because an agent will happily follow the truncated remains. Every write is
    therefore staged in a sibling directory and moved into place with a rename, so the
    destination is only ever the complete old tree, absent, or the complete new tree.

Problems with one skill never abort the others and are never raised: they are collected
in the returned report, each labelled with what went wrong, so the caller can disclose
every one of them and explain the ones that need explaining. Nothing here is part of
the public Python API -- the command-line entry point is the supported surface.
"""

from __future__ import annotations

import contextlib
import enum
import hashlib
import importlib.util
import json
import shutil
import uuid
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

#: Name of the ownership manifest written into every skill directory this module
#: installs. Its presence is what marks a directory as safe for a later run to
#: replace.
MANIFEST_NAME: Final = ".gx-skill.json"

_MANAGED_BY: Final = "great_expectations"
_PACKAGE_NAME: Final = "great_expectations"

#: Location of the bundled skills inside the installed package.
_BUNDLE_RELPATH: Final = (".agents", "skills")

#: A directory is a skill if and only if it holds an entry document.
_ENTRY_DOCUMENT: Final = "SKILL.md"

#: Prefix for staging directories. Reserved, recognizable, and swept at the start of
#: every run so that a directory left behind by an interrupted run is cleaned up.
_STAGING_PREFIX: Final = ".gx-tmp-"


class SkillTarget(enum.Enum):
    """A project-relative directory that coding agents search for skills.

    Values are the directory each platform reads: Codex and the wider ecosystem read
    ``.agents/skills``, Claude Code reads ``.claude/skills``, and Cursor reads both --
    which is why installing into both by default is what makes one command serve all
    three.
    """

    AGENTS = ".agents/skills"
    CLAUDE = ".claude/skills"


class InstallMode(enum.Enum):
    """How an installed skill relates to the bundled copy in the package.

    ``COPY`` is the default because it is the only mode every platform is known to
    support and the only one that survives the package being upgraded or removed.
    ``SYMLINK`` trades that robustness for content that tracks the installed package
    without re-running the command.
    """

    COPY = "copy"
    SYMLINK = "symlink"


class SkillFailureKind(enum.Enum):
    """What went wrong at a destination, as a fact rather than something to deduce.

    A caller that explains failures has to tell a refusal -- a destination this package
    declines to touch because of what it holds -- apart from a destination it simply
    could not read or write. The two call for opposite advice, and nothing observable
    about the destination afterwards distinguishes them: a directory refused for local
    edits and a directory whose files could not be read both still exist, both still
    hold a valid manifest, and both leave the run's own filesystem state unchanged. The
    only place that knows which happened is the code that decided, so it says so here.
    """

    #: Nothing there claims Great Expectations as its owner. Never replaced.
    FOREIGN_DESTINATION = "foreign_destination"
    #: Installed by this package and edited since. Replaced only under ``force``.
    LOCALLY_MODIFIED = "locally_modified"
    #: Could not be read, so whether it was safe to replace could not be decided.
    UNREADABLE_DESTINATION = "unreadable_destination"
    #: The new content could not be written or moved into place.
    WRITE_FAILED = "write_failed"
    #: Symlinks were asked for and the platform would not create them.
    SYMLINKS_UNSUPPORTED = "symlinks_unsupported"


@dataclass(frozen=True)
class SkillInstallFailure:
    """One destination the run left alone, and why."""

    destination: Path
    kind: SkillFailureKind
    #: Text written to be read by the user: what happened, the state the destination is
    #: in now, and one thing to do about it.
    reason: str


@dataclass(frozen=True)
class SkillInstallReport:
    """The outcome of an install run, one entry per skill per target directory.

    Every destination the run considered appears in exactly one of the four fields, so
    a caller can report the whole run without inferring anything.
    """

    #: Destinations that did not exist and were created.
    installed: tuple[Path, ...]
    #: Destinations already holding this version of the skill; left untouched.
    up_to_date: tuple[Path, ...]
    #: Unmodified destinations from another version, replaced with the bundled skill.
    replaced: tuple[Path, ...]
    #: Destinations left alone: refusals and write failures alike, each labelled.
    failed: tuple[SkillInstallFailure, ...]


class _Outcome(enum.Enum):
    """Which report field a successfully handled destination belongs to."""

    INSTALLED = "installed"
    UP_TO_DATE = "up_to_date"
    REPLACED = "replaced"


class _SkillRefusal(Exception):
    """A problem with a single destination: reported to the user, never raised at them.

    The message is the text the user reads next to the destination path, so it says
    what happened, what state the destination is in now, and what to do about it. The
    kind travels with it because a caller that groups or explains failures cannot
    recover it from the message without matching on prose.
    """

    def __init__(self, kind: SkillFailureKind, reason: str) -> None:
        super().__init__(reason)
        self.kind = kind


@dataclass(frozen=True)
class _InstallContext:
    """The settings shared by every destination in a single run."""

    mode: InstallMode
    force: bool
    version: str


_FOREIGN_DESTINATION_REASON: Final = (
    "Something already exists at this path that Great Expectations does not manage: it "
    f"holds no {MANIFEST_NAME} manifest. It was left untouched. Move or delete it if "
    "you want Great Expectations to install its skill here."
)

_LOCALLY_MODIFIED_REASON: Final = (
    "Great Expectations installed this skill, but it has local edits: its contents no "
    f"longer match the {MANIFEST_NAME} manifest recorded when it was installed. It was "
    "left untouched, so no edits were lost. Save a copy of your changes elsewhere, or "
    "re-run the install with --force to overwrite this directory with the bundled skill."
)


def _write_failure_reason(error: BaseException) -> str:
    return (
        f"Could not write this skill into the project: {error}. The destination was "
        "left as it was and any partly written files were removed. Check the free "
        "space and write permissions on the destination, then run the install again."
    )


def _swap_failure_reason(error: BaseException) -> str:
    return (
        f"Could not move this skill into place: {error}. The previous contents were "
        f"restored where possible; a leftover {_STAGING_PREFIX}* directory beside this "
        "path, if any, holds them and is removed by the next install run."
    )


def _symlink_failure_reason(error: BaseException) -> str:
    return (
        f"Could not create the symlinks for this skill: {error}. Some platforms only "
        "permit symlinks for privileged accounts. The destination was left as it was; "
        "re-run the install without --symlink to install file copies instead."
    )


def _missing_bundle_reason(searched: Sequence[str]) -> str:
    locations = ", ".join(searched) if searched else "the installed package"
    return (
        "The installed great_expectations package bundles no agent skills: no "
        f"{'/'.join(_BUNDLE_RELPATH)} directory was found in {locations}. Re-install "
        "great_expectations, and if the problem persists, report it as a packaging bug."
    )


def _empty_bundle_reason(root: Path) -> str:
    return (
        f"The installed great_expectations package bundles no agent skills: {root} "
        f"holds no directory containing a {_ENTRY_DOCUMENT} file. A partly packaged "
        "installation looks exactly like this. Re-install great_expectations, and if "
        "the problem persists, report it as a packaging bug."
    )


def _unreadable_destination_reason(error: OSError) -> str:
    path = error.filename or "a path inside this directory"
    return (
        f"Could not read {path} while checking whether this skill is up to date: "
        f"{error.strerror or error}. The destination was left untouched. Check the "
        "permissions on that path -- an install run by another user can leave files "
        "this one cannot read -- then run the install again."
    )


def _unreadable_bundle_reason(error: OSError) -> str:
    path = error.filename or "a bundled skill file"
    return (
        f"Cannot read {path} in the installed great_expectations package: "
        f"{error.strerror or error}. The bundled skills have to be readable to be "
        "installed, so this is a defect in the installation rather than in the "
        "project. Re-install great_expectations, and if the problem persists, report "
        "it as a packaging bug."
    )


def _unusable_project_root_reason(project_root: Path) -> str:
    return (
        f"Cannot install skills into {project_root}: it is not an existing directory. "
        "Pass the path of the project you want the skills installed into."
    )


def read_skill_manifest(directory: Path) -> dict[str, Any] | None:
    """Return the ownership manifest of ``directory``, or ``None`` if it has none.

    ``None`` means the directory was not installed by this package -- whether because
    the manifest is missing, unreadable, not valid JSON, or does not claim Great
    Expectations as its owner. Every one of those cases has to be treated identically:
    the only safe reading of a directory whose ownership cannot be proved is that it
    belongs to someone else.
    """
    try:
        raw = (directory / MANIFEST_NAME).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(manifest, dict) or manifest.get("managed_by") != _MANAGED_BY:
        return None
    return manifest


def iter_bundled_skills() -> Iterator[Path]:
    """Yield the skill directories bundled in the installed package, ordered by name.

    Resolution goes through the import system rather than through this file's location,
    so the same code finds the skills in a wheel install, an editable install and a
    source checkout: in each of them the skills sit beside the package's ``__init__``,
    wherever the import system says that is.

    Raises:
        FileNotFoundError: if the installed package carries no usable bundled skills --
            whether it has no bundle directory at all or a bundle directory holding
            nothing that qualifies as a skill. Both are defects in the installation
            rather than problems the caller can do anything about per skill, and both
            have to raise: returning no skills would let a caller report a run in which
            nothing was installed as a run in which nothing went wrong. A partly
            packaged installation -- reference files shipped, entry documents missed --
            produces exactly that second shape.
        OSError: if the bundle itself cannot be read. An installation whose own files
            are unreadable is defective in the same way, and saying so beats a bare
            permission error naming a path in someone else's site-packages.
    """
    root = _bundled_skills_root()
    try:
        skills = sorted(p for p in root.iterdir() if (p / _ENTRY_DOCUMENT).is_file())
    except OSError as error:
        raise OSError(_unreadable_bundle_reason(error)) from error
    if not skills:
        raise FileNotFoundError(_empty_bundle_reason(root))
    return iter(skills)


def install_skills(
    project_root: Path,
    *,
    targets: Sequence[SkillTarget] = (SkillTarget.AGENTS, SkillTarget.CLAUDE),
    mode: InstallMode = InstallMode.COPY,
    force: bool = False,
) -> SkillInstallReport:
    """Install every bundled skill into each target directory under ``project_root``.

    Re-running this is always safe: destinations already holding this version are left
    byte-for-byte alone, and a destination that Great Expectations did not install, or
    that has been edited since it was installed, is refused rather than overwritten.
    ``force`` opts into overwriting the edited ones; nothing opts into overwriting a
    directory without an ownership manifest.

    Args:
        project_root: the project the skills are installed into.
        targets: the discovery directories to install into. Both, by default, which is
            what makes one run serve every supported coding agent.
        mode: whether to install copies of the skill files or symlinks to them.
        force: replace skill directories that were installed by Great Expectations and
            have been edited since. Never applies to directories this package did
            not install.

    Returns:
        A report with every destination in exactly one of its four fields. Problems
        with individual skills are reported there, never raised.

    Raises:
        OSError: if ``project_root`` is not an existing directory, or the installed
            package bundles no skills, or the bundle cannot be read. Each makes the
            whole run meaningless, unlike a per-destination problem, which is reported.
    """
    root = Path(project_root)
    if not root.is_dir():
        raise NotADirectoryError(_unusable_project_root_reason(root))

    skills = list(iter_bundled_skills())
    try:
        digests = {skill: _tree_digest(skill) for skill in skills}
    except OSError as error:
        raise OSError(_unreadable_bundle_reason(error)) from error
    context = _InstallContext(mode=mode, force=force, version=_installed_gx_version())

    outcomes: dict[_Outcome, list[Path]] = {outcome: [] for outcome in _Outcome}
    failed: list[SkillInstallFailure] = []

    for target in targets:
        parent = root / target.value
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            reason = _write_failure_reason(error)
            failed.extend(
                SkillInstallFailure(parent / skill.name, SkillFailureKind.WRITE_FAILED, reason)
                for skill in skills
            )
            continue
        _clear_staging_remnants(parent)
        for skill in skills:
            destination = parent / skill.name
            try:
                outcome = _install_one(skill, destination, digests[skill], context)
            except _SkillRefusal as refusal:
                failed.append(SkillInstallFailure(destination, refusal.kind, str(refusal)))
            else:
                outcomes[outcome].append(destination)

    return SkillInstallReport(
        installed=tuple(outcomes[_Outcome.INSTALLED]),
        up_to_date=tuple(outcomes[_Outcome.UP_TO_DATE]),
        replaced=tuple(outcomes[_Outcome.REPLACED]),
        failed=tuple(failed),
    )


def _install_one(
    source: Path, destination: Path, digest: str, context: _InstallContext
) -> _Outcome:
    """Bring a single destination in line with a single bundled skill.

    The order of the checks is the contract: ownership before staleness, and staleness
    only for destinations that still match their own manifest. Comparing versions first
    would replace a directory the user had edited, on the very command that is supposed
    to be safe to re-run.
    """
    if not _lexists(destination):
        _materialize(source, destination, digest, context)
        return _Outcome.INSTALLED

    manifest = read_skill_manifest(destination)
    if manifest is None:
        raise _SkillRefusal(SkillFailureKind.FOREIGN_DESTINATION, _FOREIGN_DESTINATION_REASON)

    try:
        unmodified = _is_unmodified(destination, manifest)
        current = unmodified and _is_current(destination, source, manifest, digest, context)
    except OSError as error:
        # Inspecting a destination means reading it, and the destination belongs to the
        # user: a path left unreadable by an install run as another user, or by a
        # restrictive umask, has to cost this one destination and no more.
        raise _SkillRefusal(
            SkillFailureKind.UNREADABLE_DESTINATION, _unreadable_destination_reason(error)
        ) from error

    if not unmodified and not context.force:
        raise _SkillRefusal(SkillFailureKind.LOCALLY_MODIFIED, _LOCALLY_MODIFIED_REASON)
    if current:
        return _Outcome.UP_TO_DATE

    _materialize(source, destination, digest, context)
    return _Outcome.REPLACED


def _is_unmodified(destination: Path, manifest: dict[str, Any]) -> bool:
    """Report whether a destination still matches the manifest written when it was made.

    This is the question "has the user changed this?", which is asked of the
    destination against its own recorded state -- not against the bundled skill, which
    legitimately differs after an upgrade.
    """
    if manifest.get("mode") == InstallMode.SYMLINK.value:
        return _links_are_intact(destination)
    return _tree_digest(destination) == manifest.get("content_sha256")


def _is_current(
    destination: Path,
    source: Path,
    manifest: dict[str, Any],
    digest: str,
    context: _InstallContext,
) -> bool:
    """Report whether a destination already holds exactly what this run would install."""
    if (
        manifest.get("gx_version") != context.version
        or manifest.get("content_sha256") != digest
        or manifest.get("mode") != context.mode.value
    ):
        return False
    if context.mode is InstallMode.SYMLINK:
        # The links serve the package's current content, but only if they still point
        # at it: an upgrade can add a file, and a moved environment invalidates them.
        return _links_point_at(destination, source)
    return True


def _links_are_intact(destination: Path) -> bool:
    """Report whether a symlink-mode destination is still nothing but links.

    Content edits cannot be detected by hashing here -- the content lives in the
    package and the links follow it -- so what is checked is the structure the install
    created. A link the user replaced with a real file is a local modification.
    """
    try:
        entries = [entry for entry in destination.iterdir() if entry.name != MANIFEST_NAME]
    except OSError:
        return False
    return bool(entries) and all(entry.is_symlink() for entry in entries)


def _links_point_at(destination: Path, source: Path) -> bool:
    """Report whether the destination links exactly mirror the bundled skill's entries."""
    try:
        expected = {entry.name: entry for entry in source.iterdir()}
        actual = {
            entry.name: entry for entry in destination.iterdir() if entry.name != MANIFEST_NAME
        }
        if set(actual) != set(expected):
            return False
        return all(link.readlink() == expected[name] for name, link in actual.items())
    except OSError:
        return False


def _materialize(source: Path, destination: Path, digest: str, context: _InstallContext) -> None:
    """Build the skill in a staging directory, then move it onto the destination.

    Nothing is written at the destination until a complete tree exists beside it, so a
    failure -- or a crash -- at any point here leaves the destination either untouched
    or replaced whole, and at worst a staging directory the next run sweeps away.
    """
    staging = _staging_path(destination)
    try:
        _stage(source, staging, context.mode)
        _write_manifest(staging, digest, context)
    except _SkillRefusal:
        _remove(staging)
        raise
    except OSError as error:
        _remove(staging)
        raise _SkillRefusal(SkillFailureKind.WRITE_FAILED, _write_failure_reason(error)) from error
    _swap_into_place(staging, destination)


def _stage(source: Path, staging: Path, mode: InstallMode) -> None:
    """Assemble the skill's content in the staging directory.

    A symlink inside a bundled skill is copied as a symlink rather than followed. That
    is what keeps the copy a copy: dereferencing would write content from outside the
    bundle into the user's project, and it would put a real file where the digest of
    the source recorded a link, so the destination could never match its own manifest
    and every later run would report an untouched install as edited.
    """
    if mode is InstallMode.SYMLINK:
        try:
            staging.mkdir(parents=True)
            for entry in sorted(source.iterdir()):
                (staging / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        except (OSError, NotImplementedError) as error:
            raise _SkillRefusal(
                SkillFailureKind.SYMLINKS_UNSUPPORTED, _symlink_failure_reason(error)
            ) from error
    else:
        try:
            shutil.copytree(source, staging, symlinks=True)
        except (OSError, shutil.Error) as error:
            raise _SkillRefusal(
                SkillFailureKind.WRITE_FAILED, _write_failure_reason(error)
            ) from error


def _swap_into_place(staging: Path, destination: Path) -> None:
    """Move a fully staged directory onto the destination.

    A rename onto a name that does not exist is atomic, and that is the whole of the
    fresh-install case. Replacing an existing directory cannot be one rename, because
    renaming onto a non-empty directory is not allowed, so it is two: the old tree is
    renamed aside to a staging name first. The guarantee is therefore not that the
    swap is a single atomic step, but that no intermediate state is ever a partly
    written skill -- the destination is the old tree, then briefly absent, then the new
    tree, and the tree renamed aside is swept by the next run if this one dies.
    """
    if not _lexists(destination):
        try:
            staging.replace(destination)
        except OSError as error:
            _remove(staging)
            raise _SkillRefusal(
                SkillFailureKind.WRITE_FAILED, _write_failure_reason(error)
            ) from error
        return

    previous = _staging_path(destination)
    try:
        destination.replace(previous)
    except OSError as error:
        _remove(staging)
        raise _SkillRefusal(SkillFailureKind.WRITE_FAILED, _write_failure_reason(error)) from error
    try:
        staging.replace(destination)
    except OSError as error:
        with contextlib.suppress(OSError):
            previous.replace(destination)
        _remove(staging)
        raise _SkillRefusal(SkillFailureKind.WRITE_FAILED, _swap_failure_reason(error)) from error
    _remove(previous)


def _write_manifest(directory: Path, digest: str, context: _InstallContext) -> None:
    """Record what was installed, so a later run can tell this copy from an edited one."""
    manifest = {
        "managed_by": _MANAGED_BY,
        "gx_version": context.version,
        "content_sha256": digest,
        "mode": context.mode.value,
    }
    (directory / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _tree_digest(root: Path) -> str:
    """Hash the contents of a directory tree.

    Determinism across machines is the point -- the hash recorded on one machine is
    compared against a tree on another after an upgrade -- so paths are ordered and
    encoded in their platform-independent form, each entry is tagged by kind and
    length-framed so that a rename cannot produce the same digest as an edit, and the
    walk never descends through a symlinked directory, whose contents are not this
    tree's to describe. The manifest itself is excluded because it holds this digest.

    A symlink is hashed by the path it points at rather than by what it resolves to.
    Resolving would make a file and a link to an identical file indistinguishable, when
    replacing one with the other is exactly the kind of change to an installed skill
    that has to be noticed -- and it would make the digest of a tree depend on files
    outside it.
    """
    digest = hashlib.sha256()
    for relpath, path in sorted(_walk(root)):
        if relpath == MANIFEST_NAME:
            continue
        if path.is_symlink():
            digest.update(f"{relpath}\0L\0{path.readlink().as_posix()}\0".encode())
        elif path.is_file():
            payload = path.read_bytes()
            digest.update(f"{relpath}\0F\0{len(payload)}\0".encode())
            digest.update(payload)
    return digest.hexdigest()


def _walk(root: Path) -> Iterator[tuple[str, Path]]:
    """Yield every entry below ``root`` as a relative path, without following links.

    Written out rather than delegated to a recursive glob because the standard
    library's has followed symlinked directories in some versions and not in others,
    and the digest built on top of this cannot afford to depend on which.
    """
    pending = [root]
    while pending:
        for entry in pending.pop().iterdir():
            yield entry.relative_to(root).as_posix(), entry
            if entry.is_dir() and not entry.is_symlink():
                pending.append(entry)


def _bundled_skills_root() -> Path:
    """Locate the bundled skills in the installed package."""
    try:
        spec = importlib.util.find_spec(_PACKAGE_NAME)
    except (ImportError, ValueError):
        spec = None
    locations = list(spec.submodule_search_locations or ()) if spec is not None else []
    for location in locations:
        candidate = Path(location).joinpath(*_BUNDLE_RELPATH)
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(_missing_bundle_reason(locations))


def _installed_gx_version() -> str:
    """Read the version of the package these skills were bundled with.

    Read at call time, and from the package rather than from distribution metadata, so
    that it is right for an editable install as well as a released wheel.
    """
    import great_expectations

    return great_expectations.__version__


def _staging_path(destination: Path) -> Path:
    """Return an unused, recognizably temporary sibling of the destination.

    A sibling, because a rename is only guaranteed to be cheap and atomic within one
    filesystem, and the destination's parent is the only directory known to be on the
    same one.
    """
    return destination.parent / f"{_STAGING_PREFIX}{destination.name}-{uuid.uuid4().hex[:12]}"


def _clear_staging_remnants(parent: Path) -> None:
    """Sweep staging directories left behind by an interrupted run.

    Best effort, including the listing itself: if the target directory cannot even be
    read, that is worth reporting against each destination inside it rather than
    aborting the run here, where there is nothing to report it against. Listing is
    spelled with ``iterdir`` rather than a glob for the same reason the digest's walk
    is: how the standard library's glob treats an unreadable directory is an
    implementation detail, and this needs to behave the same way everywhere.
    """
    with contextlib.suppress(OSError):
        for entry in parent.iterdir():
            if entry.name.startswith(_STAGING_PREFIX):
                _remove(entry)


def _remove(path: Path) -> None:
    """Delete a file, link or tree, best effort: cleanup must not mask the real error."""
    with contextlib.suppress(OSError):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def _lexists(path: Path) -> bool:
    """Report whether anything is at ``path``, including a link to nothing."""
    try:
        path.lstat()
    except (OSError, ValueError):
        return False
    else:
        return True
