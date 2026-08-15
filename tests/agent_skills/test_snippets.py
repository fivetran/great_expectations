"""Execution tests for the code in the agent skills bundled with ``great_expectations``.

The skills teach an agent how to drive this library, and every instruction they give is
carried by a code snippet. Markdown is not compiled, imported or linted by anything, so
a snippet that stopped working would keep being handed to users indefinitely. Three
contracts are checked here, each of which fails silently without a test:

1.  **Every fenced Python block parses.** A block is dedented first -- some are nested
    inside list items -- so the check covers the source as an agent would copy it.
2.  **The blocks tagged ``executable`` on their fence really do run, in order, as one
    program.** They are executed against a throwaway in-memory session backed by a local
    SQLite database and an in-memory dataframe, and the run has to reach the end states
    the skills promise: a batch definition proven by reading data through it, a
    validation result carrying one entry per expectation, and a written-out project
    directory that a *fresh* file-backed context opens with its batch definitions and
    suites usable as they are.
3.  **The failure behavior the guidance is built on still behaves that way.** The skills
    tell an agent that retrieving a batch proves nothing, that a false ``success`` means
    two different things, and that empty tables and all-null columns produce ordinary
    results rather than errors. Each of those claims is pinned below against real
    execution, so a change in library behavior fails here -- next to a message naming
    the document whose text has to be updated -- instead of quietly turning the shipped
    guidance into misinformation.

Nothing here reaches the network. Everything runs against a local SQLite file and an
in-memory dataframe, because a check that needs a warehouse is a check that never runs.

The tagging mechanism is the fence itself: ``` ```python executable ``` marks a block as
part of the runnable sequence, which keeps the tag attached to the block it describes
instead of in a list somewhere that content edits can silently invalidate. The order the
tagged blocks run in is ``EXECUTABLE_SEQUENCE``, and its per-document counts are
asserted against the content so a tag that is added, moved or dropped fails loudly
rather than quietly leaving a block unexecuted.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import sqlite3
import textwrap
from typing import TYPE_CHECKING, Any, Callable, Final, Iterator

import pandas as pd
import pytest

import great_expectations as gx
from great_expectations.data_context import EphemeralDataContext, FileDataContext
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.exceptions.exceptions import (
    InvalidBatchRequestError,
    NoAvailableBatchesError,
)

if TYPE_CHECKING:
    from great_expectations.core import ExpectationSuite
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
        ExpectationValidationResult,
    )
    from great_expectations.datasource.fluent.sqlite_datasource import SqliteDatasource
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )

PROJECT_ROOT: Final = pathlib.Path(__file__).parents[2]
SKILLS_ROOT: Final = PROJECT_ROOT / "great_expectations" / ".agents" / "skills"

ENTRY_DOCUMENT: Final = "SKILL.md"
REFERENCE_DIR: Final = "references"
CANONICAL_SKILL: Final = "gx-configure-data-source"
SHARED_REFERENCES: Final = ("preflight.md", "write-out.md", "robustness.md")

FENCE: Final = "```"
PYTHON: Final = "python"
EXECUTABLE_TAG: Final = "executable"

#: Guards every parametrized compile check against a discovery bug reducing it to zero
#: cases. The content holds comfortably more than this; the number is a floor, not a
#: count, so ordinary editing does not have to keep it in step.
MIN_PYTHON_BLOCKS: Final = 40

#: The documents whose ``executable`` blocks make up the runnable sequence, in the order
#: they run, with the number of tagged blocks each one must contribute. Shared
#: references are listed under the skill that owns the canonical copy; the byte-identical
#: copy in the other skill is the same content and is not run twice.
EXECUTABLE_SEQUENCE: Final[tuple[tuple[str, int], ...]] = (
    (f"{CANONICAL_SKILL}/{REFERENCE_DIR}/preflight.md", 3),
    (f"{CANONICAL_SKILL}/{ENTRY_DOCUMENT}", 3),
    (f"{CANONICAL_SKILL}/{REFERENCE_DIR}/robustness.md", 1),
    (f"gx-configure-expectations/{ENTRY_DOCUMENT}", 5),
    (f"{CANONICAL_SKILL}/{REFERENCE_DIR}/write-out.md", 2),
)

#: Values the content deliberately leaves for the user to supply, spelled in angle
#: brackets so they are unmistakably placeholders. The runner fills them in and then
#: asserts it actually did, so a snippet that stopped carrying its placeholder cannot
#: leave the substitution silently doing nothing.
CONFIRMED_PATH_PLACEHOLDER: Final = "<confirmed_path>"

#: Environment left over from another project or from the retired managed cloud offering
#: changes what context discovery returns. The runnable sequence starts by discovering a
#: context, so the ambient environment has to be neutral for the run to mean anything.
AMBIENT_ENVIRONMENT: Final = (
    "GX_HOME",
    "GX_CLOUD_ACCESS_TOKEN",
    "GX_CLOUD_ORGANIZATION_ID",
    "GX_CLOUD_BASE_URL",
)

#: The table the runnable sequence configures, and the rows the skills' own worked
#: example describes: four rows, one missing customer, one negative amount, all inside a
#: single month so a monthly batch definition selects all of them.
ORDERS_ROWS: Final = (
    ("alice", 10.0, "2024-03-01"),
    (None, 20.0, "2024-03-05"),
    ("carol", -5.0, "2024-03-09"),
    ("dan", 40.0, "2024-03-20"),
)
ORDERS_COLUMNS: Final = ("customer", "amount", "ordered_at")
NULL_ROW_COUNT: Final = 3

MISSING_TABLE: Final = "does_not_exist"

#: The ceiling the guidance's own error-extraction snippet applies to a recovered cause,
#: plus the suffix it appends when it truncates.
CAUSE_CEILING: Final = 500
TRUNCATION_SUFFIX: Final = "... (truncated)"

#: Text unique to the write-out procedure snippet, used to locate it after it ran.
WRITE_OUT_STEPS_NEEDLE: Final = "for label, step in steps:"


@dataclasses.dataclass(frozen=True)
class CodeBlock:
    """One fenced block, with the fence's info string split into language and tags."""

    document: pathlib.Path
    line: int
    info: str
    source: str

    @property
    def language(self) -> str:
        parts = self.info.split()
        return parts[0] if parts else ""

    @property
    def tags(self) -> frozenset[str]:
        return frozenset(self.info.split()[1:])

    @property
    def identifier(self) -> str:
        """A stable ``<skill>/<document>:<line>`` label, used as the compiled filename."""
        try:
            name = self.document.relative_to(SKILLS_ROOT).as_posix()
        except ValueError:  # a document built by a test rather than shipped content
            name = self.document.name
        return f"{name}:{self.line}"


