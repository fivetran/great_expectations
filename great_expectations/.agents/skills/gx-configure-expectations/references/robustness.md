# Robustness: time budgets, scope reduction, and reading results correctly

Real data is large, slow, and occasionally broken in ways that don't produce
clean errors. This document covers three things every data-touching step in
this skill needs: a time budget that doesn't pretend it can cancel anything,
concrete levers for cutting a query down to size, and how to read a result
correctly so an infrastructure failure never gets reported as a data-quality
finding.

## The advisory time budget is a check-in, not a kill switch

Wrap any potentially slow call — testing a connection, retrieving a batch,
probing it, running a validation — so you can check in with the user *while
it is still running*, not only after it returns. A budget measured after the
call has already completed can't do this — by the time you'd act on it, there
is nothing left to check in about. Instead, run the call on a worker thread
and poll it with a timeout, so you get control back at regular intervals
while the real call is still in flight:

```python executable
import concurrent.futures
import time

BUDGET_SECONDS = 60   # let the user adjust this for known-slow sources
POLL_SECONDS = 5      # how often to check whether the budget has passed

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
future = executor.submit(batch.head, n_rows=5)  # or test_connection(), get_batch(), validate(), ...
start = time.monotonic()
checked_in = False
succeeded = False
result = None

while True:
    # Report state instead of racing an exception: on Python 3.11+,
    # concurrent.futures.TimeoutError IS the builtin TimeoutError, so if the
    # wrapped call itself raises a TimeoutError (a driver connect/statement
    # timeout, for example — see lever 3 below), an `except
    # concurrent.futures.TimeoutError` branch built on `future.result()`
    # cannot tell "still running" apart from "finished, with that exact
    # exception". Since a *finished* future's `.result()` returns instantly,
    # that ambiguity turns into an unthrottled busy loop with no sleep in it.
    # `concurrent.futures.wait(...)` sidesteps this entirely — it reports
    # done/not-done without ever raising the wrapped call's own exception.
    done, _ = concurrent.futures.wait([future], timeout=POLL_SECONDS)
    elapsed = time.monotonic() - start
    if not done:
        # The real call has NOT returned yet — this branch runs while it is
        # still executing on the worker thread, which is what makes an
        # in-flight check-in possible at all.
        if elapsed > BUDGET_SECONDS and not checked_in:
            checked_in = True
            # tell the user, right now, while the call is still running:
            # "This has been running <elapsed>s, past the <BUDGET_SECONDS>s
            # budget, and is still going." Then follow the three steps below.
            ...
        continue
    try:
        result = future.result()
        succeeded = True
    except Exception as e:
        # translate the exception — see "Reporting failures helpfully" below
        result = None
    break

if succeeded and checked_in:
    # tell the user it finished after all, at <elapsed>s, past the budget
    ...
```

`succeeded` — not `result is not None` — is what distinguishes "the call
returned" from "the call failed": some wrapped calls (`test_connection()`,
for one) return `None` on success, so `result` alone can't tell the two
apart.

**When the budget is exceeded, do not abandon the operation.** On most data
platforms, the query is running on the platform's own compute the moment it
was dispatched — closing the client connection or giving up on waiting does
not cancel it, and it keeps consuming (and costing) resources on the platform
regardless of whether anything is still waiting on the result. Killing the
client side only means losing visibility into a query that is still running
and still being billed. So the moment the budget check-in above fires:

1. Tell the user the operation is still running and has passed the budget.
2. State plainly that it will keep running (and, on most platforms, keep
   costing money) whether or not you keep waiting on it.
3. Ask whether to keep waiting, or to reduce the scope of data involved and
   try again — never decide this unilaterally.

**Keep the future alive; never cancel it.** Whatever the user picks, do not
call `future.cancel()` or `executor.shutdown(cancel_futures=True)` — the call
already dispatched to the platform's own compute, and cancelling the future
only makes this process stop watching it; it does not stop the remote work,
which is the point above about it continuing to run and cost money. If the
user chooses to keep waiting, stay in the polling loop shown above. If the
user chooses to reduce scope, stop polling this loop and leave `future` and
`executor` exactly as they are — still running, unattended — and submit the
reduced-scope attempt (using the levers below) as a new, separate call. Don't
block on the abandoned future first.

## Scope-reduction levers, in preference order

The goal each time is to make the specific operation touch less data, not to
change what the asset represents — an asset stays the durable, logical
collection of data a project points at; a batch definition is what selects
how much of it a given operation actually reads.

**1. A narrower batch definition window, via the existing partitioner
factories.** This is the primary lever, and it should be tried first whenever
there's a usable date/time or otherwise partitionable column. Add (or reuse) a
partitioned batch definition, then request a specific window at fetch time:

```python
# One-time setup: partition by month on a datetime column.
batch_definition = asset.add_batch_definition_monthly(name="monthly", column="event_time")

