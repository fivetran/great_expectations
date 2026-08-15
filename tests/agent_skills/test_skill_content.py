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

import pathlib
import re
import shutil
from typing import Final

import pytest
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

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
MIN_BUNDLED_SKILLS: Final = 2

FRONTMATTER_PATTERN: Final = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
CODE_SPAN_PATTERN: Final = re.compile(r"`([^`\n]+)`")
MARKDOWN_LINK_PATTERN: Final = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


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


def reference_problems(skill_dir: pathlib.Path) -> list[str]:
    """Return every reference in a skill that fails to resolve inside the skill."""
    skill_root = skill_dir.resolve()
    problems: list[str] = []
    for document in sorted(skill_dir.rglob("*.md")):
        for reference in sorted(find_relative_references(document)):
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
    return sum(len(find_relative_references(document)) for document in skill_dir.rglob("*.md"))


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


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda skill_dir: skill_dir.name)
def test_entry_document_within_size_budget(skill_dir: pathlib.Path):
    problems = entry_document_size_problems(skill_dir)
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
