"""Conformance tests for the agent skills bundled in the ``great_expectations`` package.

The skills are plain markdown, so nothing about them is checked by the interpreter.
Two separate contracts rest on that markdown and both fail silently when broken:

1.  **Discoverability.** Coding agents load a skill by reading the YAML frontmatter of
    its entry document. A skill whose frontmatter does not parse, or whose ``name``
    disagrees with its directory, is simply never offered to the user -- there is no
    error anywhere.
2.  **Self-containment.** Each skill directory must stand on its own, and the shared
    session references are committed once per skill directory rather than shared
    through a symlink or a build step. Nothing but a test stops the copies from
    drifting apart, and drift means one skill quietly teaches an older procedure.

Every check below is paired with a test that introduces the corresponding violation
into a throwaway copy of the real content and asserts the check reports it. Without
that pairing a conformance check can degrade into a no-op -- for example by looking
for markdown links in content that spells its references as inline code -- and keep
passing forever while asserting nothing.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import shutil
from typing import Final

import pytest
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from great_expectations.compatibility.pydantic import BaseModel

pytestmark = [pytest.mark.unit]

PROJECT_ROOT: Final = pathlib.Path(__file__).parents[2]
SKILLS_ROOT: Final = PROJECT_ROOT / "great_expectations" / ".agents" / "skills"

ENTRY_DOCUMENT: Final = "SKILL.md"
REFERENCE_DIR: Final = "references"

#: The data-source skill holds the authoritative copy of every shared reference.
CANONICAL_SKILL: Final = "gx-configure-data-source"
SHARED_REFERENCES: Final = ("preflight.md", "write-out.md", "robustness.md")

#: Limits imposed by the agent skills format that the bundled content targets.
MAX_NAME_LENGTH: Final = 64
MAX_DESCRIPTION_LENGTH: Final = 1024
#: A reference resolves at most one directory below the skill root, so a path
#: relative to the skill root has at most two parts (``references/<file>.md``).
MAX_REFERENCE_PARTS: Final = 2

#: The entry document is loaded into the agent's context in full, so detail belongs in
#: references that are read on demand instead.
MAX_ENTRY_DOCUMENT_LINES: Final = 500

#: Lowercase letters, digits and single interior hyphens.
SKILL_NAME_PATTERN: Final = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

#: Number of skills the package is known to bundle. Guards against a discovery bug
#: silently reducing every parametrized test below to zero cases.
MIN_BUNDLED_SKILLS: Final = 3

#: The checkpoint skill's action-catalog reference, checked against the live action
#: registry below.
ACTION_CATALOG_SKILL: Final = "gx-configure-checkpoint"
ACTION_CATALOG_REFERENCE: Final = "action-catalog.md"

FRONTMATTER_PATTERN: Final = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
CODE_SPAN_PATTERN: Final = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK_PATTERN: Final = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
#: A reference-shaped path -- one that already carries the ``references/`` prefix --
#: found inside a fenced code block. Bare filenames in fenced comments ("per
#: preflight.md") are deliberately not references (see ``_strip_code_fences``), but a
#: prefixed path is unambiguously meant as one, fence or not.
FENCED_REFERENCE_PATTERN: Final = re.compile(r"references/[\w./-]+\.md")
#: A skill of this bundle's naming family (``gx-configure-*``) named in prose as
#: inline code, e.g. a hand-off ("route to `gx-configure-checkpoint`"). Scoped to the
#: family prefix so an unrelated ``gx-``-prefixed token -- a package extra name like
#: ``gx-redshift`` -- is not mistaken for a skill hand-off.
SKILL_MENTION_PATTERN: Final = re.compile(r"`(gx-configure-[a-z0-9]+(?:-[a-z0-9]+)*)`")
#: The action catalog's stability-split table rows, e.g.
#: ``| `SlackNotificationAction` | `slack` | `@public_api` |``.
ACTION_TABLE_ROW_PATTERN: Final = re.compile(r"^\| `\w+` \| `(?P<type>\w+)` \|", re.MULTILINE)


class SkillContentError(Exception):
    """Raised when a skill's entry document cannot be read as a skill at all."""


def discover_skills(skills_root: pathlib.Path) -> list[pathlib.Path]:
    """Return every bundled skill directory, identified by its entry document.

    Discovery is by directory contents rather than a hardcoded list so that a skill
    added later is covered without anyone remembering to update this file.
    """
    if not skills_root.is_dir():
        return []
    return sorted(
        candidate for candidate in skills_root.iterdir() if (candidate / ENTRY_DOCUMENT).is_file()
    )


SKILL_DIRS: Final = discover_skills(SKILLS_ROOT)


def read_frontmatter(skill_dir: pathlib.Path) -> dict[str, object]:
    """Parse the YAML frontmatter of a skill's entry document."""
    entry = skill_dir / ENTRY_DOCUMENT
    match = FRONTMATTER_PATTERN.match(entry.read_text(encoding="utf-8"))
    if match is None:
        raise SkillContentError(
            f"{entry}: no YAML frontmatter found."
            " The file must open with a '---' line and close the block with another."
        )
    try:
        loaded = YAML(typ="safe").load(match.group("body"))
    except YAMLError as exc:
        raise SkillContentError(f"{entry}: frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SkillContentError(
            f"{entry}: frontmatter must be a YAML mapping, got {type(loaded).__name__}."
        )
    return loaded


def name_problems(skill_dir: pathlib.Path) -> list[str]:
    """Return every way the ``name`` field fails the format's rules."""
    entry = skill_dir / ENTRY_DOCUMENT
    name = read_frontmatter(skill_dir).get("name")
    if not isinstance(name, str):
        return [f"{entry}: frontmatter 'name' must be a string, got {type(name).__name__}."]

    problems: list[str] = []
    if name != skill_dir.name:
        problems.append(
            f"{entry}: frontmatter name {name!r} must equal the directory name"
            f" {skill_dir.name!r}. Rename one to match the other."
        )
    if not SKILL_NAME_PATTERN.fullmatch(name):
        problems.append(
            f"{entry}: frontmatter name {name!r} must be lowercase letters, digits and"
            " single interior hyphens only."
        )
    if len(name) > MAX_NAME_LENGTH:
        problems.append(
            f"{entry}: frontmatter name is {len(name)} characters; the limit is {MAX_NAME_LENGTH}."
        )
    return problems


def description_problems(skill_dir: pathlib.Path) -> list[str]:
    """Return every way the ``description`` field fails the format's rules."""
    entry = skill_dir / ENTRY_DOCUMENT
    description = read_frontmatter(skill_dir).get("description")
    if not isinstance(description, str):
        return [
            f"{entry}: frontmatter 'description' must be a string,"
            f" got {type(description).__name__}."
        ]

    problems: list[str] = []
    if not description.strip():
        problems.append(
            f"{entry}: frontmatter description is empty. It is the only text an agent"
            " reads when deciding whether to load the skill."
        )
    if len(description) > MAX_DESCRIPTION_LENGTH:
        problems.append(
            f"{entry}: frontmatter description is {len(description)} characters;"
            f" the limit is {MAX_DESCRIPTION_LENGTH}."
        )
    return problems


def _strip_code_fences(text: str) -> str:
    """Drop fenced code blocks.

    Snippets mention neighbouring documents in comments ("per preflight.md") without
    meaning them as paths to follow, so they are not references and must not be
    resolved as such.
    """
    kept: list[str] = []
    inside_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
            continue
        if not inside_fence:
            kept.append(line)
    return "\n".join(kept)