def iter_code_blocks(document: pathlib.Path) -> list[CodeBlock]:
    """Return every fenced block in a markdown document, dedented.

    Blocks nested inside a list item are indented in the source; an agent copying one
    out reads it without that indentation, so it is removed before the source is
    compiled or executed. Without the dedent every indented block would fail to parse.
    """
    blocks: list[CodeBlock] = []
    inside = False
    opening_line = 0
    info = ""
    body: list[str] = []
    for number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(FENCE):
            if inside:
                blocks.append(
                    CodeBlock(
                        document=document,
                        line=opening_line,
                        info=info,
                        source=textwrap.dedent("\n".join(body)),
                    )
                )
                inside = False
            else:
                inside = True
                opening_line = number
                info = stripped[len(FENCE) :].strip()
                body = []
            continue
        if inside:
            body.append(line)
    assert not inside, (
        f"{document}: a code fence opened at line {opening_line} is never closed."
        " Every fence needs a matching closing fence."
    )
    return blocks


def python_blocks(document: pathlib.Path) -> list[CodeBlock]:
    return [block for block in iter_code_blocks(document) if block.language == PYTHON]


def discover_documents(skills_root: pathlib.Path) -> list[pathlib.Path]:
    """Every markdown document in every bundled skill, found by walking the tree.

    Discovery is by directory contents rather than a hardcoded list so a document added
    later is covered without anyone remembering to update this file.
    """
    if not skills_root.is_dir():
        return []
    return sorted(skills_root.rglob("*.md"))


def canonical_relative_path(document: pathlib.Path) -> str:
    """Map a shared reference onto the skill that owns its canonical copy.

    The shared references are committed once per skill directory and asserted
    byte-identical elsewhere, so the copies carry identical tags. Collapsing them here
    keeps the runnable sequence from executing the same block twice.
    """
    relative = document.relative_to(SKILLS_ROOT)
    parts = relative.parts
    if len(parts) == 3 and parts[1] == REFERENCE_DIR and parts[2] in SHARED_REFERENCES:
        return f"{CANONICAL_SKILL}/{parts[1]}/{parts[2]}"
    return relative.as_posix()


DOCUMENTS: Final = discover_documents(SKILLS_ROOT)
ALL_PYTHON_BLOCKS: Final = [block for document in DOCUMENTS for block in python_blocks(document)]


def executable_blocks_in_sequence() -> list[CodeBlock]:
    """The tagged blocks, in the order ``EXECUTABLE_SEQUENCE`` declares."""
    ordered: list[CodeBlock] = []
    for relative_path, _expected in EXECUTABLE_SEQUENCE:
        document = SKILLS_ROOT / relative_path
        ordered.extend(block for block in python_blocks(document) if EXECUTABLE_TAG in block.tags)
    return ordered


def configuration_of(result: ExpectationValidationResult) -> ExpectationConfiguration:
    """The configuration a result came from.

    Pairing a result with the expectation it belongs to is the rule the skills state, so
    a result that arrived without its configuration would make that rule unfollowable.
    """
    configuration = result.expectation_config
    assert configuration is not None, (
        "a validation result arrived without the expectation configuration it came from,"
        " so results can no longer be paired with their expectations at all"
    )
    return configuration


def sole_block_containing(document: pathlib.Path, needle: str) -> CodeBlock:
    """The one Python block in ``document`` holding ``needle``.

    Selecting a block by something it says, rather than by position, means a block that
    moves is still found and a block that is deleted or duplicated fails here instead of
    silently changing which snippet a test exercises.
    """
    matches = [block for block in python_blocks(document) if needle in block.source]
    assert len(matches) == 1, (
        f"expected exactly one Python block in {document} containing {needle!r},"
        f" found {len(matches)} (at lines {[block.line for block in matches]})"
    )
    return matches[0]


# ---------------------------------------------------------------------------
# Every fenced Python block parses.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_python_blocks_are_extracted_from_every_skill():
    """The compile checks below are parametrized over extraction, so it is checked first."""
    assert SKILLS_ROOT.is_dir(), f"{SKILLS_ROOT} does not exist"
    assert len(ALL_PYTHON_BLOCKS) >= MIN_PYTHON_BLOCKS, (
        f"only {len(ALL_PYTHON_BLOCKS)} fenced {PYTHON} blocks were extracted from"
        f" {len(DOCUMENTS)} documents under {SKILLS_ROOT}; expected at least"
        f" {MIN_PYTHON_BLOCKS}. Either the content lost its snippets or the extractor no"
        " longer recognises how they are fenced."
    )
    skills_with_snippets = {
        block.document.relative_to(SKILLS_ROOT).parts[0] for block in ALL_PYTHON_BLOCKS
    }
    assert len(skills_with_snippets) >= 2, (
        f"snippets were only extracted from {sorted(skills_with_snippets)};"
        " every bundled skill teaches through code and should contribute some"
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "block", ALL_PYTHON_BLOCKS, ids=[block.identifier for block in ALL_PYTHON_BLOCKS]
)
def test_python_block_compiles(block: CodeBlock):
    """A snippet an agent is told to run has to be valid Python before anything else."""
    try:
        compile(block.source, block.identifier, "exec")
    except SyntaxError as error:
        pytest.fail(f"{block.identifier} does not parse as Python: {error}")


# ---------------------------------------------------------------------------
# The extraction each check above rests on reports the problems it exists for.
# ---------------------------------------------------------------------------


