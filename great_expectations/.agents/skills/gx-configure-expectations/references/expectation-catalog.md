# The expectation catalog: matching a described check to a real expectation

Great Expectations ships a machine-readable catalog of its expectations,
alongside the code, inside the installed package. Read it at runtime. **Never
work from a memorized or hand-written list of expectation types** — one goes
stale the moment a release adds or renames a check, and a type you invent
fails at construction time with an error that reads like the user asked for
something impossible. The catalog is generated from the same models that
define the expectations, so it is correct for the version actually installed
in front of you.

Everything below is derived from files inside the installed package. There is
nothing to download and no network call.

## Locating the catalog

The catalog lives under `expectations/core/schemas/` in the installed
`great_expectations` package. Reach it through `importlib.resources` rather
than by building a filesystem path from `great_expectations.__file__` — that
works whether the package is installed normally, installed in editable mode,
or imported from a zipped distribution:

```python
import json
from importlib.resources import files

SCHEMAS = files("great_expectations") / "expectations" / "core" / "schemas"
INDEX = json.loads((SCHEMAS / "index.json").read_text())
CATALOG = INDEX["expectations"]
```

Two kinds of file live there:

- `index.json` — the catalog: one entry per cataloged expectation, plus a
  `documented_absent` list covered at the end of this document.
- `<ClassName>.json` — one schema per cataloged expectation, naming the
  parameters it accepts and which of them are mandatory.

## Step 1: what each index entry carries

`INDEX["expectations"]` maps each `expectation_type` (the snake_case name that
appears in validation results) to four fields:

```python
print(json.dumps(CATALOG["expect_column_values_to_be_between"], indent=2))
```

```text
{
  "data_quality_issues": ["Numeric"],
  "schema_file": "ExpectColumnValuesToBeBetween.json",
  "short_description": "Expect the column entries to be between a minimum value and a maximum value (inclusive).",
  "supported_data_sources": ["Pandas", "Spark", "SQLite", "PostgreSQL", ...]
}
```

Each field earns its place in matching:

- **`expectation_type`** — the key. Its words are the vocabulary users
  actually reach for: `null`, `unique`, `between`, `in_set`, `match_regex`,
  `row_count`.
- **`short_description`** — one sentence of prose, which is what makes a
  natural-language phrase matchable at all.
- **`data_quality_issues`** — a small controlled vocabulary for grouping. Read
  the live set out of the index rather than assuming it —
  `sorted({i for v in CATALOG.values() for i in v["data_quality_issues"]})`
  currently gives `Completeness`, `Multi-source`, `Numeric`, `SQL`, `Schema`,
  `Uniqueness`, `Validity`, `Volume`. Use it when the user describes a
  *category* ("check the data is complete") rather than a specific check.
- **`supported_data_sources`** — the backends the expectation is known to work
  on. Check it against the backend behind the user's batch definition before
  offering a candidate, because the coverage is not uniform: the
  `*_like_pattern*` family, `expect_query_results_to_match_comparison`, and
  `expect_table_row_count_to_equal_other_table` are SQL-only and absent on
  Spark.

## Step 2: matching what the user described

Search all three text-bearing fields together. Keep it simple — the point is
to produce candidates for the user to confirm, not to guess on their behalf:

```python
def search(*terms: str) -> list[tuple[int, str, str]]:
    """Rank catalog entries by how many of the user's terms they mention."""
    terms = [t.lower() for t in terms]
    hits = []
    for expectation_type, entry in CATALOG.items():
        haystack = " ".join([
            expectation_type.replace("_", " "),
            entry["short_description"],
            " ".join(entry["data_quality_issues"]),
        ]).lower()
        score = sum(term in haystack for term in terms)
        if score:
            hits.append((score, expectation_type, entry["short_description"]))
    return sorted(hits, reverse=True)
```

For "the customer column should never be empty", `search("null")` returns
`expect_column_values_to_not_be_null`, `expect_column_values_to_be_null`, and
`expect_column_proportion_of_non_null_values_to_be_between` — three real
candidates with visibly different meanings. **Show the candidates and their
descriptions and let the user pick** when more than one is plausible. The
difference between "never null" and "at least 95% non-null" is the user's
decision, not yours.

Two filters are worth having alongside the text search:

```python
# By category, when the user described a kind of problem rather than a check.
[e for e, v in CATALOG.items() if "Uniqueness" in v["data_quality_issues"]]

# By backend, to drop candidates that won't run on this batch definition.
[e for e, v in CATALOG.items() if "Spark" in v["supported_data_sources"]]
```

## Step 3: from a matched entry to a constructed expectation

The class name is the schema filename without its `.json` suffix, and every
cataloged expectation is exposed under that name on
`great_expectations.expectations`. That derivation is exact for every entry
the package ships:

```python
import great_expectations as gx

entry = CATALOG["expect_column_values_to_be_between"]
expectation_class = getattr(gx.expectations, entry["schema_file"].removesuffix(".json"))
```