def _is_relative_document_reference(candidate: str) -> bool:
    target = candidate.split("#", 1)[0]
    if not target.endswith(".md"):
        return False
    if "://" in target or target.startswith(("/", "~")):
        return False
    # Placeholders such as `<name>.md` and prose containing spaces are not paths.
    return not any(character in target for character in "<>| \t")


def find_relative_references(document: pathlib.Path) -> set[str]:
    """Return the relative document references a markdown file points at.

    The content spells its references as inline code spans, but markdown links are
    accepted too: an extractor that recognised only one spelling would return nothing
    for the other and every downstream assertion would pass over an empty set.
    """
    text = _strip_code_fences(document.read_text(encoding="utf-8"))
    candidates = set(CODE_SPAN_PATTERN.findall(text)) | set(MARKDOWN_LINK_PATTERN.findall(text))
    return {candidate for candidate in candidates if _is_relative_document_reference(candidate)}


def _code_fence_contents(text: str) -> str:
    """Return only fenced code block content -- the inverse of ``_strip_code_fences``."""
    fenced: list[str] = []
    inside_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            fenced.append(line)
    return "\n".join(fenced)


def find_fenced_references(document: pathlib.Path) -> set[str]:
    """Return reference-shaped paths mentioned inside fenced code blocks.

    ``_strip_code_fences`` drops fenced content before ``find_relative_references``
    runs, so a wrong ``references/...`` path sitting inside a code comment resolves
    against nothing and passes silently -- that gap has already shipped a broken
    reference once, caught only by reading. This scans fenced content on its own,
    narrowly, for paths that already carry the ``references/`` prefix.
    """
    fenced_text = _code_fence_contents(document.read_text(encoding="utf-8"))
    return set(FENCED_REFERENCE_PATTERN.findall(fenced_text))


def find_all_references(document: pathlib.Path) -> set[str]:
    """Return every reference a document points at, prose and fenced alike."""
    return find_relative_references(document) | find_fenced_references(document)


def reference_problems(skill_dir: pathlib.Path) -> list[str]:
    """Return every reference in a skill that fails to resolve inside the skill."""
    skill_root = skill_dir.resolve()
    problems: list[str] = []
    for document in sorted(skill_dir.rglob("*.md")):
        for reference in sorted(find_all_references(document)):
            target = (document.parent / reference.split("#", 1)[0]).resolve()
            try:
                relative = target.relative_to(skill_root)
            except ValueError:
                problems.append(
                    f"{document}: reference {reference!r} points outside"
                    f" {skill_dir.name}. A skill directory must be self-contained."
                )
                continue
            if not target.is_file():
                problems.append(
                    f"{document}: reference {reference!r} does not exist"
                    f" (resolved to {target}). Add the file or drop the reference."
                )
                continue
            if len(relative.parts) > MAX_REFERENCE_PARTS:
                problems.append(
                    f"{document}: reference {reference!r} resolves to {relative},"
                    " which is more than one directory below the skill root."
                    " Flatten it into the references directory."
                )
    return problems


def count_references(skill_dir: pathlib.Path) -> int:
    return sum(len(find_all_references(document)) for document in skill_dir.rglob("*.md"))


def shared_reference_problems(skills_root: pathlib.Path) -> list[str]:
    """Return every shared reference copy that has drifted from the canonical one."""
    problems: list[str] = []
    for shared_name in SHARED_REFERENCES:
        canonical = skills_root / CANONICAL_SKILL / REFERENCE_DIR / shared_name
        if not canonical.is_file():
            problems.append(
                f"{canonical} is missing. It is the canonical copy every other skill's"
                f" {shared_name} is compared against."
            )
            continue
        canonical_bytes = canonical.read_bytes()
        for skill_dir in discover_skills(skills_root):
            sibling = skill_dir / REFERENCE_DIR / shared_name
            if sibling == canonical or not sibling.is_file():
                continue
            if sibling.read_bytes() != canonical_bytes:
                problems.append(
                    f"{sibling} has drifted from the canonical copy."
                    f" Copy {canonical} over {sibling} so the two are byte-identical."
                )
    return problems


def skills_holding(skills_root: pathlib.Path, shared_name: str) -> list[pathlib.Path]:
    return [
        skill_dir
        for skill_dir in discover_skills(skills_root)
        if (skill_dir / REFERENCE_DIR / shared_name).is_file()
    ]


def carriage_problems(skills_root: pathlib.Path) -> list[str]:
    """Return every bundled skill directory missing one of the shared references.

    ``shared_reference_problems`` above compares copies that exist against the
    canonical one -- it is a byte-equality check with nothing to say about a skill
    that ships without a copy at all, because there is nothing there to compare.
    This is the carriage check that byte-equality alone cannot be: every bundled
    skill must hold its own copy of every shared reference.
    """
    problems: list[str] = []
    for skill_dir in discover_skills(skills_root):
        for shared_name in SHARED_REFERENCES:
            if not (skill_dir / REFERENCE_DIR / shared_name).is_file():
                problems.append(
                    f"{skill_dir} is missing {REFERENCE_DIR}/{shared_name}. Every bundled"
                    f" skill must carry its own copy of {shared_name}; copy it from"
                    f" {skills_root / CANONICAL_SKILL / REFERENCE_DIR / shared_name}."
                )
    return problems


def find_skill_mentions(document: pathlib.Path) -> set[str]:
    """Return skill names of this bundle's naming family mentioned in prose."""
    text = _strip_code_fences(document.read_text(encoding="utf-8"))
    return set(SKILL_MENTION_PATTERN.findall(text))


def unresolved_skill_mention_problems(
    skills_root: pathlib.Path, skill_dir: pathlib.Path
) -> list[str]:
    """Return every prose-mentioned skill name that does not resolve to a bundled skill.

    Nothing else in this suite checks this: frontmatter, references, and shared-copy
    checks are all silent about a hand-off that names a skill that does not exist. A
    stale or misspelled name here passes green and misroutes a real user at runtime.
    """
    known_skill_names = {known.name for known in discover_skills(skills_root)}
    problems: list[str] = []
    for document in sorted(skill_dir.rglob("*.md")):
        for mentioned in sorted(find_skill_mentions(document)):
            if mentioned not in known_skill_names:
                problems.append(
                    f"{document}: mentions skill {mentioned!r}, which is not a bundled"
                    f" skill directory under {skills_root}. Fix the name or add the skill."
                )
    return problems


def _closure_of_subclasses(cls: type[BaseModel]) -> set[type[BaseModel]]:
    found: set[type[BaseModel]] = set(cls.__subclasses__())
    for subclass in list(found):
        found |= _closure_of_subclasses(subclass)
    return found


def _attachable_types_scoped_to(cls: type[BaseModel], owner_module: str) -> frozenset[str]:
    """Return the ``type`` default of every subclass of ``cls`` owned by ``owner_module``.

    A class is attachable when it declares its own non-``None`` default for the
    ``type`` field -- that selects concrete actions and excludes abstract bases, whose
    ``type`` has no default of its own. Scoping to ``owner_module`` is what keeps a
    third party's own registration from turning a completeness check red; split out
    as a pure function of its two inputs so that scoping can be proven against a
    synthetic hierarchy without touching Great Expectations' real action registry.
    """
    attachable = (
        candidate
        for candidate in _closure_of_subclasses(cls)
        if candidate.__module__ == owner_module and candidate.__fields__["type"].default is not None
    )
    return frozenset(candidate.__fields__["type"].default for candidate in attachable)


def gx_attachable_action_types() -> frozenset[str]:
    """Return the ``type`` literal of every action Great Expectations itself attaches.

    Mirrors the closure the action-catalog reference documents and verifies against,
    scoped to classes defined inside Great Expectations' own action module -- a third
    party registering an action of its own must not turn this assertion red.
    """
    from great_expectations.checkpoint import actions as actions_module

    return _attachable_types_scoped_to(actions_module.ValidationAction, actions_module.__name__)