def _write_markdown(directory: pathlib.Path, text: str) -> pathlib.Path:
    document = directory / "sample.md"
    document.write_text(textwrap.dedent(text), encoding="utf-8")
    return document


@pytest.mark.unit
def test_a_block_that_does_not_parse_is_reported(tmp_path: pathlib.Path):
    document = _write_markdown(
        tmp_path,
        """\
        # sample

        ```python
        def broken(
        ```
        """,
    )

    (block,) = python_blocks(document)

    with pytest.raises(SyntaxError):
        compile(block.source, block.identifier, "exec")


@pytest.mark.unit
def test_a_block_nested_in_a_list_item_is_dedented(tmp_path: pathlib.Path):
    """Without the dedent an indented block raises ``IndentationError`` on every edit."""
    document = _write_markdown(
        tmp_path,
        """\
        # sample

        - a bullet holding a snippet:

          ```python
          value = 1
          ```
        """,
    )

    (block,) = python_blocks(document)

    assert block.source == "value = 1", f"the block was not dedented: {block.source!r}"
    compile(block.source, block.identifier, "exec")


@pytest.mark.unit
def test_an_unclosed_fence_is_reported(tmp_path: pathlib.Path):
    document = _write_markdown(
        tmp_path,
        """\
        # sample

        ```python
        value = 1
        """,
    )

    with pytest.raises(AssertionError, match="is never closed"):
        python_blocks(document)


@pytest.mark.unit
def test_only_python_fences_are_collected(tmp_path: pathlib.Path):
    """Illustrative output blocks are not code and must not be compiled as code."""
    document = _write_markdown(
        tmp_path,
        """\
        # sample

        ```python
        value = 1
        ```

        ```text
        not python at all: [
        ```
        """,
    )

    blocks = python_blocks(document)

    assert [block.source for block in blocks] == ["value = 1"]
    assert len(iter_code_blocks(document)) == 2


@pytest.mark.unit
def test_the_executable_tag_is_read_off_the_fence(tmp_path: pathlib.Path):
    document = _write_markdown(
        tmp_path,
        """\
        # sample

        ```python executable
        tagged = True
        ```

        ```python
        untagged = True
        ```
        """,
    )

    tagged, untagged = python_blocks(document)

    assert tagged.language == PYTHON and EXECUTABLE_TAG in tagged.tags
    assert untagged.language == PYTHON and EXECUTABLE_TAG not in untagged.tags


@pytest.mark.unit
def test_selecting_a_block_by_its_content_reports_an_ambiguous_match(tmp_path: pathlib.Path):
    document = _write_markdown(
        tmp_path,
        """\
        # sample

        ```python
        value = 1
        ```

        ```python
        value = 1
        ```
        """,
    )

    with pytest.raises(AssertionError, match="exactly one Python block"):
        sole_block_containing(document, "value = 1")


# ---------------------------------------------------------------------------
# The runnable sequence covers exactly the blocks the content tags.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_every_tagged_block_is_part_of_the_run_sequence():
    """A tag the runner does not know about would leave a snippet silently unexecuted."""
    tagged_by_document: dict[str, int] = {}
    for document in DOCUMENTS:
        count = sum(1 for block in python_blocks(document) if EXECUTABLE_TAG in block.tags)
        if count:
            key = canonical_relative_path(document)
            assert tagged_by_document.get(key, count) == count, (
                f"{document} carries {count} tagged blocks but its byte-identical"
                f" counterpart carries {tagged_by_document[key]}"
            )
            tagged_by_document[key] = count

    assert tagged_by_document == dict(EXECUTABLE_SEQUENCE), (
        "the tagged blocks in the content do not match the declared run sequence."
        f" Content: {tagged_by_document}. Declared: {dict(EXECUTABLE_SEQUENCE)}."
        " Add the document to EXECUTABLE_SEQUENCE, or update its expected count."
    )


@pytest.mark.unit
def test_the_write_out_snippet_still_carries_its_placeholder():
    """The runner fills this in; a snippet without it would run against nothing."""
    document = SKILLS_ROOT / CANONICAL_SKILL / REFERENCE_DIR / "write-out.md"
    holders = [
        block for block in python_blocks(document) if CONFIRMED_PATH_PLACEHOLDER in block.source
    ]
    assert len(holders) == 1, (
        f"expected exactly one snippet in {document} to carry"
        f" {CONFIRMED_PATH_PLACEHOLDER!r}, found {len(holders)}"
    )


# ---------------------------------------------------------------------------
# Fixtures: a local warehouse and an in-memory session, no network anywhere.
# ---------------------------------------------------------------------------


def _build_warehouse(path: pathlib.Path) -> pathlib.Path:
    """A SQLite database holding an ordinary table and two degenerate ones."""
    types = ("TEXT", "REAL", "TEXT")
    columns = ", ".join(f"{name} {kind}" for name, kind in zip(ORDERS_COLUMNS, types, strict=True))
    connection = sqlite3.connect(path)
    try:
        for table in ("orders", "empty_orders", "all_null_orders"):
            connection.execute(f"CREATE TABLE {table} ({columns})")
        connection.executemany("INSERT INTO orders VALUES (?, ?, ?)", ORDERS_ROWS)
        connection.executemany(
            "INSERT INTO all_null_orders VALUES (?, ?, ?)",
            [(None, None, "2024-03-01")] * NULL_ROW_COUNT,
        )
        connection.commit()
    finally:
        connection.close()
    return path


def _customers_frame() -> pd.DataFrame:
    """The in-memory dataframe the runnable sequence hands to its dataframe asset."""
    return pd.DataFrame({"customer": ["erin", None], "amount": [12.5, -3.0]})