The schema names the parameters and which are mandatory:

```python
schema = json.loads((SCHEMAS / entry["schema_file"]).read_text())
print("required:", schema["required"])
print("accepted:", sorted(schema["properties"]))
```

```text
required: ['column']
accepted: ['batch_id', 'catch_exceptions', 'column', 'condition_parser', 'description',
           'id', 'max_value', 'meta', 'metadata', 'min_value', 'mostly', 'notes',
           'rendered_content', 'result_format', 'row_condition', 'severity',
           'strict_max', 'strict_min', 'windows']
```

Then construct it with keyword arguments:

```python
expectation = expectation_class(column="amount", min_value=0, mostly=0.99)
```

Reading the schema rather than guessing matters for three reasons:

- **`required` is short and the interesting parameters are optional.**
  `expect_column_values_to_be_between` requires only `column`; `min_value` and
  `max_value` are optional, and an expectation built with neither asserts
  nothing useful. Elicit the bound the user actually meant.
- **Each entry in `properties` carries its own `description`.** Read it to the
  user when they ask what a parameter means instead of paraphrasing from
  memory. `mostly`, for example, is documented as "Successful if at least
  `mostly` fraction of values match the Expectation" — a tolerance, not a
  target.
- **Treat `batch_id`, `id`, `meta`, `metadata`, `rendered_content`, and
  `windows` as reserved.** They are assigned by the library or belong to
  surfaces outside this flow; the parameters to elicit are the ones that
  describe the check.

## The `documented_absent` list

`INDEX["documented_absent"]` names expectations that are real and usable but
ship no schema file:

```python
print(INDEX["documented_absent"])
```

```text
['expect_column_values_to_be_dateutil_parseable',
 'expect_column_values_to_be_decreasing',
 'expect_column_values_to_be_increasing',
 'expect_column_values_to_be_json_parseable',
 'expect_column_values_to_match_json_schema']
```

These are **not** unavailable. Each has a class on
`great_expectations.expectations` under the usual CamelCase name and can be
constructed, added to a suite, and validated exactly like any other. What they
lack is a catalog entry, so `search()` above will never surface them and there
is no schema to read parameters from. Fall back to the class itself, which is
authoritative for the installed version:

```python
import inspect

expectation_class = gx.expectations.ExpectColumnValuesToBeIncreasing
print(inspect.signature(expectation_class))   # accepted parameters and defaults
print(expectation_class.__doc__)              # the same prose a description would carry
```

Mention them by hand when a user describes something they cover — a monotonic
sequence, a parseable date string, JSON-shaped values — since the text search
cannot.

## When nothing matches

Say so. **Never invent an expectation type**, never bend the user's
description onto a check that means something else, and never present a
candidate as though it were what they asked for.

Produce nearest candidates from the catalog itself so the user has something
concrete to react to. `difflib` is in the standard library and is enough:

```python
import difflib

def nearest(phrase: str, n: int = 5) -> list[tuple[float, str]]:
    corpus = {
        expectation_type: f"{expectation_type.replace('_', ' ')} {entry['short_description']}"
        for expectation_type, entry in CATALOG.items()
    }
    scored = sorted(
        (
            (difflib.SequenceMatcher(None, phrase.lower(), text.lower()).ratio(), expectation_type)
            for expectation_type, text in corpus.items()
        ),
        reverse=True,
    )
    return [(round(ratio, 3), expectation_type) for ratio, expectation_type in scored[:n]]
```

For "every email address must be deliverable" — a real check, and one no
shipped expectation performs — `search("deliverable", "email")` returns
nothing and `nearest(...)` returns `expect_column_values_to_be_null`,
`expect_column_value_z_scores_to_be_less_than`,
`expect_column_pair_values_to_be_equal`, and so on, all scoring around 0.3.
**A weak score is information, not a match.** Report it as one:

> Nothing in the installed catalog checks whether an email address is
> deliverable — that needs a live mail server, which is outside what an
> expectation does. The closest shipped checks are
> `expect_column_values_to_match_regex` (format only, not deliverability) and
> `expect_column_values_to_not_be_null`. Would either of those be useful, or
> should this check live outside Great Expectations?

Two honest paths forward, and either is a better answer than a wrong match:

- **A different shipped expectation that covers part of the intent**, named
  with its limitation stated plainly — format instead of deliverability,
  non-null instead of non-empty-string.
- **A custom expectation.** Great Expectations supports user-defined
  expectations, and a check with no shipped equivalent is exactly what they
  are for. Point the user at the custom-expectation documentation for the
  version they have installed rather than sketching an implementation
  mid-flow — authoring one is its own piece of work, not a step in this
  conversation.

Build the expectations that did match, run them, and report the unmatched ones
separately as unbuilt, with the reason. Do not silently drop them, and do not
substitute something else for them.
