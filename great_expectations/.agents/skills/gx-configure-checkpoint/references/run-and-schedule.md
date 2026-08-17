# Running a checkpoint, and handing it off

This document covers what `checkpoint.run()` actually does with its
arguments, one real limitation worth knowing before you assemble certain
checkpoints, and the run snippet this skill's flow ends with.

## Run semantics

```python
result = checkpoint.run(batch_parameters={"year": 2024, "month": 3})
```

`batch_parameters` is **one dict, applied to every validation definition in
the checkpoint** — there is no way to give different validation definitions
different parameters in a single `run()` call. For a checkpoint whose
validation definitions all share the same partitioning shape (all monthly by
the same convention, say), this is exactly what you want: one call, one
window, every check run against it. It stops being harmless the moment the
validation definitions don't share that shape — see both cases below.

`checkpoint.run()` also accepts `expectation_parameters`, for expectations
built with runtime parameters rather than fixed values; this skill's flow
doesn't build those, so it isn't covered further here.

### The dataframe caveat

A dataframe-backed validation definition needs its dataframe supplied at run
time, exactly as `get_batch()` does in the data-source skill:

```python
result = checkpoint.run(batch_parameters={"dataframe": df})
```

Because `batch_parameters` is shared across every validation definition in
the checkpoint, **a checkpoint containing two or more dataframe-backed
validation definitions that need different dataframes cannot be run
correctly in one call** — whichever dataframe you pass is what every
dataframe-backed validation definition in the checkpoint receives, silently.
Verified directly: a checkpoint with one validation definition over an
`orders` dataframe and another over an unrelated `products` dataframe, run
with only the `orders` frame supplied, does not raise — the `products`
validation definition runs against the `orders` data instead, and since that
frame has none of the columns the `products` suite expects, its results come
back as metric errors (`success: False`, empty `result`), which reads as a
configuration problem rather than the parameter mismatch it actually is. If
a user wants several dataframes checked by one named checkpoint, either keep
each dataframe-backed validation definition in its own checkpoint, or route
distinct dataframes through separate runs.

## When two batch definitions want incompatible parameter types

**Today's Great Expectations release cannot drive one time-partitioned
file-based batch definition and one time-partitioned SQL batch definition
from the same checkpoint run.** The monthly partitioners on the two families
disagree about what `batch_parameters` should contain — file-based
partitioners require strings, SQL partitioners require integers — and
`checkpoint.run()` has only one `batch_parameters` dict to give both. Whichever
type you pick, one side either fails loudly or fails in a way that reads as
missing data rather than a type mismatch. Verified directly, both directions:

- **Integers, aimed at a file-based monthly partitioner:**
  `InvalidBatchRequestError: All batching_regex matching options must be
  strings. The value of 'year' is not a string: 2024` — loud and immediate.
- **Strings, aimed at a SQL monthly partitioner:** `NoAvailableBatchesError:
  No available batches found.` — this is the dangerous direction. It reads
  exactly like an empty time window (a normal, non-broken outcome elsewhere
  in this skill family), not like a parameter type problem, and the data is
  actually there under the same window with integer parameters.

If a user asks for this combination, **say so before you assemble it** —
don't build a checkpoint whose validation definitions cross this line and let
them discover the misleading failure themselves. Two working alternatives:

- **Separate checkpoints, one per source family.** A checkpoint of only
  file-based validation definitions run with string parameters, and a second
  checkpoint of only SQL validation definitions run with integer parameters.
  Both stay fully automatable; wiring two run snippets instead of one is a
  minor cost for correctness.
- **A fixed, non-partitioned batch definition on one side.** If one source
  doesn't actually need month-by-month slicing, a whole-table or
  whole-dataframe batch definition sidesteps the type mismatch entirely by
  not taking `batch_parameters` for the window at all.

Per-validation-definition parameters aren't available as a third option —
`checkpoint.run()`'s one `batch_parameters` dict is the whole surface here,
for both families, whether or not their types happen to agree.

## Reporting the run

