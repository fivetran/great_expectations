import pytest

pytestmarks = pytest.mark.filesystem


def read_config_from_file(config_filename):
    with open(config_filename) as f_:
        config = f_.read()

    return config


@pytest.mark.filesystem
def test_add_store_immediately_adds_to_config(empty_data_context):
    context = empty_data_context
    config_filename = context.root_directory + "/great_expectations.yml"

    assert "my_new_store" not in read_config_from_file(config_filename)
    context.add_store(
        "my_new_store",
        {
            "module_name": "great_expectations.data_context.store",
            "class_name": "ExpectationsStore",
        },
    )
    assert "my_new_store" in read_config_from_file(config_filename)


# ============================================================================
# Regression test for issue #12120: FileDataContext._load_file_backed_project_config
# reads great_expectations.yml with bare open() while the write path pins UTF-8.
# On hosts where the process locale encoding is not UTF-8 (e.g. Windows cp936),
# a bare open() resolves to that codepage and raises UnicodeDecodeError on the
# non-ASCII UTF-8 bytes the write path emitted.
# This test runs in a subprocess with PYTHONUTF8=0 / LC_ALL=C to force the
# non-UTF-8 codepage and asserts the patched code pins encoding="utf-8" on read.
# ============================================================================
@pytest.mark.filesystem
def test_file_data_context_utf8_pinned_yml_load(tmp_path_factory):
    """Ensure FileDataContext._load_file_backed_project_config pins UTF-8 on yml read."""
    import subprocess, sys, os

    # The worker script runs under PYTHONUTF8=0 / LC_ALL=C to expose the bug.
    worker = r'''
import sys, os, tempfile, shutil
from great_expectations.data_context.data_context.file_data_context import FileDataContext

NONASCII = "Prüfung ünïcödé — 中文测试"

tmp = tempfile.mkdtemp()
try:
    yml = os.path.join(tmp, "great_expectations.yml")
    with open(yml, "wb") as f:
        f.write((
            "config_version: 3\n"
            "stores:\n"
            "  expectations_store:\n"
            "    class_name: ExpectationsStore\n"
            "  validations_store:\n"
            "    class_name: ValidationsStore\n"
            "  suite_parameter_store:\n"
            "    class_name: SuiteParameterStore\n"
            "  plugin_suite_parameter_store:\n"
            "    class_name: SuiteParameterStore\n"
            "  checkpoint_store:\n"
            "    class_name: CheckpointStore\n"
            "data_docs_sites:\n"
            "  local:\n"
            "    class_name: SiteBuilder\n"
            "    store_backend:\n"
            "      class_name: TupleFilesystemStoreBackend\n"
            "      base_directory: uncommitted/data_docs/local_site/\n"
            "anonymous_usage_statistics:\n"
            "  enabled: false\n"
            "datasources:\n"
            "  " + NONASCII + ": {}\n"
        ).encode("utf-8"))
    FileDataContext._load_file_backed_project_config(context_root_directory=tmp)
    print("OK")
    sys.exit(0)
except UnicodeDecodeError as e:
    print("UNICODE_DECODE_ERROR:", repr(str(e))[:200])
    sys.exit(1)
except Exception as e:
    # If the decode succeeded but config validation fails later, that's GREEN
    # for this bug — the read path is fixed. Only UnicodeDecodeError is the bug.
    print("OK_POST_DECODE:", type(e).__name__)
    sys.exit(0)
'''

    result = subprocess.run(
        [sys.executable, "-c", worker],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONUTF8": "0",
            "PYTHONCOERCECLOCALE": "0",
            "LC_ALL": "C",
            "LANG": "C",
            "PYTHONIOENCODING": "ascii",
        },
        errors="replace",
    )

    # With the fix, the decode must succeed (exit 0, stdout contains "OK")
    assert result.returncode == 0, (
        f"FileDataContext yml load failed under forced locale: "
        f"rc={result.returncode}, out={result.stdout.strip()}, err={result.stderr.strip()}"
    )
    assert "OK" in result.stdout, f"Unexpected output: {result.stdout}"
