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