def documented_action_types(action_catalog: pathlib.Path) -> frozenset[str]:
    """Return the ``type`` values documented in the action catalog's stability table."""
    text = action_catalog.read_text(encoding="utf-8")
    return frozenset(match.group("type") for match in ACTION_TABLE_ROW_PATTERN.finditer(text))


def action_catalog_drift_problems(action_catalog: pathlib.Path) -> list[str]:
    """Return every mismatch between the documented action catalog and the live registry."""
    documented = documented_action_types(action_catalog)
    actual = gx_attachable_action_types()
    problems: list[str] = []
    missing = actual - documented
    if missing:
        problems.append(
            f"{action_catalog} does not document action type(s) {sorted(missing)}, which"
            " Great Expectations registers as attachable. This catalog is meant to cover"
            " every action Great Expectations offers, not a curated subset -- add a row"
            " and a field table for each."
        )
    extra = documented - actual
    if extra:
        problems.append(
            f"{action_catalog} documents action type(s) {sorted(extra)}, which Great"
            " Expectations no longer registers as attachable. Remove the stale row(s)."
        )
    return problems


def entry_document_size_problems(skill_dir: pathlib.Path) -> list[str]:
    """Return a problem when the entry document exceeds its context budget."""
    entry = skill_dir / ENTRY_DOCUMENT
    line_count = len(entry.read_text(encoding="utf-8").splitlines())
    if line_count <= MAX_ENTRY_DOCUMENT_LINES:
        return []
    return [
        f"{entry} is {line_count} lines; the budget is {MAX_ENTRY_DOCUMENT_LINES}."
        f" Move detail into {REFERENCE_DIR}/."
    ]


# ---------------------------------------------------------------------------
# Consent gates: an environment-mutating or disk-writing action that a skill's
# flow can reach must be handed to the user rather than taken on their behalf.
# The register below is the data every check in this section is driven off of
# -- adding a gated action later is one row plus prose, not a new test to
# remember to write.
# ---------------------------------------------------------------------------

#: Sentinel for a register row whose gate applies to every bundled skill,
#: rather than a named subset of them.
ALL_BUNDLED_SKILLS: Final = "all"

#: The inert marker pinning a gate to the passage of content that states it.
#: Invisible to a reader (an HTML comment), but text an agent reads.
CONSENT_GATE_MARKER_PATTERN: Final = re.compile(
    r"<!--\s*consent-gate:\s*(?P<gate_id>[a-z-]+)\s*-->"
)

#: Only a "##" heading starts a new co-location unit. A "###" subsection is
#: read as part of its enclosing "##" section, so a marker or a trigger token
#: placed in either resolves to the same unit -- both reference homes are
#: "###"-nested, and a model without this inheritance would turn them into
#: false violations.
SECTION_HEADING_PATTERN: Final = re.compile(r"^##(?!#)\s+(?P<title>.+?)\s*$")


@dataclasses.dataclass(frozen=True)
class ConsentGate:
    """One row of the consent-gate register.

    ``entry_documents`` is either ``ALL_BUNDLED_SKILLS`` or an explicit tuple
    of skill directory names -- the skills whose ``SKILL.md`` must pin the
    gate. ``trigger_tokens`` is the small, literal set of spellings a check
    can search for; see the "Known trigger-token limits" note below for what
    that smallness costs.
    """

    id: str
    gated_action: str
    entry_documents: str | tuple[str, ...]
    trigger_tokens: tuple[str, ...]


CONSENT_GATES: Final = (
    ConsentGate(
        id="install",
        gated_action=(
            "installing, upgrading, or removing a package, or any other mutation of"
            " the interpreter, virtual environment, environment variables, or shell"
            " state"
        ),
        entry_documents=ALL_BUNDLED_SKILLS,
        trigger_tokens=("pip install", "uv pip install", "python -m pip", "great_expectations["),
    ),
    ConsentGate(
        id="project",
        gated_action="creating a GX project directory on the user's disk",
        entry_documents=ALL_BUNDLED_SKILLS,
        trigger_tokens=('get_context(mode="file"',),
    ),
    ConsentGate(
        id="config-file",
        gated_action="editing an existing project's great_expectations.yml",
        entry_documents=("gx-configure-checkpoint",),
        trigger_tokens=("data_docs_sites: null",),
    ),
    ConsentGate(
        id="saved-file",
        gated_action="writing a file the user did not ask for and locate",
        entry_documents=("gx-configure-checkpoint",),
        trigger_tokens=("at a path the user confirms",),
    ),
)


@dataclasses.dataclass(frozen=True)
class ConsentGateOverFireAllowance:
    """One documented, narrowly-anchored exception to the co-location check.

    Each entry names a trigger-token occurrence that legitimately sits outside
    its gate's marked section -- the passage names the gated action while
    describing something other than performing it. Anchoring by section title
    rather than bare line number is what keeps an entry from drifting into
    excusing something else as the surrounding content moves; if a listed
    title stops matching any section that actually carries the token, the
    allowance goes unused and is reported as stale rather than passing quietly.

    ``expected_occurrences`` pins *how much* is excused, not just *where*: an
    allowance keyed only on section identity would excuse every unmarked
    occurrence ever added to that section. If the section comes to hold more
    unmarked trigger-token lines than this, the excess is reported rather
    than waved through.

    Neither the section anchor nor the count guards against substitution:
    replacing the excused line's own content with a *different* occurrence of
    the same trigger token -- same count, same location, opposite meaning --
    would pass both silently. ``expected_line_substring`` closes that: it
    pins a phrase specific to the excused line's benign meaning, so a rewrite
    that keeps the count and position but changes what the line says breaks
    the anchor and is reported rather than waved through.
    """

    gate_id: str
    relative_path: str
    section_title: str
    reason: str
    expected_line_substring: str
    expected_occurrences: int = 1


CONSENT_GATE_OVER_FIRE_ALLOWANCES: Final = (
    ConsentGateOverFireAllowance(
        gate_id="project",
        relative_path="gx-configure-checkpoint/references/action-catalog.md",
        section_title="Enabling Data Docs",
        reason=(
            "reloads the project already opened at preflight -- a pre-existing"
            " comment in the fenced snippet says so outright -- not a new project"
            " directory to ask the user about."
        ),
        expected_line_substring="<the project root established at preflight>",
        expected_occurrences=1,
    ),
    ConsentGateOverFireAllowance(
        gate_id="project",
        relative_path="gx-configure-data-source/references/write-out.md",
        section_title='What "usable without modification" means, and its one exception',
        reason=(
            "a round-trip verification claim: a fresh file-backed context against the"
            " directory just written loads the same objects back. Describes a check,"
            " not a write."
        ),
        expected_line_substring="against that directory loads the same data sources",
        expected_occurrences=1,
    ),
    ConsentGateOverFireAllowance(
        gate_id="project",
        relative_path="gx-configure-expectations/references/write-out.md",
        section_title='What "usable without modification" means, and its one exception',
        reason=(
            "the same round-trip verification claim as the data-source copy above --"
            " this reference is byte-identical across all three skills."
        ),
        expected_line_substring="against that directory loads the same data sources",
        expected_occurrences=1,
    ),
    ConsentGateOverFireAllowance(
        gate_id="project",
        relative_path="gx-configure-checkpoint/references/write-out.md",
        section_title='What "usable without modification" means, and its one exception',
        reason=(
            "the same round-trip verification claim as the data-source copy above --"
            " this reference is byte-identical across all three skills."
        ),
        expected_line_substring="against that directory loads the same data sources",
        expected_occurrences=1,
    ),
)

