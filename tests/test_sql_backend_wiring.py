"""Cross-checks that every registered SQL backend's declared wiring coordinates actually exist
in the surfaces that select, install, and run its tests.

A `SqlBackendSpec` (see `tests/integration/test_utils/data_source_config/backend_spec.py`) names
its own marker, its dev-requirements file, its task-runner key, its CI workflow job and lane
token, and (for a locally containerized backend) its compose service. Declaring one of those
coordinates and never actually wiring it up produces a backend that looks configured but silently
never runs anywhere - this module is the mechanical check that catches that gap the moment a new
backend registers, rather than leaving it to be noticed the next time someone goes looking for why
a marker never seems to execute.

Every assertion here is presence-of-a-named-entry: it never pins a count, an order, or a shape,
so it survives an unrelated edit to any of the files it reads. Direction is one-way - it verifies
that every *registered* backend is wired, not that every wiring entry has a registered backend -
so it stays correct as other markers and jobs come and go for reasons that have nothing to do with
the SQL backends this module cares about.
"""

from __future__ import annotations

import pathlib
import re
from functools import cache
from typing import Any, Callable, ClassVar, Dict, Final, Protocol, Tuple, Type, TypeVar, cast

import pytest
import tomli
from tasks import MARKER_DEPENDENCY_MAP

from great_expectations.core.yaml_handler import YAMLHandler
from tests.conftest import REQUIRED_MARKERS
from tests.integration.test_utils.data_source_config.backend_spec import (
    BackendProvisioning,
    CiLaneRef,
    SqlBackendSpec,
)
from tests.integration.test_utils.data_source_config.registry import (
    isolated_registry,
    iter_sql_backends,
    register_sql_backend,
)


class _DeclaresBackendSpec(Protocol):
    """The structural shape a registered config class has: a class-level `BACKEND_SPEC`.

    Declared locally, mirroring the registry module's own protocol of the same name, so this
    module can type-check `config_class.BACKEND_SPEC` access without importing that module's
    private name.
    """

    BACKEND_SPEC: ClassVar[SqlBackendSpec]


pytestmark = pytest.mark.project

PROJECT_ROOT: Final = pathlib.Path(__file__).parent.parent
PYPROJECT_TOML: Final = PROJECT_ROOT / "pyproject.toml"
CONFTEST_PY: Final = PROJECT_ROOT / "tests" / "conftest.py"
TASKS_PY: Final = PROJECT_ROOT / "tasks.py"
CI_WORKFLOW: Final = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
COMPOSE_ROOT: Final = PROJECT_ROOT / "assets" / "docker"

_T = TypeVar("_T")


def _read_config(path: pathlib.Path, parse: Callable[[str], _T]) -> _T:
    """The one place a wiring-coordinate configuration file is read.

    Fails naming the file's absolute path - never a relative one, and never a silent pass -
    whichever way the file is unusable: absent, or present but not parseable by `parse`. A file
    read directly at each call site, instead of through here, is a second way to get this wrong
    that this module intentionally has no room for.
    """
    absolute = path.resolve()
    if not path.is_file():
        raise AssertionError(
            f"expected a wiring configuration file at {absolute}, but it does not exist"
        )
    try:
        return parse(path.read_text())
    except Exception as error:
        raise AssertionError(
            f"wiring configuration file at {absolute} could not be parsed: {error}"
        ) from error


@cache
def _pyproject_markers() -> Tuple[str, ...]:
    data = _read_config(PYPROJECT_TOML, tomli.loads)
    entries = data["tool"]["pytest"]["ini_options"]["markers"]
    return tuple(entry.split(":")[0].strip() for entry in entries)


@cache
def _ci_workflow_jobs() -> Dict[str, Any]:
    yaml_handler = YAMLHandler()
    data = _read_config(CI_WORKFLOW, yaml_handler.load)
    jobs = data.get("jobs", {})
    assert isinstance(jobs, dict), f"{CI_WORKFLOW.resolve()} has a non-mapping 'jobs' section"
    return jobs


