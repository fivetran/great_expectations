import os
import pathlib
import shutil
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest import mock

import pytest

import great_expectations as gx
from great_expectations.data_context import EphemeralDataContext
from great_expectations.data_context.cloud_constants import GXCloudEnvironmentVariable
from great_expectations.data_context.data_context.file_data_context import (
    FileDataContext,
)
from great_expectations.data_context.types.base import (
    DataContextConfig,
    InMemoryStoreBackendDefaults,
)
from great_expectations.exceptions.exceptions import (
    GitIgnoreScaffoldingError,
)
from tests.test_utils import working_directory

if TYPE_CHECKING:
    from great_expectations.datasource.fluent import SqliteDatasource

GX_CLOUD_PARAMS_ALL = {
    "cloud_base_url": "localhost:7000",
    "cloud_organization_id": "bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
    "cloud_workspace_id": "fffff6781234567812345678123fffff",
    "cloud_access_token": "i_am_a_token",
}
GX_CLOUD_PARAMS_REQUIRED = {
    "cloud_organization_id": "bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
    "cloud_access_token": "i_am_a_token",
}


@pytest.fixture()
def set_up_cloud_envs(monkeypatch):
    monkeypatch.setenv("GX_CLOUD_BASE_URL", "localhost:7000")
    monkeypatch.setenv("GX_CLOUD_ORGANIZATION_ID", "bd20fead-2c31-4392-bcd1-f1e87ad5a79c")
    monkeypatch.setenv("GX_CLOUD_ACCESS_TOKEN", "i_am_a_token")
    monkeypatch.setenv("GX_CLOUD_WORKSPACE_ID", "fffff6781234567812345678123fffff")


@pytest.fixture
def clear_env_vars(monkeypatch):
    # Delete local env vars (if present)
    for env_var in GXCloudEnvironmentVariable:
        monkeypatch.delenv(env_var, raising=False)


@pytest.mark.unit
def test_base_context(clear_env_vars):
    config: DataContextConfig = DataContextConfig(
        config_version=3.0,
        plugins_directory=None,
        expectations_store_name="expectations_store",
        checkpoint_store_name="checkpoint_store",
        stores={
            "expectations_store": {"class_name": "ExpectationsStore"},
            "checkpoint_store": {"class_name": "CheckpointStore"},
            "validation_result_store": {"class_name": "ValidationResultsStore"},
            "validation_definition_store": {"class_name": "ValidationDefinitionStore"},
        },
        validation_results_store_name="validation_result_store",
        data_docs_sites={},
    )
    assert isinstance(gx.get_context(project_config=config), EphemeralDataContext)


@pytest.mark.unit
def test_base_context__with_overridden_yml(tmp_path: pathlib.Path, clear_env_vars):
    project_path = tmp_path / "empty_data_context"
    project_path.mkdir()
    context_path = project_path / FileDataContext.GX_DIR
    context = gx.get_context(context_root_dir=context_path)
    assert isinstance(context, FileDataContext)
    assert context.expectations_store_name == "expectations_store"

    config: DataContextConfig = DataContextConfig(
        config_version=3.0,
        plugins_directory=None,
        expectations_store_name="new_expectations_store",
        checkpoint_store_name="new_checkpoint_store",
        stores={
            "new_expectations_store": {"class_name": "ExpectationsStore"},
            "new_checkpoint_store": {"class_name": "CheckpointStore"},
            "new_validation_result_store": {"class_name": "ValidationResultsStore"},
        },
        validation_results_store_name="new_validation_result_store",
        data_docs_sites={},
    )
    context = gx.get_context(project_config=config, context_root_dir=context_path)
    assert isinstance(context, FileDataContext)
    assert context.expectations_store_name == "new_expectations_store"


@pytest.mark.unit
def test_data_context_root_dir_returns_data_context(
    tmp_path: pathlib.Path,
    clear_env_vars,
):
    project_path = tmp_path / "empty_data_context"
    project_path.mkdir()
    context_path = project_path / FileDataContext.GX_DIR
    assert isinstance(gx.get_context(context_root_dir=str(context_path)), FileDataContext)


