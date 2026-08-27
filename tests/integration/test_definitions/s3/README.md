# S3 Integration tests

S3 = Amazon Simple Storage Service

S3 is a blob store similar to Google Cloud Storage and Microsoft ABS.

## Configuration

These tests read from a real S3 bucket, named by the `GX_S3_TEST_BUCKET` environment
variable. The bucket is expected to contain the taxi sample data at
`data/taxi_yellow_tripdata_samples/`, and the credentials in use must be able to read it.
The variable is required — the test scripts fail immediately if it is not set — so that a
missing or misconfigured bucket name is reported directly instead of surfacing as an
object-not-found error.

Credentials come from the standard boto3 environment chain, since the fixtures pass
`boto3_options={}`. In CI they are short-lived and obtained by assuming a role through
GitHub's OIDC provider; locally, any profile that can read the bucket will do.

The identity needs exactly two permissions: `s3:ListBucket` on the bucket and
`s3:GetObject` on its objects. Those are different resources — the bucket ARN and the
object ARN with a `/*` suffix — and granting only the former produces a clean listing
followed by a `403` on the first batch read.

## Running them

The tests are gated behind `--aws`:

```bash
pytest -v --docs-tests --aws -k "s3" tests/integration/test_script_runner.py
```

Watch for skips rather than failures — a skip means the flag or a gate is still wrong, and
a green run of zero tests is the failure mode worth guarding against.

## Exactly three objects

`partition_on_datetime.py` asserts that the monthly batch definition yields exactly three
batches, matching `yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv`. A fourth
month uploaded under the same prefix breaks that assertion, and the failure reads like a
partitioner bug rather than a data problem. Objects that do not match the regex are
harmless — the connector compiles prefix and regex together and filters on the result.

## What does not run yet: Spark

`create_a_data_source_filesystem_s3_spark` and the Spark half of
`how_to_connect_to_data_on_s3_using_spark` need both AWS and Spark. They are deliberately
left skipped: the `docs-creds-needed` leg requests `--aws` without `--spark`, and
`docs-spark` requests `--spark` without `--aws`, so no leg requests both.

The blocker is not the pytest flags. Spark reads S3 through `s3a://` URIs, which Hadoop
resolves only when the `hadoop-aws` connector and its matching `aws-java-sdk-bundle` are
on the JVM classpath. Without them the read fails:

```
java.lang.ClassNotFoundException: org.apache.hadoop.fs.s3a.S3AFileSystem
```

Those jars must be present when the JVM starts, so no Python requirement can supply them —
it needs `PYSPARK_SUBMIT_ARGS` or a pre-staged jar in the workflow, plus Hadoop
credential-provider configuration. This mirrors the GCS situation described in
`tests/integration/test_definitions/gcs/README.md`. Adding `--aws` to `docs-spark` before
that exists only converts a skip into a failure.
