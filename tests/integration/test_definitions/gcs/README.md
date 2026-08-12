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