@pytest.fixture(scope="module")
def warehouse_path(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    return _build_warehouse(tmp_path_factory.mktemp("warehouse") / "warehouse.sqlite")


@pytest.fixture
def ephemeral_context(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> EphemeralDataContext:
    """An in-memory session, discovered exactly the way the skills tell an agent to."""
    monkeypatch.chdir(tmp_path)
    for name in AMBIENT_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
    context = gx.get_context(cloud_mode=False)
    assert isinstance(context, EphemeralDataContext), (
        f"expected an in-memory session in an empty directory, got {type(context).__name__}"
    )
    return context


@pytest.fixture
def warehouse(
    ephemeral_context: EphemeralDataContext, warehouse_path: pathlib.Path
) -> SqliteDatasource:
    return ephemeral_context.data_sources.add_or_update_sqlite(
        name="warehouse", connection_string=f"sqlite:///{warehouse_path}"
    )


def whole_table_batch(datasource: SqliteDatasource, table: str) -> Batch:
    asset = datasource.add_table_asset(name=table, table_name=table)
    return asset.add_batch_definition_whole_table(name="all_rows").get_batch()


# ---------------------------------------------------------------------------
# The tagged blocks run, in order, and reach the end states the skills promise.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ExecutedFlow:
    """The result of running the tagged sequence as one program."""

    blocks: tuple[CodeBlock, ...]
    namespace: dict[str, Any]
    #: The namespace as it stood after each block, so an intermediate end state can be
    #: asserted even though a later block rebinds the name.
    snapshots: tuple[dict[str, Any], ...]
    substituted: frozenset[str]
    project_root: pathlib.Path
    dataframe: pd.DataFrame

    def after(self, needle: str) -> dict[str, Any]:
        """The namespace as it stood after the one executed block saying ``needle``.

        Selecting the block by something it says, rather than by line number, keeps
        these assertions attached to the snippet they are about when the surrounding
        prose is edited -- and turns a snippet that was deleted or duplicated into a
        failure here rather than into an assertion that quietly moved to another block.
        """
        matched = [
            snapshot
            for block, snapshot in zip(self.blocks, self.snapshots, strict=True)
            if needle in block.source
        ]
        assert len(matched) == 1, (
            f"expected exactly one executed block containing {needle!r}, found {len(matched)}"
        )
        return matched[0]


@pytest.fixture(scope="module")
def executed_flow(tmp_path_factory: pytest.TempPathFactory) -> Iterator[ExecutedFlow]:
    """Run every ``executable`` block, in sequence, in one shared namespace."""
    root = tmp_path_factory.mktemp("skill_flow")
    warehouse_file = _build_warehouse(root / "warehouse.sqlite")
    project_root = root / "written_out"
    project_root.mkdir()
    working_directory = root / "no_project_here"
    working_directory.mkdir()

    blocks = tuple(executable_blocks_in_sequence())
    dataframe = _customers_frame()
    namespace: dict[str, Any] = {"df": dataframe}
    snapshots: list[dict[str, Any]] = []
    substituted: set[str] = set()

    def load_written_out_project(state: dict[str, Any]) -> None:
        """Reopen the written-out project the way a later session would.

        The final snippet retrieves a batch through a batch definition; pointing that
        name at the *reloaded* definition is what makes the retrieval evidence that the
        written-out project is usable rather than evidence about objects still in memory.
        """
        reloaded = gx.get_context(mode="file", project_root_dir=str(project_root))
        state["reloaded_context"] = reloaded
        state["batch_definition"] = (
            reloaded.data_sources.get("my_datasource")
            .get_asset("my_asset")
            .get_batch_definition("my_batch_definition")
        )

    hooks: dict[tuple[str, int], Callable[[dict[str, Any]], None]] = {
        (f"{CANONICAL_SKILL}/{REFERENCE_DIR}/write-out.md", 1): load_written_out_project,
    }
    fired: set[tuple[str, int]] = set()
    seen_per_document: dict[str, int] = {}

    with pytest.MonkeyPatch.context() as patch:
        patch.chdir(working_directory)
        patch.setenv("WAREHOUSE_PATH", str(warehouse_file))
        for name in AMBIENT_ENVIRONMENT:
            patch.delenv(name, raising=False)

        for block in blocks:
            key = canonical_relative_path(block.document)
            position = seen_per_document.get(key, 0)
            seen_per_document[key] = position + 1
            hook = hooks.get((key, position))
            if hook is not None:
                hook(namespace)
                fired.add((key, position))

            source = block.source
            if CONFIRMED_PATH_PLACEHOLDER in source:
                source = source.replace(CONFIRMED_PATH_PLACEHOLDER, str(project_root))
                substituted.add(CONFIRMED_PATH_PLACEHOLDER)

            try:
                exec(compile(source, block.identifier, "exec"), namespace)
            except Exception as error:  # pragma: no cover - the failure is the report
                raise AssertionError(
                    f"the snippet at {block.identifier} failed to run as part of the"
                    f" documented sequence: {type(error).__name__}: {error}"
                ) from error
            snapshots.append(dict(namespace))

    assert fired == set(hooks), f"a run-sequence hook never fired: {set(hooks) - fired}"

    yield ExecutedFlow(
        blocks=blocks,
        namespace=namespace,
        snapshots=tuple(snapshots),
        substituted=frozenset(substituted),
        project_root=project_root,
        dataframe=dataframe,
    )

    executor = namespace.get("executor")
    if executor is not None:
        executor.shutdown(wait=True)


@pytest.mark.sqlite
def test_the_whole_tagged_sequence_ran(executed_flow: ExecutedFlow):
    """Everything below reads state the sequence produced, so the run is checked first."""
    expected = sum(count for _document, count in EXECUTABLE_SEQUENCE)
    assert len(executed_flow.blocks) == expected
    assert len(executed_flow.snapshots) == expected, "a block was skipped mid-sequence"
    assert executed_flow.substituted == frozenset({CONFIRMED_PATH_PLACEHOLDER}), (
        "the write-out snippet's placeholder was never substituted, so the procedure did"
        " not run against the confirmed directory"
    )


@pytest.mark.sqlite
def test_preflight_lands_in_an_announced_in_memory_session(executed_flow: ExecutedFlow):
    """Discovery in a directory with no project is an in-memory session, not an error."""
    discovered = executed_flow.after("context = gx.get_context(cloud_mode=False)")["context"]
    assert isinstance(discovered, EphemeralDataContext)

    branch = executed_flow.after("isinstance(context, FileDataContext)")
    assert branch["FileDataContext"] is FileDataContext, (
        "the branch snippet no longer imports the type it branches on"
    )
    assert "context_root" not in branch, (
        "the file-backed branch ran against an in-memory session; the snippet's"
        " isinstance check is not doing what the guidance says it does"
    )


@pytest.mark.sqlite
def test_the_batch_definition_is_verified_by_reading_data_through_it(
    executed_flow: ExecutedFlow,
):
    """Retrieval plus a probe that returns rows is the end state the flow promises."""
    probed = executed_flow.after("head = batch.head(n_rows=5)")
    batch = probed["batch"]
    assert isinstance(batch, Batch)

    frame = probed["head"].data
    assert list(frame.columns) == list(ORDERS_COLUMNS)
    assert len(frame) == len(ORDERS_ROWS)

    batch_definition = probed["batch_definition"]
    assert batch_definition.name == "by_month"

    context = executed_flow.namespace["context"]
    reachable = (
        context.data_sources.get("warehouse").get_asset("orders").get_batch_definition("by_month")
    )
    assert reachable.name == batch_definition.name, (
        "the verified batch definition is not retrievable from the session by name,"
        " so nothing was actually saved for a later step to use"
    )


@pytest.mark.sqlite
def test_the_time_budget_wrapper_returns_the_probe_result(executed_flow: ExecutedFlow):
    """The wrapper polls while the call is in flight; a fast call just returns."""
    wrapped = executed_flow.after("BUDGET_SECONDS")
    assert wrapped["succeeded"] is True, (
        "the duration-tracked wrapper reported failure for a call that works;"
        f" update {CANONICAL_SKILL}/{REFERENCE_DIR}/robustness.md if this is intended"
    )
    assert wrapped["checked_in"] is False, "a sub-second probe should not trip the budget"
    assert wrapped["result"] is not None
    assert wrapped["result"].data is not None


@pytest.mark.sqlite
def test_validation_reports_every_expectation_on_its_own_terms(executed_flow: ExecutedFlow):
    """One entry per expectation, each carrying the configuration it came from."""
    result: ExpectationSuiteValidationResult = executed_flow.after(
        "result = batch.validate(suite)"
    )["result"]
    by_type = {configuration_of(each).type: each for each in result.results}
    assert set(by_type) == {
        "expect_column_values_to_not_be_null",
        "expect_column_values_to_be_between",
    }

    missing_customer = by_type["expect_column_values_to_not_be_null"]
    negative_amount = by_type["expect_column_values_to_be_between"]
    assert missing_customer.success is False
    assert negative_amount.success is False
    assert missing_customer.result["element_count"] == len(ORDERS_ROWS)
    assert missing_customer.result["unexpected_count"] == 1
    assert missing_customer.result["partial_unexpected_list"] == [None]
    assert negative_amount.result["partial_unexpected_list"] == [-5.0]

    described = json.loads(result.describe())
    assert described["statistics"]["evaluated_expectations"] == len(result.results)


@pytest.mark.sqlite
def test_the_suite_the_flow_built_is_registered_with_the_session(executed_flow: ExecutedFlow):
    """Expectations added to a suite the context never saw are lost without a word.

    Fetching the suite back by name is the only thing that distinguishes a suite that
    was registered before its expectations were added from one that was not: building,
    adding and validating all work either way.
    """
    context = executed_flow.namespace["context"]
    registered = context.suites.get("orders_quality")
    assert [type(each).__name__ for each in registered.expectations] == [
        "ExpectColumnValuesToNotBeNull",
        "ExpectColumnValuesToBeBetween",
    ], (
        "the suite the flow built did not come back from the session with its"
        " expectations; the register-first ordering in"
        f" gx-configure-expectations/{ENTRY_DOCUMENT} is what keeps them"
    )


@pytest.mark.sqlite
def test_the_write_out_procedure_reports_every_object_it_wrote(executed_flow: ExecutedFlow):
    """The procedure records failures instead of raising, so the record is the evidence."""
    written = executed_flow.after(WRITE_OUT_STEPS_NEEDLE)["written"]
    failed = executed_flow.after(WRITE_OUT_STEPS_NEEDLE)["failed"]
    assert failed == [], f"write-out steps failed: {failed}"
    assert written == [
        "data source my_datasource",
        "asset my_asset",
        "batch definition my_batch_definition",
        "suite my_suite",
    ]


@pytest.mark.sqlite
def test_a_fresh_file_backed_context_loads_the_written_out_work(executed_flow: ExecutedFlow):
    """The written-out project is usable as it stands, from a context that never saw the session."""
    reloaded = gx.get_context(mode="file", project_root_dir=str(executed_flow.project_root))
    assert isinstance(reloaded, FileDataContext)

    batch_definition = (
        reloaded.data_sources.get("my_datasource")
        .get_asset("my_asset")
        .get_batch_definition("my_batch_definition")
    )
    suite: ExpectationSuite = reloaded.suites.get("orders_quality")
    assert [type(each).__name__ for each in suite.expectations] == [
        "ExpectColumnValuesToNotBeNull",
        "ExpectColumnValuesToBeBetween",
    ]

    # A dataframe asset carries configuration but no data, which is the one documented
    # caveat on "usable without modification" -- the frame is supplied at retrieval time.
    batch = batch_definition.get_batch(batch_parameters={"dataframe": executed_flow.dataframe})
    assert len(batch.head(n_rows=5).data) == len(executed_flow.dataframe)

    result = batch.validate(suite)
    assert len(result.results) == len(suite.expectations)
    assert all(each.result for each in result.results), (
        "the reloaded suite produced no per-expectation payloads, so it did not actually"
        " evaluate against the reloaded batch"
    )

    # The snippet the sequence ended on retrieved a batch through the reloaded definition.
    assert isinstance(executed_flow.namespace["batch"], Batch)


# ---------------------------------------------------------------------------
# The failure behavior the guidance is built on.
# ---------------------------------------------------------------------------


@pytest.mark.sqlite
def test_a_query_over_a_missing_table_yields_a_batch_and_fails_only_when_probed(
    warehouse: SqliteDatasource,
):
    """Retrieval touches nothing, which is why the guidance mandates a probe."""
    asset = warehouse.add_query_asset(name="broken", query=f"SELECT * FROM {MISSING_TABLE}")
    batch = asset.add_batch_definition_whole_table(name="all_rows").get_batch()

    assert isinstance(batch, Batch), (
        "retrieving a batch over a missing table no longer succeeds; the probe-first"
        f" rule in {CANONICAL_SKILL}/{REFERENCE_DIR}/robustness.md rests on it doing so"
    )

    with pytest.raises(KeyError) as raised:
        batch.head(n_rows=5)

    assert MISSING_TABLE not in str(raised.value), (
        "the probe failure now names the real problem, so the recovery procedure in"
        f" {CANONICAL_SKILL}/{REFERENCE_DIR}/robustness.md is heavier than it needs to be"
    )


@pytest.mark.sqlite
def test_the_guidance_recovers_the_real_cause_behind_a_bare_probe_failure(
    warehouse: SqliteDatasource,
):
    """The reference's own capture snippet is executed, not paraphrased."""
    asset = warehouse.add_query_asset(name="broken", query=f"SELECT * FROM {MISSING_TABLE}")
    batch = asset.add_batch_definition_whole_table(name="all_rows").get_batch()

    document = SKILLS_ROOT / CANONICAL_SKILL / REFERENCE_DIR / "robustness.md"
    snippet = sole_block_containing(document, "class _CaptureHandler")
    namespace: dict[str, Any] = {"batch": batch}
    exec(compile(snippet.source, snippet.identifier, "exec"), namespace)

    cause = namespace.get("cause")
    assert cause is not None, (
        "the capture snippet's KeyError branch never ran, so nothing was recovered"
    )
    assert MISSING_TABLE in cause, (
        f"the capture snippet in {document} no longer recovers the underlying database"
        f" error; it produced {cause!r}"
    )
    assert len(cause) <= CAUSE_CEILING + len(TRUNCATION_SUFFIX)
    assert "Traceback (most recent call last)" not in cause, (
        "the recovered cause carries a traceback, which the reporting rule forbids"
    )


@pytest.mark.sqlite
def test_a_metric_error_and_a_data_failure_are_told_apart_by_the_result_payload(
    warehouse: SqliteDatasource,
):
    """``success is False`` alone cannot distinguish broken configuration from bad data."""
    batch = whole_table_batch(warehouse, "orders")

    errored = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="nope"))
    failed = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"))
    passed = batch.validate(gx.expectations.ExpectColumnToExist(column="customer"))

    assert errored.success is False and not errored.result
    assert failed.success is False and failed.result
    # Both halves of the discriminator are load-bearing: a *passing* expectation also
    # carries an empty payload, so emptiness alone would misclassify it.
    assert passed.success is True and not passed.result

    def is_metric_error(result: ExpectationValidationResult) -> bool:
        return result.success is False and not result.result

    assert [is_metric_error(each) for each in (errored, failed, passed)] == [
        True,
        False,
        False,
    ]

    messages = {key: value["exception_message"] for key, value in errored.exception_info.items()}
    assert messages, "a metric error no longer names its cause in exception_info"
    assert all(isinstance(key, str) for key in messages), (
        "exception_info keys are no longer strings, so the documented iteration over"
        " .items() is the only lookup that works"
    )
    assert any(
        message == 'Error: The column "nope" in BatchData does not exist.'
        for message in messages.values()
    ), f"the cause message changed shape: {messages}"


