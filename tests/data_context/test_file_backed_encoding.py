"""Regression tests for filesystem-backed reads/writes under a non-UTF-8 locale.

See https://github.com/fivetran/great_expectations/issues/12120. GX always writes
its own files as UTF-8, but several read paths opened files with a bare open(),
which resolves its encoding from the process's ambient locale. On a host whose
locale encoding isn't UTF-8 (chiefly Windows, where nothing coerces the locale
to UTF-8 the way POSIX's PEP 538 does), reading back a value GX itself wrote can
raise UnicodeDecodeError.

These tests force a non-UTF-8 locale the same way the issue's own repro does:
by spawning a subprocess with LC_ALL, LANG, PYTHONCOERCECLOCALE, and PYTHONUTF8
set so that open()'s default encoding resolves to something other than UTF-8.
A test that instead relies on the ambient locale would pass either way here,
since CI runners are UTF-8 and no workflow sets these variables.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import pathlib

NON_UTF8_ENV = dict(
    os.environ,
    LC_ALL="C",
    LANG="C",
    PYTHONCOERCECLOCALE="0",
    PYTHONUTF8="0",
)

NON_ASCII_VALUE = "Prüfung ünïcödé Straße café naïve 中文测试"

GITIGNORE_WITH_NON_ASCII = f"# Local ignores\n{NON_ASCII_VALUE}\n*.pyc\n"

PROJECT_YAML_TEMPLATE = """config_version: 3.0
config_variables_file_path: uncommitted/config_variables.yml
plugins:
  credentials: ~/.gx/gx_flavors/
data_sources:
  - class_name: PandasDatasource
    name: "{value}"
    execution_engine:
      class_name: PandasExecutionEngine
