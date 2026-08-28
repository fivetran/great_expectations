import os
import pathlib
from dataclasses import dataclass
from typing import List, Optional, Tuple

from tests.integration.backend_dependencies import BackendDependencies

GCS_TEST_BUCKET_ENV_VAR = "GX_GCS_TEST_BUCKET"
S3_TEST_BUCKET_ENV_VAR = "GX_S3_TEST_BUCKET"
TEST_BUCKET_ENV_VARS = (GCS_TEST_BUCKET_ENV_VAR, S3_TEST_BUCKET_ENV_VAR)


@dataclass
class IntegrationTestFixture:
    """IntegrationTestFixture

    Configurations for integration tests are defined as IntegrationTestFixture dataclass objects.

    Individual tests can also be run by setting the '-k' flag and referencing the name of test, like the following example:
    pytest -v --docs-tests -k "test_docs[migration_guide_spark_v2_api]" tests/integration/test_script_runner.py

    Args:
        name: Name for integration test. Individual tests can be run by using the -k option and specifying the name of the test.
        user_flow_script: Required script for integration test.
        backend_dependencies: Flag allows you to tie an individual test with a BackendDependency. Allows for tests to be run / disabled using cli flags (like --aws which enables AWS integration tests). If no backends are required, must explicitly set to empty list.
        data_context_dir: Path of great_expectations/ that is used in the test.
        data_dir: Folder that contains data used in the test.
        other_files: other files (like credential information) to copy into the test environment. These are presented as Tuple(path_to_source_file, path_to_target_file), where path_to_target_file is relative to the test_script.py file in our test environment
        util_script: Path of optional util script that is used in test script (for loading test_specific methods like load_data_into_test_database())
    """  # noqa: E501 # FIXME CoP

    name: str
    user_flow_script: str
    backend_dependencies: List[BackendDependencies]
    data_context_dir: Optional[str] = None
    data_dir: Optional[str] = None
    other_files: Optional[Tuple[Tuple[str, str]]] = None
    util_script: Optional[str] = None


def substitute_test_buckets(config_path: pathlib.Path) -> None:
    """Resolve object-store bucket placeholders in a copied test Data Context config.

    The GCS- and S3-backed `data_context_dir` configs name their bucket with a
    placeholder rather than a literal, so the bucket can be changed without editing the
    fixtures. GX applies config substitution to credential fields only, not to `bucket`
    or `bucket_or_name`, so the placeholder is resolved here — on the copy the test runs
    against, never the checked-in fixture.

    Only these placeholders are substituted. Other config templates are left for GX to
    resolve, since exercising that path is the point of the fixtures that use them.
    """
    if not config_path.exists():
        return
    original = config_path.read_text()
    config = original
    for env_var in TEST_BUCKET_ENV_VARS:
        template = "${" + env_var + "}"
        if template not in config:
            continue
        bucket = os.environ.get(env_var)
        if not bucket:
            raise RuntimeError(
                f"{config_path.name} requires an object-store bucket, but the"
                f" {env_var} environment variable is not set."
            )
        config = config.replace(template, bucket)
    if config != original:
        config_path.write_text(config)