# Splitting the whole serialized subtree once and comparing by exact token membership is what
# makes this a whole-token check rather than a substring search. The distinction matters because a
# marker name can be a prefixed form of another (`docs-spark` contains `spark`): under substring
# matching, a backend declaring the shorter name would look wired to a job that only ever mentions
# the longer one, and its lane would appear configured while nothing ran it.
#
# Non-word characters split a token, but `-` does not, which is what keeps a hyphenated marker one
# token instead of two. A plain `\b` word boundary would not do - `\b` does not treat `-` as part
# of a word, so it would match the shorter name inside the longer one just as substring search
# does.
_TOKEN_SPLIT_PATTERN: Final = re.compile(r"[^\w-]+")


def _tokens(text: str) -> Tuple[str, ...]:
    return tuple(sorted({token for token in _TOKEN_SPLIT_PATTERN.split(text) if token}))


def _backend_label(config_class: Type[_DeclaresBackendSpec]) -> str:
    return config_class.BACKEND_SPEC.label


_REGISTERED_BACKENDS: Final = iter_sql_backends()


def test_registry_is_non_empty_at_collection() -> None:
    """Guards every parametrized test below against passing vacuously. A registry emptied by an
    import-order accident would make each `@pytest.mark.parametrize(..., _REGISTERED_BACKENDS)`
    test collect zero cases and report as passed, which is indistinguishable from a real pass
    unless something asserts the collection was non-empty in the first place.
    """
    assert _REGISTERED_BACKENDS, "no SQL backends were registered to check"


def test_a_lane_token_inside_a_compound_expression_is_found() -> None:
    """Pins the one thing `_tokens` has to do for a real declaration.

    A lane token has to be found inside a job that selects several markers in one expression,
    which rules out comparing the job's entry for equality. Relaxing the matching in the other
    direction, to whole-entry equality, fails immediately against the real backends below.
    """
    assert "sqlite" in _tokens("openpyxl or pyarrow or project or sqlite or aws_creds")


# --------------------------------------------------------------------------------------------
# The six wiring assertions. Each is a standalone function so it can be exercised two ways: once
# per registered backend below, and once more per synthetic, deliberately-broken declaration in
# the failure-path tests further down - the same assertion code both proves the happy path and
# is proven, by those failure-path tests, to actually fire when wiring is missing.
# --------------------------------------------------------------------------------------------


def _assert_marker_is_registered_in_pyproject(
    config_class: Type[_DeclaresBackendSpec], spec: SqlBackendSpec
) -> None:
    assert spec.marker in _pyproject_markers(), (
        f"{config_class.__name__} declares marker {spec.marker!r} but it is not in the "
        f"markers list in {PYPROJECT_TOML.resolve()}"
    )


def _assert_marker_is_a_required_marker(
    config_class: Type[_DeclaresBackendSpec], spec: SqlBackendSpec
) -> None:
    assert spec.marker in REQUIRED_MARKERS, (
        f"{config_class.__name__} declares marker {spec.marker!r} but it is not in "
        f"REQUIRED_MARKERS in {CONFTEST_PY.resolve()}"
    )


def _assert_dev_requirements_file_exists(
    config_class: Type[_DeclaresBackendSpec], spec: SqlBackendSpec
) -> None:
    if spec.dev_requirements_file is None:
        return
    path = PROJECT_ROOT / spec.dev_requirements_file
    assert path.is_file(), (
        f"{config_class.__name__} declares dev_requirements_file "
        f"{spec.dev_requirements_file!r} but {path.resolve()} does not exist"
    )


def _assert_task_runner_entry_exists_and_lists_requirements_file(
    config_class: Type[_DeclaresBackendSpec], spec: SqlBackendSpec
) -> None:
    if spec.task_runner_marker is None:
        return
    entry = MARKER_DEPENDENCY_MAP.get(spec.task_runner_marker)
    assert entry is not None, (
        f"{config_class.__name__} declares task-runner marker {spec.task_runner_marker!r} but "
        f"MARKER_DEPENDENCY_MAP in {TASKS_PY.resolve()} has no such key"
    )
    if spec.dev_requirements_file is not None:
        assert spec.dev_requirements_file in entry.requirement_files, (
            f"{config_class.__name__} declares dev_requirements_file "
            f"{spec.dev_requirements_file!r} but MARKER_DEPENDENCY_MAP"
            f"[{spec.task_runner_marker!r}] in {TASKS_PY.resolve()} does not list it among "
            f"{entry.requirement_files!r}"
        )