"""


def _run_under_non_utf8_locale(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # FIXME CoP
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=NON_UTF8_ENV,
        check=False,
    )


@pytest.mark.filesystem
def test_tuple_filesystem_store_backend_reads_own_writes_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """A value TupleFilesystemStoreBackend writes must read back unchanged, regardless
    of what encoding the process's ambient locale resolves to.
    """  # FIXME CoP
    store_dir = tmp_path / "store"
    store_dir.mkdir()
    payload_path = tmp_path / "payload.txt"
    payload_path.write_text(NON_ASCII_VALUE, encoding="utf-8")

    script = textwrap.dedent(f"""
        from great_expectations.data_context.store.tuple_store_backend import (
            TupleFilesystemStoreBackend,
        )

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        backend = TupleFilesystemStoreBackend(
            root_directory={str(store_dir)!r},
            base_directory={str(store_dir)!r},
            filepath_template="my_file_{{0}}",
        )
        backend.set(("AAA",), non_ascii_value)
        assert backend.get(("AAA",)) == non_ascii_value
        print("OK")
    """)

    result = _run_under_non_utf8_locale(script)

    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


@pytest.mark.filesystem
def test_file_data_context_reloads_non_ascii_project_yaml_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """A great_expectations.yml written on one host (or under one locale) must load on
    another, even if a data source name or other config value contains non-ASCII text.

    Both the write and the reload run under a forced non-UTF-8 locale: a write under the
    ambient (UTF-8) locale would emit correct bytes regardless of whether the write path
    pins its encoding, leaving nothing for the reload assertion to catch.
    """  # FIXME CoP
    project_root = tmp_path / "project"
    payload_path = tmp_path / "payload.txt"
    payload_path.write_text(NON_ASCII_VALUE, encoding="utf-8")

    write_script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        context = gx.get_context(mode="file", context_root_dir={str(project_root)!r})
        context.data_sources.add_pandas(name=non_ascii_value)
    """)
    write_result = _run_under_non_utf8_locale(write_script)
    assert write_result.returncode == 0, write_result.stderr

    reload_script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        context = gx.get_context(mode="file", context_root_dir={str(project_root)!r})
        assert non_ascii_value in context.data_sources.all()
        print("OK")
    """)

    reload_result = _run_under_non_utf8_locale(reload_script)

    assert reload_result.returncode == 0, reload_result.stderr
    assert "OK" in reload_result.stdout


@pytest.mark.filesystem
def test_inline_store_backend_saves_non_ascii_variable_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """InlineStoreBackend._save_changes() is a separate write path from
    FileDataContext._save_project_config(): it backs DataContextVariables (things like
    checkpoint_store_name), not fluent datasources, which persist through
    _save_project_config's own to_yaml call instead. Exercise it directly by setting a
    variable to a non-ASCII value and saving.

    Uses checkpoint_store_name rather than config_variables_file_path: the latter is itself
    a filesystem path, and under a forced non-UTF-8 locale a genuinely non-ASCII path can't
    be encoded for the open() syscall used to read substitution variables from it -- a real
    OS/locale limitation, not a bug in the read path this suite covers. expectations_store_name
    doesn't work either: unlike checkpoint_store_name, a context looks it up unconditionally
    (not via dict.get) while constructing its data_context_id, so an override that names no
    real store raises KeyError before the assertion this test cares about ever runs.
    """  # FIXME CoP
    project_root = tmp_path / "project"
    payload_path = tmp_path / "payload.txt"
    payload_path.write_text(NON_ASCII_VALUE, encoding="utf-8")

    write_script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        context = gx.get_context(mode="file", context_root_dir={str(project_root)!r})
        context.variables.checkpoint_store_name = non_ascii_value
        context.variables.save()
    """)
    write_result = _run_under_non_utf8_locale(write_script)
    assert write_result.returncode == 0, write_result.stderr

    reload_script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        context = gx.get_context(mode="file", context_root_dir={str(project_root)!r})
        assert context.variables.checkpoint_store_name == non_ascii_value
        print("OK")
    """)

    reload_result = _run_under_non_utf8_locale(reload_script)

    assert reload_result.returncode == 0, reload_result.stderr
    assert "OK" in reload_result.stdout


@pytest.mark.filesystem
def test_scaffold_gitignore_preserves_non_ascii_gitignore_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """Scaffolding a project over an existing .gitignore that holds non-ASCII text must
    read that file as UTF-8 rather than raise.

    See https://github.com/fivetran/great_expectations/issues/12181. This is the live
    path of the four fixed here: get_context(mode="file") -> FileDataContext._scaffold_project
    -> _scaffold -> _scaffold_directories -> _scaffold_gitignore, and _scaffold_directories
    re-raises the decode error as GitIgnoreScaffoldingError, so a user with a non-ASCII
    .gitignore cannot initialize a project at all under a non-UTF-8 locale.

    Only the read needs pinning: the append that follows writes the literal ASCII string
    "uncommitted/", which encodes identically under any ASCII-compatible codec.
    """  # FIXME CoP
    context_root_dir = tmp_path / "project"
    context_root_dir.mkdir()
    gitignore_path = context_root_dir / ".gitignore"
    gitignore_path.write_text(GITIGNORE_WITH_NON_ASCII, encoding="utf-8")

    script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        gx.get_context(mode="file", context_root_dir={str(context_root_dir)!r})
        print("OK")
    """)

    result = _run_under_non_utf8_locale(script)

    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout

    # read_bytes keeps this assertion independent of the parent process's locale
    contents = gitignore_path.read_bytes().decode("utf-8")
    assert NON_ASCII_VALUE in contents, "scaffolding rewrote the user's .gitignore lossily"
    assert "uncommitted/" in contents, "scaffolding never recorded the uncommitted dir"


