# The datasource catalog: finding types, factories, and asset surfaces

Great Expectations ships a machine-readable catalog of every data source type
it can configure, alongside the code, inside the installed package. Read it at
runtime. **Never work from a memorized or hand-written list of types** — one
goes stale the moment a release adds a backend, and a wrong guess sends the
user down a path that doesn't exist. The catalog is generated from the same
code that defines the factories, so it is correct for the version that is
actually installed in front of you.

Everything below is derived from files inside the installed package. There is
nothing to download and no network call.

## Locating the catalog

The catalog lives under `datasource/fluent/schemas/` in the installed
`great_expectations` package. Reach it through `importlib.resources` rather
than by building a filesystem path from `great_expectations.__file__` — that
works whether the package is installed normally, installed in editable mode,
or imported from a zipped distribution:

```python
import json
from importlib.resources import files

SCHEMAS = files("great_expectations") / "datasource" / "fluent" / "schemas"
```

Three kinds of file live there:

- `index.json` — the type index: one entry per configurable data source type.
- `<Name>Datasource.json` — one connection schema per type, naming the
  arguments its factory accepts.
- `<Name>Datasource/` — a sibling directory per type, holding one schema per
  asset type that data source supports.

## Step 1: the type index gives you the factory name

`index.json` maps each connection schema filename to the **exact** name of the
factory method on `context.data_sources` that creates that type:

```python
index = json.loads((SCHEMAS / "index.json").read_text())

for schema_file, factory in sorted(index.items()):
    print(f"{schema_file[:-len('Datasource.json')]:<28} context.data_sources.{factory}(...)")
```

**Read the factory name out of the index; never derive it from the type
name.** There is no naming rule that holds — the index exists precisely
because the mapping is irregular in both directions. `BigQueryDatasource.json`
maps to `add_or_update_bigquery`, not `add_or_update_big_query`;
`PandasAzureBlobStorageDatasource.json` maps to `add_or_update_pandas_abs`.
Any snake-casing rule you might infer from the regular cases will silently
produce a method name that doesn't exist for the irregular ones, and the
failure surfaces as a confusing `AttributeError` rather than "no such data
source type".

Use the index for two things: to answer "what can Great Expectations connect
to?" for the user, and to turn the type they pick into a call you can actually
make.

## Step 2: the connection schema gives you the arguments

Once the user has picked a type, its `<Name>Datasource.json` schema names
exactly what its factory accepts and which of those are mandatory:

```python
schema_file = "PostgresDatasource.json"        # whichever type the user picked
schema = json.loads((SCHEMAS / schema_file).read_text())

print("factory:  context.data_sources." + index[schema_file])
print("required:", schema["required"])
print("accepted:", sorted(schema["properties"]))
```

For `PostgresDatasource.json` that prints:

```text
factory:  context.data_sources.add_or_update_postgres
required: ['name', 'connection_string']
accepted: ['assets', 'connection_string', 'create_temp_table', 'id', 'kwargs', 'name', 'type']
```

`required` is what you must elicit from the user before you can make the call.
Treat `assets`, `id`, and `type` as reserved: `assets` is populated by the
asset factories rather than passed in, `id` is assigned, and `type` is implied
by the factory you chose. Each entry in `properties` carries its own
`description` and `type` where the source defines one — read those to the user
when they ask what a particular argument means, instead of guessing.

`required` is a floor, not the whole story: some optional fields are filled in
from other values rather than left empty. A SQL table asset, for example,
lists only `name` as required, and its `table_name` defaults to the asset
name. If a default like that would be wrong for the user's data, pass the
field explicitly.

## Step 3: the sibling directory gives you the asset types

Each type's asset surface is the set of JSON files in the directory named
after its connection schema. Every asset schema carries the asset's type token
under `properties.type`, and the factory that creates it is **`add_<token>_asset`
on the data source object** — that derivation is exact for every asset schema
the package ships, unlike the data-source factory names in step 1:

```python
asset_dir = SCHEMAS / schema_file.removesuffix(".json")

for entry in sorted(p.name for p in asset_dir.iterdir() if p.name.endswith(".json")):
    asset_schema = json.loads((asset_dir / entry).read_text())
    asset_type = asset_schema["properties"]["type"]["enum"][0]
    print(f"datasource.add_{asset_type}_asset(...)  required={asset_schema['required']}")
```

For `PostgresDatasource` that prints:

```text
datasource.add_query_asset(...)  required=['name', 'query']
datasource.add_table_asset(...)  required=['name']
```