def _assert_workflow_job_and_lane_token(
    config_class: Type[_DeclaresBackendSpec], spec: SqlBackendSpec
) -> None:
    job = _ci_workflow_jobs().get(spec.ci_lane.workflow_job)
    assert job is not None, (
        f"{config_class.__name__} declares CI workflow job {spec.ci_lane.workflow_job!r} but "
        f"{CI_WORKFLOW.resolve()} has no such job under 'jobs'"
    )
    tokens = _tokens(str(job))
    assert spec.ci_lane.marker_token in tokens, (
        f"{config_class.__name__} declares CI lane token {spec.ci_lane.marker_token!r} in "
        f"workflow job {spec.ci_lane.workflow_job!r}, but that token does not appear in "
        f"{CI_WORKFLOW.resolve()}; tokens found: {list(tokens)}"
    )


def _assert_container_service_wired(
    config_class: Type[_DeclaresBackendSpec], spec: SqlBackendSpec
) -> None:
    if spec.provisioning is not BackendProvisioning.LOCAL_CONTAINER:
        return
    service = spec.container_service
    compose_path = COMPOSE_ROOT / str(service) / "docker-compose.yml"
    assert compose_path.is_file(), (
        f"{config_class.__name__} declares container service {service!r} but "
        f"{compose_path.resolve()} does not exist"
    )
    entry = MARKER_DEPENDENCY_MAP.get(spec.task_runner_marker) if spec.task_runner_marker else None
    assert entry is not None and service in entry.services, (
        f"{config_class.__name__} declares container service {service!r} but "
        f"MARKER_DEPENDENCY_MAP[{spec.task_runner_marker!r}] in {TASKS_PY.resolve()} does not "
        f"list it among its services"
    )


# --------------------------------------------------------------------------------------------
# One pytest test per assertion, parametrized over the registry so each backend is its own case
# and each failure names exactly one backend. A skip is reported as SKIPPED, not folded silently
# into a pass, so an omitted coordinate stays visible in the test run.
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("config_class", _REGISTERED_BACKENDS, ids=_backend_label)
def test_marker_is_registered_in_pyproject(config_class: Type[_DeclaresBackendSpec]) -> None:
    _assert_marker_is_registered_in_pyproject(config_class, config_class.BACKEND_SPEC)


@pytest.mark.parametrize("config_class", _REGISTERED_BACKENDS, ids=_backend_label)
def test_marker_is_a_required_marker(config_class: Type[_DeclaresBackendSpec]) -> None:
    _assert_marker_is_a_required_marker(config_class, config_class.BACKEND_SPEC)


@pytest.mark.parametrize("config_class", _REGISTERED_BACKENDS, ids=_backend_label)
def test_dev_requirements_file_exists(config_class: Type[_DeclaresBackendSpec]) -> None:
    spec = config_class.BACKEND_SPEC
    if spec.dev_requirements_file is None:
        pytest.skip(f"{config_class.__name__} declares no dev_requirements_file")
    _assert_dev_requirements_file_exists(config_class, spec)


@pytest.mark.parametrize("config_class", _REGISTERED_BACKENDS, ids=_backend_label)
def test_task_runner_entry_exists_and_lists_requirements_file(
    config_class: Type[_DeclaresBackendSpec],
) -> None:
    spec = config_class.BACKEND_SPEC
    if spec.task_runner_marker is None:
        pytest.skip(f"{config_class.__name__} declares no task_runner_marker")
    _assert_task_runner_entry_exists_and_lists_requirements_file(config_class, spec)


@pytest.mark.parametrize("config_class", _REGISTERED_BACKENDS, ids=_backend_label)
def test_workflow_job_and_lane_token_are_wired(config_class: Type[_DeclaresBackendSpec]) -> None:
    _assert_workflow_job_and_lane_token(config_class, config_class.BACKEND_SPEC)


@pytest.mark.parametrize("config_class", _REGISTERED_BACKENDS, ids=_backend_label)
def test_container_service_is_wired(config_class: Type[_DeclaresBackendSpec]) -> None:
    spec = config_class.BACKEND_SPEC
    if spec.provisioning is not BackendProvisioning.LOCAL_CONTAINER:
        pytest.skip(f"{config_class.__name__} does not use local-container provisioning")
    _assert_container_service_wired(config_class, spec)