@pytest.mark.filesystem
def test_config_variables_yml_exist_reads_non_ascii_project_yaml_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """config_variables_yml_exist() loads great_expectations.yml to find the config
    variables path, so a non-ASCII value anywhere in that file makes it raise under a
    non-UTF-8 locale instead of answering the yes/no question it is named for.

    See https://github.com/fivetran/great_expectations/issues/12181. It has no caller
    anywhere in the repository -- it is a public classmethod, so the fix keeps it
    usable by downstream code rather than repairing a crash on a path the library
    itself takes.
    """  # FIXME CoP
    project_root_dir = tmp_path / "project"
    gx_dir = project_root_dir / "gx"
    gx_dir.mkdir(parents=True)
    (gx_dir / "great_expectations.yml").write_text(
        PROJECT_YAML_TEMPLATE.format(value=NON_ASCII_VALUE), encoding="utf-8"
    )
    (gx_dir / "uncommitted").mkdir()
    (gx_dir / "uncommitted" / "config_variables.yml").write_text("a: 1\n", encoding="utf-8")

    script = textwrap.dedent(f"""
        from great_expectations.data_context.data_context.serializable_data_context import (
            SerializableDataContext,
        )

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        assert SerializableDataContext.config_variables_yml_exist({str(gx_dir)!r}) is True
        print("OK")
    """)

    result = _run_under_non_utf8_locale(script)

    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


@pytest.mark.filesystem
def test_get_ge_config_version_reads_non_ascii_project_yaml_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """get_ge_config_version() answers a question about config_version, which is a plain
    number -- a non-ASCII value elsewhere in the same file must not stop it answering.

    See https://github.com/fivetran/great_expectations/issues/12181. Like
    config_variables_yml_exist, this is a public classmethod with no caller anywhere in the
    repository -- pinning it matters for the same cross-host scenario the issue describes
    (a project authored under a UTF-8 locale read back under another one), reached through
    user code rather than through GX's own bootstrap.
    """  # FIXME CoP
    project_root_dir = tmp_path / "project"
    gx_dir = project_root_dir / "gx"
    gx_dir.mkdir(parents=True)
    (gx_dir / "great_expectations.yml").write_text(
        PROJECT_YAML_TEMPLATE.format(value=NON_ASCII_VALUE), encoding="utf-8"
    )

    script = textwrap.dedent(f"""
        from great_expectations.data_context.data_context.serializable_data_context import (
            SerializableDataContext,
        )

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        got = SerializableDataContext.get_ge_config_version(
            context_root_dir={str(project_root_dir)!r}
        )
        assert got == 3.0, got
        print("OK")
    """)

    result = _run_under_non_utf8_locale(script)

    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


@pytest.mark.filesystem
def test_set_ge_config_version_rewrites_non_ascii_project_yaml_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """set_ge_config_version() is a read-modify-write, so it is the one site here that can
    lose data rather than merely raise: the bare open() pair reads great_expectations.yml
    with one codec and writes it back with another.

    See https://github.com/fivetran/great_expectations/issues/12181. The module's YAML()
    is ruamel's round-trip formatter, which emits non-ASCII scalars as raw characters
    rather than escaping them the way PyYAML does, so the re-serialized document really
    does carry the original bytes and both handles have to agree on UTF-8.
    """  # FIXME CoP
    project_root_dir = tmp_path / "project"
    gx_dir = project_root_dir / "gx"
    gx_dir.mkdir(parents=True)
    yml_path = gx_dir / "great_expectations.yml"
    yml_path.write_text(PROJECT_YAML_TEMPLATE.format(value=NON_ASCII_VALUE), encoding="utf-8")

    script = textwrap.dedent(f"""
        from great_expectations.data_context.data_context.serializable_data_context import (
            SerializableDataContext,
        )

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        assert SerializableDataContext.set_ge_config_version(
            3.1, context_root_dir={str(project_root_dir)!r}
        ) is True
        print("OK")
    """)

    result = _run_under_non_utf8_locale(script)

    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout

    written = yml_path.read_bytes()
    assert NON_ASCII_VALUE.encode("utf-8") in written, "the rewrite dropped non-ASCII config"
    assert b"config_version: 3.1" in written, "the version bump itself did not land"