Pair each result to the validation definition it came from **by identity**,
never by position in a list — `checkpoint.run()` gives no guarantee that
results come back in the order the validation definitions were added, and
this skill's own worked example builds a checkpoint where they don't:

```python
result = checkpoint.run(batch_parameters={"dataframe": df})

for vr_id, vr in result.run_results.items():
    print(f"validation definition: batch={vr_id.batch_identifier} suite={vr.suite_name}")
    for each in vr.results:
        config = each.expectation_config
        if each.success:
            print(f"  PASS {config.type} {config.kwargs}")
        elif not each.result:
            # metric error -- see SKILL.md step 6
            for _metric_id, info in each.exception_info.items():
                print(f"  ERROR {config.type} {config.kwargs}: {info['exception_message']}")
        else:
            print(f"  FAIL {config.type} {config.kwargs}: {each.result}")
```

`result.describe()` (the `@public_api` summary method — its underlying
`describe_dict()` is not public API and shouldn't be called directly) gives
the same information as a JSON string and is a good basis for a short written
summary, but its per-validation-definition entries don't self-identify by
name — use the loop above when you need to say *which* validation definition
a given outcome belongs to, and `describe()` when an overall JSON summary is
what's wanted (as in the run snippet below).

## The run snippet

This is what the flow hands off: a small, self-contained script that
re-runs the persisted checkpoint from outside any agent session — a cron job,
a CI step, a scheduler's Python operator, or just a terminal.

```python
import sys
import great_expectations as gx

context = gx.get_context(mode="file", project_root_dir="<absolute path to the project>")
checkpoint = context.checkpoints.get("<checkpoint name>")
result = checkpoint.run()
print(result.describe())
sys.exit(0 if result.success else 1)
```

Three things about this shape are deliberate, each verified by actually
running it as a subprocess from a working directory unrelated to the
project:

<!-- consent-gate: project -->
- **`project_root_dir` is absolute, not relative.** A snippet invoked by a
  scheduler runs from whatever working directory the scheduler happens to
  use, which is very unlikely to be the project directory. A relative path
  either resolves against the wrong location or, worse, silently scaffolds a
  *new* project there — the same trap `preflight.md` warns about
  for `gx.get_context(mode="file")` with no `project_root_dir` at all, just
  reached a different way.
- **`mode="file"` is explicit**, for the same reason `preflight.md`'s
  `cloud_mode=False` is explicit: it skips discovery and any stale
  `GX_CLOUD_*` environment on the machine actually running the snippet, which
  is not necessarily the machine this conversation is happening on.
- **The exit code is derived from `result.success`, not from whether the
  script raised.** A scheduler (cron, CI, an orchestrator's shell step) reads
  the process exit code to decide whether the step passed — printing a
  failure report and then exiting 0 makes every consumer of this snippet
  believe the checkpoint always passes. Verified directly: exit `0` against a
  checkpoint that passed, exit `1` against one that didn't, both read
  directly rather than through anything that would swallow the code.

**For a checkpoint holding a dataframe-backed validation definition, this
snippet does not apply as written** — there is no dataframe to pass, running
outside any session that built one. Say this plainly rather than handing over
a snippet that will fail: a dataframe-backed check is re-run from within a
session that has the dataframe, not from this kind of standalone script.

### Offering the snippet

<!-- consent-gate: saved-file -->
Show the snippet in the conversation, filled in with the actual project root
and checkpoint name. **Offer to save it to a file at a path the user
confirms — never write it unasked.** This is the same offer-don't-do pattern
as `write-out.md`: presenting it in chat is not the same as
putting it on disk, and only the second one is something to ask permission
for first.

### Where scheduling stops

Wiring this snippet into an actual cadence — a cron entry, an Airflow
operator, a CI job on a schedule — is the user's orchestrator's job, not
this skill's. The snippet is deliberately runnable by any of them without
modification; which one, and how often, is a decision this flow doesn't
make. If the user asks how to schedule it with a specific tool, say plainly
that wiring the specific scheduler is outside what this skill covers, and
that the snippet above is the piece their scheduler needs to call.