@pytest.mark.unit
def test_base_context_invalid_root_dir(clear_env_vars, tmp_path):
    config: DataContextConfig = DataContextConfig(
        config_version=3.0,
        plugins_directory=None,
        expectations_store_name="expectations_store",
        checkpoint_store_name="checkpoint_store",
        stores={
            "expectations_store": {"class_name": "ExpectationsStore"},
            "checkpoint_store": {"class_name": "CheckpointStore"},
            "validation_result_store": {"class_name": "ValidationResultsStore"},
        },
        validation_results_store_name="validation_result_store",
        data_docs_sites={},
    )

    context_root_dir = tmp_path / "root"
    context_root_dir.mkdir()
    assert isinstance(
        gx.get_context(project_config=config, context_root_dir=context_root_dir),
        FileDataContext,
    )


_CLOUD_SHUTDOWN_MESSAGE = (
    "GX Cloud has been shut down, so this no longer functions "
    "and will be removed in great_expectations 2.0."
)


@pytest.mark.parametrize("cloud_mode", [True, None])
@pytest.mark.cloud
def test_get_context_with_cloud_env_raises_shutdown_error(set_up_cloud_envs, cloud_mode):
    """GX Cloud is shut down: resolving a cloud context from GX_CLOUD_* env raises."""
    with pytest.raises(gx.exceptions.GreatExpectationsError, match=_CLOUD_SHUTDOWN_MESSAGE):
        gx.get_context(cloud_mode=cloud_mode)


@pytest.mark.parametrize("params", [GX_CLOUD_PARAMS_REQUIRED, GX_CLOUD_PARAMS_ALL])
@pytest.mark.cloud
def test_get_context_with_cloud_params_raises_shutdown_error(
    unset_gx_env_variables: None,
    # params is annotated with Any since mypy will fail with str values when checking
    # gx.get_context(**params) because there are no str only value variants.
    params: dict[str, Any],
):
    """GX Cloud is shut down: a complete set of cloud_* kwargs raises."""
    with pytest.raises(gx.exceptions.GreatExpectationsError, match=_CLOUD_SHUTDOWN_MESSAGE):
        gx.get_context(**params)


@pytest.mark.cloud
def test_get_context_with_mode_equals_cloud_raises_shutdown_error(set_up_cloud_envs):
    """GX Cloud is shut down: requesting mode="cloud" raises before any context is built."""
    with pytest.raises(gx.exceptions.GreatExpectationsError, match=_CLOUD_SHUTDOWN_MESSAGE):
        gx.get_context(mode="cloud")


@pytest.mark.unit
def test_get_context_with_no_arguments_returns_ephemeral_with_sensible_defaults():
    context = gx.get_context()
    assert isinstance(context, EphemeralDataContext)

    defaults = InMemoryStoreBackendDefaults(init_temp_docs_sites=True)
    assert context.config.stores == defaults.stores


@pytest.mark.unit
def test_get_context_with_mode_equals_ephemeral_returns_ephemeral_data_context():
    context = gx.get_context(mode="ephemeral")
    assert isinstance(context, EphemeralDataContext)