@pytest.mark.sqlite
def test_results_come_back_grouped_by_column_rather_than_in_the_order_added(
    ephemeral_context: EphemeralDataContext, warehouse: SqliteDatasource
):
    """Pairing results with inputs by position mislabels every finding once this bites."""
    batch = whole_table_batch(warehouse, "orders")
    suite = ephemeral_context.suites.add(gx.ExpectationSuite(name="ordering"))
    added = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"),
        gx.expectations.ExpectColumnMeanToBeBetween(column="amount", min_value=0, max_value=100),
        gx.expectations.ExpectColumnValuesToBeUnique(column="customer"),
        gx.expectations.ExpectColumnMaxToBeBetween(column="amount", min_value=0, max_value=100),
    ]
    for expectation in added:
        suite.add_expectation(expectation)

    result = batch.validate(suite)
    returned = [configuration_of(each).kwargs["column"] for each in result.results]

    assert returned == ["customer", "customer", "amount", "amount"], (
        "validation no longer groups a suite by column; the ordering rule in"
        f" gx-configure-expectations/{ENTRY_DOCUMENT} describes this grouping"
    )
    assert returned != ["customer", "amount", "customer", "amount"], (
        "results came back in the order they were added, so this suite no longer"
        " demonstrates the trap it exists to demonstrate"
    )
    assert len(result.results) == len(added), "every added expectation is still reported"