# ---------------------------------------------------------------------------
# Known trigger-token limits.
#
# The token sets above are small and literal on purpose: that lets them miss a
# new spelling, but it also lets them over-fire on an incidental mention --
# and over-firing is the safe direction, since it fails the build instead of
# passing silently. Token matching is whitespace-normalizing (see
# `_line_token_occurrences` below), so a token split only by a markdown soft
# wrap is still found -- a line break is not semantic, and a reader sees one
# phrase either way. What remains uncaught is recorded here rather than
# papered over by widening a token to reach it:
#
# - `references/run-and-schedule.md:149` reads a bare `mode="file"` with no
#   `get_context(` prefix, so it is not a `project` token match. Harmless: it
#   sits in "## The run snippet" beside two occurrences that do match.
# - `references/action-catalog.md:265` carries two bare `data_docs_sites`
#   occurrences on one line ("Change `data_docs_sites: null` to
#   `data_docs_sites: {}`"); relevant only to a checker that counts lines
#   rather than token occurrences -- the checks below count occurrences.
# - Whitespace normalization collapses a blank line (a paragraph break) the
#   same as any other whitespace run, so a token can match split across two
#   paragraphs, not only across a single soft wrap -- verified directly:
#   "...the user\n\nconfirms..." matches a "the user confirms" token. A list
#   item, fenced block, heading, or table-cell boundary still blocks a match
#   because markup intervenes there, not whitespace alone; only the
#   paragraph case is affected. Left uncollapsed-vs-not as it is (collapsing
#   is not restricted to a single newline) rather than narrowed: over-firing
#   across a paragraph break still fails the build instead of passing
#   silently, matching the safe direction the rest of this section already
#   accepts, and no content in the tree today depends on the distinction.
# - A gate stated in both an entry document and a reference is shielded from
#   the tree-wide vacuity check (`consent_gate_vacuity_problems`) if one home
#   is deleted wholesale: the other home's occurrence keeps the gate's token
#   count above zero, so vacuity never fires. This is a property of checking
#   at the set level across the whole tree, not a limit of the token sets
#   themselves, so it is recorded here rather than folded into the register.
# ---------------------------------------------------------------------------


def _entry_document_skill_names(gate: ConsentGate, skills_root: pathlib.Path) -> tuple[str, ...]:
    if gate.entry_documents == ALL_BUNDLED_SKILLS:
        return tuple(skill_dir.name for skill_dir in discover_skills(skills_root))
    assert isinstance(gate.entry_documents, tuple)
    return gate.entry_documents


def find_consent_gate_markers(document: pathlib.Path) -> list[tuple[int, str]]:
    """Return every (1-indexed line number, gate id) marker in a document."""
    markers: list[tuple[int, str]] = []
    for lineno, line in enumerate(document.read_text(encoding="utf-8").splitlines(), start=1):
        match = CONSENT_GATE_MARKER_PATTERN.search(line)
        if match:
            markers.append((lineno, match.group("gate_id")))
    return markers


def carriage_gate_problems(skills_root: pathlib.Path) -> list[str]:
    """Return every gate missing its marker from one of the entry documents it must reach.

    This is the check that would have failed on the shipped v1 content, where
    every bundled ``SKILL.md`` contained zero occurrences of "install".
    """
    problems: list[str] = []
    for gate in CONSENT_GATES:
        for skill_name in _entry_document_skill_names(gate, skills_root):
            entry = skills_root / skill_name / ENTRY_DOCUMENT
            if not entry.is_file():
                problems.append(
                    f"{entry} does not exist; cannot carry the {gate.id!r} consent gate."
                )
                continue
            marker_ids = {marker_id for _, marker_id in find_consent_gate_markers(entry)}
            if gate.id not in marker_ids:
                problems.append(
                    f"{entry} does not carry a '<!-- consent-gate: {gate.id} -->' marker."
                    f" This entry document's flow can reach {gate.gated_action}, so it must"
                    " pin the gate where the standing rule against doing that unasked is"
                    " stated."
                )
    return problems


