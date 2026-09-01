# GCS Integration tests

GCS = Google Cloud Storage

GCS is a blob store similar to AWS S3 and Microsoft ABS.

## Configuration

These tests read from a real GCS bucket, named by the `GX_GCS_TEST_BUCKET` environment
variable. The bucket is expected to contain the taxi sample data at
`data/taxi_yellow_tripdata_samples/`, and the credentials in use must be able to read it.
The variable is required — the test scripts fail immediately if it is not set — so that a
missing or misconfigured bucket name is reported directly instead of surfacing as an
object-not-found error.

Credentials come from Application Default Credentials, so `GOOGLE_APPLICATION_CREDENTIALS`
must point at a service account key that can read the bucket. Use an absolute path: the
docs snippet runner chdirs into a temp directory before executing each script, and ADC
resolves the path when the client is constructed.

## Running them

The tests are gated behind `--gcs`:

```bash
pytest -v --docs-tests --gcs -k "gcs" tests/integration/test_script_runner.py
```

Watch for skips rather than failures — a skip means the flag or a gate is still wrong, and
a green run of zero tests is the failure mode worth guarding against.

## What does not run yet: Spark

Two fixtures need both GCS and Spark — `create_a_data_source_filesystem_gcs_spark` and
`create_a_data_asset_filesystem_gcs_directory_asset` — plus the Spark half of
`how_to_connect_to_data_on_gcs_using_spark`. They are deliberately left skipped: the
`docs-creds-needed` leg requests `--gcs` without `--spark`, and `docs-spark` requests
`--spark` without `--gcs`, so no leg requests both.

The blocker is not the pytest flags. Spark reads GCS through `gs://` URIs, which Hadoop
resolves only when the GCS connector is on the JVM classpath. Without it the read fails:

```
org.apache.hadoop.fs.UnsupportedFileSystemException: No FileSystem for scheme "gs"
```

The connector is a jar that must be present when the JVM starts, so no Python requirement
can supply it — it needs `PYSPARK_SUBMIT_ARGS` or a pre-staged jar in the workflow, and
Hadoop config for `fs.gs.impl` and service account auth. Adding `--gcs` to `docs-spark`
before that exists only converts a skip into a failure.