@pytest.mark.sqlite
def test_checks_without_a_column_are_grouped_on_their_own(
    ephemeral_context: EphemeralDataContext, warehouse: SqliteDatasource
):
    """Table-level checks form a group of their own, placed where it first appears."""
    batch = whole_table_batch(warehouse, "orders")
    suite = ephemeral_context.suites.add(gx.ExpectationSuite(name="table_level"))
    for expectation in (
        gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"),
        gx.expectations.ExpectTableRowCountToBeBetween(min_value=1),
        gx.expectations.ExpectColumnMeanToBeBetween(column="amount", min_value=0, max_value=100),
        gx.expectations.ExpectColumnValuesToBeUnique(column="customer"),
    ):
        suite.add_expectation(expectation)

    result = batch.validate(suite)
    returned = [configuration_of(each).kwargs.get("column", "<none>") for each in result.results]

    assert returned == ["customer", "customer", "<none>", "amount"], (
        "a table-level check no longer forms its own group between the column groups;"
        f" the ordering rule in gx-configure-expectations/{ENTRY_DOCUMENT} says it does"
    )


@pytest.mark.sqlite
def test_an_expectation_whose_metric_errored_is_moved_to_the_front(
    ephemeral_context: EphemeralDataContext, warehouse: SqliteDatasource
):
    batch = whole_table_batch(warehouse, "orders")
    suite = ephemeral_context.suites.add(gx.ExpectationSuite(name="hoisted"))
    for expectation in (
        gx.expectations.ExpectColumnToExist(column="customer"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0),
        gx.expectations.ExpectColumnMeanToBeBetween(column="nope", min_value=0, max_value=100),
    ):
        suite.add_expectation(expectation)

    result = batch.validate(suite)

    assert configuration_of(result.results[0]).type == "expect_column_mean_to_be_between", (
        "the expectation whose metric errored was added last and is no longer reported"
        f" first; gx-configure-expectations/{ENTRY_DOCUMENT} says it is"
    )
    assert not result.results[0].result, "the hoisted entry should carry no payload"