The same call against `PandasFilesystemDatasource` enumerates its file-format
assets (`add_csv_asset`, `add_parquet_asset`, `add_excel_asset`, and so on),
and against `PandasDatasource` it includes `add_dataframe_asset`. Read the
directory rather than assuming which formats a given backend supports — the
file-based backends do not all carry the same set, and the SQL backends carry
dialect-specific asset types in some cases.

## Step 4: the asset object gives you the batch-definition surface

Batch definitions are the last link in the chain, and their available shapes
depend on the asset you actually created. Ask the asset object directly, after
you have it:

```python
batch_definition_factories = sorted(
    name
    for name in dir(asset)
    if name.startswith("add_batch_definition_")
)
print(batch_definition_factories)
```

Three shapes come up constantly, and they show the pattern:

| Asset | Available `add_batch_definition_*` |
| --- | --- |
| A file-format asset (e.g. a CSV asset) | `_daily`, `_monthly`, `_yearly`, `_path` |
| A SQL table or query asset | `_daily`, `_monthly`, `_yearly`, `_whole_table` |
| A dataframe asset | `_whole_dataframe` |

Note the `startswith("add_batch_definition_")` filter, with the trailing
underscore. It deliberately excludes the bare `add_batch_definition` method,
which takes a partitioner object you would have to construct and import
yourself. Always go through the named `add_batch_definition_<shape>` factories
instead — they build the partitioner for you, and they are the supported way
to express batching.

The time-based factories (`_daily`, `_monthly`, `_yearly`) need to know which
value to slice on, and that differs by asset family: a SQL asset takes the
`column` to partition on, while a file-format asset infers the date from the
file path and takes a `regex` describing it. The whole-collection shapes
(`_whole_table`, `_whole_dataframe`) take only a `name`; `_path` takes a name
and the specific `path` to pin the batch to. Don't guess between them — read
the factory's own signature, which is authoritative for the installed version
and costs nothing:

```python
import inspect

print(inspect.signature(asset.add_batch_definition_monthly))
```

## Choosing a type with the user

The catalog answers "what is possible"; the user answers "what do you have".
Three families cover the landscape, and naming them is usually enough to get a
decision quickly:

- **Files** — data sitting in a directory, a bucket, or a filesystem, read
  through pandas or Spark. Look for the types whose names carry a storage
  location (filesystem, S3, Google Cloud Storage, Azure Blob Storage, DBFS).
- **SQL** — data in a database or warehouse, reached by connection string.
  These types name the engine or dialect, plus a generic SQL type for anything
  reachable through a SQLAlchemy connection string that has no dedicated type.
- **Dataframes** — data already in memory in the user's own process, as a
  pandas or Spark dataframe. Use this when the user has the data loaded
  already, and remember that the configuration written for it carries no data:
  the dataframe is supplied per batch at retrieval time.

If the user's backend has no dedicated type, the generic SQL type is the
fallback for anything with a SQLAlchemy connection string — say so plainly
rather than reporting the backend as unsupported. If it genuinely isn't
reachable any of these ways, say that too, and don't improvise a substitute.

## When a type needs a driver or credentials it doesn't have

Many types depend on an optional driver package, a client library, or ambient
credentials that Great Expectations does not install or provide. Adding the
data source is where this surfaces, because the factory tests the connection
as part of the call — so a type that is present in the catalog is not thereby
proven usable in this environment.

The failure arrives as a `TestConnectionError` wrapping the underlying cause.
How informative that wrapped cause is varies a lot by backend, and it is worth
expecting both shapes:

- **Precise and actionable**, which is the common case. Connecting to BigQuery
  with no application credentials configured, for example, reports
  `SQLAlchemyCreateEngineError("Unable to create SQLAlchemy Engine: due to
  DefaultCredentialsError('Your default credentials were not found. ...')")`,
  including a documentation link. Relay a cause like this close to verbatim —
  it is more specific than anything you could paraphrase.
- **Terse to the point of empty.** Some backends surface only an exception type
  with no message at all — a Spark data source on a machine with no working
  Java runtime raises `TestConnectionError: ... due to PySparkRuntimeError()`,
  where the actual problem (Java is missing) appeared only as unstructured
  output from a subprocess. When the cause is this thin, say so honestly:
  name the backend, say the connection test failed without a usable message,
  and point at the most likely environment prerequisite for that backend
  rather than inventing a specific diagnosis.

Either way, follow `robustness.md`'s rule for reporting a failure — what
failed, why as far as it is known, and one concrete next step — and stop
there. Installing packages or provisioning credentials in the user's
environment is their call, not yours.