@pytest.mark.unit
def test_get_context_with_mode_equals_file_returns_file_data_context(
    tmp_path: pathlib.Path,
):
    with working_directory(tmp_path):
        context = gx.get_context(mode="file")
    assert isinstance(context, FileDataContext)


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_scaffolds_filesystem(tmp_path: pathlib.Path):
    root = tmp_path / "root"
    context_root_dir = root.joinpath(FileDataContext.GX_DIR)
    assert not context_root_dir.exists()

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert context_root_dir.exists()
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_custom_context_root_dir_scaffolds_filesystem(tmp_path: pathlib.Path):
    root = tmp_path / "root"
    context_root_dir = root.joinpath("hello_world")
    assert not context_root_dir.exists()

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert context_root_dir.exists()
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_mode_and_custom_context_root_dir_scaffolds_filesystem(
    tmp_path: pathlib.Path,
):
    root = tmp_path / "root"
    context_root_dir = root.joinpath("hello_world")
    assert not context_root_dir.exists()

    context = gx.get_context(mode="file", context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert context_root_dir.exists()
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_errors_if_context_root_dir_and_project_root_dir_are_both_provided_for_file_context(
    tmp_path: pathlib.Path,
):
    root = tmp_path / "root"
    context_root_dir = root.joinpath("hello_world")
    assert not context_root_dir.exists()

    with pytest.raises(
        TypeError,
        match="'project_root_dir' and 'context_root_dir' are conflicting args; please only provide one",  # noqa: E501
    ):
        gx.get_context(  # type: ignore[call-overload]
            mode="file",
            context_root_dir=context_root_dir,
            project_root_dir=context_root_dir.parent,
        )


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_scaffolds_existing_gitignore(clear_env_vars, tmp_path):
    context_root_dir = tmp_path / FileDataContext.GX_DIR
    context_root_dir.mkdir()
    with open(context_root_dir / FileDataContext.GITIGNORE, "w") as f:
        f.write("asdf")

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "asdf\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_scaffolds_new_gitignore(clear_env_vars, tmp_path):
    context_root_dir = tmp_path / FileDataContext.GX_DIR
    context_root_dir.mkdir()

    context = gx.get_context(context_root_dir=context_root_dir)

    assert isinstance(context, FileDataContext)
    assert (context_root_dir / FileDataContext.GITIGNORE).read_text() == "\nuncommitted/"


@pytest.mark.filesystem
def test_get_context_with_context_root_dir_gitignore_error(clear_env_vars, tmp_path):
    context_root_dir = tmp_path / FileDataContext.GX_DIR
    context_root_dir.mkdir()

    with mock.patch(
        "great_expectations.data_context.data_context.serializable_data_context.SerializableDataContext._scaffold_gitignore",
        side_effect=OSError("Error"),
    ):
        with pytest.raises(GitIgnoreScaffoldingError):
            gx.get_context(context_root_dir=context_root_dir)


@pytest.mark.filesystem
def test_get_context_scaffolds_gx_dir(tmp_path: pathlib.Path):
    with working_directory(tmp_path):
        context = gx.get_context(mode="file")
    assert isinstance(context, FileDataContext)

    project_root_dir = pathlib.Path(context.root_directory)
    assert project_root_dir.stem == FileDataContext.GX_DIR


@pytest.mark.filesystem
def test_get_context_finds_legacy_great_expectations_dir(
    tmp_path: pathlib.Path,
):
    working_dir = tmp_path / "a" / "b" / "c" / "d" / "working_dir"

    # Scaffold great_expectations
    context_root_dir = working_dir / FileDataContext._LEGACY_GX_DIR
    context_root_dir.mkdir(parents=True)

    # Scaffold great_expectations.yml
    gx_yml = context_root_dir / FileDataContext.GX_YML
    yml_fixture = (
        pathlib.Path(__file__)
        .joinpath("../../test_fixtures/great_expectations_basic.yml")
        .resolve()
    )
    assert yml_fixture.exists()
    shutil.copy(yml_fixture, gx_yml)

    with working_directory(working_dir):
        context = gx.get_context()
    assert isinstance(context, FileDataContext)

    project_root_dir = pathlib.Path(context.root_directory)
    assert project_root_dir.stem == FileDataContext._LEGACY_GX_DIR


# --------------------------------------------------------------------------------------------
# Read-only filesystem regression suite
#
# Standing up a FileDataContext against a fully-scaffolded, version-controlled project must
# work on a read-only filesystem (e.g. a read-only CI/CD deploy target or a mounted read-only
# container filesystem), and read operations must work end to end. The fixture below builds
# such a project and then makes its subtree genuinely read-only so the guarantee is exercised
# against a real filesystem, not merely against mocked permissions.
# --------------------------------------------------------------------------------------------

_READ_ONLY_FIXTURE_SQLITE_DB = (
    pathlib.Path(__file__).parent.parent
    / "test_sets"
    / "taxi_yellow_tripdata_samples"
    / "sqlite"
    / "yellow_tripdata.db"
).resolve()
_READ_ONLY_CONN_STR_ENV_VAR = "GX_READ_ONLY_PROJECT_TEST_CONN_STR"
_READ_ONLY_DATASOURCE_NAME = "read_only_project_datasource"
_READ_ONLY_ASSET_NAME = "yellow_tripdata"
_READ_ONLY_TABLE_NAME = "yellow_tripdata_sample_2019_01"
_READ_ONLY_SUITE_NAME = "read_only_project_suite"
_READ_ONLY_EXPECTATION_COLUMN = "passenger_count"


@dataclass(frozen=True)
class ReadOnlyProject:
    """Where a fully-scaffolded, then made-read-only, project lives on disk, plus the names
    needed to look up its configured datasource and expectation suite.
    """

    project_root_dir: pathlib.Path
    datasource_name: str
    asset_name: str
    suite_name: str


def _remove_write_permissions(path: pathlib.Path) -> None:
    """Recursively strip write bits from every entry under (and including) path."""
    for dirpath, dirnames, filenames in os.walk(path):
        for entry_name in [*dirnames, *filenames]:
            entry = pathlib.Path(dirpath) / entry_name
            entry.chmod(entry.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _restore_write_permissions(path: pathlib.Path) -> None:
    """Recursively restore the owner write bit under (and including) path so tmp_path's own
    teardown can remove it.
    """
    path.chmod(path.stat().st_mode | stat.S_IWUSR)
    for dirpath, dirnames, filenames in os.walk(path):
        for entry_name in [*dirnames, *filenames]:
            entry = pathlib.Path(dirpath) / entry_name
            entry.chmod(entry.stat().st_mode | stat.S_IWUSR)


@pytest.fixture
def read_only_project(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[ReadOnlyProject]:
    """Build a fully-scaffolded project - a committed config, a datasource resolved through
    environment-variable interpolation, and a saved expectation suite - then make its subtree
    genuinely read-only.

    Deleting the gitignored ``uncommitted/`` subtree before making the project read-only is
    load-bearing, not a cleanup step. On a project that is still fully scaffolded, the
    "already set up" decision is satisfied by the uncommitted/* directories alone, and the
    filesystem store backend's eager directory creation targets a directory that already
    exists - so initialization would succeed on a read-only filesystem whether or not the
    underlying fixes are present, and the tests below would pass false-green. Removing
    uncommitted/ restores the two preconditions of a genuine fresh version-control checkout -
    the gitignored runtime directories and the config-variables file are both absent, exactly
    as they are immediately after a clone - so a regression in either fix makes these tests
    fail again.

    The datasource's connection string resolves through an environment variable rather than
    uncommitted/config_variables.yml, since that file no longer exists once the deletion above
    has run; this exercises environment-variable interpolation for real rather than only "by
    construction".
    """
    project_root_dir = tmp_path / "read_only_project"
    project_root_dir.mkdir()

    connection_string_value = f"sqlite:///{_READ_ONLY_FIXTURE_SQLITE_DB}"
    monkeypatch.setenv(_READ_ONLY_CONN_STR_ENV_VAR, connection_string_value)

    context = gx.get_context(mode="file", project_root_dir=str(project_root_dir))
    datasource = context.data_sources.add_sqlite(
        name=_READ_ONLY_DATASOURCE_NAME,
        connection_string="${" + _READ_ONLY_CONN_STR_ENV_VAR + "}",
        create_temp_table=False,
    )
    datasource.add_table_asset(name=_READ_ONLY_ASSET_NAME, table_name=_READ_ONLY_TABLE_NAME)
    context.suites.add(
        gx.ExpectationSuite(
            name=_READ_ONLY_SUITE_NAME,
            expectations=[
                gx.expectations.ExpectColumnValuesToBeBetween(
                    column=_READ_ONLY_EXPECTATION_COLUMN, min_value=0, max_value=10
                )
            ],
        )
    )

    ge_dir = pathlib.Path(context.root_directory)
    shutil.rmtree(ge_dir / "uncommitted")

    _remove_write_permissions(project_root_dir)

    # Skip-clean probe: some environments (running as root, or a filesystem/CI mount that
    # ignores mode bits) do not enforce the chmod above. Detect that and skip cleanly rather
    # than false-failing the assertions below, restoring permissions first so tmp_path's
    # teardown can still remove the directory.
    probe_path = ge_dir / "_read_only_probe"
    write_still_succeeds = True
    try:
        probe_path.mkdir()
    except OSError:
        write_still_succeeds = False
    else:
        probe_path.rmdir()

    if write_still_succeeds:
        _restore_write_permissions(project_root_dir)
        pytest.skip("read-only filesystem cannot be enforced in this environment")

    try:
        yield ReadOnlyProject(
            project_root_dir=project_root_dir,
            datasource_name=_READ_ONLY_DATASOURCE_NAME,
            asset_name=_READ_ONLY_ASSET_NAME,
            suite_name=_READ_ONLY_SUITE_NAME,
        )
    finally:
        _restore_write_permissions(project_root_dir)


@pytest.mark.filesystem
def test_get_context_succeeds_against_read_only_project(read_only_project: ReadOnlyProject):
    """Standing up a FileDataContext against a fully-scaffolded, version-controlled project on
    a read-only filesystem completes initialization without raising.
    """
    context = gx.get_context(mode="file", project_root_dir=str(read_only_project.project_root_dir))
    assert isinstance(context, FileDataContext)


@pytest.mark.filesystem
def test_read_only_project_resolves_configured_datasource(read_only_project: ReadOnlyProject):
    """A datasource configured with an environment-variable-interpolated value resolves
    without raising, even though uncommitted/config_variables.yml is absent.
    """
    context = gx.get_context(mode="file", project_root_dir=str(read_only_project.project_root_dir))

    datasource: SqliteDatasource = context.data_sources.get(  # type: ignore[assignment]
        read_only_project.datasource_name
    )

    connection_string = datasource.connection_string
    assert str(connection_string) == "${" + _READ_ONLY_CONN_STR_ENV_VAR + "}"
    assert (
        connection_string.get_config_value(  # type: ignore[union-attr]
            context.config_provider
        )
        == f"sqlite:///{_READ_ONLY_FIXTURE_SQLITE_DB}"
    )


@pytest.mark.filesystem
def test_read_only_project_runs_validation_end_to_end(read_only_project: ReadOnlyProject):
    """Loading an existing expectation suite, building a validator, and running a validation
    against a read-only project succeeds and returns an in-memory result.
    """
    context = gx.get_context(mode="file", project_root_dir=str(read_only_project.project_root_dir))
    datasource = context.data_sources.get(read_only_project.datasource_name)
    batch_request = datasource.get_asset(read_only_project.asset_name).build_batch_request()

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=read_only_project.suite_name,
    )
    result = validator.validate()

    assert result.success is True


@pytest.mark.filesystem
def test_read_only_project_write_raises_clear_error(read_only_project: ReadOnlyProject):
    """A store-backed write attempted against a read-only project (here, saving a new
    expectation suite) fails with a clear error rather than being silently swallowed.
    """
    context = gx.get_context(mode="file", project_root_dir=str(read_only_project.project_root_dir))

    with pytest.raises(OSError):
        context.suites.add(gx.ExpectationSuite(name="a_suite_that_cannot_be_saved"))


@pytest.mark.filesystem
def test_get_context_still_scaffolds_new_project_on_writable_filesystem(
    tmp_path: pathlib.Path,
):
    """A genuinely new/empty project root on a writable filesystem still receives a full
    first-use scaffold: the relaxed already-set-up decision must not affect a project with no
    great_expectations.yml on disk.
    """
    context = gx.get_context(mode="file", project_root_dir=str(tmp_path))

    ge_dir = pathlib.Path(context.root_directory)
    assert (ge_dir / FileDataContext.GX_YML).is_file()
    assert (ge_dir / "uncommitted").is_dir()
    assert (ge_dir / "uncommitted" / "config_variables.yml").is_file()