@pytest.mark.sqlite
def test_an_empty_table_produces_results_rather_than_errors(warehouse: SqliteDatasource):
    """Degenerate data is an ordinary outcome; reporting it as an error is wrong."""
    batch = whole_table_batch(warehouse, "empty_orders")

    probe = batch.head(n_rows=5)
    assert list(probe.data.columns) == list(ORDERS_COLUMNS)
    assert len(probe.data) == 0

    not_null = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"))
    mean = batch.validate(
        gx.expectations.ExpectColumnMeanToBeBetween(column="amount", min_value=0, max_value=100)
    )
    row_count = batch.validate(gx.expectations.ExpectTableRowCountToBeBetween(min_value=1))

    assert not_null.success is True
    assert not_null.result["element_count"] == 0
    assert mean.success is False
    assert mean.result == {"observed_value": None}
    assert row_count.success is False
    assert row_count.result == {"observed_value": 0}
    # ``observed_value: None`` is a *populated* payload, so the discriminator reads these
    # as data failures rather than as metric errors -- which is the correct reading.
    assert mean.result and row_count.result


@pytest.mark.sqlite
def test_an_all_null_column_produces_results_rather_than_errors(warehouse: SqliteDatasource):
    batch = whole_table_batch(warehouse, "all_null_orders")

    not_null = batch.validate(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"))
    between = batch.validate(
        gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0, max_value=100)
    )
    mean = batch.validate(
        gx.expectations.ExpectColumnMeanToBeBetween(column="amount", min_value=0, max_value=100)
    )

    assert not_null.success is False
    assert not_null.result["unexpected_count"] == NULL_ROW_COUNT
    assert not_null.result["unexpected_percent"] == 100.0
    # The counterintuitive one: nulls count as missing rather than as violations, so a
    # range check over a column of nothing but nulls passes and is not reassurance.
    assert between.success is True, (
        "a value range check over an all-null column no longer passes; the caveat in"
        f" gx-configure-expectations/{ENTRY_DOCUMENT} depends on it doing so"
    )
    assert between.result["missing_count"] == NULL_ROW_COUNT
    assert between.result["unexpected_count"] == 0
    assert mean.success is False
    assert mean.result == {"observed_value": None}


@pytest.mark.sqlite
def test_an_empty_window_fails_at_retrieval_before_any_probe_runs(
    ephemeral_context: EphemeralDataContext, warehouse: SqliteDatasource, tmp_path: pathlib.Path
):
    """An empty *window* is a different outcome from an empty collection, on both families."""
    sql_definition = warehouse.add_table_asset(
        name="orders", table_name="orders"
    ).add_batch_definition_monthly(name="by_month", column="ordered_at")

    files = tmp_path / "sales"
    files.mkdir()
    (files / "sales_2024-02.csv").write_text("customer,amount\nalice,1.0\n", encoding="utf-8")
    file_definition = (
        ephemeral_context.data_sources.add_or_update_pandas_filesystem(
            name="sales_files", base_directory=files
        )
        .add_csv_asset(name="monthly_sales")
        .add_batch_definition_monthly(
            name="by_month", regex=r"sales_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
        )
    )

    with pytest.raises(NoAvailableBatchesError):
        sql_definition.get_batch(batch_parameters={"year": 1999, "month": 1})
    with pytest.raises(NoAvailableBatchesError):
        file_definition.get_batch(batch_parameters={"year": "1999", "month": "01"})

    # The same definitions do produce a batch for a window that exists, so the failures
    # above are about the window rather than about a broken configuration.
    assert sql_definition.get_batch(batch_parameters={"year": 2024, "month": 3}) is not None
    assert file_definition.get_batch(batch_parameters={"year": "2024", "month": "02"}) is not None


@pytest.mark.sqlite
def test_batch_parameter_types_differ_between_file_and_sql_assets(
    ephemeral_context: EphemeralDataContext, warehouse: SqliteDatasource, tmp_path: pathlib.Path
):
    """File-based definitions match on strings; SQL definitions partition on integers."""
    files = tmp_path / "sales"
    files.mkdir()
    (files / "sales_2024-02.csv").write_text("customer,amount\nalice,1.0\n", encoding="utf-8")
    file_definition = (
        ephemeral_context.data_sources.add_or_update_pandas_filesystem(
            name="sales_files", base_directory=files
        )
        .add_csv_asset(name="monthly_sales")
        .add_batch_definition_monthly(
            name="by_month", regex=r"sales_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
        )
    )
    sql_definition = warehouse.add_table_asset(
        name="orders", table_name="orders"
    ).add_batch_definition_monthly(name="by_month", column="ordered_at")

    with pytest.raises(InvalidBatchRequestError):
        file_definition.get_batch(batch_parameters={"year": 2024, "month": 2})
    assert file_definition.get_batch(batch_parameters={"year": "2024", "month": "02"}) is not None

    assert sql_definition.get_batch(batch_parameters={"year": 2024, "month": 3}) is not None
    # Strings against a SQL definition are not rejected -- they simply match nothing,
    # which is why the two families cannot share one set of batch parameters.
    with pytest.raises(NoAvailableBatchesError):
        sql_definition.get_batch(batch_parameters={"year": "2024", "month": "03"})