# --------------------------------------------------------------------------------------------
# Failure paths: synthetic, deliberately-broken declarations, registered only inside the
# isolation seam. Each proves that the matching assertion above actually fires, and that its
# message names the declaring class, the missing element, and the file it belongs in.
# --------------------------------------------------------------------------------------------


def _make_spec(**overrides: object) -> SqlBackendSpec:
    defaults: Dict[str, Any] = dict(
        label="ghost-backend",
        marker="ghost_backend",
        provisioning=BackendProvisioning.LOCAL_FILE,
        ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="ghost_backend"),
        uses_schema=False,
    )
    defaults.update(overrides)
    return SqlBackendSpec(**defaults)


def _make_config_class(name: str, spec: SqlBackendSpec) -> Type[_DeclaresBackendSpec]:
    return cast("Type[_DeclaresBackendSpec]", type(name, (), {"BACKEND_SPEC": spec}))


class TestWiringDriftFailurePaths:
    def test_missing_requirements_file_names_class_and_path(self) -> None:
        before = iter_sql_backends()
        with isolated_registry():
            spec = _make_spec(
                label="ghost-reqs",
                marker="ghost_reqs",
                dev_requirements_file="reqs/requirements-dev-ghost-backend.txt",
            )
            config_class = _make_config_class("GhostRequirementsFileConfig", spec)
            register_sql_backend(config_class)

            with pytest.raises(AssertionError) as excinfo:
                _assert_dev_requirements_file_exists(config_class, spec)

            message = str(excinfo.value)
            assert spec.dev_requirements_file is not None
            expected_path = (PROJECT_ROOT / spec.dev_requirements_file).resolve()
            assert "GhostRequirementsFileConfig" in message
            assert "reqs/requirements-dev-ghost-backend.txt" in message
            assert str(expected_path) in message
        assert iter_sql_backends() == before

    def test_unknown_task_runner_key_names_class_and_path(self) -> None:
        before = iter_sql_backends()
        with isolated_registry():
            spec = _make_spec(
                label="ghost-task-runner",
                marker="ghost_task_runner",
                dev_requirements_file="reqs/requirements-dev-mysql.txt",
                task_runner_marker="not_a_real_task_runner_key",
            )
            config_class = _make_config_class("GhostTaskRunnerConfig", spec)
            register_sql_backend(config_class)

            with pytest.raises(AssertionError) as excinfo:
                _assert_task_runner_entry_exists_and_lists_requirements_file(config_class, spec)

            message = str(excinfo.value)
            assert "GhostTaskRunnerConfig" in message
            assert "not_a_real_task_runner_key" in message
            assert str(TASKS_PY.resolve()) in message
        assert iter_sql_backends() == before

    def test_unknown_workflow_job_names_class_and_path(self) -> None:
        before = iter_sql_backends()
        with isolated_registry():
            spec = _make_spec(
                label="ghost-workflow-job",
                marker="ghost_workflow_job",
                ci_lane=CiLaneRef(
                    workflow_job="not-a-real-workflow-job", marker_token="ghost_workflow_job"
                ),
            )
            config_class = _make_config_class("GhostWorkflowJobConfig", spec)
            register_sql_backend(config_class)

            with pytest.raises(AssertionError) as excinfo:
                _assert_workflow_job_and_lane_token(config_class, spec)

            message = str(excinfo.value)
            assert "GhostWorkflowJobConfig" in message
            assert "not-a-real-workflow-job" in message
            assert str(CI_WORKFLOW.resolve()) in message
        assert iter_sql_backends() == before

    def test_absent_container_service_names_class_and_path(self) -> None:
        before = iter_sql_backends()
        with isolated_registry():
            spec = _make_spec(
                label="ghost-container",
                marker="ghost_container",
                provisioning=BackendProvisioning.LOCAL_CONTAINER,
                container_service="not-a-real-container-service",
            )
            config_class = _make_config_class("GhostContainerServiceConfig", spec)
            register_sql_backend(config_class)

            with pytest.raises(AssertionError) as excinfo:
                _assert_container_service_wired(config_class, spec)

            message = str(excinfo.value)
            expected_path = COMPOSE_ROOT / "not-a-real-container-service" / "docker-compose.yml"
            assert "GhostContainerServiceConfig" in message
            assert "not-a-real-container-service" in message
            assert str(expected_path.resolve()) in message
        assert iter_sql_backends() == before


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