@pytest.mark.filesystem
def test_config_variables_round_trip_non_ascii_value_under_non_utf8_locale(
    tmp_path: pathlib.Path,
) -> None:
    """A non-ASCII config variable saved by AbstractDataContext.save_config_variable()
    must read back through the config-variables provider regardless of what encoding
    the process's ambient locale resolves to.

    See https://github.com/fivetran/great_expectations/issues/12181. Sibling of the
    tuple-store and great_expectations.yml cases above (#12120): the provider read
    (FileConfigurationProvider.get_values) and both save_config_variables writes
    opened config_variables.yml with a bare open().

    Both the save and the reload run under a forced non-UTF-8 locale: either side
    under the ambient (UTF-8) locale would resolve to UTF-8 regardless of whether
    the encoding is pinned, leaving nothing for the assertions to catch.
    """  # FIXME CoP
    project_root = tmp_path / "project"
    payload_path = tmp_path / "payload.txt"
    payload_path.write_text(NON_ASCII_VALUE, encoding="utf-8")

    write_script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        context = gx.get_context(mode="file", context_root_dir={str(project_root)!r})
        context.save_config_variable("db_password", non_ascii_value)
    """)
    write_result = _run_under_non_utf8_locale(write_script)
    assert write_result.returncode == 0, write_result.stderr

    reload_script = textwrap.dedent(f"""
        import great_expectations as gx

        import os

        assert open(os.devnull).encoding != "utf-8"  # locale override did not take effect

        with open({str(payload_path)!r}, encoding="utf-8") as f:
            non_ascii_value = f.read()

        context = gx.get_context(mode="file", context_root_dir={str(project_root)!r})
        assert context.config_variables["db_password"] == non_ascii_value
        print("OK")
    """)

    reload_result = _run_under_non_utf8_locale(reload_script)

    assert reload_result.returncode == 0, reload_result.stderr
    assert "OK" in reload_result.stdout


@pytest.mark.filesystem
def test_a_non_utf8_project_yaml_is_unreadable_before_this_fix_rewrites_it(
    tmp_path: pathlib.Path,
) -> None:
    """The scenario raised in review on #12204 and reproduced by #12208: a
    great_expectations.yml whose bytes are cp1252, which is what
    set_ge_config_version()'s unpinned read-modify-write used to leave behind on a host
    whose locale codec is not UTF-8.

    Pinning the read makes this call site raise, which is the behavior change under
    review. What the measurement adds is what those bytes were good for before: nothing.
    The save and load paths in FileDataContext were already pinned to UTF-8 before this PR
    (file_data_context.py:185 and :197, both untouched here), so a project config left in
    the host codec was unreadable by the next normal GX operation on the same host.

    Pinning both halves of that: the call now reports the offending path instead of
    failing with a bare decode error, and the bytes the unpinned write produced are
    themselves not readable as UTF-8.
    """  # FIXME CoP
    from great_expectations.data_context.data_context.serializable_data_context import (
        SerializableDataContext,
    )
    from great_expectations.exceptions import InvalidConfigurationYamlError

    project_root_dir = tmp_path / "project"
    gx_dir = project_root_dir / "gx"
    gx_dir.mkdir(parents=True)
    yml_path = gx_dir / "great_expectations.yml"

    cp1252_value = "Prüfung ünïcödé Straße café naïve"
    yml_path.write_bytes(PROJECT_YAML_TEMPLATE.format(value=cp1252_value).encode("cp1252"))

    with pytest.raises(InvalidConfigurationYamlError) as excinfo:
        SerializableDataContext.set_ge_config_version(3.1, context_root_dir=str(project_root_dir))

    assert str(yml_path) in str(excinfo.value), "the error does not name the unreadable file"

    # The bytes the pre-fix read-modify-write left behind are not UTF-8 either, which is
    # why the pinned loader path cannot open such a project.
    with pytest.raises(UnicodeDecodeError):
        with open(yml_path, encoding="utf-8") as f:
            f.read()
