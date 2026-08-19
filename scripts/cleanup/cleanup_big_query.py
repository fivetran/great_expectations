from __future__ import annotations

import datetime
import logging
import re
import sys

from great_expectations.compatibility.google import NotFound, python_bigquery
from great_expectations.compatibility.pydantic import BaseSettings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class BigQueryConnectionConfig(BaseSettings):
    """Environment variables for BigQuery access.
    These are injected in via CI, but when running locally, you may use your own credentials.
    GOOGLE_APPLICATION_CREDENTIALS must be kept secret. It is not read directly by this script;
    Application Default Credentials picks it up automatically.
    """

    GE_TEST_GCP_PROJECT: str
    GE_TEST_BIGQUERY_DATASET: str
    GOOGLE_APPLICATION_CREDENTIALS: str


# Tables created by the SQL test framework, named by `SQLBatchTestSetup._create_table_name`:
# a fixed prefix, an optional caller-supplied label, and a uuid4-derived suffix. The suffix
# is anchored and required so a table someone created deliberately in this dataset is never
# a candidate for deletion.
TABLE_PATTERN = re.compile(r"^expectation_test_table(?:_[A-Za-z0-9_]+)?_[0-9a-f]{10}$")

# Only sweep tables older than this, so a table belonging to a run that is still in progress
# is never deleted out from under it.
DEFAULT_MAX_AGE = datetime.timedelta(hours=1)


def find_stale_table_ids(
    client: python_bigquery.Client,
    dataset_id: str,
    max_age: datetime.timedelta = DEFAULT_MAX_AGE,
) -> list[str]:
    """Find test table ids in ``dataset_id`` old enough to be cleaned up.

    Scoped to the single configured CI dataset rather than searching the project. Tests
    create their tables there directly, so there is nowhere else to look -- and staying
    dataset-scoped means this runs with a credential that can see only that dataset, and
    never pays to enumerate a project that may hold many thousands of unrelated datasets.

    ``tables.list`` reports creation time for each table, so age filtering needs no
    follow-up request per candidate.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    listed = 0
    matched = 0
    stale_ids = []

    for table_item in client.list_tables(dataset_id):
        listed += 1
        if not TABLE_PATTERN.match(table_item.table_id):
            continue
        matched += 1

        created = table_item.created
        # Treat an unknown creation time as too new to touch: with no age to compare we
        # cannot tell a leftover from a table an in-flight run is about to query.
        if created is not None and now - created > max_age:
            stale_ids.append(table_item.table_id)

    # A pattern that has drifted away from what the harness generates and a dataset that is
    # genuinely clean both end this function with nothing to delete, and both would otherwise
    # log the same reassuring line. Reporting the counts separately distinguishes them: tables
    # listed but none matched is the signature of the pattern no longer describing the names,
    # which is otherwise invisible until the dataset has grown without bound.
    logger.info(
        f"{listed} table(s) in {dataset_id}; {matched} matched the test-table pattern; "
        f"{len(stale_ids)} older than {max_age}"
    )

    return stale_ids


def cleanup_big_query(
    config: BigQueryConnectionConfig, max_age: datetime.timedelta = DEFAULT_MAX_AGE
) -> None:
    client = python_bigquery.Client(project=config.GE_TEST_GCP_PROJECT)
    dataset_id = f"{config.GE_TEST_GCP_PROJECT}.{config.GE_TEST_BIGQUERY_DATASET}"

    stale_ids = find_stale_table_ids(client, dataset_id, max_age=max_age)
    if not stale_ids:
        logger.info("No BigQuery tables to clean up!")
        return

    cleaned_up = 0
    for table_id in stale_ids:
        try:
            client.delete_table(f"{dataset_id}.{table_id}")
            cleaned_up += 1
        except NotFound:
            # Deleted between listing and deleting, by a concurrent sweep or by its own
            # run reaching teardown.
            logger.info(f"Table {table_id} was already deleted")

    logger.info(f"Cleaned up {cleaned_up} BigQuery table(s)")


if __name__ == "__main__":
    config = BigQueryConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_big_query(config)