# Per-attempt: fetch only one narrow window instead of the whole asset.
batch = batch_definition.get_batch(batch_parameters={"year": 2024, "month": 3})
```

The equivalent daily/yearly variants exist too
(`add_batch_definition_daily`, `add_batch_definition_yearly`), as does a
directory-scoped daily/monthly/yearly split for file-based assets. Always
reach these through the asset's own `add_batch_definition_*` methods and
`batch_parameters` — never by constructing a partitioner object directly.

**2. A row-limiting argument on the read itself, for local file-based
sources.** Where the underlying reader supports it (for example, a pandas
CSV asset), pass its native `nrows` option — a hard cap on how many rows get
read — as a keyword argument when adding the asset:

```python
asset = pandas_datasource.add_csv_asset(
    name="my_asset",
    filepath_or_buffer="/path/to/large_file.csv",
    nrows=1000,
)
```

This helps specifically with large local files rather than remote queries.

**3. A driver-level connection or statement timeout**, for SQL sources. Pass
driver-specific timeout options through the datasource's `kwargs`, which are
forwarded straight to engine creation:

```python
datasource = context.data_sources.add_or_update_postgres(
    name="my_datasource",
    connection_string="postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@host/db",
    kwargs={"connect_args": {"connect_timeout": 10}},
)
```

The exact keys are driver-specific (a `connect_timeout` for one driver may be
a different name for another) — this caps how long a *connection attempt*
can hang, not how much data a query returns, so treat it as a complement to
lever 1, not a substitute.

**4. Last resort: a row limit on a query asset, for exploration only.** If no
column exists to partition on (no usable date/time or other partitionable
column), and the goal is just to inspect a sample of the data rather than
operate on the real batch, a query asset with an explicit `LIMIT` in its SQL
text is an acceptable stopgap:

```python
asset = datasource.add_query_asset(
    name="sample_events",
    query="SELECT * FROM events LIMIT 1000",
)
```

Flag this to the user explicitly as temporary and exploration-only when you
use it. A query asset's row limit is baked into that one query's text — it
isn't a general batching mechanism, it doesn't compose with the partitioner
levers above, and it isn't something to reach for as a default way to make a
slow asset faster. If a project keeps needing this, the honest answer is that
the reduction lever it actually needs doesn't exist yet in the partitioner set
— that's a gap to name to the user, not one to paper over with query-asset
limits everywhere.

## Reporting failures helpfully

Whenever something in this flow raises, report three things and stop there —
never a raw traceback: **what failed** (the operation you were attempting),
**why, as far as it's known** (the clearest available cause), and **one
concrete next step** the user can take.

Two exception shapes are common enough to call out by name:

- **Connection and configuration failures** (a failed `test_connection()`
  during `add_or_update_*`, or an import error for an optional driver
  dependency) already carry an actionable message from Great Expectations
  itself — relay it close to verbatim, plus one next step (fix the connection
  string, install the missing driver package, check the credential).
- **A missing credential.** If a data operation fails because a referenced
  `${ENV_VAR}` isn't set, say exactly which variable is missing and how to
  provide it (set the environment variable, or add it to the project's
  uncommitted config-variables file if working in a file-backed project).
  Never hardcode a value or invent a placeholder to work around it.
- **A bare `KeyError` out of a batch probe.** Retrieving a batch off a broken
  query or table does not itself fail — see "Why a retrieved batch doesn't
  prove anything" below — but probing it can raise a plain `KeyError`, not a
  Great Expectations exception, with no readable message of its own (its text
  is just an internal cache key). The real underlying cause (the actual
  database error, including which table or column it choked on) is emitted
  during metric resolution as a **`WARNING`-level log record on the
  `great_expectations.validator.metrics_calculator` logger** — not printed to
  stdout. Attach a handler to that logger before the probe so you capture the
  record directly, rather than trusting the `KeyError`'s own text or scanning
  raw console output — this avoids depending on stdout/stderr being
  visible, or on the *root* logger's own level. It does **not** avoid this
  logger's own effective level: a handler only sees records the logger lets
  past its own threshold, so if a host has raised
  `great_expectations.validator.metrics_calculator` above `WARNING`, force it
  down to `WARNING` for the duration of the probe and restore it afterward:

  ```python
  import logging
  import re
  import ast

  class _CaptureHandler(logging.Handler):
      def __init__(self):
          super().__init__(level=logging.WARNING)
          self.records: list[str] = []

      def emit(self, record: logging.LogRecord) -> None:
          self.records.append(record.getMessage())

  def _extract_cause(message: str, ceiling: int = 500) -> str:
      # The log message is a stringified dict of MetricConfigurationID ->
      # {"exception_message": ..., "exception_traceback": ..., ...} — often
      # several thousand characters, wrapping a full traceback with absolute
      # filesystem paths. Never relay it verbatim (see the no-raw-traceback
      # rule above). Pull out just the exception_message value(s); if the
      # shape ever changes and the pattern doesn't match, fall back to a
      # hard-truncated slice so a ceiling is guaranteed either way.
      found = re.findall(r"'exception_message': (.+?), 'raised_exception':", message, re.DOTALL)
      try:
          # A match is not automatically a valid Python literal: an error text
          # containing the terminator itself truncates the non-greedy match
          # mid-literal. Fall through to truncation rather than raising from
          # inside the error-reporting path.
          cause = "; ".join(ast.literal_eval(m) for m in found) if found else message
      except Exception:
          cause = message
      if len(cause) > ceiling:
          cause = cause[:ceiling] + "... (truncated)"
      return cause

  handler = _CaptureHandler()
  metrics_logger = logging.getLogger("great_expectations.validator.metrics_calculator")
  metrics_logger.addHandler(handler)
  prior_level = metrics_logger.level
  metrics_logger.setLevel(logging.WARNING)
  try:
      head = batch.head(n_rows=5)
  except KeyError:
      cause = _extract_cause(handler.records[-1]) if handler.records else "<no warning captured>"
      # report: the batch could not be read; cause holds the real database error
      ...
  finally:
      metrics_logger.removeHandler(handler)
      metrics_logger.setLevel(prior_level)
  ```

  Report to the user that the batch could not be read, relay the extracted
  cause (a few hundred characters, not the raw log message), and point them
  at checking the query or table name, and the connection, as the next step.
- **Resource exhaustion on a large dataset** (a `MemoryError`, or a
  driver/engine error whose message names memory or disk space). This is not
  a data-quality finding and not a connection problem — it means the
  operation tried to hold more of the dataset in memory than the machine
  running it has. Report plainly that it ran out of resources processing the
  full dataset, then route straight to the scope-reduction levers above: a
  narrower batch-definition window (lever 1) is the first thing to try, in
  the same partitioner-first order used for a slow-but-successful call.

## Why a retrieved batch doesn't prove anything, for SQL query assets

`batch_definition.get_batch()` succeeds and returns a real `Batch` object even
when the underlying table or query is broken — for a SQL query asset, nothing
about building the batch touches the database. So retrieving a batch is not,
by itself, evidence of a working configuration. Always follow it with a cheap,
duration-tracked probe before declaring success:

```python
batch = batch_definition.get_batch()
head = batch.head(n_rows=5)  # this is what actually touches the data
```

A probe that raises means the configuration doesn't work — report per the
`KeyError` guidance above. A probe that returns means there's a real, working
batch definition.

## Distinguishing an infrastructure failure from a real data-quality result

After running an expectation (or a suite) against a batch, `success is False`
can mean two very different things, and they must be reported differently:

- **The metric itself errored** — a broken column reference, a query that
  fails, a type mismatch the engine can't evaluate. Great Expectations
  reports this the same way it reports a real failure — `success: False` —
  but the result payload is empty. Check `result.result`: an empty dict means
  nothing was actually evaluated; there is no data-quality finding to report,
  only a configuration problem to fix. Don't guess at what that problem is —
  `result.exception_info` names it exactly. On this branch it's a dict with
  one entry per metric that errored, keyed by the **string repr** of a
  `MetricConfigurationID` (not a `MetricConfigurationID` instance itself — a
  keyed lookup with one won't match), and each value is a dict whose
  `exception_message` key holds the real cause verbatim, e.g.
  `'Error: The column "nope" in BatchData does not exist.'`. Report that
  message as the *why*, not a guess. Reached through the normal flow these
  messages are short and clean, because the batch-definition probe catches a
  broken table long before validation runs. Apply the same length ceiling
  used for captured log output anyway: validating against a batch that was
  never probed can surface an engine-level message carrying a full traceback,
  and the no-raw-traceback rule holds on every path.
- **The data genuinely failed the expectation.** The result payload is
  populated — counts, examples, percentages of the specific values that
  violated the check.

```python
result = batch.validate(expectation)
if not result.success and not result.result:
    # a metric error: result.exception_info is a dict of
    # {str(MetricConfigurationID): {"exception_message": ..., ...}}, one entry
    # per metric that errored — report each exception_message verbatim as the
    # why, not a data-quality finding. Keys are strings; iterating .items()
    # works, but a keyed lookup with a MetricConfigurationID instance won't.
    for metric_id, info in result.exception_info.items():
        # tell the user: info["exception_message"]
        ...
elif not result.success:
    # a genuine data-quality failure: report result.result's counts/examples
    ...
```

Never report an empty-`result` failure to the user as "your data failed this
check" — it didn't get evaluated at all.