@pytest.mark.sqlite
def test_updating_a_data_source_drops_every_asset_on_it(
    ephemeral_context: EphemeralDataContext, warehouse_path: pathlib.Path
):
    """Why the data-source factory runs at most once per flow, and never as an update."""
    connection_string = f"sqlite:///{warehouse_path}"
    datasource = ephemeral_context.data_sources.add_or_update_sqlite(
        name="warehouse", connection_string=connection_string
    )
    datasource.add_table_asset(name="orders", table_name="orders")
    datasource.add_table_asset(name="empty_orders", table_name="empty_orders")
    assert [asset.name for asset in ephemeral_context.data_sources.get("warehouse").assets] == [
        "orders",
        "empty_orders",
    ]

    ephemeral_context.data_sources.add_or_update_sqlite(
        name="warehouse", connection_string=connection_string
    )

    assert [asset.name for asset in ephemeral_context.data_sources.get("warehouse").assets] == [], (
        "updating a data source no longer drops its assets; the reuse-first rule in"
        f" {CANONICAL_SKILL}/{ENTRY_DOCUMENT} is written around it doing so"
    )


@pytest.mark.sqlite
def test_the_flow_snippet_reuses_a_data_source_rather_than_replacing_it(
    ephemeral_context: EphemeralDataContext,
    warehouse_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """The shipped configure snippet must fetch before it creates, not just say so.

    The test above pins the destructive behavior as a fact about the library. This one
    pins the guidance's response to it as a property of the snippet an agent copies:
    run against a session that already holds the data source, the snippet has to leave
    the assets already on it alone. Rewriting its fetch-first branch into a plain
    ``add_or_update_<type>`` call satisfies every other check in this file while
    silently destroying work the user did not ask it to touch, so nothing else here
    would notice.
    """
    monkeypatch.setenv("WAREHOUSE_PATH", str(warehouse_path))
    seeded = ephemeral_context.data_sources.add_or_update_sqlite(
        name="warehouse", connection_string=f"sqlite:///{warehouse_path}"
    )
    seeded.add_table_asset(name="empty_orders", table_name="empty_orders")
    assert [asset.name for asset in ephemeral_context.data_sources.get("warehouse").assets] == [
        "empty_orders"
    ], "the sibling asset this test is about was not seeded"

    snippet = sole_block_containing(
        SKILLS_ROOT / CANONICAL_SKILL / ENTRY_DOCUMENT,
        "DATASOURCE_NAME, ASSET_NAME, BATCH_DEFINITION_NAME",
    )
    assert EXECUTABLE_TAG in snippet.tags, (
        f"{snippet.identifier} is no longer part of the runnable sequence, so this"
        " test and the end-to-end run have drifted apart"
    )
    namespace: dict[str, Any] = {"context": ephemeral_context}
    exec(compile(snippet.source, snippet.identifier, "exec"), namespace)

    surviving = [asset.name for asset in ephemeral_context.data_sources.get("warehouse").assets]
    assert "empty_orders" in surviving, (
        f"the configure snippet in {CANONICAL_SKILL}/{ENTRY_DOCUMENT} destroyed an asset"
        " that was already on the data source. It must fetch the data source and create"
        " one only when absent -- calling add_or_update_<type> against a name that"
        f" already exists replaces it wholesale. Assets left: {surviving}"
    )
    assert "orders" in surviving, "the snippet did not add the asset it exists to add"
    assert namespace["batch_definition"].name == "by_month"


@pytest.mark.sqlite
def test_assets_and_batch_definitions_refuse_a_duplicate_name(warehouse: SqliteDatasource):
    """There is no update factory for either, so the flow has to fetch before it creates."""
    asset = warehouse.add_table_asset(name="orders", table_name="orders")
    asset.add_batch_definition_whole_table(name="all_rows")

    assert not hasattr(warehouse, "add_or_update_table_asset")
    assert not hasattr(asset, "add_or_update_batch_definition_whole_table")

    with pytest.raises(ValueError, match="already exists"):
        warehouse.add_table_asset(name="orders", table_name="orders")
    with pytest.raises(ValueError, match="already exists"):
        asset.add_batch_definition_whole_table(name="all_rows")

    # Fetching the existing objects is the path the guidance takes instead, and both
    # signal absence with a LookupError subclass.
    assert warehouse.get_asset("orders") is not None
    with pytest.raises(LookupError):
        warehouse.get_asset("never_created")
    with pytest.raises(LookupError):
        asset.get_batch_definition("never_created")


@pytest.mark.sqlite
def test_updating_a_suite_replaces_it_instead_of_merging(ephemeral_context: EphemeralDataContext):
    """A fresh suite under an existing name empties it, with no error and no warning."""
    suite = ephemeral_context.suites.add(gx.ExpectationSuite(name="orders_quality"))
    for expectation in (
        gx.expectations.ExpectColumnToExist(column="customer"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="amount", min_value=0),
    ):
        suite.add_expectation(expectation)
    assert len(ephemeral_context.suites.get("orders_quality").expectations) == 3

    ephemeral_context.suites.add_or_update(gx.ExpectationSuite(name="orders_quality"))

    assert len(ephemeral_context.suites.get("orders_quality").expectations) == 0, (
        "updating a suite no longer discards its contents; the fetch-first rule in"
        f" gx-configure-expectations/{ENTRY_DOCUMENT} is written around it doing so"
    )


@pytest.mark.sqlite
def test_adding_expectations_to_an_unregistered_suite_persists_nothing(
    ephemeral_context: EphemeralDataContext, warehouse: SqliteDatasource
):
    """The ordering rule exists because the wrong order fails silently, not loudly."""
    batch = whole_table_batch(warehouse, "orders")
    unregistered = gx.ExpectationSuite(name="never_registered")
    unregistered.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="customer"))

    result = batch.validate(unregistered)
    assert len(result.results) == 1, "validating against an unregistered suite still works"

    assert "never_registered" not in {suite.name for suite in ephemeral_context.suites.all()}, (
        "an unregistered suite is now stored anyway; the register-first rule in"
        f" gx-configure-expectations/{ENTRY_DOCUMENT} would no longer be necessary"
    )