def _normalize_whitespace_with_line_map(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace runs to a single space, tracking each output
    character's 1-indexed source line.

    A markdown soft wrap is a whitespace run (a newline, maybe surrounded by
    spaces) like any other -- collapsing it is what lets a token search find
    prose split only by a line break. The returned list maps each index in
    the normalized string back to the line the corresponding source
    character (or, for a collapsed run, the run's first character) came from,
    so a match found in the normalized text can still be reported against a
    real line.
    """
    normalized: list[str] = []
    line_map: list[int] = []
    lineno = 1
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            run_start_line = lineno
            while index < length and text[index].isspace():
                if text[index] == "\n":
                    lineno += 1
                index += 1
            normalized.append(" ")
            line_map.append(run_start_line)
        else:
            normalized.append(char)
            line_map.append(lineno)
            index += 1
    return "".join(normalized), line_map


def _line_token_occurrences(text: str, tokens: tuple[str, ...]) -> list[int]:
    """Return the 1-indexed line numbers containing at least one of ``tokens``.

    Matching is whitespace-normalizing: runs of whitespace, including a
    markdown soft wrap, collapse to a single space in both the document and
    the token before the search runs, and each match's start offset is then
    mapped back to the line it began on. This tolerates only a line break --
    it cannot match text that is not there -- so it stays a match on what the
    content says, not a widened net. See "Known trigger-token limits" above
    for what still goes uncaught.
    """
    normalized_text, line_map = _normalize_whitespace_with_line_map(text)
    lines: set[int] = set()
    for token in tokens:
        normalized_token = " ".join(token.split())
        search_from = 0
        while True:
            match_index = normalized_text.find(normalized_token, search_from)
            if match_index == -1:
                break
            lines.add(line_map[match_index])
            search_from = match_index + 1
    return sorted(lines)


def _normalized_substring_lines(text: str, substring: str) -> set[int]:
    """Return the 1-indexed source lines a whitespace-normalized ``substring`` starts on.

    Shares ``_normalize_whitespace_with_line_map`` with ``_line_token_occurrences``
    so an allowance's anchor is checked the same way its gate's trigger token is
    matched -- a soft wrap inside the anchor phrase doesn't break the check any
    more than one inside a trigger token would.
    """
    normalized_text, line_map = _normalize_whitespace_with_line_map(text)
    normalized_substring = " ".join(substring.split())
    lines: set[int] = set()
    search_from = 0
    while True:
        match_index = normalized_text.find(normalized_substring, search_from)
        if match_index == -1:
            break
        lines.add(line_map[match_index])
        search_from = match_index + 1
    return lines


def _mask_fenced_lines(text: str) -> str:
    """Blank the content of fenced code blocks, keeping every line in place.

    Used only to find section headings: a fenced example is never meant as a
    real "##" boundary, so a line that merely starts with "##" inside one
    (a shell comment, a markdown-about-markdown example) must not split a
    section. Blanking rather than dropping lines keeps line numbers aligned
    with the unmasked text, so callers can still report a real line.
    """
    masked: list[str] = []
    inside_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside_fence = not inside_fence
            masked.append("")
            continue
        masked.append("" if inside_fence else line)
    return "\n".join(masked)


def _toplevel_sections(text: str) -> list[tuple[str, int, int]]:
    """Split a document into ``(heading title, start line, end line)`` "##" sections.

    Content before the first "##" heading -- the title and any lead-in prose
    -- is its own section keyed by an empty title.

    Heading detection ignores fenced code blocks (``_mask_fenced_lines``), but
    the line ranges returned still cover the whole, unmasked document -- a
    trigger-token match inside a fence is still counted against its enclosing
    section, only the heading search itself is fence-blind.
    """
    lines = text.splitlines()
    masked_lines = _mask_fenced_lines(text).splitlines()
    boundaries: list[tuple[str, int]] = [("", 1)]
    for lineno, line in enumerate(masked_lines, start=1):
        match = SECTION_HEADING_PATTERN.match(line)
        if match:
            boundaries.append((match.group("title"), lineno))
    sections: list[tuple[str, int, int]] = []
    for index, (title, start) in enumerate(boundaries):
        end = boundaries[index + 1][1] - 1 if index + 1 < len(boundaries) else len(lines)
        sections.append((title, start, end))
    return sections


def _document_co_location_problems(
    document: pathlib.Path,
    gate: ConsentGate,
    relative_path: str,
    allowance_index_by_key: dict[tuple[str, str, str], int],
    used_allowances: set[int],
) -> list[str]:
    """Return one document's co-location problems for one gate.

    Split out of ``consent_gate_co_location_problems`` so that function stays
    a plain double loop over gates and documents; all the per-document
    section/marker/allowance logic lives here instead.
    """
    text = document.read_text(encoding="utf-8")
    token_lines = set(_line_token_occurrences(text, gate.trigger_tokens))
    if not token_lines:
        return []
    marker_lines = {
        lineno for lineno, gate_id in find_consent_gate_markers(document) if gate_id == gate.id
    }

    problems: list[str] = []
    for title, start, end in _toplevel_sections(text):
        lines_in_section = sorted(lineno for lineno in token_lines if start <= lineno <= end)
        if not lines_in_section:
            continue
        if any(start <= marker_line <= end for marker_line in marker_lines):
            continue
        key = (gate.id, relative_path, title)
        allowance_index = allowance_index_by_key.get(key)
        if allowance_index is not None:
            used_allowances.add(allowance_index)
            allowance = CONSENT_GATE_OVER_FIRE_ALLOWANCES[allowance_index]
            excused_lines = lines_in_section[: allowance.expected_occurrences]
            excess_lines = lines_in_section[allowance.expected_occurrences :]
            anchor_lines = _normalized_substring_lines(text, allowance.expected_line_substring)
            mismatched_lines = [lineno for lineno in excused_lines if lineno not in anchor_lines]
            if mismatched_lines:
                problems.append(
                    f"{document}:{mismatched_lines}: the {gate.id!r} gate's allowance in"
                    f" section '## {title}' excuses this line on the strength of"
                    f" {allowance.expected_line_substring!r}, but the line no longer contains"
                    " that text. The allowance no longer describes what is there -- treat"
                    " this as a fresh, unexcused occurrence: gate it, or update the"
                    " allowance's anchor if the rewrite still means the same excused thing."
                )
            if excess_lines:
                problems.append(
                    f"{document}:{excess_lines}: the {gate.id!r} gate's trigger token has"
                    f" {len(lines_in_section)} unmarked occurrence(s) in section '## {title}',"
                    f" but the allowance there ({allowance.reason!r}) covers only"
                    f" {allowance.expected_occurrences}. The extra occurrence(s) are not excused --"
                    " gate them, or widen the allowance's expected_occurrences with a reason that"
                    " covers them too."
                )
            continue
        problems.append(
            f"{document}:{lines_in_section}: the {gate.id!r} gate's trigger token"
            f" appears in section '## {title}', which carries no"
            f" '<!-- consent-gate: {gate.id} -->' marker. Either the section gates"
            " the action too, or the mention belongs in the allowance list, or it"
            " has to move somewhere that already gates the action."
        )
    return problems


def consent_gate_co_location_problems(skills_root: pathlib.Path) -> list[str]:
    """Return every trigger-token occurrence not co-located with its gate's marker.

    A token match is co-located when it falls inside a "##" section (its
    "###" subsections included) that also carries a
    ``<!-- consent-gate: <id> -->`` marker for the same gate somewhere in that
    section. A handful of occurrences are legitimately elsewhere --
    ``CONSENT_GATE_OVER_FIRE_ALLOWANCES`` above -- and an allowance that stops
    matching anything is reported here too, rather than excusing whatever
    happens to sit at its old address.
    """
    problems: list[str] = []
    allowance_index_by_key = {
        (allowance.gate_id, allowance.relative_path, allowance.section_title): index
        for index, allowance in enumerate(CONSENT_GATE_OVER_FIRE_ALLOWANCES)
    }
    used_allowances: set[int] = set()

    for gate in CONSENT_GATES:
        for skill_dir in discover_skills(skills_root):
            for document in sorted(skill_dir.rglob("*.md")):
                relative_path = document.relative_to(skills_root).as_posix()
                problems.extend(
                    _document_co_location_problems(
                        document, gate, relative_path, allowance_index_by_key, used_allowances
                    )
                )

    for index, allowance in enumerate(CONSENT_GATE_OVER_FIRE_ALLOWANCES):
        if index not in used_allowances:
            problems.append(
                f"the over-fire allowance for {allowance.gate_id!r} at {allowance.relative_path}"
                f" section '## {allowance.section_title}' matched no unmarked trigger-token"
                " occurrence there. It is not excusing anything; fix its anchor or remove it."
            )
    return problems


def consent_gate_vacuity_problems(skills_root: pathlib.Path) -> list[str]:
    """Return every gate whose trigger-token set matches nothing in the bundled tree.

    Set-level per gate, not per token: no other install spelling lives beside
    "pip install" in the shipped content today, so a per-token guard on
    "uv pip install" or "python -m pip" would fail for the wrong reason.
    Without this check at all, deleting a gate's guidance outright would turn
    the co-location check green -- there would be nothing left for it to
    flag.
    """
    problems: list[str] = []
    for gate in CONSENT_GATES:
        matched = any(
            _line_token_occurrences(document.read_text(encoding="utf-8"), gate.trigger_tokens)
            for document in skills_root.rglob("*.md")
        )
        if not matched:
            problems.append(
                f"none of the {gate.id!r} gate's trigger tokens {gate.trigger_tokens!r} matched"
                f" anywhere under {skills_root}. Either the content stopped naming the gated"
                " action, or the token set no longer matches how it's spelled."
            )
    return problems


@pytest.fixture
def violating_skills(tmp_path: pathlib.Path) -> pathlib.Path:
    """A disposable copy of the real content for violations to be introduced into."""
    destination = tmp_path / "skills"
    shutil.copytree(SKILLS_ROOT, destination)
    assert len(discover_skills(destination)) == len(SKILL_DIRS), (
        f"the copy at {destination} does not hold the same skills as {SKILLS_ROOT}"
    )
    return destination


def rewrite_frontmatter_field(skill_dir: pathlib.Path, field: str, value: str) -> None:
    entry = skill_dir / ENTRY_DOCUMENT
    text = entry.read_text(encoding="utf-8")
    rewritten = re.sub(rf"^{field}: .*$", f"{field}: {value}", text, count=1, flags=re.MULTILINE)
    assert rewritten != text, f"fixture setup did not rewrite {field!r} in {entry}"
    entry.write_text(rewritten, encoding="utf-8")


def _first_entry_document_skill(gate: ConsentGate, skills_root: pathlib.Path) -> str:
    """Return one skill whose entry document must carry ``gate``'s marker.

    Used by the carriage mutation below: proving the check can fail needs only
    one of a gate's entry documents broken, not all of them.
    """
    return _entry_document_skill_names(gate, skills_root)[0]


def _strip_gate_marker(text: str, gate_id: str) -> str:
    """Remove every marker for ``gate_id`` from ``text``, leaving others intact."""
    marker = f"<!-- consent-gate: {gate_id} -->"
    assert marker in text, f"fixture setup expected to find {marker!r} before removing it"
    return text.replace(marker, "")


def _scrub_token(text: str, token: str) -> str:
    """Remove every whitespace-tolerant occurrence of ``token`` from ``text``.

    A literal ``str.replace`` can miss an occurrence split by a markdown soft
    wrap and leave the vacuity mutation green for the wrong reason -- this
    mirrors the whitespace normalization ``_line_token_occurrences`` performs
    when matching the real content, so the mutation and the check agree on
    what counts as "still there".
    """
    pattern = re.compile(r"\s+".join(re.escape(part) for part in token.split()))
    return pattern.sub(" ", text)


# ---------------------------------------------------------------------------
# The real bundled content conforms.
# ---------------------------------------------------------------------------


def test_bundled_skills_are_discovered():
    """Everything below is parametrized over discovery, so discovery is checked first."""
    assert SKILLS_ROOT.is_dir(), f"{SKILLS_ROOT} does not exist"
    assert len(SKILL_DIRS) >= MIN_BUNDLED_SKILLS, (
        f"expected at least {MIN_BUNDLED_SKILLS} skill directories with an"
        f" {ENTRY_DOCUMENT} under {SKILLS_ROOT}, found"
        f" {[skill_dir.name for skill_dir in SKILL_DIRS]}"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_frontmatter_parses(skill_dir: pathlib.Path):
    frontmatter = read_frontmatter(skill_dir)
    assert set(frontmatter) >= {"name", "description"}, (
        f"{skill_dir / ENTRY_DOCUMENT}: frontmatter is missing required fields;"
        f" found {sorted(frontmatter)}"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_name_matches_directory_and_format(skill_dir: pathlib.Path):
    problems = name_problems(skill_dir)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_description_is_present_and_within_limit(skill_dir: pathlib.Path):
    problems = description_problems(skill_dir)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_entry_document_references_its_reference_documents(skill_dir: pathlib.Path):
    """A skill that appears to reference nothing is the signature of a broken extractor."""
    references = find_relative_references(skill_dir / ENTRY_DOCUMENT)
    assert references, (
        f"{skill_dir / ENTRY_DOCUMENT}: no relative document references were extracted."
        " Either the entry document stopped routing into its references or the"
        " extractor no longer recognises how they are written."
    )
    assert {reference for reference in references if reference.startswith(f"{REFERENCE_DIR}/")}, (
        f"{skill_dir / ENTRY_DOCUMENT}: no references into {REFERENCE_DIR}/: {sorted(references)}"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_references_resolve_at_most_one_level_deep(skill_dir: pathlib.Path):
    assert count_references(skill_dir) > 0, f"no references were extracted from {skill_dir}"
    problems = reference_problems(skill_dir)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("shared_name", SHARED_REFERENCES)
def test_shared_reference_is_carried_by_every_skill_that_needs_it(shared_name: str):
    """The equality check below is vacuous unless at least two copies exist."""
    holders = skills_holding(SKILLS_ROOT, shared_name)
    assert len(holders) >= MIN_BUNDLED_SKILLS, (
        f"{shared_name} was found in {[holder.name for holder in holders]};"
        f" expected at least {MIN_BUNDLED_SKILLS} skills to carry their own copy"
    )


def test_shared_references_are_byte_identical():
    problems = shared_reference_problems(SKILLS_ROOT)
    assert not problems, "\n".join(problems)


def test_every_bundled_skill_carries_every_shared_reference():
    problems = carriage_problems(SKILLS_ROOT)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_skill_mentions_in_prose_resolve_to_bundled_skills(skill_dir: pathlib.Path):
    problems = unresolved_skill_mention_problems(SKILLS_ROOT, skill_dir)
    assert not problems, "\n".join(problems)


def test_action_catalog_matches_the_live_action_registry():
    action_catalog = SKILLS_ROOT / ACTION_CATALOG_SKILL / REFERENCE_DIR / ACTION_CATALOG_REFERENCE
    assert action_catalog.is_file(), f"{action_catalog} does not exist"
    problems = action_catalog_drift_problems(action_catalog)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_entry_document_within_size_budget(skill_dir: pathlib.Path):
    problems = entry_document_size_problems(skill_dir)
    assert not problems, "\n".join(problems)


def test_every_consent_gate_is_carried_by_its_entry_documents():
    problems = carriage_gate_problems(SKILLS_ROOT)
    assert not problems, "\n".join(problems)


def test_every_consent_gate_trigger_token_is_co_located_with_its_marker():
    problems = consent_gate_co_location_problems(SKILLS_ROOT)
    assert not problems, "\n".join(problems)


def test_every_consent_gate_trigger_token_set_matches_something_in_the_tree():
    problems = consent_gate_vacuity_problems(SKILLS_ROOT)
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------------------
# Each check above catches the violation it exists for.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ["entry_text", "expected_message"],
    [
        pytest.param("# no frontmatter here\n", "no YAML frontmatter", id="delimiters_missing"),
        pytest.param(
            '---\nname: gx-configure-data-source\ndescription: "unterminated\n---\n# body\n',
            "not valid YAML",
            id="unparseable_yaml",
        ),
        pytest.param(
            "---\njust a string\n---\n# body\n",
            "must be a YAML mapping",
            id="not_a_mapping",
        ),
    ],
)
def test_broken_frontmatter_is_reported(
    violating_skills: pathlib.Path, entry_text: str, expected_message: str
):
    skill_dir = violating_skills / CANONICAL_SKILL
    (skill_dir / ENTRY_DOCUMENT).write_text(entry_text, encoding="utf-8")

    with pytest.raises(SkillContentError, match=expected_message):
        read_frontmatter(skill_dir)


def test_name_that_disagrees_with_the_directory_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    rewrite_frontmatter_field(skill_dir, "name", "some-other-skill")

    problems = name_problems(skill_dir)

    assert [problem for problem in problems if "must equal the directory name" in problem]


def test_name_outside_the_allowed_character_set_is_reported(violating_skills: pathlib.Path):
    # The directory is renamed to match, so the character-set rule is the only one left
    # that can fail -- otherwise this would ride on the directory-match check instead.
    disallowed = "GX_Configure_Data_Source"
    skill_dir = (violating_skills / CANONICAL_SKILL).rename(violating_skills / disallowed)
    rewrite_frontmatter_field(skill_dir, "name", disallowed)

    problems = name_problems(skill_dir)

    assert [problem for problem in problems if "lowercase letters" in problem]
    assert not [problem for problem in problems if "must equal the directory name" in problem]


def test_name_over_the_length_limit_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    over_limit = "-".join(["gx"] * ((MAX_NAME_LENGTH // 3) + 1))
    assert len(over_limit) > MAX_NAME_LENGTH
    skill_dir = skill_dir.rename(skill_dir.parent / over_limit)
    rewrite_frontmatter_field(skill_dir, "name", over_limit)

    problems = name_problems(skill_dir)

    assert [problem for problem in problems if "the limit is" in problem]


def test_empty_description_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    rewrite_frontmatter_field(skill_dir, "description", '"   "')

    problems = description_problems(skill_dir)

    assert [problem for problem in problems if "description is empty" in problem]


def test_description_over_the_length_limit_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    rewrite_frontmatter_field(skill_dir, "description", "d" * (MAX_DESCRIPTION_LENGTH + 1))

    problems = description_problems(skill_dir)

    assert [problem for problem in problems if "the limit is" in problem]


def test_dangling_reference_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    entry = skill_dir / ENTRY_DOCUMENT
    entry.write_text(
        f"{entry.read_text(encoding='utf-8')}\nSee `{REFERENCE_DIR}/does-not-exist.md`.\n",
        encoding="utf-8",
    )

    problems = reference_problems(skill_dir)

    assert [problem for problem in problems if "does not exist" in problem]


def test_reference_more_than_one_level_deep_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    nested = skill_dir / REFERENCE_DIR / "nested" / "buried.md"
    nested.parent.mkdir()
    nested.write_text("# buried\n", encoding="utf-8")
    entry = skill_dir / ENTRY_DOCUMENT
    entry.write_text(
        f"{entry.read_text(encoding='utf-8')}\nSee `{REFERENCE_DIR}/nested/buried.md`.\n",
        encoding="utf-8",
    )

    problems = reference_problems(skill_dir)

    assert [problem for problem in problems if "more than one directory below" in problem]


def test_reference_escaping_the_skill_directory_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    entry = skill_dir / ENTRY_DOCUMENT
    sibling = next(
        candidate
        for candidate in discover_skills(violating_skills)
        if candidate.name != CANONICAL_SKILL
    )
    escaping = f"../{sibling.name}/{REFERENCE_DIR}/preflight.md"
    entry.write_text(f"{entry.read_text(encoding='utf-8')}\nSee `{escaping}`.\n", encoding="utf-8")

    # The reference resolves to a real file, so only the containment rule catches it.
    assert (entry.parent / escaping).is_file()
    problems = reference_problems(skill_dir)

    assert [problem for problem in problems if "points outside" in problem]


@pytest.mark.parametrize("shared_name", SHARED_REFERENCES)
def test_diverged_shared_reference_is_reported(violating_skills: pathlib.Path, shared_name: str):
    sibling = next(
        skill_dir / REFERENCE_DIR / shared_name
        for skill_dir in discover_skills(violating_skills)
        if skill_dir.name != CANONICAL_SKILL
    )
    sibling.write_text(
        f"{sibling.read_text(encoding='utf-8')}\nAn edit made to one copy only.\n",
        encoding="utf-8",
    )

    problems = shared_reference_problems(violating_skills)

    canonical = violating_skills / CANONICAL_SKILL / REFERENCE_DIR / shared_name
    remedy = f"Copy {canonical} over {sibling}"
    assert [problem for problem in problems if "drifted from the canonical copy" in problem]
    assert [problem for problem in problems if remedy in problem], (
        f"the failure must name the fix; got {problems}"
    )


@pytest.mark.parametrize("shared_name", SHARED_REFERENCES)
def test_missing_canonical_shared_reference_is_reported(
    violating_skills: pathlib.Path, shared_name: str
):
    (violating_skills / CANONICAL_SKILL / REFERENCE_DIR / shared_name).unlink()

    problems = shared_reference_problems(violating_skills)

    assert [problem for problem in problems if "is missing" in problem]


def test_over_budget_entry_document_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / CANONICAL_SKILL
    entry = skill_dir / ENTRY_DOCUMENT
    padding = "\n".join(["padding"] * (MAX_ENTRY_DOCUMENT_LINES + 1))
    entry.write_text(f"{entry.read_text(encoding='utf-8')}\n{padding}\n", encoding="utf-8")

    problems = entry_document_size_problems(skill_dir)

    assert [problem for problem in problems if "the budget is" in problem]


def test_fenced_reference_that_does_not_exist_is_reported(violating_skills: pathlib.Path):
    """The extractor used to see only prose references -- a wrong path inside a fenced
    code comment resolved against nothing and passed silently. This is the mutation
    proof that fenced content is checked too.
    """
    skill_dir = violating_skills / CANONICAL_SKILL
    entry = skill_dir / ENTRY_DOCUMENT
    text = entry.read_text(encoding="utf-8")
    entry.write_text(
        f"{text}\n```python\n# step 1, per references/does-not-exist-in-a-fence.md\n```\n",
        encoding="utf-8",
    )

    problems = reference_problems(skill_dir)

    assert [
        problem
        for problem in problems
        if "does-not-exist-in-a-fence.md" in problem and "does not exist" in problem
    ]


def test_fenced_bare_filename_comment_is_not_treated_as_a_reference(
    violating_skills: pathlib.Path,
):
    """A bare filename in a fenced comment ("per preflight.md") is deliberately not a
    reference -- only a path already carrying the ``references/`` prefix is. This is
    the counter-proof that the fenced check does not over-fire on ordinary prose.
    """
    skill_dir = violating_skills / CANONICAL_SKILL
    entry = skill_dir / ENTRY_DOCUMENT
    text = entry.read_text(encoding="utf-8")
    entry.write_text(
        f"{text}\n```python\n# step 1, per preflight.md, not a path\n```\n",
        encoding="utf-8",
    )

    references = find_fenced_references(entry)

    assert "preflight.md" not in references
    assert not [reference for reference in references if "does-not-exist" in reference]


@pytest.mark.parametrize("shared_name", SHARED_REFERENCES)
def test_skill_missing_a_shared_reference_is_reported_by_carriage_check_only(
    violating_skills: pathlib.Path, shared_name: str
):
    """The existing byte-equality check compares copies that exist -- it has nothing
    to say about a skill that ships without a copy at all. This proves the carriage
    check catches exactly that gap, and that byte-equality alone does not.
    """
    sibling = next(
        skill_dir
        for skill_dir in discover_skills(violating_skills)
        if skill_dir.name != CANONICAL_SKILL
    )
    (sibling / REFERENCE_DIR / shared_name).unlink()

    carriage = carriage_problems(violating_skills)
    byte_equality = shared_reference_problems(violating_skills)

    assert [problem for problem in carriage if str(sibling) in problem and shared_name in problem]
    assert not [problem for problem in byte_equality if str(sibling) in problem], (
        "byte-equality alone must not notice a missing copy -- that is exactly the gap"
        " the carriage check exists to close"
    )


def test_unresolved_skill_mention_is_reported(violating_skills: pathlib.Path):
    skill_dir = violating_skills / ACTION_CATALOG_SKILL
    entry = skill_dir / ENTRY_DOCUMENT
    anchor = "- No batch definition → hand off to `gx-configure-data-source`.\n"
    text = entry.read_text(encoding="utf-8")
    assert text.count(anchor) == 1, f"anchor is not unique in {entry}"
    entry.write_text(
        text.replace(
            anchor, "- No batch definition → hand off to `gx-configure-nonexistent`.\n", 1
        ),
        encoding="utf-8",
    )

    problems = unresolved_skill_mention_problems(violating_skills, skill_dir)

    assert [problem for problem in problems if "gx-configure-nonexistent" in problem]


def test_action_catalog_missing_a_registered_action_is_reported(violating_skills: pathlib.Path):
    action_catalog = (
        violating_skills / ACTION_CATALOG_SKILL / REFERENCE_DIR / ACTION_CATALOG_REFERENCE
    )
    text = action_catalog.read_text(encoding="utf-8")
    anchor = "| `UpdateDataDocsAction` | `update_data_docs` | `@public_api` |\n"
    assert text.count(anchor) == 1, f"anchor is not unique in {action_catalog}"
    action_catalog.write_text(text.replace(anchor, "", 1), encoding="utf-8")

    problems = action_catalog_drift_problems(action_catalog)

    assert [
        problem
        for problem in problems
        if "update_data_docs" in problem and "does not document" in problem
    ]


def test_action_catalog_documenting_a_nonexistent_action_is_reported(
    violating_skills: pathlib.Path,
):
    action_catalog = (
        violating_skills / ACTION_CATALOG_SKILL / REFERENCE_DIR / ACTION_CATALOG_REFERENCE
    )
    text = action_catalog.read_text(encoding="utf-8")
    anchor = "| `SlackNotificationAction` | `slack` | `@public_api` |\n"
    assert text.count(anchor) == 1, f"anchor is not unique in {action_catalog}"
    bogus_row = "| `FakeAction` | `fake_action_type` | `@public_api` |\n"
    action_catalog.write_text(text.replace(anchor, anchor + bogus_row, 1), encoding="utf-8")

    problems = action_catalog_drift_problems(action_catalog)

    assert [
        problem
        for problem in problems
        if "fake_action_type" in problem and "no longer registers" in problem
    ]


def test_action_type_filter_is_scoped_to_the_owning_module():
    """The action-catalog completeness check must fire for Great Expectations' own
    action registrations and must not fire for anyone else's. Proven against a
    synthetic hierarchy -- not Great Expectations' real action registry -- because
    subclassing the real `ValidationAction` registers the class into Great
    Expectations' process-wide action registry as a side effect, which would leak a
    fake action into that registry for the rest of the test session.
    """

    class Base(BaseModel):
        type: str
        name: str

    class OwnedAction(Base):
        type: str = "owned_action_type"

    class ForeignAction(Base):
        type: str = "foreign_action_type"

    ForeignAction.__module__ = "some_third_party_package.actions"

    scoped = _attachable_types_scoped_to(Base, __name__)

    assert scoped == frozenset({"owned_action_type"})
    assert "foreign_action_type" not in scoped


# ---------------------------------------------------------------------------
# Consent gates: mutation proofs, one per check per gate, driven from
# ``CONSENT_GATES`` -- a fifth register row gains all three proofs below
# automatically, with no new test to remember to write for it.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gate", CONSENT_GATES, ids=lambda gate: gate.id)
def test_carriage_gate_missing_marker_is_reported(
    violating_skills: pathlib.Path, gate: ConsentGate
):
    """One of the gate's entry documents loses its marker; the carriage check must
    name both that document and that gate.
    """
    skill_name = _first_entry_document_skill(gate, violating_skills)
    entry = violating_skills / skill_name / ENTRY_DOCUMENT
    entry.write_text(
        _strip_gate_marker(entry.read_text(encoding="utf-8"), gate.id), encoding="utf-8"
    )

    problems = carriage_gate_problems(violating_skills)

    assert [
        problem
        for problem in problems
        if str(entry) in problem and f"consent-gate: {gate.id} -->" in problem
    ]


@pytest.mark.parametrize("gate", CONSENT_GATES, ids=lambda gate: gate.id)
def test_co_location_unmarked_trigger_token_is_reported(
    violating_skills: pathlib.Path, gate: ConsentGate
):
    """A fresh, unmarked section carrying the gate's trigger token is appended to
    the canonical skill's entry document; the co-location check must name that
    section. Each gate gets its own section title so the failure is unambiguous
    about which gate's proof produced it.
    """
    section_title = f"Mutation probe: {gate.id} trigger without a marker"
    entry = violating_skills / CANONICAL_SKILL / ENTRY_DOCUMENT
    addition = f"\n## {section_title}\n\n{gate.trigger_tokens[0]}\n"
    entry.write_text(entry.read_text(encoding="utf-8") + addition, encoding="utf-8")

    problems = consent_gate_co_location_problems(violating_skills)

    assert [
        problem
        for problem in problems
        if f"'## {section_title}'" in problem and f"the {gate.id!r} gate" in problem
    ]


@pytest.mark.parametrize("gate", CONSENT_GATES, ids=lambda gate: gate.id)
def test_vacuity_gate_with_no_occurrences_is_reported(
    violating_skills: pathlib.Path, gate: ConsentGate
):
    """Every occurrence of the gate's trigger tokens is scrubbed, whitespace-
    tolerantly, from the whole copied tree; the vacuity check must name that
    gate and no other.
    """
    for document in violating_skills.rglob("*.md"):
        text = document.read_text(encoding="utf-8")
        scrubbed = text
        for token in gate.trigger_tokens:
            scrubbed = _scrub_token(scrubbed, token)
        if scrubbed != text:
            document.write_text(scrubbed, encoding="utf-8")

    remaining = [
        document
        for document in violating_skills.rglob("*.md")
        if _line_token_occurrences(document.read_text(encoding="utf-8"), gate.trigger_tokens)
    ]
    assert not remaining, (
        f"fixture setup did not remove every occurrence of the {gate.id!r} gate's"
        f" trigger tokens; still present in {remaining}"
    )

    problems = consent_gate_vacuity_problems(violating_skills)

    assert [
        problem
        for problem in problems
        if gate.id in problem and repr(gate.trigger_tokens) in problem
    ]


# ---------------------------------------------------------------------------
# The over-fire allowance machinery: its three failure modes, proven against
# the real "project" allowance for the checkpoint skill's action catalog.
# The allowances exist only for the "project" gate today, so these are not
# parametrized over the register the way the checks above are.
# ---------------------------------------------------------------------------

_ALLOWANCE_ANCHOR_LINE: Final = (
    'context = gx.get_context(mode="file",'
    ' project_root_dir="<the project root established at preflight>")'
)


def _rewrite_allowance_anchor_line(
    violating_skills: pathlib.Path, replacement: str
) -> pathlib.Path:
    action_catalog = (
        violating_skills / ACTION_CATALOG_SKILL / REFERENCE_DIR / ACTION_CATALOG_REFERENCE
    )
    text = action_catalog.read_text(encoding="utf-8")
    assert text.count(_ALLOWANCE_ANCHOR_LINE) == 1, f"anchor is not unique in {action_catalog}"
    rewritten = text.replace(_ALLOWANCE_ANCHOR_LINE, replacement, 1)
    action_catalog.write_text(rewritten, encoding="utf-8")
    return action_catalog


def test_allowance_substitution_is_reported(violating_skills: pathlib.Path):
    """The excused line's own content changes while its trigger token, count, and
    section stay exactly the same -- same shape, opposite meaning. Only the
    anchor substring check catches this.
    """
    replacement = (
        'context = gx.get_context(mode="file",'
        ' project_root_dir="<a brand new directory the user has not seen>")'
    )
    _rewrite_allowance_anchor_line(violating_skills, replacement)

    problems = consent_gate_co_location_problems(violating_skills)

    assert [
        problem
        for problem in problems
        if "no longer contains that text" in problem and "Enabling Data Docs" in problem
    ]


def test_allowance_excess_is_reported(violating_skills: pathlib.Path):
    """A second, unmarked occurrence of the gate's trigger token lands in the same
    excused section -- the allowance covers one occurrence, not two.
    """
    addition = (
        f"{_ALLOWANCE_ANCHOR_LINE}\n"
        'reloaded = gx.get_context(mode="file",'
        ' project_root_dir="<a second, unexcused reload>")'
    )
    _rewrite_allowance_anchor_line(violating_skills, addition)

    problems = consent_gate_co_location_problems(violating_skills)

    assert [
        problem
        for problem in problems
        if "unmarked occurrence(s)" in problem and "Enabling Data Docs" in problem
    ]


def test_allowance_stale_is_reported(violating_skills: pathlib.Path):
    """The excused line's trigger token is removed entirely -- nothing in that
    section needs excusing anymore, so the allowance itself goes unused and is
    reported rather than passing quietly.
    """
    _rewrite_allowance_anchor_line(violating_skills, "context = _reloaded_context_from_preflight()")

    problems = consent_gate_co_location_problems(violating_skills)

    assert [
        problem
        for problem in problems
        if "matched no unmarked trigger-token occurrence" in problem
        and "Enabling Data Docs" in problem
    ]
