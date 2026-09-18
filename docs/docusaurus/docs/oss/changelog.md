---
title: Changelog
slug: /core/changelog
description: Release notes for Great Expectations Core.
---

### Deprecation policy

GX Core follows [Semantic Versioning 2.0.0](https://semver.org/#semantic-versioning-200), including its [guidelines for deprecation](https://semver.org/#how-should-i-handle-deprecating-functionality).

When we deprecate public functionality, we will

- update our documentation to let you know about the change.
- issue a new minor release with the deprecation in place.

Before we completely remove the functionality in a new major release, there will be at least one minor release that contains the deprecation so that you can smoothly transition.

### Deprecation timeline

This table lists every deprecated item, the version that deprecated it, and the version that removes it; a row is never deleted, even after the removal ships.

| Deprecated | Since | Removal | Replacement |
| --- | --- | --- | --- |
| String values for numeric batch parameters (`year`, `month`, `day`, …) | 1.21.0 | 2.0.0 | Pass integers |
| `_atomic_prescriptive_template` | 0.15.43 | 1.17.1 |  |
| `str` support for `Validator.validate` `run_id` | 0.13.0 | 1.17.0 | `RunIdentifier` or dict |
| `ColumnMetricProvider` (and `DeprecatedMetaMetricProvider`) | 0.13.25 | 1.17.0 | `ColumnAggregateMetricProvider` |
| `Batch` args `data_context`, `datasource_name`, `batch_parameters`, `batch_kwargs` | 0.14.0 | 1.17.0 |  |
| `PandasDBFSDatasource` | 1.16.0 | 2.0.0 | `PandasFilesystemDatasource` |
| `SparkDBFSDatasource` | 1.16.0 | 2.0.0 | `SparkFilesystemDatasource` |
| `schema_name` argument of `TableAsset` / `add_table_asset` | 1.14.0 | 2.0.0 | Schema-qualified `table_name` |
| `DatabaseStoreBackend`, `TupleStoreBackend` family, `QueryStore`, `MetricStore` | 1.0.0 | 1.13.0 |  |
| String-style `row_condition` | 1.9.0 | 2.0.0 | `RowCondition` expression objects |
| `RuleBasedProfiler` | 1.0.0 | 1.5.1 |  |
| `DataContext.add_or_update_datasource` | 1.3.0 | 2.0.0 | `context.data_sources.add_*` / `update_*` |
| `context.get_datasource` | 1.1.2 | 2.0.0 | `context.data_sources.get` |
| `result_url` on `CheckpointResult` | 1.1.2 | 1.1.2 |  |
| `mostly` on `ExpectColumnUniqueValueCountToBeBetween` | 1.1.0 | 1.1.0 |  |
| `force_reuse_spark_context` argument of `SparkDFExecutionEngine` / Spark datasources | 1.0.0 | 2.0.0 | `spark_config` |
| `get_or_create_spark_application()` | 1.0.0 | 2.0.0 | Create the Spark session outside GX |
| `get_or_create_spark_session()` | 1.0.0 | 2.0.0 | Create the Spark session outside GX |
| `MapMetricProvider.is_sqlalchemy_metric_selectable` | 0.16.1 | 2.0.0 |  |
| `context.sources.delete_<type>` CRUD methods | 0.17.2 | 2.0.0 | `context.sources.delete` |
| V2 API style custom rendering | 0.13.28 | 2.0.0 |  |

### 1.23.0
* [BUGFIX] Cache the SQL execution engine across calls instead of rebuilding it every time ([#12148](https://github.com/great-expectations/great_expectations/pull/12148))
* [BUGFIX] query asset SQL ending in a comment fails validation ([#12124](https://github.com/great-expectations/great_expectations/pull/12124)) (thanks @nanjeshramesh)
* [BUGFIX] Wrap a query asset's SQL whole so Oracle does not add FROM DUAL ([#12162](https://github.com/great-expectations/great_expectations/pull/12162))
* [BUGFIX] TupleFilesystemStoreBackend reads with ambient locale encoding ([#12125](https://github.com/great-expectations/great_expectations/pull/12125)) (thanks @nanjeshramesh)
* [BUGFIX] Make ExpectColumnValueZScoresToBeLessThan pass rather than fail or raise on zero or undefined variance ([#12145](https://github.com/great-expectations/great_expectations/pull/12145)) (thanks @Star-cloud626, Claude Opus 5 (1M context))
* [BUGFIX] expect_column_values_to_be_unique raises KeyError on mixed-case column names ([#12180](https://github.com/great-expectations/great_expectations/pull/12180))
* [BUGFIX] Report an undefined SQLite standard deviation as None instead of raising ([#12168](https://github.com/great-expectations/great_expectations/pull/12168)) (thanks @siddharthgaur1, Claude Opus 5)
* [DOCS] Update repository links to the fivetran org ([#12126](https://github.com/great-expectations/great_expectations/pull/12126)) (thanks @iamfeldman)
* [MAINTENANCE] Declare metric values, render-content payloads, and metric keys as what they actually are ([#12116](https://github.com/great-expectations/great_expectations/pull/12116))
* [MAINTENANCE] Generalize the data source declaration record beyond SQL backends ([#12110](https://github.com/great-expectations/great_expectations/pull/12110))
* [MAINTENANCE] Pin the fluent datasource management API with a per-type CRUD contract suite ([#12141](https://github.com/great-expectations/great_expectations/pull/12141))
* [MAINTENANCE] Say what the shared fixture column types mean ([#12147](https://github.com/great-expectations/great_expectations/pull/12147))
* [MAINTENANCE] Type-check tests/test_utils.py, tests/actions/ and tests/checkpoint/ ([#12146](https://github.com/great-expectations/great_expectations/pull/12146)) (thanks @MannXo)
* [MAINTENANCE] Clean up check-actor-permissions and dead CI workflow code ([#12159](https://github.com/great-expectations/great_expectations/pull/12159))
* [MAINTENANCE] Bump browserslist from 4.28.1 to 4.28.8 in /docs/docusaurus ([#12155](https://github.com/great-expectations/great_expectations/pull/12155))
* [MAINTENANCE] Bump fast-uri from 3.1.5 to 3.1.7 in /docs/docusaurus ([#12151](https://github.com/great-expectations/great_expectations/pull/12151))
* [MAINTENANCE] Type-check tests/render ([#12152](https://github.com/great-expectations/great_expectations/pull/12152)) (thanks @Ryota-Di)
* [MAINTENANCE] Type-check tests/core/ #12130 ([#12140](https://github.com/great-expectations/great_expectations/pull/12140)) (thanks @AnandkumarMall)
* [MAINTENANCE] Type-check tests/execution_engine/partition_and_sample/ ([#12169](https://github.com/great-expectations/great_expectations/pull/12169)) (thanks @siddharthgaur1, Claude Opus 5)
* [MAINTENANCE] Bump colord from 2.9.3 to 2.10.0 in /docs/docusaurus ([#12170](https://github.com/great-expectations/great_expectations/pull/12170))
* [MAINTENANCE] Type-check tests/data_context/ ([#12171](https://github.com/great-expectations/great_expectations/pull/12171)) (thanks @nanjeshramesh)
* [MAINTENANCE] Remove unused checkpoint test fixtures ([#12174](https://github.com/great-expectations/great_expectations/pull/12174))
* [MAINTENANCE] Bump svgo from 3.3.4 to 3.3.5 in /docs/docusaurus ([#12175](https://github.com/great-expectations/great_expectations/pull/12175))
* [MAINTENANCE] Bump joi from 17.13.4 to 17.13.7 in /docs/docusaurus ([#12176](https://github.com/great-expectations/great_expectations/pull/12176))
* [MAINTENANCE] Publish the oracle extra ([#12091](https://github.com/great-expectations/great_expectations/pull/12091))
* [CONTRIB] Type-check validator tests ([#12149](https://github.com/great-expectations/great_expectations/pull/12149)) (thanks @yigitcan-ozturk)
* [CONTRIB] Remove the dead match_on value key from the not-match-like-pattern-list metric ([#12157](https://github.com/great-expectations/great_expectations/pull/12157)) (thanks @Star-cloud626, Claude Opus 5)
* [CONTRIB] [MAINTENANCE] Type-check the excluded modules under tests/integration/ ([#12173](https://github.com/great-expectations/great_expectations/pull/12173)) (thanks @adimalkar)

### 1.22.0
* [BUGFIX] Give the date-part string cast a length Oracle accepts ([#12102](https://github.com/great-expectations/great_expectations/pull/12102))
* [BUGFIX] Add an Oracle branch to the dialect-regex helper ([#12103](https://github.com/great-expectations/great_expectations/pull/12103))
* [BUGFIX] Render the derived-table alias in the form each grammar accepts ([#12104](https://github.com/great-expectations/great_expectations/pull/12104))
* [BUGFIX] Restore the metrics coverage MySQL, SQL Server and Redshift were silently missing ([#12107](https://github.com/great-expectations/great_expectations/pull/12107))
* [BUGFIX] Render Data Docs pages for results whose meta has no run_id ([#12098](https://github.com/great-expectations/great_expectations/pull/12098)) (thanks @MannXo)
* [BUGFIX] pass usedforsecurity=False on non-security md5 calls for FIPS hosts ([#12099](https://github.com/great-expectations/great_expectations/pull/12099)) (thanks @nanjeshramesh)
* [BUGFIX] Drop the taxi test table by name instead of scanning the database ([#12119](https://github.com/great-expectations/great_expectations/pull/12119))
* [BUGFIX] Stop add_store from crashing and truncating great_expectations.yml ([#12081](https://github.com/great-expectations/great_expectations/pull/12081))
* [DOCS] Teach users to install, use, and remove the agent skills bundled with GX ([#12074](https://github.com/great-expectations/great_expectations/pull/12074))
* [DOCS] Teach integer batch parameters across the documentation ([#12066](https://github.com/great-expectations/great_expectations/pull/12066))
* [DOCS] Restructure the agent skills page for progressive disclosure ([#12106](https://github.com/great-expectations/great_expectations/pull/12106))
* [MAINTENANCE] Add Oracle to the SQL test harness with live curated coverage ([#12085](https://github.com/great-expectations/great_expectations/pull/12085))
* [MAINTENANCE] Make the mypy configuration mean what it says ([#12112](https://github.com/great-expectations/great_expectations/pull/12112))
* [MAINTENANCE] Remove two structural blockers to type-checking the test tree ([#12113](https://github.com/great-expectations/great_expectations/pull/12113))
* [MAINTENANCE] Refuse silent relaxations of the type-check configuration ([#12115](https://github.com/great-expectations/great_expectations/pull/12115))
* [MAINTENANCE] Restore the S3 docs fixtures ([#12111](https://github.com/great-expectations/great_expectations/pull/12111))
* [MAINTENANCE] Request the docs-creds-needed backends that are live again ([#12114](https://github.com/great-expectations/great_expectations/pull/12114))
* [MAINTENANCE] Run the Azure Blob docs tests against live storage again ([#12117](https://github.com/great-expectations/great_expectations/pull/12117))
* [MAINTENANCE] Bound every apt call in the SQL Server ODBC driver install ([#12079](https://github.com/great-expectations/great_expectations/pull/12079))
* [MAINTENANCE] Add a marshmallow 4 CI lane ([#12118](https://github.com/great-expectations/great_expectations/pull/12118))
* [CONTRIB] Mask Azure connection-string AccountKey regardless of field order ([#12094](https://github.com/great-expectations/great_expectations/pull/12094)) (thanks @dkling-it, @hemalrajput18)
* [CONTRIB] Fix pandas column-pair validation with non-default indexes ([#12097](https://github.com/great-expectations/great_expectations/pull/12097)) (thanks @joebasrawi)
* [CONTRIB] add explanatory message to NotImplementedError for unsupported regex dialects ([#12109](https://github.com/great-expectations/great_expectations/pull/12109)) (thanks @ArjunPakhan)
* [CONTRIB] Support Marshmallow 4.x ([#12092](https://github.com/great-expectations/great_expectations/pull/12092)) (thanks @Dev-iL)

### 1.21.0
* [FEATURE] SQL Harness Backend Framework ([#12049](https://github.com/great-expectations/great_expectations/pull/12049))
* [FEATURE] Trino SQL backend test harness ([#12050](https://github.com/great-expectations/great_expectations/pull/12050))
* [FEATURE] ClickHouse SQL backend test harness ([#12053](https://github.com/great-expectations/great_expectations/pull/12053))
* [FEATURE] Ship agent-skill guidance for configuring data sources and expectations ([#12061](https://github.com/great-expectations/great_expectations/pull/12061))
* [FEATURE] Harden the data-source skill's driver, cadence, and example guidance ([#12062](https://github.com/great-expectations/great_expectations/pull/12062))
* [FEATURE] Gate project creation on the user having named the directory ([#12063](https://github.com/great-expectations/great_expectations/pull/12063))
* [FEATURE] Accept integers for numeric batch parameters on every datasource family ([#12065](https://github.com/great-expectations/great_expectations/pull/12065))
* [FEATURE] Route validated expectations onward into checkpoint orchestration ([#12068](https://github.com/great-expectations/great_expectations/pull/12068))
* [FEATURE] Make environment-affecting actions reachable-in-flow and mechanically gated ([#12073](https://github.com/great-expectations/great_expectations/pull/12073))
* [BUGFIX] Restore the install and test steps to py312-min-versions ([#12076](https://github.com/great-expectations/great_expectations/pull/12076))
* [MAINTENANCE] Bump dompurify from 3.4.12 to 3.4.13 in /docs/docusaurus ([#12048](https://github.com/great-expectations/great_expectations/pull/12048))
* [MAINTENANCE] Bump nanoid from 3.3.16 to 3.3.18 in /docs/docusaurus ([#12052](https://github.com/great-expectations/great_expectations/pull/12052))
* [MAINTENANCE] Bump mermaid from 11.15.0 to 11.16.1 in /docs/docusaurus ([#12047](https://github.com/great-expectations/great_expectations/pull/12047))
* [MAINTENANCE] Pin SingleStore dev image to 0.2.82 instead of :latest ([#12054](https://github.com/great-expectations/great_expectations/pull/12054))
* [MAINTENANCE] Read the GCS test bucket from a repository variable ([#12056](https://github.com/great-expectations/great_expectations/pull/12056))
* [MAINTENANCE] Restore the GCS datasource tests and run them in CI ([#12058](https://github.com/great-expectations/great_expectations/pull/12058))
* [MAINTENANCE] Restore the GCP credentials setup for the docs-snippets job ([#12057](https://github.com/great-expectations/great_expectations/pull/12057))
* [MAINTENANCE] Run the GCS docs snippet tests ([#12059](https://github.com/great-expectations/great_expectations/pull/12059))
* [MAINTENANCE] Surface the RFC threshold in the PR template, AGENTS.md, and a new check ([#12043](https://github.com/great-expectations/great_expectations/pull/12043))
* [MAINTENANCE] Use the upstream sqlalchemy-redshift dialect instead of the GX fork ([#12044](https://github.com/great-expectations/great_expectations/pull/12044))
* [MAINTENANCE] Drop the gx-redshift CI marker ([#12060](https://github.com/great-expectations/great_expectations/pull/12060))
* [MAINTENANCE] Add integration coverage for quoted schema names on PostgreSQL ([#12051](https://github.com/great-expectations/great_expectations/pull/12051))
* [MAINTENANCE] Create BigQuery test tables in the configured dataset and sweep tables, not datasets ([#12024](https://github.com/great-expectations/great_expectations/pull/12024))
* [MAINTENANCE] Ship version-matched expectation and datasource catalogs ([#12055](https://github.com/great-expectations/great_expectations/pull/12055))
* [MAINTENANCE] Sync SparkDBFSDatasource schema with its deprecation notice ([#12077](https://github.com/great-expectations/great_expectations/pull/12077))
* [MAINTENANCE] Remove the "How to Edit This Suite" button from Data Docs ([#12078](https://github.com/great-expectations/great_expectations/pull/12078))
* [CONTRIB] Add a great-expectations user-agent suffix to S3 clients ([#11937](https://github.com/great-expectations/great_expectations/pull/11937)) (thanks @goanpeca)
* [CONTRIB] Promote multicolumn values equal expectation ([#12018](https://github.com/great-expectations/great_expectations/pull/12018)) (thanks @AtomicGlance)
* [CONTRIB] Add ExpectColumnValuesToNotBeOutliers across Pandas, SQL, and Spark ([#12011](https://github.com/great-expectations/great_expectations/pull/12011)) (thanks @chavalasantosh)

### 1.20.0
* [BUGFIX] Support standing up a FileDataContext on a read-only filesystem ([#12000](https://github.com/fivetran/great_expectations/pull/12000))
* [BUGFIX] Narrow single-pass column_values.unique on SQLAlchemy (Redshift WLM) ([#11863](https://github.com/fivetran/great_expectations/pull/11863)) (thanks @leodrivera)
* [BUGFIX] deduplicate sql metric aliases to prevent view schema collisions (#10926) ([#11905](https://github.com/fivetran/great_expectations/pull/11905)) (thanks @TemidayoA)
* [BUGFIX] Report an unmet expectation when a column has no quantiles ([#12026](https://github.com/fivetran/great_expectations/pull/12026))
* [BUGFIX] Exclude nulls and fix the rank offset in the SQLite quantile metric ([#12008](https://github.com/fivetran/great_expectations/pull/12008)) (thanks @SreeramaYeshwanthGowd)
* [MAINTENANCE] Explain why a not-ready issue can't be self-claimed ([#11999](https://github.com/fivetran/great_expectations/pull/11999))
* [MAINTENANCE] Bump postcss from 8.5.12 to 8.5.25 in /docs/docusaurus ([#12013](https://github.com/fivetran/great_expectations/pull/12013))
* [MAINTENANCE] Bump brace-expansion from 1.1.16 to 1.1.18 in /docs/docusaurus ([#12014](https://github.com/fivetran/great_expectations/pull/12014))
* [MAINTENANCE] Namespace ephemeral SQL test schemas under gx_ci_test_ and fix cleanup regex charsets ([#12015](https://github.com/fivetran/great_expectations/pull/12015))
* [MAINTENANCE] Bump fast-uri from 3.1.4 to 3.1.5 in /docs/docusaurus ([#12019](https://github.com/fivetran/great_expectations/pull/12019))
* [MAINTENANCE] Defer the schema listing in TableAsset.test_connection to the failure path ([#12020](https://github.com/fivetran/great_expectations/pull/12020))
* [MAINTENANCE] BigQuery CI ([#12016](https://github.com/fivetran/great_expectations/pull/12016))
* [CONTRIB] Promote ExpectColumnValuesToMatchStrftimeFormat to supported-core ([#12009](https://github.com/fivetran/great_expectations/pull/12009)) (thanks @nanjeshramesh)

### 1.19.1
* [FEATURE] Self-hosted CLA status check ([#11985](https://github.com/fivetran/great_expectations/pull/11985))
* [BUGFIX] Pin actions/checkout to v4.3.1 across workflows ([#11988](https://github.com/fivetran/great_expectations/pull/11988))
* [BUGFIX] Sync CLA labels directly from the CLA check, not via the status webhook ([#11992](https://github.com/fivetran/great_expectations/pull/11992))
* [BUGFIX] Render id/pk-only unexpected indices instead of raising (fixes #11933) ([#11935](https://github.com/fivetran/great_expectations/pull/11935)) (thanks @anxkhn)
* [MAINTENANCE] Update CLA links ([#11974](https://github.com/fivetran/great_expectations/pull/11974))
* [MAINTENANCE] Ignore pyOpenSSL X509.get_subject deprecation warning for snowflake ([#11979](https://github.com/fivetran/great_expectations/pull/11979))
* [MAINTENANCE] CLA Enforcement ([#11980](https://github.com/fivetran/great_expectations/pull/11980))
* [MAINTENANCE] Update cla links ([#11982](https://github.com/fivetran/great_expectations/pull/11982))
* [MAINTENANCE] Report CLA status on merge-queue commits ([#11983](https://github.com/fivetran/great_expectations/pull/11983))
* [MAINTENANCE] enable redshift ci ([#11984](https://github.com/fivetran/great_expectations/pull/11984))
* [MAINTENANCE] Bump websocket-driver from 0.7.4 to 0.7.5 in /docs/docusaurus ([#11977](https://github.com/fivetran/great_expectations/pull/11977))
* [MAINTENANCE] Bump webpack-dev-server from 5.2.5 to 5.2.6 in /docs/docusaurus ([#11990](https://github.com/fivetran/great_expectations/pull/11990))
* [MAINTENANCE] pre-commit autoupdate (ruff 0.15.12 -> 0.15.15) ([#11895](https://github.com/fivetran/great_expectations/pull/11895))
* [MAINTENANCE] Assert store access in DatasourceDict just-in-time tests ([#11949](https://github.com/fivetran/great_expectations/pull/11949)) (thanks @anxkhn)
* [MAINTENANCE] Bump brace-expansion from 1.1.13 to 1.1.16 in /docs/docusaurus ([#11991](https://github.com/fivetran/great_expectations/pull/11991))
* [MAINTENANCE] Bump body-parser from 1.20.4 to 1.20.6 in /docs/docusaurus ([#11989](https://github.com/fivetran/great_expectations/pull/11989))
* [MAINTENANCE] Bump svgo from 3.3.3 to 3.3.4 in /docs/docusaurus ([#11994](https://github.com/fivetran/great_expectations/pull/11994))
* [MAINTENANCE] Bump immutable from 4.3.8 to 4.3.9 in /docs/docusaurus ([#11996](https://github.com/fivetran/great_expectations/pull/11996))
* [MAINTENANCE] Bump fast-uri from 3.1.2 to 3.1.4 in /docs/docusaurus ([#11995](https://github.com/fivetran/great_expectations/pull/11995))
* [MAINTENANCE] Bump dompurify from 3.4.11 to 3.4.12 in /docs/docusaurus ([#11997](https://github.com/fivetran/great_expectations/pull/11997))
* [MAINTENANCE] Add per-metric override hooks for SqlAlchemy row-retrieval providers ([#11998](https://github.com/fivetran/great_expectations/pull/11998))
* [CONTRIB] Update distinct values set Expectations to document observed_value contract ([#11934](https://github.com/fivetran/great_expectations/pull/11934)) (thanks @EshwarCVS)

### 1.19.0
* [FEATURE] Spark 4 support ([#11969](https://github.com/fivetran/great_expectations/pull/11969))
* [BUGFIX] Preserve date-like strings in SQL distinct value sets ([#11947](https://github.com/fivetran/great_expectations/pull/11947)) (thanks @yuricavalcanti06)
* [BUGFIX] Reject empty regex_list in ExpectColumnValuesToMatchRegexList ([#11958](https://github.com/fivetran/great_expectations/pull/11958)) (thanks @anxkhn)
* [BUGFIX] Fix broken link in issue assign welcome message ([#11961](https://github.com/fivetran/great_expectations/pull/11961))
* [DOCS] Enumerate Ephemeral Data Context use cases in type overview ([#11931](https://github.com/fivetran/great_expectations/pull/11931)) (thanks @zozo123)
* [MAINTENANCE] remove broken redirect entries ([#11936](https://github.com/fivetran/great_expectations/pull/11936))
* [MAINTENANCE] Replace broken Wistia embed with YouTube on GX Core intro page ([#11932](https://github.com/fivetran/great_expectations/pull/11932))
* [MAINTENANCE] Skip broken GCP SDK setup in docs-snippets during CI transition ([#11959](https://github.com/fivetran/great_expectations/pull/11959))
* [MAINTENANCE] Self-provision data in Snowflake connection tests ([#11945](https://github.com/fivetran/great_expectations/pull/11945))
* [MAINTENANCE] Contrib Docs ([#11950](https://github.com/fivetran/great_expectations/pull/11950))
* [MAINTENANCE] Add bot-enforced issue claiming and scope stale bot to needs-info issues ([#11957](https://github.com/fivetran/great_expectations/pull/11957))
* [MAINTENANCE] Bump launch-editor from 2.12.0 to 2.14.1 in /docs/docusaurus ([#11918](https://github.com/fivetran/great_expectations/pull/11918))
* [MAINTENANCE] clean up unused code ([#11717](https://github.com/fivetran/great_expectations/pull/11717))
* [MAINTENANCE] Extract type comparison logic into dedicated module ([#11798](https://github.com/fivetran/great_expectations/pull/11798)) 
* [MAINTENANCE] Bump dompurify from 3.4.3 to 3.4.11 in /docs/docusaurus ([#11917](https://github.com/fivetran/great_expectations/pull/11917))
* [MAINTENANCE] Make pyarrow compatibility type-ignore environment-independent ([#11966](https://github.com/fivetran/great_expectations/pull/11966))
* [MAINTENANCE] Bump joi from 17.13.3 to 17.13.4 in /docs/docusaurus ([#11914](https://github.com/fivetran/great_expectations/pull/11914))
* [MAINTENANCE] Remove dead expectation helpers and types/attributes ([#11765](https://github.com/fivetran/great_expectations/pull/11765))
* [MAINTENANCE] Databricks CI ([#11968](https://github.com/fivetran/great_expectations/pull/11968))
* [MAINTENANCE] Authenticate Databricks CI via OAuth M2M service principal ([#11970](https://github.com/fivetran/great_expectations/pull/11970))
* [MAINTENANCE] Remove Codecov from CI and documentation ([#11971](https://github.com/fivetran/great_expectations/pull/11971))

### 1.18.2
* [BUGFIX] Fix .rdd usage in Spark distinct-values metrics for Spark Connect compatibility ([#11922](https://github.com/fivetran/great_expectations/pull/11922))
* [DOCS] Fix typos in the Run a Validation Definition guide ([#11920](https://github.com/fivetran/great_expectations/pull/11920)) (thanks @zozo123)
* [MAINTENANCE] Fix pytest parametrize non-Collection iterable deprecation breaking scheduled CI ([#11921](https://github.com/fivetran/great_expectations/pull/11921))
* [MAINTENANCE] Fix BigQuery Python 3.13 collection error from NumPy 'generic' unit DeprecationWarning ([#11924](https://github.com/fivetran/great_expectations/pull/11924))
* [MAINTENANCE] Bump http-proxy-middleware from 2.0.9 to 2.0.10 in /docs/docusaurus ([#11927](https://github.com/fivetran/great_expectations/pull/11927))
* [MAINTENANCE] Bump webpack-dev-server from 5.2.3 to 5.2.5 in /docs/docusaurus ([#11926](https://github.com/fivetran/great_expectations/pull/11926))
* [MAINTENANCE] Bump @babel/core from 7.28.6 to 7.29.6 in /docs/docusaurus ([#11925](https://github.com/fivetran/great_expectations/pull/11925))

### 1.18.1
* [BUGFIX] Regex angle brackets not HTML-escaped in Data Docs ([#11909](https://github.com/great-expectations/great_expectations/pull/11909))
* [DOCS] Sync docs version label to released 1.18.0 ([#11900](https://github.com/great-expectations/great_expectations/pull/11900))
* [DOCS] Remove gx cloud docs site ([#11906](https://github.com/great-expectations/great_expectations/pull/11906))
* [MAINTENANCE] Temporarily skip bigquery tests ([#11908](https://github.com/great-expectations/great_expectations/pull/11908))
* [MAINTENANCE] Temporarily skip snowflake integration tests ([#11911](https://github.com/great-expectations/great_expectations/pull/11911))

### 1.18.0
* [MINORBUMP] GX Cloud shutdown: raise on CloudDataContext construction and remove cloud test suites ([#11894](https://github.com/great-expectations/great_expectations/pull/11894))
* [MAINTENANCE] Remove dead CodeSee architecture diagram workflow ([#11886](https://github.com/great-expectations/great_expectations/pull/11886))
* [MAINTENANCE] Accept Snowflake parameterized BINARY observed type in type-list expectation test ([#11892](https://github.com/great-expectations/great_expectations/pull/11892))
* [MAINTENANCE] Skip Microsoft Teams webhook integration tests during CI transition ([#11893](https://github.com/great-expectations/great_expectations/pull/11893))
* [MAINTENANCE] Pull CI Docker images directly from Docker Hub ([#11898](https://github.com/great-expectations/great_expectations/pull/11898))
* [MAINTENANCE] Skip external warehouse backend tests during CI transition ([#11896](https://github.com/great-expectations/great_expectations/pull/11896))
* [MAINTENANCE] Temporarily skip cloud object-store docs tests during CI transition ([#11897](https://github.com/great-expectations/great_expectations/pull/11897))

### 1.17.2
* [BUGFIX] Preserve boolean values passed to add_csv_asset (fixes #11206) ([#11867](https://github.com/great-expectations/great_expectations/pull/11867)) (thanks @EshwarCVS)
* [BUGFIX] Restore SQLAlchemy 1.4 compatibility in column_values_unique (fixes #11875) ([#11876](https://github.com/great-expectations/great_expectations/pull/11876)) (thanks @ranophoenix)
* [MAINTENANCE] [pre-commit.ci] pre-commit autoupdate ([#11864](https://github.com/great-expectations/great_expectations/pull/11864))
* [MAINTENANCE] Bump fast-uri from 3.1.0 to 3.1.2 in /docs/docusaurus ([#11872](https://github.com/great-expectations/great_expectations/pull/11872))
* [MAINTENANCE] Bump @babel/plugin-transform-modules-systemjs from 7.28.5 to 7.29.4 in /docs/docusaurus ([#11873](https://github.com/great-expectations/great_expectations/pull/11873))
* [MAINTENANCE] Bump mermaid from 11.12.2 to 11.15.0 in /docs/docusaurus ([#11874](https://github.com/great-expectations/great_expectations/pull/11874))

### 1.17.1
* [BUGFIX] Spark nested columns break unexpected_index_column_names (GX-3253) ([#11835](https://github.com/great-expectations/great_expectations/pull/11835))
* [BUGFIX] Spark column names with dots not recognized in BatchData (GX-3274) ([#11851](https://github.com/great-expectations/great_expectations/pull/11851))
* [BUGFIX] Fix docs-snippets CI broken by sqlalchemy-redshift 1.0.0 ([#11857](https://github.com/great-expectations/great_expectations/pull/11857))
* [BUGFIX] Pydantic Field alias not respected during expectation validation ([#11854](https://github.com/great-expectations/great_expectations/pull/11854))
* [BUGFIX] Avoid .toPandas() in Spark multicolumn unexpected values (#11633) ([#11861](https://github.com/great-expectations/great_expectations/pull/11861)) (thanks @smcl)
* [BUGFIX] Use uuid4 for test datasource names to avoid global-RNG collisions ([#11862](https://github.com/great-expectations/great_expectations/pull/11862))
* [BUGFIX] Data Docs uses vulnerable jQuery 3.4.1 ([#11856](https://github.com/great-expectations/great_expectations/pull/11856))
* [DOCS] Backfill 1.17.0 changelog entry ([#11865](https://github.com/great-expectations/great_expectations/pull/11865))
* [MAINTENANCE] Remove deprecated _atomic_prescriptive_template (v0.15.43) ([#11847](https://github.com/great-expectations/great_expectations/pull/11847))
* [MAINTENANCE] Temporarily run CI on maint/shard-marker-tests branch pushes ([#11858](https://github.com/great-expectations/great_expectations/pull/11858))
* [MAINTENANCE] Shard snowflake marker-tests + xdist for bigquery/databricks ([#11850](https://github.com/great-expectations/great_expectations/pull/11850))
* [MAINTENANCE] Bump postcss from 8.5.6 to 8.5.12 in /docs/docusaurus ([#11859](https://github.com/great-expectations/great_expectations/pull/11859))

### 1.17.0
* [FEATURE] Pass batch_definition_id to GET /expectation-parameters ([#11831](https://github.com/great-expectations/great_expectations/pull/11831))
* [BUGFIX] Fix pact-broker command not found in record-release CI step ([#11819](https://github.com/great-expectations/great_expectations/pull/11819))
* [BUGFIX] Fix SingleStoreDB expectations ([#11828](https://github.com/great-expectations/great_expectations/pull/11828))
* [BUGFIX] Fix Spark metric strftime validation failing with timezone-aware formats ([#11817](https://github.com/great-expectations/great_expectations/pull/11817))
* [BUGFIX] SQLAlchemy ignores strict_min/strict_max in column value lengths (GX-3252) ([#11836](https://github.com/great-expectations/great_expectations/pull/11836))
* [BUGFIX] Spark ignores strict_min/strict_max in column value lengths (GX-3252) ([#11834](https://github.com/great-expectations/great_expectations/pull/11834))
* [DOCS] expect column proportion of non-null values to be between supports forecasted range ([#11821](https://github.com/great-expectations/great_expectations/pull/11821))
* [DOCS] trino and bigquery ([#11747](https://github.com/great-expectations/great_expectations/pull/11747))
* [MAINTENANCE] Bump dompurify from 3.3.2 to 3.4.0 in /docs/docusaurus ([#11820](https://github.com/great-expectations/great_expectations/pull/11820))
* [MAINTENANCE] Add can-i-deploy check to cloud-tests CI ([#11801](https://github.com/great-expectations/great_expectations/pull/11801))
* [MAINTENANCE] bump jest-environment-jsdom 30.2.0 → 30.3.0 (CVE-2026-33671) ([#11823](https://github.com/great-expectations/great_expectations/pull/11823))
* [MAINTENANCE] fix minimatch 3.1.2→3.1.5 and lodash-es 4.17.x→4.18.1 in docs ([#11827](https://github.com/great-expectations/great_expectations/pull/11827))
* [MAINTENANCE] fix path-to-regexp 0.1.12→0.1.13 and picomatch 2.3.1→2.3.2 in docs (CVE-2026-4867, CVE-2026-33671) ([#11824](https://github.com/great-expectations/great_expectations/pull/11824))
* [MAINTENANCE] allow Can I deploy? step to continue on failure ([#11829](https://github.com/great-expectations/great_expectations/pull/11829))
* [MAINTENANCE] Move pact contract check into dedicated parallel job ([#11822](https://github.com/great-expectations/great_expectations/pull/11822))
* [MAINTENANCE] Remove deprecated str support for Validator.validate run_id ([#11826](https://github.com/great-expectations/great_expectations/pull/11826))
* [MAINTENANCE] Silence mypy assignment error after pyarrow 24.0.0 ([#11838](https://github.com/great-expectations/great_expectations/pull/11838))
* [MAINTENANCE] Remove DeprecatedMetaMetricProvider and ColumnMetricProvider ([#11832](https://github.com/great-expectations/great_expectations/pull/11832))
* [MAINTENANCE] Add singlestore documentation ([#11837](https://github.com/great-expectations/great_expectations/pull/11837))
* [MAINTENANCE] Backfill test on custom sql expectations ([#11844](https://github.com/great-expectations/great_expectations/pull/11844))
* [MAINTENANCE] Remove deprecated Batch args (data_context, datasource_name, batch_parameters, batch_kwargs) ([#11843](https://github.com/great-expectations/great_expectations/pull/11843))
* [MAINTENANCE] SingleStore quoted identifier support ([#11839](https://github.com/great-expectations/great_expectations/pull/11839))
* [MAINTENANCE] Init singlestore db when container is created ([#11842](https://github.com/great-expectations/great_expectations/pull/11842))
* [MAINTENANCE] Extend pact can-i-deploy retry window to 20 minutes ([#11846](https://github.com/great-expectations/great_expectations/pull/11846))

### 1.16.1
* [FEATURE] Add Pact contract tests for datasource API coverage gaps ([#11813](https://github.com/great-expectations/great_expectations/pull/11813))
* [BUGFIX] Fix ExpectColumnValuesToMatchStrftimeFormat failing with timezone-aware formats ([#11812](https://github.com/great-expectations/great_expectations/pull/11812)) (thanks @choinhet)
* [DOCS] Clarify Python version support in compatibility reference ([#11784](https://github.com/great-expectations/great_expectations/pull/11784)) (thanks @Adeyinka1)
* [MAINTENANCE] Update Pact contract tests to align with Mercury API and use isolated org/workspace ([#11797](https://github.com/great-expectations/great_expectations/pull/11797))
* [MAINTENANCE] Hardcode pact org/workspace IDs for contract test isolation ([#11808](https://github.com/great-expectations/great_expectations/pull/11808))
* [MAINTENANCE] Fix pact branch resolution for merge_group CI events ([#11810](https://github.com/great-expectations/great_expectations/pull/11810))
* [MAINTENANCE] Add Pact contract tests for data-context-variables GET and PUT ([#11803](https://github.com/great-expectations/great_expectations/pull/11803))
* [MAINTENANCE] Add Pact contract tests for validation-definition update and checkpoint expectation-parameters ([#11802](https://github.com/great-expectations/great_expectations/pull/11802))
* [MAINTENANCE] Add Pact contract tests for metric-runs POST and accounts/me GET ([#11804](https://github.com/great-expectations/great_expectations/pull/11804))
* [MAINTENANCE] [pre-commit.ci] pre-commit autoupdate ([#11779](https://github.com/great-expectations/great_expectations/pull/11779))
* [MAINTENANCE] Remove E2E docker-compose tests replaced by Pact contracts ([#11811](https://github.com/great-expectations/great_expectations/pull/11811))
* [MAINTENANCE] Add Pact record-release to PyPI publish workflow ([#11816](https://github.com/great-expectations/great_expectations/pull/11816))
* [MAINTENANCE] Bump follow-redirects from 1.15.11 to 1.16.0 in /docs/docusaurus ([#11815](https://github.com/great-expectations/great_expectations/pull/11815))

### 1.16.0
* [MINORBUMP] Deprecate DBFS datasources (GX-2543) ([#11759](https://github.com/great-expectations/great_expectations/pull/11759))
* [FEATURE] Remove deprecated legacy Pact contract tests (GX-3023) ([#11768](https://github.com/great-expectations/great_expectations/pull/11768))
* [FEATURE] Migrate pact-python v2 → v3 (GX-3024) ([#11769](https://github.com/great-expectations/great_expectations/pull/11769))
* [FEATURE] Add client-driven Pact contracts for validation definition and checkpoint CRUD (GX-2730) ([#11757](https://github.com/great-expectations/great_expectations/pull/11757))
* [FEATURE] Add client-driven Pact contracts for expectation suite CRUD (GX-2729) ([#11756](https://github.com/great-expectations/great_expectations/pull/11756))
* [FEATURE] Add client-driven Pact contracts for datasource CRUD (GX-2727) ([#11754](https://github.com/great-expectations/great_expectations/pull/11754))
* [FEATURE] Add multi-step workflow contract test (GX-2731) ([#11783](https://github.com/great-expectations/great_expectations/pull/11783))
* [FEATURE] Support `column.unique_proportion` in metric list runs ([#11786](https://github.com/great-expectations/great_expectations/pull/11786))
* [BUGFIX] Fix suite freshness check after add in ephemeral context (GX-2891) ([#11758](https://github.com/great-expectations/great_expectations/pull/11758))
* [BUGFIX] Fix unclosed SQLite connections causing ResourceWarning on Python 3.13 ([#11766](https://github.com/great-expectations/great_expectations/pull/11766))
* [BUGFIX] Pin invoke==3.0.0 to avoid breaking change in 3.0.2 ([#11781](https://github.com/great-expectations/great_expectations/pull/11781))
* [BUGFIX] Fix default exact_match value in ExpectTableColumnsToMatchSet renderers ([#11785](https://github.com/great-expectations/great_expectations/pull/11785))
* [DOCS] Jira integration ([#11741](https://github.com/great-expectations/great_expectations/pull/11741))
* [DOCS] teams integration ([#11761](https://github.com/great-expectations/great_expectations/pull/11761))
* [DOCS] Hide magic-comment lines when line numbers are enabled ([#11731](https://github.com/great-expectations/great_expectations/pull/11731))
* [MAINTENANCE] Remove dead code: profile module ([#11763](https://github.com/great-expectations/great_expectations/pull/11763))
* [MAINTENANCE] Bump lodash from 4.17.23 to 4.18.1 in /docs/docusaurus ([#11776](https://github.com/great-expectations/great_expectations/pull/11776))
* [MAINTENANCE] Add pact-broker publish step to CI (GX-3025) ([#11775](https://github.com/great-expectations/great_expectations/pull/11775))
* [MAINTENANCE] Fix pact-broker publish step in CI ([#11787](https://github.com/great-expectations/great_expectations/pull/11787))
* [MAINTENANCE] Fix pact publish to use PR head SHA ([#11790](https://github.com/great-expectations/great_expectations/pull/11790))
* [MAINTENANCE] Bump brace-expansion from 1.1.12 to 1.1.13 in /docs/docusaurus ([#11777](https://github.com/great-expectations/great_expectations/pull/11777))
* [MAINTENANCE] Skip code CI jobs for docs-only PRs ([#11792](https://github.com/great-expectations/great_expectations/pull/11792))
* [MAINTENANCE] Increase SQL test connection pool size ([#11793](https://github.com/great-expectations/great_expectations/pull/11793))
* [MAINTENANCE] Use pact regex matcher for Gx-Version header in contract tests ([#11791](https://github.com/great-expectations/great_expectations/pull/11791))
* [MAINTENANCE] Skip pact publish on release tag CI runs ([#11796](https://github.com/great-expectations/great_expectations/pull/11796))

### 1.15.2
* [FEATURE] Refactor rest_contracts/conftest.py for client-driven Pact testing (GX-2725) ([#11753](https://github.com/great-expectations/great_expectations/pull/11753))
* [DOCS] Small wording change ([#11715](https://github.com/great-expectations/great_expectations/pull/11715))
* [DOCS] Add documentation for ValidationDefinition.get_unexpected_rows() ([#11712](https://github.com/great-expectations/great_expectations/pull/11712))
* [MAINTENANCE] Add generic sql test harness ([#11718](https://github.com/great-expectations/great_expectations/pull/11718))
* [MAINTENANCE] update schema names to be unique to prevent collision between CI runs ([#11733](https://github.com/great-expectations/great_expectations/pull/11733))
* [MAINTENANCE] Pin localstack to 4.14.0 ([#11740](https://github.com/great-expectations/great_expectations/pull/11740))
* [MAINTENANCE] Bump flatted from 3.3.3 to 3.4.2 in /docs/docusaurus ([#11737](https://github.com/great-expectations/great_expectations/pull/11737))
* [MAINTENANCE] CI improvements ([#11743](https://github.com/great-expectations/great_expectations/pull/11743))
* [MAINTENANCE] [pre-commit.ci] pre-commit autoupdate ([#11582](https://github.com/great-expectations/great_expectations/pull/11582))
* [MAINTENANCE] Bump yaml from 1.10.2 to 1.10.3 in /docs/docusaurus ([#11746](https://github.com/great-expectations/great_expectations/pull/11746))
* [MAINTENANCE] ci health report script ([#11751](https://github.com/great-expectations/great_expectations/pull/11751))
* [CONTRIB] add BigQuery datasource methods to sources.pyi stub file ([#11736](https://github.com/great-expectations/great_expectations/pull/11736)) (thanks @Julian901)

### 1.15.1
* [DOCS] Expectation history ([#11704](https://github.com/great-expectations/great_expectations/pull/11704))
* [MAINTENANCE] remove nested actions format ([#11713](https://github.com/great-expectations/great_expectations/pull/11713))
* [MAINTENANCE] increase expectation parameter timeout ([#11716](https://github.com/great-expectations/great_expectations/pull/11716))

### 1.15.0
* [MINORBUMP] SQL Server and Fabric Data Sources ([#11686](https://github.com/great-expectations/great_expectations/pull/11686))
* [MINORBUMP] Add ValidationDefinition.get_unexpected_rows() ([#11711](https://github.com/great-expectations/great_expectations/pull/11711))
* [BUGFIX] retry individual metrics when bulk resolution fails ([#11708](https://github.com/great-expectations/great_expectations/pull/11708))
* [DOCS] reflect changes to Validate button ([#11691](https://github.com/great-expectations/great_expectations/pull/11691))
* [DOCS] loose ends for new result format option ([#11705](https://github.com/great-expectations/great_expectations/pull/11705))
* [DOCS] Set workspace ID for the agent ([#11709](https://github.com/great-expectations/great_expectations/pull/11709))
* [DOCS] DOC-1168 - How to edit expectations using the API ([#11697](https://github.com/great-expectations/great_expectations/pull/11697))
* [DOCS] Slack alerts ([#11681](https://github.com/great-expectations/great_expectations/pull/11681))
* [MAINTENANCE] Bump immutable from 4.3.7 to 4.3.8 in /docs/docusaurus ([#11703](https://github.com/great-expectations/great_expectations/pull/11703))
* [MAINTENANCE] Bump svgo from 3.3.2 to 3.3.3 in /docs/docusaurus ([#11701](https://github.com/great-expectations/great_expectations/pull/11701))
* [MAINTENANCE] Bump dompurify from 3.3.1 to 3.3.2 in /docs/docusaurus ([#11706](https://github.com/great-expectations/great_expectations/pull/11706))
* [MAINTENANCE] Suppress mypy assignment errors in Trino compatibility module ([#11707](https://github.com/great-expectations/great_expectations/pull/11707))

### 1.14.0
* [FEATURE] Add `trust_server_certificate` to `SQLServerDatasource` ([#11694](https://github.com/great-expectations/great_expectations/pull/11694))
* [DOCS] Add ServiceNow to email alerts Cloud documentation ([#11669](https://github.com/great-expectations/great_expectations/pull/11669))
* [MAINTENANCE] Bump qs from 6.14.1 to 6.14.2 in /docs/docusaurus ([#11660](https://github.com/great-expectations/great_expectations/pull/11660))
* [MAINTENANCE] Improve error message on ConfigStr substitution ([#11693](https://github.com/great-expectations/great_expectations/pull/11693))
* [MAINTENANCE] Add sentry error tracking for the Doc Site ([#11695](https://github.com/great-expectations/great_expectations/pull/11695))
* [MAINTENANCE] Install ODBC driver in `docs-creds-needed` ([#11698](https://github.com/great-expectations/great_expectations/pull/11698))
* [MAINTENANCE] Deprecate `schema_name` on all `TableAsset`s ([#11689](https://github.com/great-expectations/great_expectations/pull/11689))

### 1.13.0
* [MINORBUMP] `ExpectColumnDistinctValuesToBeInSet` with database-pushed comparison ([#11614](https://github.com/great-expectations/great_expectations/pull/11614))
* [MINORBUMP] `ExpectColumnDistinctValuesToContainSet` with database-pushed comparison ([#11615](https://github.com/great-expectations/great_expectations/pull/11615))
* [MINORBUMP] `ExpectColumnDistinctValuesToEqualSet` with database-pushed comparison ([#11616](https://github.com/great-expectations/great_expectations/pull/11616))
* [FEATURE] Auto-strip ORDER BY for MSSQL COUNT(*) subqueries ([#11670](https://github.com/great-expectations/great_expectations/pull/11670))
* [FEATURE] Add `FabricDatasource` ([#11685](https://github.com/great-expectations/great_expectations/pull/11685))
* [BUGFIX] Fix Databricks identifier quoting in batch query compilation. ([#11671](https://github.com/great-expectations/great_expectations/pull/11671))
* [BUGFIX] Roll back connection after failed retry in _execute_query_with_recovery to prevent SQL Server teardown hang ([#11680](https://github.com/great-expectations/great_expectations/pull/11680))
* [DOCS] ExpectAI for the agent ([#11644](https://github.com/great-expectations/great_expectations/pull/11644))
* [DOCS] fix ExpectAI for the agent prereqs ([#11678](https://github.com/great-expectations/great_expectations/pull/11678))
* [MAINTENANCE] Add azure ad service principal auth connection details ([#11653](https://github.com/great-expectations/great_expectations/pull/11653))
* [MAINTENANCE] Add `SQLServerDatasource` schema ([#11662](https://github.com/great-expectations/great_expectations/pull/11662))
* [MAINTENANCE] Remove unsupported Entra ID Password authentication ([#11665](https://github.com/great-expectations/great_expectations/pull/11665))
* [MAINTENANCE] Human-readable MSSQL test connection exceptions ([#11661](https://github.com/great-expectations/great_expectations/pull/11661))
* [MAINTENANCE] Only run python 3.13 marker tests on PRs ([#11666](https://github.com/great-expectations/great_expectations/pull/11666))
* [MAINTENANCE] Rename MSSQL references to SQL Server for brand consistency ([#11674](https://github.com/great-expectations/great_expectations/pull/11674))
* [MAINTENANCE] Avoid unnecessary _get_default_value() calls for non-field keys ([#11626](https://github.com/great-expectations/great_expectations/pull/11626)) (thanks @jni-bot)
* [MAINTENANCE] Remove problematic runtime context fixture ([#11683](https://github.com/great-expectations/great_expectations/pull/11683))
* [MAINTENANCE] Remove Pandas Upper Pin ([#11677](https://github.com/great-expectations/great_expectations/pull/11677))
* [MAINTENANCE] Normalize SQL Server column type metrics ([#11684](https://github.com/great-expectations/great_expectations/pull/11684))
* [MAINTENANCE] remove deprecated store backends ([#11675](https://github.com/great-expectations/great_expectations/pull/11675))

### 1.12.3
* [MINORBUMP] Add support for pd.Timestamp for datetime comparison operations ([#11637](https://github.com/great-expectations/great_expectations/pull/11637)) (thanks @subediparas5)
* [FEATURE] Add sql server types stubs and use api in integration tests ([#11643](https://github.com/great-expectations/great_expectations/pull/11643))
* [FEATURE] MSSQL support for UnexpectedRowsExpectation ([#11646](https://github.com/great-expectations/great_expectations/pull/11646))
* [FEATURE] SQL Server Azure AD password authentication ([#11645](https://github.com/great-expectations/great_expectations/pull/11645))
* [FEATURE] MSSQL schema support ([#11649](https://github.com/great-expectations/great_expectations/pull/11649))
* [FEATURE] Support asymmetric quoted identifiers in dialect quoting ([#11652](https://github.com/great-expectations/great_expectations/pull/11652))
* [BUGFIX] Remove table domain key from ExpectColumnToExist ([#11630](https://github.com/great-expectations/great_expectations/pull/11630))
* [BUGFIX] Fix missing unexpected_index_query for ExpectCompoundColumnsToBeUnique on SQL ([#11639](https://github.com/great-expectations/great_expectations/pull/11639))
* [DOCS] Agent request next steps ([#11619](https://github.com/great-expectations/great_expectations/pull/11619))
* [DOCS] define asterisks in core result format docs ([#11631](https://github.com/great-expectations/great_expectations/pull/11631))
* [DOCS] Fix link to expect_table_row_count_to_equal_other_table in documentation ([#11634](https://github.com/great-expectations/great_expectations/pull/11634)) (thanks @teixeirazeus)
* [DOCS] Email alerts ([#11628](https://github.com/great-expectations/great_expectations/pull/11628))
* [DOCS] Revise contribution guidelines and readiness criteria ([#11638](https://github.com/great-expectations/great_expectations/pull/11638)) (thanks @adeola-ak)
* [DOCS] Add an Expectation using the GX Cloud API ([#11567](https://github.com/great-expectations/great_expectations/pull/11567))
* [DOCS] remove info about deprecated DBFS ([#11648](https://github.com/great-expectations/great_expectations/pull/11648))
* [MAINTENANCE] Remove duplicate flaky test ([#11623](https://github.com/great-expectations/great_expectations/pull/11623))
* [MAINTENANCE] Bump diff from 3.5.0 to 3.5.1 in /docs/docusaurus ([#11627](https://github.com/great-expectations/great_expectations/pull/11627))
* [MAINTENANCE] Add database-pushdown metrics for distinct values set comparisons ([#11629](https://github.com/great-expectations/great_expectations/pull/11629))
* [MAINTENANCE] Bump webpack from 5.94.0 to 5.104.1 in /docs/docusaurus ([#11636](https://github.com/great-expectations/great_expectations/pull/11636))
* [MAINTENANCE] `SQLServerDatasource` with SQL Server authentication ([#11640](https://github.com/great-expectations/great_expectations/pull/11640))
* [MAINTENANCE] Add `start_period` to mercury healthcheck to prevent flaky CI failures ([#11655](https://github.com/great-expectations/great_expectations/pull/11655))
* [MAINTENANCE] Bump docker compose timeout to 3 min ([#11659](https://github.com/great-expectations/great_expectations/pull/11659))
* [MAINTENANCE] Dispose of mssql connections in integration tests ([#11663](https://github.com/great-expectations/great_expectations/pull/11663))

### 1.11.3
* [BUGFIX] Fix Redshift fallback column detection for schema-qualified tables ([#11606](https://github.com/great-expectations/great_expectations/pull/11606)) (thanks @jni-bot)
* [BUGFIX] Update isinstance check for ColumnElement in SqlAlchemyExecutionEngine ([#11612](https://github.com/great-expectations/great_expectations/pull/11612)) (thanks @subediparas5)
* [DOCS] Update airflow provider refs ([#11621](https://github.com/great-expectations/great_expectations/pull/11621))
* [DOCS] Atlan integration ([#11580](https://github.com/great-expectations/great_expectations/pull/11580))
* [MAINTENANCE] Fix flaky test by removing sqlite dependency ([#11618](https://github.com/great-expectations/great_expectations/pull/11618))
* [MAINTENANCE] Remove references to v0 api in dockerfile ([#11624](https://github.com/great-expectations/great_expectations/pull/11624))
* [MAINTENANCE] Bump lodash from 4.17.21 to 4.17.23 in /docs/docusaurus ([#11608](https://github.com/great-expectations/great_expectations/pull/11608))

### 1.11.2
* [DOCS] RCA result format ([#11596](https://github.com/great-expectations/great_expectations/pull/11596))
* [MAINTENANCE] Upper bound pandas to be below 3.0.0 ([#11607](https://github.com/great-expectations/great_expectations/pull/11607))

### 1.11.1
* [BUGFIX] Include Expectation ID in equality ([#11593](https://github.com/great-expectations/great_expectations/pull/11593))
* [BUGFIX] fix CustomSQL & MultiSource row-level result population ([#11601](https://github.com/great-expectations/great_expectations/pull/11601))
* [MAINTENANCE] Use run_fastapi.py to launch mercury v1 ([#11599](https://github.com/great-expectations/great_expectations/pull/11599))
* [MAINTENANCE] Fix npm security vulnerabilities in docusaurus ([#11600](https://github.com/great-expectations/great_expectations/pull/11600))
* [CONTRIB] Fix typing export for get_context ([#11578](https://github.com/great-expectations/great_expectations/pull/11578)) (thanks @ipriyankalimbad)

### 1.11.0
* [MINORBUMP] Format `unexpected_rows` as dicts in map expectation validation results ([#11591](https://github.com/great-expectations/great_expectations/pull/11591))
* [BUGFIX] batch.columns() returns empty list for Redshift batches ([#11534](https://github.com/great-expectations/great_expectations/pull/11534)) (thanks @leodrivera)
* [DOCS] reframe and clarify Data Source limitations ([#11570](https://github.com/great-expectations/great_expectations/pull/11570))
* [DOCS] Prevent copying hidden lines from code blocks when pressing copy button ([#11571](https://github.com/great-expectations/great_expectations/pull/11571))
* [DOCS] remove temporary row conditions notes ([#11581](https://github.com/great-expectations/great_expectations/pull/11581))
* [DOCS] remove beta from ExpectAI ([#11590](https://github.com/great-expectations/great_expectations/pull/11590))
* [MAINTENANCE] Improve local type checking developer experience ([#11574](https://github.com/great-expectations/great_expectations/pull/11574))
* [MAINTENANCE] Add `--pty` and `--no-pty` flags to `invoke deps` ([#11586](https://github.com/great-expectations/great_expectations/pull/11586))
* [MAINTENANCE] Serialize `unexpected_rows` for all Map expectations when opt-in flag is provided ([#11583](https://github.com/great-expectations/great_expectations/pull/11583))
* [MAINTENANCE] Ignore `DeprecationWarning` emitted by deps ([#11587](https://github.com/great-expectations/great_expectations/pull/11587))
* [MAINTENANCE] Include SUMMARY in result_format query support ([#11594](https://github.com/great-expectations/great_expectations/pull/11594))

### 1.10.0
* [FEATURE] Support query and PK columns on BOOLEAN_ONLY and BASIC ([#11563](https://github.com/great-expectations/great_expectations/pull/11563))
* [DOCS] remove temporary severity note ([#11564](https://github.com/great-expectations/great_expectations/pull/11564))
* [DOCS] Cloud result format ([#11558](https://github.com/great-expectations/great_expectations/pull/11558))
* [DOCS] data health dashboard metric filters ([#11529](https://github.com/great-expectations/great_expectations/pull/11529))
* [MAINTENANCE] Fix add_dataframe_asset docstring for spark ([#11561](https://github.com/great-expectations/great_expectations/pull/11561))
* [MAINTENANCE] Fix flaky sqlite ResourceWarning ([#11562](https://github.com/great-expectations/great_expectations/pull/11562))
* [MAINTENANCE] Bump ruff version ([#11568](https://github.com/great-expectations/great_expectations/pull/11568))
* [MAINTENANCE] Don't fail CI if codecov upload fails ([#11569](https://github.com/great-expectations/great_expectations/pull/11569))
* [MAINTENANCE] Filter out google warning about using python 3.10 ([#11572](https://github.com/great-expectations/great_expectations/pull/11572))

### 1.9.3
* [FEATURE] infer primary keys during column_types metric fetch ([#11554](https://github.com/great-expectations/great_expectations/pull/11554))
* [BUGFIX] Prevent FROM DUAL from being added to a properly formatted ORACLE SQL query when using SQLAlchemy ([#11538](https://github.com/great-expectations/great_expectations/pull/11538)) (thanks @konnor-b)
* [DOCS] asset history ([#11543](https://github.com/great-expectations/great_expectations/pull/11543))
* [DOCS] typos on manage_expectations.md ([#11547](https://github.com/great-expectations/great_expectations/pull/11547))
* [DOCS] combined compatibility reference updates ([#11555](https://github.com/great-expectations/great_expectations/pull/11555))
* [DOCS] unexpected_rows ([#11553](https://github.com/great-expectations/great_expectations/pull/11553))
* [MAINTENANCE] pre-commit autoupdate ([#11539](https://github.com/great-expectations/great_expectations/pull/11539))
* [MAINTENANCE] Fix build_docs invocation of invoke ([#11545](https://github.com/great-expectations/great_expectations/pull/11545))
* [MAINTENANCE] Bump ruff to 0.14.8 ([#11550](https://github.com/great-expectations/great_expectations/pull/11550))
* [MAINTENANCE] restore null columns to rendered_content tables on multi-source expectations ([#11548](https://github.com/great-expectations/great_expectations/pull/11548))
* [MAINTENANCE] ensure sqlite tests cleanup connections ([#11552](https://github.com/great-expectations/great_expectations/pull/11552))
* [MAINTENANCE] Bump mypy to 0.19.0 ([#11551](https://github.com/great-expectations/great_expectations/pull/11551))
* [MAINTENANCE] Update ruff pre-commit and remove TCH001 from tests ruff ignore list ([#11557](https://github.com/great-expectations/great_expectations/pull/11557))

### 1.9.2
* [DOCS] validations with the Cloud API ([#11400](https://github.com/great-expectations/great_expectations/pull/11400))
* [DOCS] remove "read-only" deployment pattern as a misnomer ([#11533](https://github.com/great-expectations/great_expectations/pull/11533))
* [DOCS] DOC-1180 - Add documentation for Custom Actions in GX Cloud ([#11521](https://github.com/great-expectations/great_expectations/pull/11521))
* [DOCS] add dependencies to compatibility reference ([#11530](https://github.com/great-expectations/great_expectations/pull/11530))
* [MAINTENANCE] Warn when snowflake pkey exists in kwargs ([#11520](https://github.com/great-expectations/great_expectations/pull/11520))
* [MAINTENANCE] pin posthog-docusaurus ([#11531](https://github.com/great-expectations/great_expectations/pull/11531))
* [MAINTENANCE] Bump node-forge from 1.3.1 to 1.3.2 in /docs/docusaurus ([#11536](https://github.com/great-expectations/great_expectations/pull/11536))
* [MAINTENANCE] Reenable stale bot for PRs ([#11544](https://github.com/great-expectations/great_expectations/pull/11544))
* [MAINTENANCE] Bump mdast-util-to-hast from 13.2.0 to 13.2.1 in /docs/docusaurus ([#11541](https://github.com/great-expectations/great_expectations/pull/11541))
* [MAINTENANCE] Bump express from 4.21.2 to 4.22.1 in /docs/docusaurus ([#11540](https://github.com/great-expectations/great_expectations/pull/11540))
* [MAINTENANCE] pre-commit autoupdate ([#11539](https://github.com/great-expectations/great_expectations/pull/11539))

### 1.9.1
* [DOCS] clarify language on deploy the GX agent ([#11518](https://github.com/great-expectations/great_expectations/pull/11518))
* [MAINTENANCE] Update exclude list ([#11517](https://github.com/great-expectations/great_expectations/pull/11517))
* [MAINTENANCE] Deprecate string-style `row_condition`s ([#11515](https://github.com/great-expectations/great_expectations/pull/11515))
* [MAINTENANCE] Databricks SQLAlchemy 2.0 transaction handling and connection recovery ([#11524](https://github.com/great-expectations/great_expectations/pull/11524))
* [MAINTENANCE] [pre-commit.ci] pre-commit autoupdate ([#11502](https://github.com/great-expectations/great_expectations/pull/11502))

### 1.9.0 (2025-11-07)

Compatibility: Python `<3.14,>=3.9` → `<3.14,>=3.10`; `numpy` removed (`python_version == "3.9"`); `pandas` removed (`python_version == "3.9"`)

#### Highlights

- **Row conditions: documented, importable, and rendered in Data Docs** — Row conditions are now a supported way to scope an Expectation to a subset of rows. The condition classes (including `Column` and the comparison, nullity, and boolean conditions) are part of the public API and are imported from `great_expectations.expectations.row_conditions`; the previous `great_expectations.expectations.conditions` import path still works. Conditions are validated more strictly (an in/not-in parameter must be an iterable whose members share a single type, and boolean members are rejected), a bare string condition is always turned into a condition object even when no condition parser is given, and Data Docs now renders every condition when an Expectation carries more than one. New documentation pages, screenshots, and notes on the minimum GX Cloud API and agent versions required for certain row-condition features round this out. ([#11478](https://github.com/fivetran/great_expectations/pull/11478), [#11494](https://github.com/fivetran/great_expectations/pull/11494), [#11497](https://github.com/fivetran/great_expectations/pull/11497), [#11500](https://github.com/fivetran/great_expectations/pull/11500), [#11504](https://github.com/fivetran/great_expectations/pull/11504), [#11506](https://github.com/fivetran/great_expectations/pull/11506), [#11507](https://github.com/fivetran/great_expectations/pull/11507), [#11509](https://github.com/fivetran/great_expectations/pull/11509), [#11511](https://github.com/fivetran/great_expectations/pull/11511), [#11512](https://github.com/fivetran/great_expectations/pull/11512))

  ```python
  from great_expectations.expectations.row_conditions import Column

  condition = Column("age") > 21
  ```

- **Python 3.10 is now the minimum supported version** — Great Expectations no longer supports Python 3.9. Install on Python 3.10 or newer; the documentation now states 3.10 as the minimum. ([#11501](https://github.com/fivetran/great_expectations/pull/11501), [#11485](https://github.com/fivetran/great_expectations/pull/11485))

- **`unexpected_index_column_names` returned by ExpectColumnValuesToNotBeNull** — When you request unexpected index columns in `result_format`, ExpectColumnValuesToNotBeNull now includes `unexpected_index_column_names` in its validation result, matching the other column-value Expectations. ([#11513](https://github.com/fivetran/great_expectations/pull/11513))

  ```python
  result_format={"result_format": "COMPLETE", "unexpected_index_column_names": ["customer_id"]}
  ```

#### Changes

##### Bug fixes

- ExpectColumnValuesToNotBeNull now includes `unexpected_index_column_names` in its validation results when they are requested through `result_format`. ([#11513](https://github.com/fivetran/great_expectations/pull/11513))

##### Docs

- Documented the minimum GX Cloud API and agent versions required to use certain row-condition capabilities. ([#11512](https://github.com/fivetran/great_expectations/pull/11512))
- Updated the documented minimum supported Python version to 3.10. ([#11485](https://github.com/fivetran/great_expectations/pull/11485))
- Added screenshots to the row conditions documentation. ([#11509](https://github.com/fivetran/great_expectations/pull/11509))
- Added documentation and code samples for using row conditions to scope Expectations to a subset of rows. ([#11478](https://github.com/fivetran/great_expectations/pull/11478))

<details>
<summary>Maintenance</summary>

- Removed the discontinued Common Room script from the documentation site and captured documentation page views directly with PostHog. ([#11514](https://github.com/fivetran/great_expectations/pull/11514))
- Dropped support for Python 3.9; Great Expectations now requires Python 3.10 or newer. ([#11501](https://github.com/fivetran/great_expectations/pull/11501))
- Continuous integration now runs against a mock LaunchDarkly server instead of a live feature-flag service. ([#11510](https://github.com/fivetran/great_expectations/pull/11510))
- The row condition subclasses are now part of the documented public API. ([#11511](https://github.com/fivetran/great_expectations/pull/11511))
- Restored page-view capture on the documentation site so single-page navigation is tracked again. ([#11508](https://github.com/fivetran/great_expectations/pull/11508))
- Data Docs now renders every condition when an Expectation is scoped by more than one row condition. ([#11507](https://github.com/fivetran/great_expectations/pull/11507))
- A row condition supplied as a string is now always converted into a condition object, including when no condition parser is specified. ([#11504](https://github.com/fivetran/great_expectations/pull/11504))
- The row conditions `Column` class and its siblings are now imported from `great_expectations.expectations.row_conditions`; the previous `great_expectations.expectations.conditions` import path continues to work. ([#11506](https://github.com/fivetran/great_expectations/pull/11506))
- Suppressed the boto warning about the deprecation of Python 3.9 support. ([#11505](https://github.com/fivetran/great_expectations/pull/11505))
- Snowflake tests now authenticate with key-pair authentication. ([#11498](https://github.com/fivetran/great_expectations/pull/11498))
- Boolean values are no longer accepted as members of the parameter passed to `Column.is_in()` and `Column.is_not_in()`. ([#11500](https://github.com/fivetran/great_expectations/pull/11500))
- Comparison conditions using the in/not-in operators now require an iterable parameter whose members are all of the same type (or all numeric), and report an error otherwise. ([#11494](https://github.com/fivetran/great_expectations/pull/11494))
- Added the Snowflake private key to the continuous integration environment variables. ([#11499](https://github.com/fivetran/great_expectations/pull/11499))
- The conditions `Column` class now takes its column name as a positional argument, so it can be constructed as `Column("age")`. ([#11497](https://github.com/fivetran/great_expectations/pull/11497))
- Fixed a flaky validation definition test caused by a race between raised errors when reusing a context from other tests. ([#11495](https://github.com/fivetran/great_expectations/pull/11495))

</details>

#### Contributors

Thanks to @chay0112 (first contribution).

### 1.8.1 (2025-10-30)

#### Highlights

- **Null checks in row conditions** — Row conditions now express null comparisons explicitly with `is_null()` and `is_not_null()` on a column, and passing `None` as the value of a comparison operator is rejected instead of silently producing an invalid condition. ([#11491](https://github.com/fivetran/great_expectations/pull/11491))

  ```python
  import great_expectations.expectations as gxe
  from great_expectations.core.expectation_condition import Column

  gxe.ExpectColumnValuesToBeBetween(
      column="amount",
      min_value=0,
      row_condition=Column("cancelled_at").is_null(),
  )
  ```

- **Legacy row condition strings keep working alongside condition objects** — Existing string-based `row_condition` values are accepted and converted into the new condition objects, the `condition_parser` field is preserved, pandas and Spark conditions have a passthrough path, and rendered expectation content displays the new condition types correctly. ([#11474](https://github.com/fivetran/great_expectations/pull/11474), [#11484](https://github.com/fivetran/great_expectations/pull/11484), [#11480](https://github.com/fivetran/great_expectations/pull/11480), [#11481](https://github.com/fivetran/great_expectations/pull/11481))

- **Clearer limits on combining row conditions** — Nested `AndCondition`s are flattened automatically, while `OrCondition`s nested inside `AndCondition`s or other `OrCondition`s now raise an explicit error, as does supplying more than 100 conditions. ([#11488](https://github.com/fivetran/great_expectations/pull/11488))

- **Updated Snowflake connection documentation** — The Snowflake documentation now covers the deprecation of password authentication and gives corrected guidance for configuring private key authentication. ([#11416](https://github.com/fivetran/great_expectations/pull/11416), [#11490](https://github.com/fivetran/great_expectations/pull/11490))

#### Changes

##### Bug fixes

- Test runs no longer fail on the `google.api_core` Python 3.10 end-of-life warning. ([#11493](https://github.com/fivetran/great_expectations/pull/11493))
- Cloud-marked tests can no longer reach the live API: unmocked HTTP requests are blocked, preventing accidental production calls during test runs. ([#11492](https://github.com/fivetran/great_expectations/pull/11492))
- Rendered expectation content is generated correctly for the new row condition types. ([#11481](https://github.com/fivetran/great_expectations/pull/11481))

##### Docs

- Corrected the Snowflake private key authentication guidance. ([#11490](https://github.com/fivetran/great_expectations/pull/11490))
- Documented the deprecation of Snowflake password authentication and the recommended alternatives. ([#11416](https://github.com/fivetran/great_expectations/pull/11416))

<details>
<summary>Maintenance</summary>

- Passing `None` as the value of a column comparison in a row condition is now rejected; use `is_null()` or `is_not_null()` for null checks, and the comparison parameter is required. ([#11491](https://github.com/fivetran/great_expectations/pull/11491))
- Expectation suites stored in GX Cloud are now read and written through the v2 REST endpoints. ([#11487](https://github.com/fivetran/great_expectations/pull/11487))
- Microsoft SQL Server drivers are installed in CI only for the jobs that need them, and the installation script reports failures more clearly. ([#11489](https://github.com/fivetran/great_expectations/pull/11489))
- Row condition groups are constrained: nested `AndCondition`s are flattened, `OrCondition`s nested inside `AndCondition`s or `OrCondition`s raise an error, and more than 100 conditions raises an error. ([#11488](https://github.com/fivetran/great_expectations/pull/11488))
- Added a passthrough path for the pandas and Spark row condition parsers so existing condition expressions are handled directly. ([#11480](https://github.com/fivetran/great_expectations/pull/11480))
- Test runs no longer surface the Python 3.9 end-of-life future warning. ([#11486](https://github.com/fivetran/great_expectations/pull/11486))
- Spark test environments now use the Apache-published Spark image after the previously used Bitnami image was removed. ([#11444](https://github.com/fivetran/great_expectations/pull/11444))
- The `condition_parser` field is retained for backwards compatibility so single-condition row conditions still convert to string syntax on older API versions. ([#11484](https://github.com/fivetran/great_expectations/pull/11484))
- Legacy string `row_condition` values are transformed into the new condition objects. ([#11474](https://github.com/fivetran/great_expectations/pull/11474))
- Disabled the documentation link checker, which was reporting too many false positives. ([#11477](https://github.com/fivetran/great_expectations/pull/11477))
- Python 3.12 marker tests no longer run on every pull request; only the minimum and maximum supported Python versions are exercised for those events. ([#11457](https://github.com/fivetran/great_expectations/pull/11457))

</details>

### 1.8.0 (2025-10-23)

#### Highlights

- **Snowflake key pair authentication** — Snowflake data sources now accept key pair authentication as a first-class part of the connection API, so you can configure a Snowflake data source with a private key instead of a password. ([#11395](https://github.com/fivetran/great_expectations/pull/11395))

  ```python
  context.data_sources.add_snowflake(
      name="my_snowflake",
      connection_details={
          "account": "myOrg-my_account",
          "user": "my_user",
          "database": "my_db",
          "schema": "my_schema",
          "warehouse": "my_wh",
          "role": "my_role",
          "private_key": "<PEM-encoded private key>",
      },
  )
  ```

- **Row conditions are honored by Volume Expectations** — Volume Expectations now apply the configured row condition, so expected row counts are evaluated against the filtered rows rather than the whole batch. ([#11467](https://github.com/fivetran/great_expectations/pull/11467))

- **Documented schema handling in Redshift and PostgreSQL connection strings** — The connection documentation now explains how to specify a schema in Redshift and PostgreSQL connection strings. ([#11433](https://github.com/fivetran/great_expectations/pull/11433))

- **GX Cloud Data Health documentation for failed Expectations** — New GX Cloud documentation covers the Data Health view for failed Expectations, with screenshots refreshed to match the current interface, alongside new GX Cloud architecture supporting content. ([#11419](https://github.com/fivetran/great_expectations/pull/11419), [#11458](https://github.com/fivetran/great_expectations/pull/11458), [#11439](https://github.com/fivetran/great_expectations/pull/11439))

#### Changes

##### Features

- Snowflake data sources can now be configured with key pair authentication as a supported set of connection details. ([#11395](https://github.com/fivetran/great_expectations/pull/11395))

##### Bug fixes

- Volume Expectations now respect the configured row condition when counting rows. ([#11467](https://github.com/fivetran/great_expectations/pull/11467))

##### Docs

- Documentation now describes how to include a schema in Redshift and PostgreSQL connection strings. ([#11433](https://github.com/fivetran/great_expectations/pull/11433))
- Re-enabled the documentation link checker. ([#11449](https://github.com/fivetran/great_expectations/pull/11449))
- Added supporting content to the GX Cloud architecture documentation. ([#11439](https://github.com/fivetran/great_expectations/pull/11439))
- Updated the Data Health failed Expectations screenshots to match recent interface changes. ([#11458](https://github.com/fivetran/great_expectations/pull/11458))
- Added GX Cloud documentation for the Data Health view of failed Expectations. ([#11419](https://github.com/fivetran/great_expectations/pull/11419))

<details>
<summary>Maintenance</summary>

- SQL execution now handles the structured row-condition type internally, with no change to how existing string conditions behave. ([#11473](https://github.com/fivetran/great_expectations/pull/11473))
- Spark execution now handles the structured row-condition type internally, with no change to how existing string conditions behave. ([#11470](https://github.com/fivetran/great_expectations/pull/11470))
- Updated the lychee link-checking GitHub Action used in CI from 2.0.1 to 2.0.2. ([#11466](https://github.com/fivetran/great_expectations/pull/11466))
- The pandas execution engine now handles the structured row-condition type for row conditions, with no change to existing behavior. ([#11469](https://github.com/fivetran/great_expectations/pull/11469))
- Added internal filter-clause support for SQLAlchemy row conditions. ([#11459](https://github.com/fivetran/great_expectations/pull/11459))
- CI cleanup of test data source schemas now removes schemas older than one hour instead of two. ([#11463](https://github.com/fivetran/great_expectations/pull/11463))
- Expectation row conditions now accept the new structured condition type in their schemas, though passing a condition object currently raises an error. ([#11464](https://github.com/fivetran/great_expectations/pull/11464))
- Suppressed a pkg_resources deprecation warning that was causing spurious test failures. ([#11465](https://github.com/fivetran/great_expectations/pull/11465))
- Added internal filter-clause support for Spark row conditions. ([#11456](https://github.com/fivetran/great_expectations/pull/11456))
- Added internal filter-clause support for pandas row conditions. ([#11455](https://github.com/fivetran/great_expectations/pull/11455))
- CI now cleans up test data sources hourly and covers more leftover schemas. ([#11462](https://github.com/fivetran/great_expectations/pull/11462))
- Added internal execution-engine scaffolding for structured row conditions. ([#11452](https://github.com/fivetran/great_expectations/pull/11452))
- Added comparison, nullity, and column classes used to build row conditions. ([#11450](https://github.com/fivetran/great_expectations/pull/11450))
- The SQLite connection used to register helper functions is now closed, removing a resource warning seen in test runs. ([#11451](https://github.com/fivetran/great_expectations/pull/11451))
- Added AND/OR classes for combining multiple row conditions. ([#11448](https://github.com/fivetran/great_expectations/pull/11448))

</details>

### 1.7.1 (2025-10-15)

#### Highlights

- **Databricks SQL parameters are now compiled in `unexpected_index_query`** — Validation results for Databricks now return an `unexpected_index_query` with its parameters fully rendered, so the query can be copied and run as-is. The query compilation is also no longer sensitive to unfamiliar bind-parameter patterns or to the ordering of parameter values. ([#11437](https://github.com/fivetran/great_expectations/pull/11437))

- **`ExpectColumnValuesToBeOfType` works against Trino** — `ExpectColumnValuesToBeOfType` now evaluates correctly when validating data in Trino. ([#11438](https://github.com/fivetran/great_expectations/pull/11438))

  ```python
  import great_expectations as gx

  gx.expectations.ExpectColumnValuesToBeOfType(column="id", type_="INTEGER")
  ```

#### Changes

##### Bug fixes

- Databricks SQL parameters are now compiled into `unexpected_index_query`, so the returned query is complete and runnable, and no longer depends on bind-parameter naming patterns or dictionary ordering. ([#11437](https://github.com/fivetran/great_expectations/pull/11437))
- Fixed `ExpectColumnValuesToBeOfType` so it evaluates correctly against Trino. ([#11438](https://github.com/fivetran/great_expectations/pull/11438))

##### Docs

- Added documentation for connecting to data in Amazon S3. ([#11375](https://github.com/fivetran/great_expectations/pull/11375))
- Clarified in the documentation that a workspace is required. ([#11443](https://github.com/fivetran/great_expectations/pull/11443))
- Documented support for Python 3.13. ([#11442](https://github.com/fivetran/great_expectations/pull/11442))
- Updated documentation to describe finding the workspace ID in the UI. ([#11435](https://github.com/fivetran/great_expectations/pull/11435))

<details>
<summary>Maintenance</summary>

- Updated pre-commit hooks to newer versions of pre-commit-hooks and ruff. ([#11355](https://github.com/fivetran/great_expectations/pull/11355))
- Type checkers no longer flag passing Redshift connection details when adding or updating a Redshift data source; the type stubs now accept them alongside a connection string. ([#11434](https://github.com/fivetran/great_expectations/pull/11434))

</details>

#### Contributors

Thanks to @dctalbot.

### 1.7.0 (2025-10-09)

Compatibility: Python `<3.13,>=3.9` → `<3.14,>=3.9`; `numpy` added (`python_version >= "3.13"`); `pandas` added (`python_version >= "3.13"`); `posthog` removed; `pandas` removed (extra `snowflake`) (`python_version >= "3.9"`)

#### Highlights

- **Python 3.13 support** — Great Expectations now installs and runs on Python 3.13, in addition to the previously supported 3.9 through 3.12. ([#11426](https://github.com/fivetran/great_expectations/pull/11426))

- **Works with pandas 2.2 and newer** — The `<2.2` upper bound on pandas has been removed, so you can install Great Expectations alongside pandas 2.2.0 and later and pick up the newest pandas features and fixes. ([#11423](https://github.com/fivetran/great_expectations/pull/11423))

  ```python
  pip install great_expectations "pandas>=2.2"
  ```

- **Usage analytics removed** — Great Expectations no longer collects or sends usage analytics, and the `posthog` dependency is no longer installed with the library. ([#11420](https://github.com/fivetran/great_expectations/pull/11420))

- **Reassigning a Snowflake connection string now works as expected** — Setting a new connection string on an existing SQL data source — including Snowflake — is now converted to the proper connection type, so the data source stays usable after the reassignment. ([#11410](https://github.com/fivetran/great_expectations/pull/11410))

  ```python
  datasource.connection_string = "snowflake://user:password@account/db/schema?warehouse=wh&role=role"
  ```

#### Changes

##### Features

- Added support for running Great Expectations on Python 3.13. ([#11426](https://github.com/fivetran/great_expectations/pull/11426))
- The `Renderer` class is no longer part of the public API. ([#10866](https://github.com/fivetran/great_expectations/pull/10866))
- Removed the `<2.2` upper bound on pandas so Great Expectations can be used with pandas 2.2.0 and above. ([#11423](https://github.com/fivetran/great_expectations/pull/11423))

##### Bug fixes

- Fixed AWS authentication errors at validation time when credentials were supplied to `PandasS3Datasource` through `boto3_options` rather than environment variables. ([#11412](https://github.com/fivetran/great_expectations/pull/11412))
- Fixed an issue where assigning a new connection string to a SQL data source after creation — most visibly with Snowflake — left the value in an unusable form. ([#11410](https://github.com/fivetran/great_expectations/pull/11410))

##### Docs

- Removed the migration guide from the documentation. ([#11405](https://github.com/fivetran/great_expectations/pull/11405))
- Documentation now states that Completeness Anomaly Detection is opt-in. ([#11406](https://github.com/fivetran/great_expectations/pull/11406))
- Documentation now states that schedules are opt-in. ([#11408](https://github.com/fivetran/great_expectations/pull/11408))

<details>
<summary>Maintenance</summary>

- Redshift connection details now accept a discrete `schema` field, so a schema can be supplied separately when configuring a Redshift connection. ([#11431](https://github.com/fivetran/great_expectations/pull/11431))
- Re-enabled publishing of pact contract tests. ([#11427](https://github.com/fivetran/great_expectations/pull/11427))
- A warning is now emitted when the workspace ID is not set. ([#11425](https://github.com/fivetran/great_expectations/pull/11425))
- Removed usage analytics collection from the library, along with its `posthog` dependency. ([#11420](https://github.com/fivetran/great_expectations/pull/11420))
- Upgraded the mypy version used for type checking. ([#11422](https://github.com/fivetran/great_expectations/pull/11422))
- Upgraded the ruff version used for linting and formatting. ([#11421](https://github.com/fivetran/great_expectations/pull/11421))
- Skipped tests that fail on the combination of SQLAlchemy below 2.0 and pandas 2.2 or newer to keep CI stable. ([#11417](https://github.com/fivetran/great_expectations/pull/11417))
- Pinned pact-python to avoid an installation error on Python 3.12. ([#11418](https://github.com/fivetran/great_expectations/pull/11418))
- Updated test assertions to use truthiness checks instead of identity comparisons for NumPy 2.x compatibility. ([#11415](https://github.com/fivetran/great_expectations/pull/11415))
- Bumped the SQLAlchemy version used when testing documentation snippets. ([#11411](https://github.com/fivetran/great_expectations/pull/11411))

</details>

### 1.6.4 (2025-10-01)

#### Changes

##### Docs

- Corrected a typo and updated verb tense in the documentation. ([#11404](https://github.com/fivetran/great_expectations/pull/11404))

<details>
<summary>Maintenance</summary>

- Removed the upper version pin on PyAthena, allowing newer PyAthena releases to be installed. ([#11402](https://github.com/fivetran/great_expectations/pull/11402))
- Athena tests now run as a separate step in continuous integration. ([#11401](https://github.com/fivetran/great_expectations/pull/11401))

</details>

### 1.6.3 (2025-09-24)

Compatibility: new extra `test`

#### Highlights

- **Tutorial for validating unstructured data in GX Cloud** — A new tutorial walks through validating unstructured data in GX Cloud end to end. ([#11380](https://github.com/fivetran/great_expectations/pull/11380))

- **Documentation for severity tagging** — The GX Cloud documentation now covers severity tagging, including refreshed screenshots that match the current UI, plus new diagrams illustrating GX integration points. ([#11354](https://github.com/fivetran/great_expectations/pull/11354), [#11394](https://github.com/fivetran/great_expectations/pull/11394), [#11391](https://github.com/fivetran/great_expectations/pull/11391))

#### Changes

##### Docs

- Added a tutorial for validating unstructured data in GX Cloud. ([#11380](https://github.com/fivetran/great_expectations/pull/11380))
- Added diagrams illustrating GX integration points. ([#11391](https://github.com/fivetran/great_expectations/pull/11391))
- Updated screenshots to reflect the current UI for severity tagging. ([#11394](https://github.com/fivetran/great_expectations/pull/11394))
- Documented severity tagging for validation results. ([#11354](https://github.com/fivetran/great_expectations/pull/11354))

<details>
<summary>Maintenance</summary>

- Added `column.non_null_count` to the recognized metric types. ([#11397](https://github.com/fivetran/great_expectations/pull/11397))
- Broadened the Databricks test cleanup routine so temporary schemas created by metrics test utilities are removed. ([#11398](https://github.com/fivetran/great_expectations/pull/11398))

</details>

### 1.6.2 (2025-09-19)

Compatibility: `pyarrow` removed (extra `arrow`); new extra `arrow`; new extra `snowflake`; removed extra `snowflake`; `pyarrow` removed (extra `test`); new extra `test`

#### Highlights

- **Expectation reference documentation now describes the severity parameter** — Every Expectation type's reference documentation now lists `severity` under "Other Parameters", with a link to the severity documentation, so you can see how to set failure severity directly from the Expectation reference. ([#11387](https://github.com/fivetran/great_expectations/pull/11387))

- **Type-list validation works against Trino** — `ExpectColumnValuesToBeInTypeList` now compares column types correctly when validating data through the Trino dialect, instead of misreporting matching types. ([#11386](https://github.com/fivetran/great_expectations/pull/11386))

- **Documentation for workspaces** — The documentation site now covers workspaces. ([#11366](https://github.com/fivetran/great_expectations/pull/11366))

#### Changes

##### Bug fixes

- `ExpectColumnValuesToBeInTypeList` now handles type comparisons correctly for the Trino dialect. ([#11386](https://github.com/fivetran/great_expectations/pull/11386))

##### Docs

- Added a `severity` description with a documentation link to the "Other Parameters" section of every Expectation type, and capitalized "Expectation" in the `FailureSeverity` description. ([#11387](https://github.com/fivetran/great_expectations/pull/11387))
- Added documentation covering workspaces. ([#11366](https://github.com/fivetran/great_expectations/pull/11366))

<details>
<summary>Maintenance</summary>

- Fixed Snowflake dependency resolution on Python 3.10 so installs with Snowflake support succeed. ([#11390](https://github.com/fivetran/great_expectations/pull/11390))
- Pinned `pyarrow>=14` for Python 3.12 in the development arrow requirements so Snowflake marker test jobs install a prebuilt wheel instead of failing to build from source; no runtime behavior changes. ([#11388](https://github.com/fivetran/great_expectations/pull/11388))

</details>

### 1.6.1 (2025-09-15)

#### Changes

##### Bug fixes

- Users without any associated workspaces — such as the system user used by the runner — no longer hit an error when retrieving cloud user information, so analytics can be logged with no workspaces present. ([#11378](https://github.com/fivetran/great_expectations/pull/11378))

### 1.6.0 (2025-09-12)

#### Highlights

- **GX Cloud workspace awareness** — Data Contexts are now workspace aware, laying the groundwork for GX Cloud's multi-workspace support. A workspace id supplied to a Cloud context is carried through to Cloud requests and to the credentials used by its stores. ([#11369](https://github.com/fivetran/great_expectations/pull/11369), [#11371](https://github.com/fivetran/great_expectations/pull/11371), [#11373](https://github.com/fivetran/great_expectations/pull/11373))

  ```python
  # GX_CLOUD_WORKSPACE_ID is read alongside your Cloud access token and organization id
  import great_expectations as gx

  context = gx.get_context(mode="cloud")
  ```

- **S3 data assets read past the first page of results** — Listing files in an S3 directory or bucket with more results than fit in a single response now returns all of them instead of raising an error part-way through. ([#11361](https://github.com/fivetran/great_expectations/pull/11361))

- **More robust handling of quoted and mixed-case SQL identifiers** — Schema and table names that are quoted, use data-source-specific quote characters, or use mixed case are now handled correctly when building queries and when collecting column metadata. ([#11367](https://github.com/fivetran/great_expectations/pull/11367), [#11365](https://github.com/fivetran/great_expectations/pull/11365))

#### Changes

##### Features

- Data Contexts are now workspace aware, adding initial support for GX Cloud's upcoming multi-workspace feature. ([#11369](https://github.com/fivetran/great_expectations/pull/11369))

##### Bug fixes

- Reading an S3 directory that spans multiple pages of results no longer fails; the continuation token is no longer reused in subsequent requests. ([#11361](https://github.com/fivetran/great_expectations/pull/11361))
- Quoted schema and table names are handled more reliably: the quote characters used by all supported SQL data sources are now recognized, and identifiers are quoted correctly when serialized. ([#11367](https://github.com/fivetran/great_expectations/pull/11367))
- Column metadata is now computed correctly for tables whose names use mixed case. ([#11365](https://github.com/fivetran/great_expectations/pull/11365))

##### Docs

- Documentation for building custom agent Docker images now recommends the stable base image instead of latest. ([#11353](https://github.com/fivetran/great_expectations/pull/11353))

<details>
<summary>Maintenance</summary>

- A Cloud context now passes its workspace id along with the access token and organization id in the credentials used by its stores, and requests for the data context configuration are scoped to the workspace. ([#11371](https://github.com/fivetran/great_expectations/pull/11371))
- The Cloud test job in continuous integration now supplies a workspace id, so workspace-aware behavior is exercised in CI. ([#11373](https://github.com/fivetran/great_expectations/pull/11373))
- Added test coverage confirming that the unexpected_rows result format option behaves consistently across the canonical column map expectations for Pandas and SQL data sources. ([#11368](https://github.com/fivetran/great_expectations/pull/11368))

</details>

#### Contributors

Thanks to @pawel99k (first contribution).

### 1.5.11 (2025-09-04)

#### Highlights

- **Severity-aware Checkpoint notifications** — Expectations that carry a severity value can now be validated and acted on end to end: validation results expose the highest-severity failure they contain, and built-in Checkpoint actions use it to decide whether to notify. ([#11341](https://github.com/fivetran/great_expectations/pull/11341), [#11343](https://github.com/fivetran/great_expectations/pull/11343), [#11347](https://github.com/fivetran/great_expectations/pull/11347))

  ```python
  result = checkpoint.run()
  validation_result = result.run_results[next(iter(result.run_results))]
  max_severity = validation_result.get_max_severity_failure()
  ```

- **Quoted table names stay quoted in GX Cloud** — A table asset whose table name is quoted keeps its quoting when it is sent to and fetched back from GX Cloud, so the name continues to be treated as quoted. ([#11357](https://github.com/fivetran/great_expectations/pull/11357))

#### Changes

##### Features

- Validation results expose a new get_max_severity_failure method that reports the highest-severity failing Expectation in the result, which is also used when deciding whether to send notifications. ([#11341](https://github.com/fivetran/great_expectations/pull/11341))
- Expectations with a severity value set can now be validated; previously validation failed because the expectation configuration could not be serialized. ([#11343](https://github.com/fivetran/great_expectations/pull/11343))
- Built-in Checkpoint actions now take Expectation severity into account when deciding whether to send a notification. ([#11347](https://github.com/fivetran/great_expectations/pull/11347))

##### Bug fixes

- Quoted table names on a table asset keep their quotes when the asset is serialized for GX Cloud, so a fetched asset is still treated as having a quoted table name. ([#11357](https://github.com/fivetran/great_expectations/pull/11357))
- Unexpected rows are now included in validation results whenever they are requested. ([#11358](https://github.com/fivetran/great_expectations/pull/11358))

##### Docs

- Added GX Cloud documentation for the built-in validation actions. ([#11338](https://github.com/fivetran/great_expectations/pull/11338))

<details>
<summary>Maintenance</summary>

- Updated the ports used by the Cloud test suite to match the new service ports. ([#11351](https://github.com/fivetran/great_expectations/pull/11351))

</details>

#### Contributors

Thanks to @klavavej.

### 1.5.10 (2025-08-27)

#### Changes

##### Docs

- Documented a limitation of the forecasted range used by anomaly detection. ([#11349](https://github.com/fivetran/great_expectations/pull/11349))
- Documentation now explains that completeness anomaly detection uses the forecasted range. ([#11346](https://github.com/fivetran/great_expectations/pull/11346))

<details>
<summary>Maintenance</summary>

- Updated the mermaid diagram library used to build the documentation site from 11.9.0 to 11.10.1. ([#11348](https://github.com/fivetran/great_expectations/pull/11348))

</details>

### 1.5.9 (2025-08-20)

#### Highlights

- **Expectation JSON schemas now carry failure severity** — Expectations can express a failure severity, and the published JSON schemas now include the new `severity` field backed by a `FailureSeverity` enum. ([#11337](https://github.com/fivetran/great_expectations/pull/11337))

- **Documentation for Cloud API version 0.18 sunset** — The compatibility reference and related documentation now reflect the sunset of Cloud API version 0.18. ([#11334](https://github.com/fivetran/great_expectations/pull/11334))

#### Changes

##### Features

- Expectation JSON schemas now include a `severity` field, with a new `FailureSeverity` enum describing Expectation failure severity. ([#11337](https://github.com/fivetran/great_expectations/pull/11337))

##### Docs

- The "Manage Expectations" documentation is split into separate, more focused pages. ([#11340](https://github.com/fivetran/great_expectations/pull/11340))
- Temporarily removed the documentation link checker to unblock documentation builds. ([#11342](https://github.com/fivetran/great_expectations/pull/11342))
- Documentation now reflects the sunset of Cloud API version 0.18, including an updated compatibility reference. ([#11334](https://github.com/fivetran/great_expectations/pull/11334))
- Corrected a typo in an environment variable name in the documentation. ([#11335](https://github.com/fivetran/great_expectations/pull/11335))
- Documentation navigation paths no longer include "Settings", matching the updated UI navigation. ([#11332](https://github.com/fivetran/great_expectations/pull/11332))

<details>
<summary>Maintenance</summary>

- Updated documentation site dependencies (Docusaurus 3.8.1, webpack-dev-server 5.2.2, jest-environment-jsdom 30.0.5) to resolve CVE-2025-30360 and CVE-2025-7783. ([#11339](https://github.com/fivetran/great_expectations/pull/11339))

</details>

### 1.5.8 (2025-08-07)

#### Highlights

- **Validations against Databricks no longer fail on large bundled metric queries** — Metric queries that exceed Databricks' 256 query-parameter limit are now split into smaller batches automatically, so validating batches with many parameters against Databricks completes instead of erroring. ([#11317](https://github.com/fivetran/great_expectations/pull/11317))

- **Documentation for retrying Expectation generation with your own input** — The documentation now describes the retry workflows for supplying user input when generating Expectations, so you can guide generation when the first attempt isn't what you wanted. ([#11325](https://github.com/fivetran/great_expectations/pull/11325))

#### Changes

##### Bug fixes

- Bundled metric queries are now split into batches when they would exceed Databricks' 256 query-parameter limit, so validations no longer fail on that limit. ([#11317](https://github.com/fivetran/great_expectations/pull/11317))

##### Docs

- Documented the retry workflows for providing user input during Expectation generation. ([#11325](https://github.com/fivetran/great_expectations/pull/11325))
- Corrected a typo ("retreive" to "retrieve") in the guide on configuring metadata stores. ([#11316](https://github.com/fivetran/great_expectations/pull/11316))
- Updated the "GX Cloud in your environment" diagram to reposition data ingestion. ([#11329](https://github.com/fivetran/great_expectations/pull/11329))

<details>
<summary>Maintenance</summary>

- Updated pinned development tooling, bumping the ruff pre-commit hook to v0.12.7. ([#11330](https://github.com/fivetran/great_expectations/pull/11330))
- Restored the documentation link checker step in continuous integration. ([#11327](https://github.com/fivetran/great_expectations/pull/11327))

</details>

#### Contributors

Thanks to @NathanFarmer, @Abdelkrim (first contribution).

### 1.5.7 (2025-07-30)

#### Highlights

- **Spark Connect and Databricks shared clusters now supported for column comparisons** — Expectations that reference columns on Spark now build those references in a way Spark Connect accepts, so validations that previously failed with "[CANNOT_RESOLVE_DATAFRAME_COLUMN] Cannot resolve dataframe column" on Spark Connect and Databricks shared clusters now run correctly. Expectations such as ExpectColumnValueLengthsToBeBetween and ExpectColumnPairValuesAToBeGreaterThanB are fixed; behavior on local Spark is unchanged. ([#11286](https://github.com/fivetran/great_expectations/pull/11286))

#### Changes

##### Bug fixes

- Fixed Spark column references so expectations no longer fail with "Cannot resolve dataframe column" on Spark Connect and Databricks shared clusters. ([#11286](https://github.com/fivetran/great_expectations/pull/11286))

<details>
<summary>Maintenance</summary>

- Release artifacts are now built with the standard build tooling so source and wheel distributions are produced reliably. ([#11324](https://github.com/fivetran/great_expectations/pull/11324))
- Added the typing_extensions dependency to the build step so the release build no longer fails. ([#11323](https://github.com/fivetran/great_expectations/pull/11323))
- Bumped mypy to 1.16.1. ([#11262](https://github.com/fivetran/great_expectations/pull/11262))
- Updated pre-commit hooks, including ruff to v0.12.2. ([#11287](https://github.com/fivetran/great_expectations/pull/11287))
- Sped up marker tests in CI by bulk loading test data instead of inserting records one at a time. ([#11321](https://github.com/fivetran/great_expectations/pull/11321))
- Bumped form-data from 4.0.2 to 4.0.4 in the documentation site dependencies. ([#11310](https://github.com/fivetran/great_expectations/pull/11310))
- Bumped posthog to 6.1.0. ([#11303](https://github.com/fivetran/great_expectations/pull/11303))
- Fixed the MSSQL compatibility test CI flow, which would hang on an interactive package upgrade prompt. ([#11320](https://github.com/fivetran/great_expectations/pull/11320))
- Temporarily removed the documentation link checker step from CI. ([#11322](https://github.com/fivetran/great_expectations/pull/11322))

</details>

#### Contributors

Thanks to @alansk97 (first contribution), @dctalbot.

### 1.5.6 (2025-07-24)

#### Highlights

- **New documentation for Data Health, SQL generation, and pipeline architecture** — The docs now cover the Data Health dashboard (including a screenshot of it), generating SQL, the newly supported data sources, and a pipeline architecture diagram. ([#11294](https://github.com/fivetran/great_expectations/pull/11294), [#11307](https://github.com/fivetran/great_expectations/pull/11307), [#11289](https://github.com/fivetran/great_expectations/pull/11289), [#11293](https://github.com/fivetran/great_expectations/pull/11293), [#11298](https://github.com/fivetran/great_expectations/pull/11298))

- **Range expectations reject incompatible date and datetime bounds** — ExpectColumnUniqueValueCountToBeBetween, ExpectColumnStdevToBeBetween, and ExpectColumnValueLengthsToBeBetween no longer accept date or datetime values for their min and max inputs, so these expectations now only allow bounds that make sense for the value they measure. ([#11305](https://github.com/fivetran/great_expectations/pull/11305))

#### Changes

##### Bug fixes

- ExpectColumnUniqueValueCountToBeBetween, ExpectColumnStdevToBeBetween, and ExpectColumnValueLengthsToBeBetween no longer accept date or datetime values for their min and max inputs. ([#11305](https://github.com/fivetran/great_expectations/pull/11305))

##### Docs

- Added a screenshot of the new Data Health dashboard to the documentation. ([#11307](https://github.com/fivetran/great_expectations/pull/11307))
- Restored the documentation link checker now that the new and renamed pages it covers have been published. ([#11308](https://github.com/fivetran/great_expectations/pull/11308))
- Documented the newly supported data sources. ([#11293](https://github.com/fivetran/great_expectations/pull/11293))
- Standardized data source naming across expectation docstrings and related schemas. ([#11306](https://github.com/fivetran/great_expectations/pull/11306))
- Added a pipeline architecture diagram to the documentation. ([#11298](https://github.com/fivetran/great_expectations/pull/11298))
- Expectation docstrings now list the supported Postgres flavors. ([#11304](https://github.com/fivetran/great_expectations/pull/11304))
- Added documentation for the Data Health dashboard. ([#11294](https://github.com/fivetran/great_expectations/pull/11294))
- Added documentation for generating SQL. ([#11289](https://github.com/fivetran/great_expectations/pull/11289))

<details>
<summary>Maintenance</summary>

- Cloud documentation snippets are now covered by tests. ([#11292](https://github.com/fivetran/great_expectations/pull/11292))
- Updated the docstring for Postgres flavor data sources. ([#11302](https://github.com/fivetran/great_expectations/pull/11302))
- Added scheduled clean-up scripts for Databricks and Snowflake test schemas. ([#11297](https://github.com/fivetran/great_expectations/pull/11297))

</details>

### 1.5.5 (2025-07-10)

#### Highlights

- **BigQuery data source** — A dedicated BigQuery data source class is now available, so BigQuery connections can be declared as their own data source type rather than as a generic SQL connection. ([#11296](https://github.com/fivetran/great_expectations/pull/11296))

- **Postgres-compatible data source flavors** — New data source classes cover Postgres-compatible services — Google Cloud AlloyDB, Amazon Aurora, Citus, and Neon — so each of these backends can be selected directly when connecting to data. ([#11290](https://github.com/fivetran/great_expectations/pull/11290))

- **Disabling analytics is now fully respected** — When analytics is disabled in the Data Context configuration, analytics initialization is no longer performed at all. This resolves permission-denied errors raised while looking for a user-level configuration file in restricted environments such as Databricks streaming jobs. ([#11276](https://github.com/fivetran/great_expectations/pull/11276))

#### Changes

##### Features

- Added a BigQuery data source class for connecting to BigQuery. ([#11296](https://github.com/fivetran/great_expectations/pull/11296))
- Added Postgres-compatible data source classes for Google Cloud AlloyDB, Amazon Aurora, Citus, and Neon. ([#11290](https://github.com/fivetran/great_expectations/pull/11290))

##### Bug fixes

- Analytics initialization is now skipped entirely when analytics is disabled in the Data Context configuration, avoiding permission-denied errors from looking up a user-level configuration file. ([#11276](https://github.com/fivetran/great_expectations/pull/11276))

##### Docs

- Corrected an inaccurate statement about forecasted ranges in the documentation. ([#11295](https://github.com/fivetran/great_expectations/pull/11295))

<details>
<summary>Maintenance</summary>

- Upgraded the ruff linter and formatter used for development to 0.12.2. ([#11288](https://github.com/fivetran/great_expectations/pull/11288))

</details>

#### Contributors

Thanks to @jmcorreia.

### 1.5.4 (2025-07-02)

#### Highlights

- **Corrected result summary for ExpectTableColumnsToMatchSet** — Validation results for ExpectTableColumnsToMatchSet now render correctly, so the expectation's summary reads accurately wherever results are displayed. ([#11281](https://github.com/fivetran/great_expectations/pull/11281))

- **New documentation for Anomaly Detection expectations** — The docs now cover the Anomaly Detection expectation drawer and its underlying model, so you can understand how anomaly detection expectations are configured and how they behave. ([#11234](https://github.com/fivetran/great_expectations/pull/11234))

#### Changes

##### Bug fixes

- Fixed the rendering of ExpectTableColumnsToMatchSet so its results display correctly. ([#11281](https://github.com/fivetran/great_expectations/pull/11281))
- Generalized the schema expectation so it behaves correctly across a wider range of inputs. ([#11272](https://github.com/fivetran/great_expectations/pull/11272))

##### Docs

- Clarified the integration support policy documentation and renamed the "resources" section to "help". ([#11247](https://github.com/fivetran/great_expectations/pull/11247))
- Added documentation for the Anomaly Detection expectation drawer and the anomaly detection model. ([#11234](https://github.com/fivetran/great_expectations/pull/11234))

<details>
<summary>Maintenance</summary>

- Snowflake and Databricks integration tests now use the shared data-source parameterization helper instead of the table factory fixture, with no change to library behavior. ([#11277](https://github.com/fivetran/great_expectations/pull/11277))
- Upgraded the ruff linter used for development to 0.12.0. ([#11263](https://github.com/fivetran/great_expectations/pull/11263))
- Snowflake end-to-end Cloud tests now use the shared data-source parameterization decorator for connection pooling and table setup and teardown, with no change to library behavior. ([#11274](https://github.com/fivetran/great_expectations/pull/11274))

</details>

#### Contributors

Thanks to @ashmortar.

### 1.5.3 (2025-06-25)

#### Highlights

- **ExpectTableColumnsToMatchSet now matches column names case-insensitively** — On SQL dialects where column names are compared case-insensitively (PostgreSQL, Databricks SQL, and Snowflake), ExpectTableColumnsToMatchSet no longer fails when the expected column set differs only by letter casing from the table's actual columns. It now behaves consistently with the other column-name expectations such as expect_table_columns_to_match_ordered_list and expect_column_to_exist. ([#11266](https://github.com/fivetran/great_expectations/pull/11266))

  ```python
  import great_expectations.expectations as gxe

  # Passes against a table whose columns are PASSENGER_COUNT and TRIP_DISTANCE
  suite.add_expectation(
      gxe.ExpectTableColumnsToMatchSet(column_set=["passenger_count", "trip_distance"])
  )
  ```

#### Changes

##### Bug fixes

- ExpectTableColumnsToMatchSet now compares column names case-insensitively on dialects that treat column names as case-insensitive, so expectations no longer fail purely because of letter casing. ([#11266](https://github.com/fivetran/great_expectations/pull/11266))

##### Docs

- Added documentation for the ExpectColumnProportionOfNonNullValuesToBeBetween expectation. ([#11257](https://github.com/fivetran/great_expectations/pull/11257))

<details>
<summary>Maintenance</summary>

- Widened the supported posthog dependency range to allow versions 4 and 5. ([#11265](https://github.com/fivetran/great_expectations/pull/11265))

</details>

#### Contributors

Thanks to @klavavej.

### 1.5.2 (2025-06-18)

#### Highlights

- **Suite parameters accepted in every expectation argument** — All expectation arguments now accept suite parameters, so any keyword argument of an expectation can be supplied at validation time instead of being hard-coded when the expectation is defined. ([#11222](https://github.com/fivetran/great_expectations/pull/11222))

  ```python
  import great_expectations as gx

  expectation = gx.expectations.ExpectColumnValuesToBeBetween(
      column="passenger_count",
      min_value={"$PARAMETER": "min_passengers"},
      max_value={"$PARAMETER": "max_passengers"},
  )

  results = batch.validate(
      expectation,
      expectation_parameters={"min_passengers": 1, "max_passengers": 6},
  )
  ```

- **Whole-directory batch definitions read every file again** — Batch definitions created with `add_batch_definition_whole_directory` on S3, Azure Blob Storage, and Google Cloud Storage data assets now read all files in the directory instead of only one. ([#11254](https://github.com/fivetran/great_expectations/pull/11254))

  ```python
  asset = data_source.add_directory_csv_asset(name="my_asset", s3_prefix="data/")
  batch_definition = asset.add_batch_definition_whole_directory("all_files")
  batch = batch_definition.get_batch()
  ```

#### Changes

##### Features

- Every expectation argument now accepts a suite parameter, so all expectation keyword arguments can be parameterized and supplied at validation time. ([#11222](https://github.com/fivetran/great_expectations/pull/11222))

##### Bug fixes

- The `min_value` and `max_value` parameters of `ExpectColumnProportionOfNonNullValuesToBeBetween` and `ExpectColumnProportionOfUniqueValuesToBeBetween` no longer accept date or datetime values; they now accept only numbers (or a suite parameter), and their published schemas reflect this. ([#11259](https://github.com/fivetran/great_expectations/pull/11259))
- Fixed `add_batch_definition_whole_directory` reading only a single file for S3, Azure Blob Storage, and Google Cloud Storage data assets; the whole directory is now read as one batch. ([#11254](https://github.com/fivetran/great_expectations/pull/11254))
- Fixed a `ValidationError` raised when using `ExpectColumnPairValuesToHaveDifferenceOfCustomPercentage`; the expectation now declares its required `percentage` argument. ([#11209](https://github.com/fivetran/great_expectations/pull/11209))

##### Docs

- Added a tip about Cloud API data sources to the documentation. ([#11248](https://github.com/fivetran/great_expectations/pull/11248))
- Temporarily disabled the documentation link checker while changed page paths are sorted out. ([#11250](https://github.com/fivetran/great_expectations/pull/11250))

<details>
<summary>Maintenance</summary>

- Bumped the `brace-expansion` documentation-site dependency from 1.1.11 to 1.1.12. ([#11251](https://github.com/fivetran/great_expectations/pull/11251))
- Rendered output for the non-null proportion expectation now says "proportion" instead of "fraction". ([#11253](https://github.com/fivetran/great_expectations/pull/11253))

</details>

#### Contributors

Thanks to @Pascal06S (first contribution), @sariaslaso (first contribution).

### 1.5.1 (2025-06-11)

#### Highlights

- **New expectation: ExpectColumnProportionOfUniqueValuesToBeBetween** — You can now assert that the proportion of unique values in a column falls within an expected range, letting you catch columns that become unexpectedly duplicated or unexpectedly high-cardinality. ([#11235](https://github.com/fivetran/great_expectations/pull/11235))

  ```python
  import great_expectations.expectations as gxe

  expectation = gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
      column="passenger_count",
      min_value=0.1,
      max_value=0.9,
  )
  ```

- **Non-null count available as a column metric** — A column aggregate metric for the number of non-null values in a column is now available, so expectations and custom checks can reason about how much data a column actually contains. ([#11229](https://github.com/fivetran/great_expectations/pull/11229))

#### Changes

##### Features

- Added `ExpectColumnProportionOfUniqueValuesToBeBetween`, which validates that the proportion of unique values in a column falls between a minimum and maximum value. ([#11235](https://github.com/fivetran/great_expectations/pull/11235))
- Added a `ColumnAggregateNonNullCount` metric that reports the number of non-null values in a column. ([#11229](https://github.com/fivetran/great_expectations/pull/11229))

##### Docs

- Fixed a documentation link that pointed at content removed in an earlier change. ([#11232](https://github.com/fivetran/great_expectations/pull/11232))
- Revised documentation wording around the term "API" for consistency with the current style guidance. ([#11196](https://github.com/fivetran/great_expectations/pull/11196))

<details>
<summary>Maintenance</summary>

- Removed the Rule-Based Profiler and its references, moving the column-filtering behavior it provided into a standalone module. ([#11231](https://github.com/fivetran/great_expectations/pull/11231))
- Restored database connection pooling in the expectation test suite, including cleanup of the temporary schemas the tests create. ([#11228](https://github.com/fivetran/great_expectations/pull/11228))
- Reverted a change that gated Snowflake tests behind a `--snowflake` flag, so those tests run again in CI via the `snowflake` marker. ([#11230](https://github.com/fivetran/great_expectations/pull/11230))

</details>

### 1.5.0 (2025-06-05)

#### Highlights

- **Multi-source Expectations documentation** — The documentation now covers Multi-source Expectations, explaining how to compare data across two different data sources. ([#11165](https://github.com/fivetran/great_expectations/pull/11165))

- **Redshift geometry and super column types supported** — Redshift data sources now recognize the `GEOMETRY` and `SUPER` column types, so assets containing these columns can be introspected and validated. ([#11194](https://github.com/fivetran/great_expectations/pull/11194))

- **No more pkg_resources dependency** — GX Core no longer depends on the deprecated `pkg_resources` package, removing its import-time deprecation warnings on modern Python installs. ([#11213](https://github.com/fivetran/great_expectations/pull/11213))

#### Changes

##### Features

- Added support for the Redshift `GEOMETRY` and `SUPER` column types. ([#11194](https://github.com/fivetran/great_expectations/pull/11194))

##### Docs

- Restored the documentation link checker that had been temporarily disabled. ([#11212](https://github.com/fivetran/great_expectations/pull/11212))
- Added documentation for Multi-source Expectations. ([#11165](https://github.com/fivetran/great_expectations/pull/11165))
- Revised how the term "Cloud" is used throughout the GX Core documentation for consistency. ([#11207](https://github.com/fivetran/great_expectations/pull/11207))

<details>
<summary>Maintenance</summary>

- Added test coverage for suite parameters used as `min_value` and `max_value` in `ExpectColumnMaxToBeBetween`. ([#11225](https://github.com/fivetran/great_expectations/pull/11225))
- Removed the `pkg_resources` dependency, replacing requirements parsing with a pip compatibility module and a self-contained parser in `setup.py`. ([#11213](https://github.com/fivetran/great_expectations/pull/11213))
- Reverted the session-scoped SQL engine pool in the expectation test suite because it broke test schema cleanup. ([#11224](https://github.com/fivetran/great_expectations/pull/11224))
- Updated pre-commit hooks, bumping ruff-pre-commit to v0.11.12. ([#11218](https://github.com/fivetran/great_expectations/pull/11218))
- Added a session-scoped SQL engine pool to the expectation tests (subsequently reverted in this release). ([#11219](https://github.com/fivetran/great_expectations/pull/11219))
- Improved the `ExpectQueryResultsToMatchComparison` docstring so parameter names and descriptions read consistently. ([#11221](https://github.com/fivetran/great_expectations/pull/11221))
- Updated the diagnostic renderer labels shown for `ExpectQueryResultsToMatchComparison`. ([#11216](https://github.com/fivetran/great_expectations/pull/11216))
- Added a warning filter to the test configuration to quiet expected warnings. ([#11217](https://github.com/fivetran/great_expectations/pull/11217))

</details>

#### Contributors

Thanks to @VolkovGeoPhy.

### 1.4.6 (2025-05-28)

#### Highlights

- **Clearer errors for unhashable column types in ExpectQueryResultsToMatchComparison** — When a query returns unhashable data types such as JSONB, ExpectQueryResultsToMatchComparison now raises a helpful error that names the first column containing unhashable data instead of failing with an unclear message. ([#11193](https://github.com/fivetran/great_expectations/pull/11193))

- **Case-insensitive column type checks on Databricks, Snowflake, and Postgres** — expect_column_values_to_be_of_type now treats unquoted identifiers in column_name and column_type as case-insensitive on Databricks, Postgres, and Snowflake, so type expectations pass regardless of the casing you write. ([#11192](https://github.com/fivetran/great_expectations/pull/11192))

  ```python
  suite.add_expectation(
      gxe.ExpectColumnValuesToBeOfType(column="my_column", type_="varchar")
  )
  ```

- **Documentation for anomaly detection** — The documentation now covers anomaly detection, alongside refreshed wording for the terms "Core" and "platform" and updated guidance noting that both tables and views are supported as data assets. ([#11172](https://github.com/fivetran/great_expectations/pull/11172), [#11187](https://github.com/fivetran/great_expectations/pull/11187), [#11198](https://github.com/fivetran/great_expectations/pull/11198), [#11205](https://github.com/fivetran/great_expectations/pull/11205))

#### Changes

##### Bug fixes

- UUID values are now handled correctly when rendering expectation content. ([#11204](https://github.com/fivetran/great_expectations/pull/11204))
- Rendering of ExpectQueryResultsToMatchComparison now handles cases where results contain sets. ([#11203](https://github.com/fivetran/great_expectations/pull/11203))
- expect_column_values_to_be_of_type now treats unquoted column names and column types as case-insensitive on Databricks, Postgres, and Snowflake. ([#11192](https://github.com/fivetran/great_expectations/pull/11192))
- ExpectQueryResultsToMatchComparison now raises a clear error naming the first column with unhashable data (for example JSONB) instead of failing unhelpfully. ([#11193](https://github.com/fivetran/great_expectations/pull/11193))

##### Docs

- Revised how the term "Core" is used in relation to GX Cloud throughout the documentation. ([#11205](https://github.com/fivetran/great_expectations/pull/11205))
- Data Source connection and Expectation docs now state that views are supported in addition to tables. ([#11198](https://github.com/fivetran/great_expectations/pull/11198))
- Refined how the term "platform" is used across the documentation. ([#11187](https://github.com/fivetran/great_expectations/pull/11187))
- Added documentation covering anomaly detection. ([#11172](https://github.com/fivetran/great_expectations/pull/11172))

<details>
<summary>Maintenance</summary>

- Snowflake tests now run only when the Snowflake flag is enabled, so local test runs no longer hit external backends by default. ([#10605](https://github.com/fivetran/great_expectations/pull/10605))
- Updated the parameter descriptions for the multi-source comparison parameter. ([#11202](https://github.com/fivetran/great_expectations/pull/11202))
- Suppressed a newly surfaced pkg_resources deprecation warning. ([#11201](https://github.com/fivetran/great_expectations/pull/11201))
- Restricted the supported pyspark range to >=2.3.2,\<4.0, since pyspark 4.0 introduces incompatible type changes. ([#11197](https://github.com/fivetran/great_expectations/pull/11197))
- GX Cloud logs are now surfaced when cloud tests fail. ([#11188](https://github.com/fivetran/great_expectations/pull/11188))
- Added a CloudAMQP connection string environment variable to the CI configuration. ([#11190](https://github.com/fivetran/great_expectations/pull/11190))

</details>

### 1.4.5 (2025-05-22)

#### Highlights

- **Redshift GEOMETRY and SUPER column types supported** — Redshift data sources now recognize the GEOMETRY and SUPER column types, so assets using those columns can be used without an unsupported-type error. ([#11183](https://github.com/fivetran/great_expectations/pull/11183))

- **ExpectAI documentation now covers all Data Sources** — The ExpectAI documentation has been reorganized so it applies to every supported Data Source rather than a subset. ([#11178](https://github.com/fivetran/great_expectations/pull/11178))

- **Fewer secret-store lookups when resolving config secrets** — Secret substitution now reuses a cached secrets store client instead of rebuilding it on every lookup, avoiding repeated calls to the secrets backend when loading configuration. ([#11184](https://github.com/fivetran/great_expectations/pull/11184))

#### Changes

##### Features

- Redshift data sources now support the GEOMETRY and SUPER column types. ([#11183](https://github.com/fivetran/great_expectations/pull/11183))

##### Bug fixes

- Secret lookups now reuse the existing cached secrets store client rather than recreating it for each substitution. ([#11184](https://github.com/fivetran/great_expectations/pull/11184))

##### Docs

- Updated the ExpectAI documentation to cover all Data Sources. ([#11178](https://github.com/fivetran/great_expectations/pull/11178))

<details>
<summary>Maintenance</summary>

- When a multi-source query comparison produces exactly one differing record in a single column, the validation result now renders the observed and expected values as plain single values instead of a table. ([#11186](https://github.com/fivetran/great_expectations/pull/11186))
- Renamed the multi-source Expectation to ExpectQueryResultsToMatchComparison and renamed its parameters to base_query, comparison_data_source_name, and comparison_query. ([#11185](https://github.com/fivetran/great_expectations/pull/11185))
- Updated the Posthog analytics events emitted by the library. ([#11179](https://github.com/fivetran/great_expectations/pull/11179))
- Upgraded the ruff linter to 0.11.8 and applied the resulting code cleanups. ([#11182](https://github.com/fivetran/great_expectations/pull/11182))
- Test runs no longer fail on Snowflake SSL connection warnings. ([#11180](https://github.com/fivetran/great_expectations/pull/11180))
- Updated pre-commit hooks, bumping ruff-pre-commit from v0.9.9 to v0.11.8. ([#10480](https://github.com/fivetran/great_expectations/pull/10480))
- Fixed the setup of the nightly data source cleanup CI action. ([#11176](https://github.com/fivetran/great_expectations/pull/11176))

</details>

#### Contributors

Thanks to @VolkovGeoPhy.

### 1.4.4 (2025-05-14)

#### Highlights

- **New Expectation: ExpectQueryResultsToMatchSource** — You can now compare the results of a SQL query run against your Data Source with the results of a query run against another Data Source, and require that at least a `mostly` fraction of records match. Supported on PostgreSQL, Snowflake, Databricks (SQL), Redshift, and SQLite. ([#11144](https://github.com/fivetran/great_expectations/pull/11144))

  ```python
  import great_expectations as gx

  expectation = gx.expectations.ExpectQueryResultsToMatchSource(
      target_query="SELECT id, amount FROM orders",
      source_data_source_name="my_source_data_source",
      source_query="SELECT id, amount FROM orders",
      mostly=0.95,
  )
  ```

- **Richer results and rendering for ExpectQueryResultsToMatchSource** — Validation results for ExpectQueryResultsToMatchSource now report the specific rows missing from or unexpected in the target query results, and those differences are presented as a diagnostic table — with a simplified presentation when the source and target queries each return a single column. The Expectation also renders a readable summary showing the target query and the source Data Source it is compared against. ([#11161](https://github.com/fivetran/great_expectations/pull/11161), [#11168](https://github.com/fivetran/great_expectations/pull/11168), [#11173](https://github.com/fivetran/great_expectations/pull/11173), [#11160](https://github.com/fivetran/great_expectations/pull/11160))

#### Changes

##### Features

- ExpectQueryResultsToMatchSource results now use a simplified diagnostic rendering when the target and source queries each return a single column. ([#11173](https://github.com/fivetran/great_expectations/pull/11173))
- ExpectQueryResultsToMatchSource validation results are now displayed as a diagnostic table of differences between the target and source query results. ([#11168](https://github.com/fivetran/great_expectations/pull/11168))
- ExpectQueryResultsToMatchSource now computes and reports the rows missing from and unexpected in the target query results. ([#11161](https://github.com/fivetran/great_expectations/pull/11161))
- Added the ExpectQueryResultsToMatchSource Expectation, which compares the results of a SQL query against the results of a query on another Data Source and passes when at least a `mostly` fraction of records match. ([#11144](https://github.com/fivetran/great_expectations/pull/11144))

##### Docs

- Updated the Ruff badge in the README to point at the current astral-sh/ruff endpoint. ([#10905](https://github.com/fivetran/great_expectations/pull/10905))
- Temporarily removed the documentation link checker as a workaround for a known issue. ([#11162](https://github.com/fivetran/great_expectations/pull/11162))
- Updated the ExpectAI documentation to reflect current email alert behavior. ([#11154](https://github.com/fivetran/great_expectations/pull/11154))

<details>
<summary>Maintenance</summary>

- Updated the data quality issue category reported for ExpectQueryResultsToMatchSource. ([#11174](https://github.com/fivetran/great_expectations/pull/11174))
- Bumped @babel/helpers from 7.26.9 to 7.27.0 in the documentation site. ([#11123](https://github.com/fivetran/great_expectations/pull/11123))
- Updated the data quality issue metadata for ExpectQueryResultsToMatchSource. ([#11164](https://github.com/fivetran/great_expectations/pull/11164))
- Fixed a flaky test caused by floating-point comparison and simplified a related assertion to use pytest.approx. ([#11163](https://github.com/fivetran/great_expectations/pull/11163))
- CI now ensures a recent Docker Compose version to avoid a race condition when pulling many images concurrently. ([#11156](https://github.com/fivetran/great_expectations/pull/11156))
- Bumped @babel/runtime from 7.26.9 to 7.27.0 in the documentation site. ([#11124](https://github.com/fivetran/great_expectations/pull/11124))
- Bumped estree-util-value-to-estree from 3.3.2 to 3.3.3 in the documentation site. ([#11121](https://github.com/fivetran/great_expectations/pull/11121))
- Bumped http-proxy-middleware from 2.0.7 to 2.0.9 in the documentation site. ([#11120](https://github.com/fivetran/great_expectations/pull/11120))
- ExpectQueryResultsToMatchSource now renders a prescriptive summary showing the target SQL query and the source Data Source it is compared against. ([#11160](https://github.com/fivetran/great_expectations/pull/11160))
- Removed deprecated datetime.utcnow() and utcfromtimestamp() usage so no datetime deprecation warnings are emitted on Python 3.12+. ([#11134](https://github.com/fivetran/great_expectations/pull/11134))
- Bumped image-size from 1.2.0 to 1.2.1 in the documentation site, picking up a denial-of-service fix. ([#11125](https://github.com/fivetran/great_expectations/pull/11125))
- Cleaned up the nightly Redshift test setup. ([#11166](https://github.com/fivetran/great_expectations/pull/11166))
- Clarified the ExpectQueryResultsToMatchSource documentation to note that column names do not matter but column order does. ([#11158](https://github.com/fivetran/great_expectations/pull/11158))
- Restored Redshift credentials needed by the documentation tests in CI. ([#11169](https://github.com/fivetran/great_expectations/pull/11169))
- Split the Redshift tests into their own CI job. ([#11167](https://github.com/fivetran/great_expectations/pull/11167))
- Bumped prismjs from 1.29.0 to 1.30.0 in the documentation site. ([#11126](https://github.com/fivetran/great_expectations/pull/11126))
- Repaired the failing MSSQL compatibility test runs. ([#11153](https://github.com/fivetran/great_expectations/pull/11153))
- Bumped @babel/runtime-corejs3 from 7.26.9 to 7.27.0 in the documentation site. ([#11122](https://github.com/fivetran/great_expectations/pull/11122))

</details>

#### Contributors

Thanks to @esadek (first contribution), @emmanuel-ferdman (first contribution).

### 1.4.3 (2025-05-07)

#### Highlights

- **Redshift data source support in the public API** — Redshift data sources are now exposed through the public API decorator, and new documentation walks through connecting Great Expectations Cloud to Redshift. ([#11097](https://github.com/fivetran/great_expectations/pull/11097), [#11095](https://github.com/fivetran/great_expectations/pull/11095))

- **QueryDataSourceTable metric and provider** — A new QueryDataSourceTable metric and its provider are available, enabling queries against a data source table as part of metric computation. ([#11149](https://github.com/fivetran/great_expectations/pull/11149))

- **ExpectAI approval workflow documentation** — The Cloud documentation now describes the ExpectAI approval workflow for generating and approving Expectations. ([#11072](https://github.com/fivetran/great_expectations/pull/11072))

#### Changes

##### Features

- Added a QueryDataSourceTable metric and accompanying metric provider. ([#11149](https://github.com/fivetran/great_expectations/pull/11149))
- Added test infrastructure to support source-to-target Expectations. ([#11138](https://github.com/fivetran/great_expectations/pull/11138))
- Added the Redshift data source to the public API surface. ([#11097](https://github.com/fivetran/great_expectations/pull/11097))

##### Docs

- Re-enabled the documentation broken-link checker now that the new Redshift pages are published. ([#11135](https://github.com/fivetran/great_expectations/pull/11135))
- Documented the ExpectAI approval workflow for generating Expectations in Great Expectations Cloud. ([#11072](https://github.com/fivetran/great_expectations/pull/11072))
- Added documentation for connecting to Redshift. ([#11095](https://github.com/fivetran/great_expectations/pull/11095))
- Hid the table of contents on documentation pages where nested headers inside tabbed content made it unhelpful. ([#11130](https://github.com/fivetran/great_expectations/pull/11130))
- Updated the Try GX Core code sample so it prints the validation results the surrounding text says you will see. ([#11129](https://github.com/fivetran/great_expectations/pull/11129))

<details>
<summary>Maintenance</summary>

- Removed the temporary gx-sqlalchemy-redshift version pin for Python 3.9, restoring the unpinned requirement. ([#11151](https://github.com/fivetran/great_expectations/pull/11151))
- Removed the obsolete test_expectations_v3_api.py test module. ([#11098](https://github.com/fivetran/great_expectations/pull/11098))
- Removed slow test cases that duplicated coverage of quoted identifiers in column names, substantially shortening Databricks test runs. ([#11152](https://github.com/fivetran/great_expectations/pull/11152))
- Restored the documentation broken-link checker in CI. ([#11146](https://github.com/fivetran/great_expectations/pull/11146))
- Added a SupportedDataSources enum and updated Expectation references and schemas to use it. ([#11143](https://github.com/fivetran/great_expectations/pull/11143))
- Capitalized "Expectation" in the `mostly` parameter description shown in Expectation docstrings and schemas. ([#11147](https://github.com/fivetran/great_expectations/pull/11147))
- Temporarily disabled the documentation broken-link checker in CI while a link issue was resolved. ([#11145](https://github.com/fivetran/great_expectations/pull/11145))
- Temporarily pinned gx-sqlalchemy-redshift for Python 3.9. ([#11142](https://github.com/fivetran/great_expectations/pull/11142))

</details>

### 1.4.2 (2025-04-24)

#### Highlights

- **Redshift connection strings can be supplied as a dictionary** — When adding a Redshift datasource, `connection_string` may now be given as a dictionary of connection components in addition to a string URL. ([#11119](https://github.com/fivetran/great_expectations/pull/11119))

  ```python
  import great_expectations as gx

  context = gx.get_context()
  datasource = context.data_sources.add_redshift(
      name="my_redshift",
      connection_string={
          "drivername": "redshift+psycopg2",
          "username": "my_user",
          "password": "my_password",
          "host": "my-cluster.redshift.amazonaws.com",
          "port": 5439,
          "database": "my_database",
      },
  )
  ```

- **Expectation coverage for Redshift assets** — Expectations running against Redshift assets are now verified to the same level as Postgres, so Redshift users can rely on the same set of expectations behaving as documented. ([#11128](https://github.com/fivetran/great_expectations/pull/11128))

- **More type information shipped with the package** — The published distribution now exposes more of the library's type information, so type checkers resolve Great Expectations types in your own code more completely. ([#11115](https://github.com/fivetran/great_expectations/pull/11115))

#### Changes

##### Features

- Expectations against Redshift assets are now covered to parity with Postgres. ([#11128](https://github.com/fivetran/great_expectations/pull/11128))
- Redshift datasources now accept a `connection_string` provided as a dictionary in addition to a string. ([#11119](https://github.com/fivetran/great_expectations/pull/11119))

<details>
<summary>Maintenance</summary>

- `Batch.compute_metrics()` is now typed to include `MetricErrorResult`, and metric error types were simplified and consolidated. ([#11127](https://github.com/fivetran/great_expectations/pull/11127))
- More type information is now exported in the published PyPI distribution. ([#11115](https://github.com/fivetran/great_expectations/pull/11115))
- Added docstrings for metrics and corrected metric import paths. ([#11118](https://github.com/fivetran/great_expectations/pull/11118))
- Updated the list of core developers credited in the project. ([#11117](https://github.com/fivetran/great_expectations/pull/11117))

</details>

### 1.4.1 (2025-04-21)

#### Highlights

- **New `ColumnDescriptiveStats` metric** — You can now compute a column's minimum, maximum, mean, and standard deviation in a single metric with `ColumnDescriptiveStats`, available on the pandas, SQL, and Spark backends. ([#11108](https://github.com/fivetran/great_expectations/pull/11108), [#11109](https://github.com/fivetran/great_expectations/pull/11109))

  ```python
  from great_expectations.metrics import ColumnDescriptiveStats

  result = batch.compute_metrics(ColumnDescriptiveStats(column="passenger_count"))
  print(result.value.min, result.value.max, result.value.mean, result.value.standard_deviation)
  ```

- **New `ColumnValuesNotMatchRegexCount` metric** — You can now count the values in a column that do not match a regular expression with `ColumnValuesNotMatchRegexCount`, available on the pandas, SQL, and Spark backends. ([#11103](https://github.com/fivetran/great_expectations/pull/11103))

  ```python
  from great_expectations.metrics import ColumnValuesNotMatchRegexCount

  result = batch.compute_metrics(
      ColumnValuesNotMatchRegexCount(column="vendor_id", regex="^(a|d).+")
  )
  print(result.value)
  ```

- **Connect to Redshift with connection details** — A Redshift data source can now be configured by supplying individual connection details instead of a full connection string. ([#11105](https://github.com/fivetran/great_expectations/pull/11105))

- **Redshift schema introspection no longer raises a TypeError** — Using the `gx-redshift` extra to introspect schema information, such as computing column descriptive metrics, no longer fails with a runtime `TypeError`. ([#11112](https://github.com/fivetran/great_expectations/pull/11112))

#### Changes

##### Features

- Added the `ColumnDescriptiveStats` metric, which returns a column's minimum, maximum, mean, and standard deviation on pandas, SQL, and Spark backends. ([#11108](https://github.com/fivetran/great_expectations/pull/11108))
- Redshift data sources can now be configured with individual connection details in addition to a `connection_string`. ([#11105](https://github.com/fivetran/great_expectations/pull/11105))
- Added the `ColumnValuesNotMatchRegexCount` metric, which counts column values that do not match a given regular expression on pandas, SQL, and Spark backends. ([#11103](https://github.com/fivetran/great_expectations/pull/11103))

##### Bug fixes

- Fixed a runtime `TypeError` when using the `gx-redshift` extra to perform schema introspection, such as computing column descriptive metrics. ([#11112](https://github.com/fivetran/great_expectations/pull/11112))
- `ExpectColumnValuesToBeBetween` now correctly rejects configurations where both `min_value` and `max_value` are omitted, `None`, or empty strings. ([#11102](https://github.com/fivetran/great_expectations/pull/11102))
- Fixed `MicrosoftTeamsNotificationAction` failing with a 400 Bad Request when sending notifications. ([#11106](https://github.com/fivetran/great_expectations/pull/11106))

##### Docs

- Temporarily disabled documentation link checking while an upstream issue is resolved. ([#11099](https://github.com/fivetran/great_expectations/pull/11099))

<details>
<summary>Maintenance</summary>

- Reorganized the public metrics package so column metrics are importable from `great_expectations.metrics` under consistent module names. ([#11109](https://github.com/fivetran/great_expectations/pull/11109))
- Fixed pageview analytics tracking and related console errors on the documentation site, and documented local environment setup for it. ([#11093](https://github.com/fivetran/great_expectations/pull/11093))

</details>

#### Contributors

Thanks to @jwalant-dattani (first contribution).

### 1.4.0 (2025-04-15)

Compatibility: new extra `gx-redshift`

#### Highlights

- **Redshift support via a new `gx-redshift` extra** — Great Expectations can now be installed with Redshift support through a dedicated extra, and Redshift is listed among the supported data sources for the expectations that run against it. ([#11092](https://github.com/fivetran/great_expectations/pull/11092), [#11084](https://github.com/fivetran/great_expectations/pull/11084), [#11094](https://github.com/fivetran/great_expectations/pull/11094))

  ```python
  pip install 'great_expectations[gx-redshift]'
  ```

- **SQLAlchemy 2.x support for BigQuery** — The BigQuery extra now works with SQLAlchemy 2.x as well as 1.x, so you can install great_expectations[bigquery] in a SQLAlchemy 2.x environment. ([#11059](https://github.com/fivetran/great_expectations/pull/11059))

  ```python
  pip install 'great_expectations[bigquery]'
  ```

- **New column metrics for sampling and regex counts** — You can compute a sample of values from a column and a count of values matching a regular expression directly from a batch. ([#11083](https://github.com/fivetran/great_expectations/pull/11083), [#11091](https://github.com/fivetran/great_expectations/pull/11091))

  ```python
  from great_expectations.metrics.column.column_values_match_regex_count import (
      ColumnValuesMatchRegexCount,
  )

  metric = ColumnValuesMatchRegexCount(column="my_column", regex="ab")
  result = batch.compute_metrics(metric)
  ```

- **Sets and tuples accepted for `value_set`** — Expectations such as ExpectColumnValuesToBeInSet now accept sets and tuples for `value_set` instead of failing validation; these inputs are coerced to lists automatically. ([#11082](https://github.com/fivetran/great_expectations/pull/11082))

  ```python
  from great_expectations.expectations import ExpectColumnValuesToBeInSet

  expectation = ExpectColumnValuesToBeInSet(
      column="country_name_en",
      value_set={"UNITED STATES", "CHINA", "SPAIN"},
  )
  ```

- **`get_context` honors `context_root_dir`** — Requesting a file-backed Data Context with an explicit root directory now creates and loads the context in that directory. ([#11078](https://github.com/fivetran/great_expectations/pull/11078))

  ```python
  import great_expectations as gx

  context = gx.get_context(mode="file", context_root_dir="/path/to/my/project")
  ```

#### Changes

##### Features

- Add a ColumnValuesMatchRegexCount metric that reports how many column values match a given regular expression, available on Pandas, SQL, and Spark batches. ([#11091](https://github.com/fivetran/great_expectations/pull/11091))
- Add a `gx-redshift` install extra so Redshift dependencies can be installed with `pip install 'great_expectations[gx-redshift]'`. ([#11092](https://github.com/fivetran/great_expectations/pull/11092))
- List Redshift among the supported data sources for the expectations that are verified against Redshift. ([#11084](https://github.com/fivetran/great_expectations/pull/11084))
- Add a ColumnSampleValues metric for retrieving a sample of values from a column. ([#11083](https://github.com/fivetran/great_expectations/pull/11083))
- The BigQuery extra now supports SQLAlchemy 2.x as well as 1.x, requiring sqlalchemy-bigquery 1.11.0 or newer. ([#11059](https://github.com/fivetran/great_expectations/pull/11059))

##### Bug fixes

- Expectations that take a `value_set`, such as ExpectColumnValuesToBeInSet, no longer fail validation when given a set or tuple; such inputs are coerced to a list (strings and bytes excluded). ([#11082](https://github.com/fivetran/great_expectations/pull/11082))
- `get_context` now respects `context_root_dir` when scaffolding and reloading a file-backed Data Context, and the overload accepts `mode="file"` together with `context_root_dir`. ([#11078](https://github.com/fivetran/great_expectations/pull/11078))

##### Docs

- Correct the outdated default Great Expectations directory named in a docstring. ([#11077](https://github.com/fivetran/great_expectations/pull/11077))
- Update the scheduling instructions to match the current user interface. ([#11080](https://github.com/fivetran/great_expectations/pull/11080))

<details>
<summary>Maintenance</summary>

- Run the gx-sqlalchemy-redshift test suite in continuous integration. ([#11094](https://github.com/fivetran/great_expectations/pull/11094))
- Add a ColumnValuesNotMatchRegexValues metric that returns a sample of column values that do not match a given regular expression. ([#11096](https://github.com/fivetran/great_expectations/pull/11096))
- Add a ColumnValuesMatchRegexValues metric that returns a sample of column values matching a regular expression, rather than a pass/fail column map result. ([#11088](https://github.com/fivetran/great_expectations/pull/11088))
- Narrow the return type of `compute_metrics` when called with a single metric, so the result type is known without extra casting. ([#11089](https://github.com/fivetran/great_expectations/pull/11089))
- Add a ColumnDistinctValues metric that returns the distinct values found in a column. ([#11081](https://github.com/fivetran/great_expectations/pull/11081))
- Improve PostHog pageview tracking on the documentation site by disabling automatic capture and tracking single-page navigation instead, removing duplicate pageviews. ([#11087](https://github.com/fivetran/great_expectations/pull/11087))
- Revert the earlier gx-redshift extra, which pointed at a direct GitHub dependency and blocked uploading the release to PyPI. ([#11079](https://github.com/fivetran/great_expectations/pull/11079))
- Add a ColumnNullCount metric that reports the number of null values in a column. ([#11073](https://github.com/fivetran/great_expectations/pull/11073))
- Add a ColumnDistinctValuesCount metric that reports the number of distinct values in a column. ([#11075](https://github.com/fivetran/great_expectations/pull/11075))
- Add a SampleValues metric for retrieving a sample of values from a batch. ([#11071](https://github.com/fivetran/great_expectations/pull/11071))

</details>

#### Contributors

Thanks to @gyermich.

### 1.3.14 (2025-04-08)

Compatibility: `sqlalchemy` minimum set to 1.4.0 (extra `bigquery`); `sqlalchemy` minimum set to 1.4.0 (extra `gcp`)

#### Highlights

- **New `gx-redshift` extra for Redshift users** — Great Expectations can now be installed with a dedicated Redshift extra, `pip install great_expectations[gx-redshift]`, which pulls in a Redshift driver compatible with newer SQLAlchemy versions. Note that installing both `redshift` and `gx-redshift` together will fail to resolve, because their SQLAlchemy requirements do not overlap. ([#11063](https://github.com/fivetran/great_expectations/pull/11063))

  ```python
  pip install great_expectations[gx-redshift]
  ```

- **`ExpectColumnValuesToBeOfType` corrected and SQLAlchemy 2 compatible** — `ExpectColumnValuesToBeOfType` now reports the correct result and works against SQLAlchemy 2 backends. ([#11062](https://github.com/fivetran/great_expectations/pull/11062))

  ```python
  import great_expectations as gx

  suite.add_expectation(
      gx.expectations.ExpectColumnValuesToBeOfType(column="passenger_count", type_="INTEGER")
  )
  ```

- **Cleaner autocompletion for the top-level `gx` namespace** — Importing `great_expectations as gx` no longer suggests the recursive `gx.great_expectations` attribute in IDE autocompletion, so the public API is easier to navigate. Accessing `gx.great_expectations` now raises an `AttributeError`, while `gx.get_context`, `gx.data_context`, `gx.core`, `gx.ExpectationSuite` and the rest of the intended public API remain available. ([#11070](https://github.com/fivetran/great_expectations/pull/11070))

  ```python
  import great_expectations as gx

  context = gx.get_context()  # still available; gx.great_expectations is not
  ```

#### Changes

##### Features

- Added a `gx-redshift` extra so Redshift support can be installed with `pip install great_expectations[gx-redshift]`; installing it alongside the older `redshift` extra will fail to resolve due to non-overlapping SQLAlchemy requirements. ([#11063](https://github.com/fivetran/great_expectations/pull/11063))
- Fixed `ExpectColumnValuesToBeOfType` and made it work with SQLAlchemy 2. ([#11062](https://github.com/fivetran/great_expectations/pull/11062))

##### Bug fixes

- Row conditions containing 8-bit characters such as é, ü and ï are now confirmed to parse correctly, covered by a new test. ([#11053](https://github.com/fivetran/great_expectations/pull/11053))

<details>
<summary>Maintenance</summary>

- Added a `BatchColumnTypes` metric for reporting the column types of a batch. ([#11069](https://github.com/fivetran/great_expectations/pull/11069))
- Importing `great_expectations as gx` no longer exposes a recursive `gx.great_expectations` attribute, improving IDE autocompletion; accessing it now raises an `AttributeError` while the rest of the public API is unchanged. ([#11070](https://github.com/fivetran/great_expectations/pull/11070))
- Documentation site analytics now use the PostHog Docusaurus plugin to capture default pageviews and events. ([#11060](https://github.com/fivetran/great_expectations/pull/11060))

</details>

### 1.3.13 (2025-04-03)

#### Highlights

- **Amazon Redshift data source support** — You can now connect to Amazon Redshift with a dedicated Redshift data source, alongside the existing SQL data sources. ([#11011](https://github.com/fivetran/great_expectations/pull/11011))

#### Changes

##### Features

- Added an initial Amazon Redshift datasource so you can connect Great Expectations directly to Redshift. ([#11011](https://github.com/fivetran/great_expectations/pull/11011))

##### Bug fixes

- Prevented SQLite-specific metric implementations from overriding the default SQLAlchemy implementations, so metrics resolve correctly on other SQL backends. This issue was never present in a published release. ([#11055](https://github.com/fivetran/great_expectations/pull/11055))

##### Docs

- Updated the coverage health screenshot in the documentation. ([#11057](https://github.com/fivetran/great_expectations/pull/11057))
- Follow-up corrections to the completeness change detection documentation. ([#11056](https://github.com/fivetran/great_expectations/pull/11056))
- Added documentation for completeness change detection. ([#11039](https://github.com/fivetran/great_expectations/pull/11039))
- Expanded the test coverage metrics documentation with a reference table. ([#11046](https://github.com/fivetran/great_expectations/pull/11046))
- Clarified which roles can create Data Sources and updated the metrics page to reflect the removal of the asset info card. ([#11052](https://github.com/fivetran/great_expectations/pull/11052))
- Documented that ExpectAI supports only Snowflake Data Sources using password authentication; key-pair authentication is not yet available. ([#11047](https://github.com/fivetran/great_expectations/pull/11047))

<details>
<summary>Maintenance</summary>

- Internal metric registry now resolves metric providers through a single internal lookup path; no user-facing change. ([#11044](https://github.com/fivetran/great_expectations/pull/11044))

</details>

#### Contributors

Thanks to @NathanFarmer.

### 1.3.12 (2025-03-26)

#### Changes

##### Docs

- Corrected the documentation for ExpectColumnKLDivergenceToBeLessThan so its Expectation Gallery entry shows the details already present in the codebase. ([#11040](https://github.com/fivetran/great_expectations/pull/11040))

<details>
<summary>Maintenance</summary>

- Added internal SQLite execution engine support along with one SQLite-specific metric. ([#11042](https://github.com/fivetran/great_expectations/pull/11042))
- Accepted an additional title tag in the pull request title check for contributors. ([#10841](https://github.com/fivetran/great_expectations/pull/10841))

</details>

### 1.3.11 (2025-03-19)

#### Highlights

- **Run checkpoints that use Cloud windowed expectations** — Checkpoints can now be run against suites containing GX Cloud windowed expectations, so validations whose thresholds are derived from a window of past results execute as expected. ([#11027](https://github.com/fivetran/great_expectations/pull/11027))

  ```python
  import great_expectations as gx

  context = gx.get_context(mode="cloud")
  checkpoint = context.checkpoints.get("my_checkpoint")
  result = checkpoint.run()
  ```

- **Distinct values expectations handle dates and datetimes correctly** — Expectations that compare a column's distinct values against a value set now compare correctly when the data holds dates or datetimes but the expectation was configured with string values. Both the validation result and the observed value shown in rendered diagnostic output now report matching values as expected instead of flagging them as unexpected. ([#11030](https://github.com/fivetran/great_expectations/pull/11030), [#11033](https://github.com/fivetran/great_expectations/pull/11033))

  ```python
  import datetime

  import great_expectations as gx

  expectation = gx.expectations.ExpectColumnDistinctValuesToBeInSet(
      column="col A",
      value_set=[str(datetime.date(2024, 11, 19)), str(datetime.date(2024, 11, 20))],
  )
  ```

#### Changes

##### Features

- Checkpoints can now be run with GX Cloud windowed expectations. ([#11027](https://github.com/fivetran/great_expectations/pull/11027))

##### Bug fixes

- ExpectColumnDistinctValuesToContainSet, ExpectColumnDistinctValuesToBeInSet, and ExpectColumnValuesToBeInSet now validate correctly when the column holds dates or datetimes and the value set is given as strings. ([#11030](https://github.com/fivetran/great_expectations/pull/11030))

##### Docs

- Corrected an error in the filesystem data source documentation that led to a regex compile error when adding a batch definition path. ([#11019](https://github.com/fivetran/great_expectations/pull/11019))
- Expectations previously listed under both Numeric and Validity are now documented under Validity only. ([#11008](https://github.com/fivetran/great_expectations/pull/11008))
- Restored the documentation link checker after a temporary workaround. ([#11025](https://github.com/fivetran/great_expectations/pull/11025))

<details>
<summary>Maintenance</summary>

- Rendered diagnostic observed values for distinct-values expectations now compare dates and datetimes correctly when the configured value set was stored as strings, so matching values are no longer shown as unexpected. ([#11033](https://github.com/fivetran/great_expectations/pull/11033))
- Test suites now point at AWS buckets in the open-source account. ([#11034](https://github.com/fivetran/great_expectations/pull/11034))
- Added AWS credentials to the continuous integration configuration. ([#11037](https://github.com/fivetran/great_expectations/pull/11037))
- Reverted the continuous integration change that switched AWS credential secrets, restoring the previous secret variable names. ([#11036](https://github.com/fivetran/great_expectations/pull/11036))
- Updated the AWS secret variable names used by continuous integration (later reverted in this same release). ([#11035](https://github.com/fivetran/great_expectations/pull/11035))
- Removed the timber entry from CODEOWNERS. ([#10996](https://github.com/fivetran/great_expectations/pull/10996))
- Updated the continuous integration workflow so pull request targets are treated as pull-request-event targets. ([#11031](https://github.com/fivetran/great_expectations/pull/11031))
- The context mode is now included in the properties sent with analytics events. ([#11001](https://github.com/fivetran/great_expectations/pull/11001))
- Removed the default role applied when connecting to Snowflake. ([#11004](https://github.com/fivetran/great_expectations/pull/11004))

</details>

#### Contributors

Thanks to @NathanFarmer.

### 1.3.10 (2025-03-12)

#### Highlights

- **Docs reference cards render correctly** — The cards at the top of the docs reference page no longer show stray characters, and the documentation site now builds on the latest Docusaurus with upgraded transitive dependencies that resolve reported vulnerabilities. ([#11009](https://github.com/fivetran/great_expectations/pull/11009))

- **Outdated walkthrough modal removed from Data Docs** — Data Docs no longer opens a walkthrough modal that pointed to the deprecated CLI and workflows that are no longer recommended. ([#11022](https://github.com/fivetran/great_expectations/pull/11022))

#### Changes

##### Docs

- Added documentation covering test coverage metrics. ([#11002](https://github.com/fivetran/great_expectations/pull/11002))
- Applied the new beta badge styling to an additional documentation header. ([#11015](https://github.com/fivetran/great_expectations/pull/11015))

<details>
<summary>Maintenance</summary>

- Raised the MySQL max_connections setting used by the test environment so more MySQL-backed tests can run. ([#11023](https://github.com/fivetran/great_expectations/pull/11023))
- Removed the outdated walkthrough modal from Data Docs, which referenced the deprecated CLI and workflows that are no longer recommended. ([#11022](https://github.com/fivetran/great_expectations/pull/11022))
- Simplified CI failure notifications so skipped jobs no longer trigger alerts. ([#11021](https://github.com/fivetran/great_expectations/pull/11021))
- Upgraded documentation site dependencies to the latest Docusaurus, removed the unused local search plugin, and fixed stray characters rendered in the cards on the docs reference page. ([#11009](https://github.com/fivetran/great_expectations/pull/11009))
- Removed the Numeric data quality issue tag from validity expectations, which are now categorized under Validity only. ([#11005](https://github.com/fivetran/great_expectations/pull/11005))
- Removed redundant tests that are already covered by dedicated test files. ([#11007](https://github.com/fivetran/great_expectations/pull/11007))
- Refactored a number of tests to share a common data context fixture. ([#10997](https://github.com/fivetran/great_expectations/pull/10997))

</details>

### 1.3.9 (2025-03-05)

Compatibility: `pandas-gbq` added (extra `bigquery`); `pandas-gbq` added (extra `gcp`)

#### Highlights

- **Clearer error when checking value ranges on non-numeric columns** — Running ExpectColumnValuesToBeBetween against a column whose underlying type is not numeric or datetime (for example a SQL VARCHAR column) now raises an explicit, actionable Great Expectations error instead of an opaque database exception that could also cause every other expectation in the same run to fail. ([#10995](https://github.com/fivetran/great_expectations/pull/10995))

- **New metrics: query row count, column-pair, and multi-column** — The metrics API gains QueryRowCount, ColumnPairValuesInSetUnexpectedCount, and MultiColumnSumEqualUnexpectedCount, extending the typed metrics you can compute directly against a batch. ([#10964](https://github.com/fivetran/great_expectations/pull/10964), [#10969](https://github.com/fivetran/great_expectations/pull/10969), [#10973](https://github.com/fivetran/great_expectations/pull/10973))

  ```python
  from great_expectations.metrics import QueryRowCount

  metric = QueryRowCount(query="SELECT * FROM my_table WHERE passenger_count > 2")
  result = batch.compute_metrics(metric)
  ```

- **More reliable batch.compute_metrics results** — batch.compute_metrics no longer drops results when two metrics share a name, computes distinct configuration IDs per batch, and always returns a list of results when a list of metrics is passed — so the number of results always matches the number of metrics requested. ([#10979](https://github.com/fivetran/great_expectations/pull/10979))

- **Cleaner Slack notification messages** — Slack validation notifications no longer repeat the link text, highlight the asset and expectation suite names in Markdown for easier scanning, and once again include a summary of how many expectations passed out of the total. ([#10890](https://github.com/fivetran/great_expectations/pull/10890))

#### Changes

##### Features

- Added the first multi-column metric, MultiColumnSumEqualUnexpectedCount, along with multi-column metric support including column_list, row_condition, condition_parser, and ignore_row_if options. ([#10973](https://github.com/fivetran/great_expectations/pull/10973))
- Added the first column-pair metric, ColumnPairValuesInSetUnexpectedCount, with test coverage. ([#10969](https://github.com/fivetran/great_expectations/pull/10969))
- Added a QueryRowCount metric for computing the number of rows returned by a query. ([#10964](https://github.com/fivetran/great_expectations/pull/10964))
- Removed the batch_id parameter from Metric classes, so metrics are defined without specifying a batch. ([#10971](https://github.com/fivetran/great_expectations/pull/10971))

##### Bug fixes

- ExpectColumnValuesToBeBetween now raises a clear error when run against a column whose type is not numeric or datetime, instead of surfacing an opaque database exception. ([#10995](https://github.com/fivetran/great_expectations/pull/10995))
- Batch definitions returned by Asset.get_batch_definition now always include their ID. ([#10986](https://github.com/fivetran/great_expectations/pull/10986))
- Fixed batch.compute_metrics so identically named metrics no longer overwrite each other, configuration IDs differ per batch, and passing a list of metrics always returns a list of results of matching length. ([#10979](https://github.com/fivetran/great_expectations/pull/10979))
- ValidationDefinition add_or_update can now update a batch definition that belongs to a different data source instead of failing unexpectedly. ([#10960](https://github.com/fivetran/great_expectations/pull/10960))

##### Docs

- API reference code blocks now place each method parameter on its own line for easier reading. ([#10985](https://github.com/fivetran/great_expectations/pull/10985))
- Updated the documentation site search key to fix broken search. ([#10994](https://github.com/fivetran/great_expectations/pull/10994))
- Custom action documentation now shows how to define a user-defined field on an action so runtime values can be passed through to custom run logic. ([#10987](https://github.com/fivetran/great_expectations/pull/10987))
- Added documentation covering volume change detection. ([#10927](https://github.com/fivetran/great_expectations/pull/10927))
- Temporarily disabled the documentation link checker while a known issue is resolved. ([#10992](https://github.com/fivetran/great_expectations/pull/10992))
- Fixed the formatting of the parameters for the ValidationDefinition run method in the API reference. ([#10981](https://github.com/fivetran/great_expectations/pull/10981))
- Added a README to the docs scripts folder explaining how to run the API reference link-versioning script. ([#10982](https://github.com/fivetran/great_expectations/pull/10982))
- Documentation pages can now show a beta badge on a section, visible both in the heading and the table of contents. ([#10980](https://github.com/fivetran/great_expectations/pull/10980))
- Added a script that rewrites API reference links with an explicit docs version after a new documentation version is cut, so archived links no longer break. ([#10976](https://github.com/fivetran/great_expectations/pull/10976))
- API reference pages now show a heading above each method's code block. ([#10970](https://github.com/fivetran/great_expectations/pull/10970))
- Made the Airflow provider easier to discover in the documentation. ([#10967](https://github.com/fivetran/great_expectations/pull/10967))

<details>
<summary>Maintenance</summary>

- Removed duplicated metric configuration information from metric error results. ([#10989](https://github.com/fivetran/great_expectations/pull/10989))
- Upgraded ruff from 0.7.2 to 0.9.9. ([#10990](https://github.com/fivetran/great_expectations/pull/10990))
- Added an analytics event for validation definition runs and a mode field on all analytics events distinguishing ephemeral, file, and cloud usage. ([#10984](https://github.com/fivetran/great_expectations/pull/10984))
- Removed the unused table domain key from ExpectTableColumnsToMatchOrderedList. ([#10983](https://github.com/fivetran/great_expectations/pull/10983))
- Changed which GitHub Actions event name is excluded from marker tests in CI. ([#10991](https://github.com/fivetran/great_expectations/pull/10991))
- Upgraded mypy to 1.15.0. ([#10988](https://github.com/fivetran/great_expectations/pull/10988))
- Slack validation notifications drop the duplicated link text, highlight the asset and expectation suite names, and include a summary of expectations met out of the total. ([#10890](https://github.com/fivetran/great_expectations/pull/10890))
- Removed the unused PEP 273 compatibility CI workflow. ([#10975](https://github.com/fivetran/great_expectations/pull/10975))
- Replaced the Domain mixin in the metrics API with dedicated Metric subclasses. ([#10966](https://github.com/fivetran/great_expectations/pull/10966))

</details>

#### Contributors

Thanks to @data-han (first contribution).

### 1.3.8 (2025-02-26)

#### Highlights

- **Compute metrics directly from a Batch** — Batches now expose a `compute_metrics()` method, so you can request one or more metrics for a batch and get back typed results without assembling a validation run. ([#10950](https://github.com/fivetran/great_expectations/pull/10950))

  ```python
  batch = batch_definition.get_batch()
  results = batch.compute_metrics([ColumnMean(column="passenger_count")])
  ```

- **New metrics: column mean and non-null counts** — The metrics API now includes a mean metric along with `ColumnValuesNonNull` and `ColumnValuesNonNullCount`, so you can measure column averages and how many values in a column are populated. ([#10961](https://github.com/fivetran/great_expectations/pull/10961), [#10959](https://github.com/fivetran/great_expectations/pull/10959))

  ```python
  batch.compute_metrics([ColumnValuesNonNullCount(column="passenger_count")])
  ```

- **API reference arguments, returns, and raises now render as tables** — API reference pages present a method's arguments, return values, and raised exceptions in readable tables, and every argument and raised exception is listed instead of only the first one. ([#10910](https://github.com/fivetran/great_expectations/pull/10910), [#10968](https://github.com/fivetran/great_expectations/pull/10968))

#### Changes

##### Features

- Added a mean metric to the metrics API, so column averages can be requested directly. ([#10961](https://github.com/fivetran/great_expectations/pull/10961))
- Added `ColumnValuesNonNull` and `ColumnValuesNonNullCount` metrics for inspecting which column values are populated and how many there are. ([#10959](https://github.com/fivetran/great_expectations/pull/10959))
- Added `Batch.compute_metrics()` for requesting metrics from a batch, with typed metric results. ([#10950](https://github.com/fivetran/great_expectations/pull/10950))

##### Docs

- API reference pages now list every entry under Args and Raises instead of showing only a single row, so documented arguments and exceptions are no longer lost. ([#10968](https://github.com/fivetran/great_expectations/pull/10968))
- Fixed a typo in the documentation. ([#10965](https://github.com/fivetran/great_expectations/pull/10965))
- API reference pages now display arguments, returns, and raises as tables instead of plain bulleted text. ([#10910](https://github.com/fivetran/great_expectations/pull/10910))
- Added a single sign-on call to action to the Cloud user management documentation. ([#10872](https://github.com/fivetran/great_expectations/pull/10872))

<details>
<summary>Maintenance</summary>

- Removed the table domain key from metric domains in the new metrics API. ([#10956](https://github.com/fivetran/great_expectations/pull/10956))
- Removed the `table` parameter from metric domains in the new metrics API. ([#10954](https://github.com/fivetran/great_expectations/pull/10954))

</details>

#### Contributors

Thanks to @VolkovGeoPhy (first contribution).

### 1.3.7 (2025-02-19)

Compatibility: `jinja2` minimum 2.10 → 3

#### Highlights

- **New batch-level row count metric** — A new `BatchRowCount` metric computes the number of rows in a batch and works against pandas, Spark, and SQL (Postgres) data sources. Its result is returned as a typed `BatchRowCountResult`, alongside a new `Batch` metric domain for metrics that compute over an entire batch. ([#10944](https://github.com/fivetran/great_expectations/pull/10944))

  ```python
  from great_expectations.metrics.batch.batch import BatchRowCount

  metric = BatchRowCount(batch_id=batch.id)
  ```

- **Quieter metric resolution** — Batch and column-map expectations no longer carry an unused `table` domain key, so resolving metrics no longer emits a flood of unnecessary log messages. ([#10951](https://github.com/fivetran/great_expectations/pull/10951))

#### Changes

##### Features

- Added the `BatchRowCount` metric and its `BatchRowCountResult`, plus a `Batch` metric domain, for computing row counts over an entire batch on pandas, Spark, and SQL data sources. ([#10944](https://github.com/fivetran/great_expectations/pull/10944))

##### Bug fixes

- Removed the unused `table` domain key from batch and column-map expectations, eliminating the noisy log messages it produced during metric resolution. ([#10951](https://github.com/fivetran/great_expectations/pull/10951))

##### Docs

- Documentation search configuration now uses environment variables in place of hardcoded search keys. ([#10940](https://github.com/fivetran/great_expectations/pull/10940))

<details>
<summary>Maintenance</summary>

- Metric classes now require an explicit `name` rather than having one inferred from the class and domain names, making metric naming predictable. ([#10953](https://github.com/fivetran/great_expectations/pull/10953))
- Dropped support for jinja2 2.x; great_expectations now requires jinja2 3 or newer. ([#10941](https://github.com/fivetran/great_expectations/pull/10941))
- `Metric.config` can no longer be instantiated directly and is hidden from editor auto-complete. ([#10938](https://github.com/fivetran/great_expectations/pull/10938))

</details>

### 1.3.6 (2025-02-14)

#### Highlights

- **ExpectTableRowCountToBeBetween works again with runtime parameters** — Creating or running ExpectTableRowCountToBeBetween with `min_value` or `max_value` supplied as runtime parameters no longer fails validation. Values are only compared to each other when both are concrete; a parameter dictionary is instead checked for a `$PARAMETER` key. ([#10925](https://github.com/fivetran/great_expectations/pull/10925))

  ```python
  gxe.ExpectTableRowCountToBeBetween(
      min_value={"$PARAMETER": "min_rows"},
      max_value={"$PARAMETER": "max_rows"},
  )
  ```

- **Snowflake connections accept passwords with special characters** — Passwords are now URL-quoted before the Snowflake connection URL is built, so credentials containing special characters connect successfully. ([#10919](https://github.com/fivetran/great_expectations/pull/10919))

- **Unexpected rows queries tolerate trailing whitespace and semicolons** — An unexpected rows query that ends with trailing whitespace or a `;` is now trimmed and accepted instead of being rejected. ([#10923](https://github.com/fivetran/great_expectations/pull/10923))

  ```python
  gxe.UnexpectedRowsExpectation(
      unexpected_rows_query="SELECT * FROM {batch} WHERE passenger_count > 6;"
  )
  ```

- **Clear error when cloud mode is requested without credentials** — Requesting a cloud context without the required environment variables now produces the intended, explicit error message instead of an opaque message about the Data Context being `None`. ([#10916](https://github.com/fivetran/great_expectations/pull/10916))

  ```python
  import great_expectations as gx

  context = gx.get_context(mode="cloud")
  ```

- **Documentation for AI-recommended Expectations** — The GX Cloud documentation now covers AI-recommended Expectations. ([#10913](https://github.com/fivetran/great_expectations/pull/10913))

#### Changes

##### Bug fixes

- ExpectTableRowCountToBeBetween can again be created and run when `min_value` or `max_value` is supplied as a runtime parameter; the min/max comparison is only applied when both values are concrete, and parameter dictionaries are validated for a `$PARAMETER` key. ([#10925](https://github.com/fivetran/great_expectations/pull/10925))
- Fixed an incorrect import in the diagnostic checklist test that pulled from the test package. ([#10934](https://github.com/fivetran/great_expectations/pull/10934))
- Metric configuration identifiers are now immutable, preventing identifiers from changing partway through metric computation. ([#10929](https://github.com/fivetran/great_expectations/pull/10929))
- Unexpected rows queries with trailing whitespace or a trailing `;` are now trimmed and accepted. ([#10923](https://github.com/fivetran/great_expectations/pull/10923))
- Snowflake passwords are URL-quoted when building the connection URL, so passwords containing special characters no longer prevent connecting. ([#10919](https://github.com/fivetran/great_expectations/pull/10919))

##### Docs

- Restored a missing test mock for the documentation site's location hook so the "Was this helpful?" component renders and tests pass again. ([#10939](https://github.com/fivetran/great_expectations/pull/10939))
- Removed in-page subsection entries from the documentation sidebar so the correct page is highlighted when selected; the right-hand table of contents continues to provide in-page navigation. ([#10903](https://github.com/fivetran/great_expectations/pull/10903))
- Documentation feedback submissions now create tickets that remain in "Intake" status instead of moving to "To-do". ([#10933](https://github.com/fivetran/great_expectations/pull/10933))
- Moved code examples out of parameter descriptions in the checkpoint action API reference, so email and Slack notification action docs render with correct formatting. ([#10918](https://github.com/fivetran/great_expectations/pull/10918))
- Added documentation for AI-recommended Expectations. ([#10913](https://github.com/fivetran/great_expectations/pull/10913))
- Fixed `*` being rendered as an escaped HTML entity in API reference code blocks. ([#10915](https://github.com/fivetran/great_expectations/pull/10915))

<details>
<summary>Maintenance</summary>

- Introduced a general set of metric result types covering the majority of commonly requested metrics. ([#10932](https://github.com/fivetran/great_expectations/pull/10932))
- Removed documentation snippet files that were no longer referenced by any docs page. ([#10937](https://github.com/fivetran/great_expectations/pull/10937))
- Added `Metric` and `Domain` base classes for defining and instantiating metrics, such as `ColumnValuesBetween` from `great_expectations.metrics`. ([#10920](https://github.com/fivetran/great_expectations/pull/10920))
- Removed the concurrency block from the GitHub CI workflow that was causing jobs to be cancelled. ([#10930](https://github.com/fivetran/great_expectations/pull/10930))
- Requesting a cloud context without the necessary environment variables now raises the intended, clear error instead of an opaque message; existing behavior for `cloud_mode` and explicit `mode` precedence is unchanged. ([#10916](https://github.com/fivetran/great_expectations/pull/10916))

</details>

#### Contributors

Thanks to @eric-brady (first contribution).

### 1.3.5 (2025-02-03)

#### Changes

##### Docs

- Fixed documentation site search behavior. ([#10907](https://github.com/fivetran/great_expectations/pull/10907))
- Documentation admonitions (notes, tips, warnings) now display new icons. ([#10899](https://github.com/fivetran/great_expectations/pull/10899))

<details>
<summary>Maintenance</summary>

- Validation results produced by running a Validation Definition now consistently carry a run identifier. ([#10909](https://github.com/fivetran/great_expectations/pull/10909))
- The Window type now accepts a `strict` setting so it can be used with dynamic-parameter Expectations. ([#10906](https://github.com/fivetran/great_expectations/pull/10906))
- BigQuery test resources are now cleaned up every three hours. ([#10900](https://github.com/fivetran/great_expectations/pull/10900))
- Expanded `row_condition` datetime test coverage for Pandas and Spark, added Spark support for `column_types` and Pandas/Spark I/O options in the Expectation testing framework, corrected handling of Spark partition filenames that contain but do not end in a file name, and documented how to run Spark tests locally. ([#10892](https://github.com/fivetran/great_expectations/pull/10892))

</details>

#### Contributors

Thanks to @nicgrayson.

### 1.3.4 (2025-01-29)

#### Highlights

- **Datetime `row_condition` values no longer truncated to dates** — A `row_condition` that filters on a datetime column now compares the full timestamp instead of being truncated to a date, so expectations validated against Postgres `timestamp` columns filter the rows you asked for. ([#10891](https://github.com/fivetran/great_expectations/pull/10891))

- **Clearer API reference pages** — API reference pages now render method signatures as Python code blocks and class properties as tables, making them easier to scan. ([#10882](https://github.com/fivetran/great_expectations/pull/10882), [#10880](https://github.com/fivetran/great_expectations/pull/10880))

- **Migration guide available in the 0.18 docs** — The 0.18 documentation now includes the migration guide, so users still on 0.18 can find upgrade instructions without leaving the versioned docs. ([#10885](https://github.com/fivetran/great_expectations/pull/10885))

#### Changes

##### Bug fixes

- Fixed `row_condition` datetime values being truncated to dates against Postgres `timestamp` columns, and expanded date-type test coverage across backends. ([#10891](https://github.com/fivetran/great_expectations/pull/10891))

##### Docs

- Removed incorrectly versioned 0.18 copies of the docs home page and integration support policy page, and hid the version dropdown on the Integration support policy and Get support pages. ([#10893](https://github.com/fivetran/great_expectations/pull/10893))
- Documented dynamic parameters for completeness expectations in the expectation management docs. ([#10873](https://github.com/fivetran/great_expectations/pull/10873))
- API reference pages now display method signatures as Python code blocks. ([#10882](https://github.com/fivetran/great_expectations/pull/10882))
- API reference pages now display class properties as tables. ([#10880](https://github.com/fivetran/great_expectations/pull/10880))
- Restored the lychee link check for the documentation. ([#10889](https://github.com/fivetran/great_expectations/pull/10889))
- Added the migration guide to the 0.18 documentation. ([#10885](https://github.com/fivetran/great_expectations/pull/10885))

<details>
<summary>Maintenance</summary>

- Simplified the permissions checker workflow so it fails when a user lacks permissions, without a separate bot check. ([#10895](https://github.com/fivetran/great_expectations/pull/10895))
- Pull requests opened from forks can now run CI after a repository member retries the failed jobs. ([#10894](https://github.com/fivetran/great_expectations/pull/10894))

</details>

### 1.3.3 (2025-01-22)

Compatibility: `databricks-sql-connector` removed (extra `databricks`); `databricks-sqlalchemy` added (extra `databricks`)

#### Highlights

- **Expectations with identical attributes can now coexist in a Suite** — Adding two Expectations of different types that happen to have identical attributes to the same Suite now works as expected — previously the second Expectation was silently not added. ([#10884](https://github.com/fivetran/great_expectations/pull/10884))

  ```python
  suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="passenger_count"))
  suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="passenger_count"))
  ```

- **Validation result descriptions are JSON-serializable** — `describe_dict()` on suite and expectation validation results now returns a plain, JSON-serializable dictionary, so the output of `describe()` can be passed straight to `json.dumps` without errors. ([#10863](https://github.com/fivetran/great_expectations/pull/10863))

  ```python
  result = batch.validate(suite)
  print(json.dumps(result.describe_dict()))
  ```

- **Databricks SQLAlchemy support via `databricks-sqlalchemy`** — Databricks connectivity now relies on the `databricks-sqlalchemy` package instead of `databricks-sql-connector`, which dropped SQLAlchemy support in its 4.0.0 release. Installing the `databricks` extra pulls in the new dependency. ([#10886](https://github.com/fivetran/great_expectations/pull/10886))

#### Changes

##### Bug fixes

- Expectations of different types with identical attributes can now both be added to the same Suite. ([#10884](https://github.com/fivetran/great_expectations/pull/10884))
- `describe_dict()` on suite and expectation validation results now returns a JSON-serializable dictionary, so `describe()` output can be passed to `json.dumps`. ([#10863](https://github.com/fivetran/great_expectations/pull/10863))

##### Docs

- Corrected and clarified the documentation on choosing a result format. ([#10875](https://github.com/fivetran/great_expectations/pull/10875))
- Updated the documentation about batch parameters and linked to the updated API docs. ([#10877](https://github.com/fivetran/great_expectations/pull/10877))
- API Reference pages now show titles for the properties and methods sections. ([#10821](https://github.com/fivetran/great_expectations/pull/10821))

<details>
<summary>Maintenance</summary>

- Databricks support now uses the `databricks-sqlalchemy` package instead of `databricks-sql-connector`, which removed SQLAlchemy support in version 4.0.0. ([#10886](https://github.com/fivetran/great_expectations/pull/10886))
- Reworked the batch test setup helpers so tests create their own assets instead of sharing one, avoiding duplicate batch definition names across tests. ([#10864](https://github.com/fivetran/great_expectations/pull/10864))
- Added a method for setting the analytics user agent string. ([#10883](https://github.com/fivetran/great_expectations/pull/10883))
- Analytics events and contexts now carry a user agent string, allowing callers such as GX operators to identify themselves. ([#10869](https://github.com/fivetran/great_expectations/pull/10869))
- The S3 store backend now correctly handles objects returned with `aws-chunked` content encoding. ([#10861](https://github.com/fivetran/great_expectations/pull/10861))

</details>

### 1.3.2 (2025-01-17)

#### Highlights

- **Strict bounds for table row count expectations** — `ExpectTableRowCountToBeBetween` now accepts `strict_min` and `strict_max`, so you can require the row count to be strictly greater than the minimum and strictly less than the maximum. ([#10845](https://github.com/fivetran/great_expectations/pull/10845))

  ```python
  import great_expectations.expectations as gxe

  expectation = gxe.ExpectTableRowCountToBeBetween(
      min_value=10,
      max_value=100,
      strict_min=True,
      strict_max=True,
  )
  ```

- **Add or update a Checkpoint in one call** — The Checkpoint factory now offers `add_or_update`, which creates a Checkpoint if it does not exist yet and replaces the stored configuration if it does. ([#10856](https://github.com/fivetran/great_expectations/pull/10856))

  ```python
  checkpoint = context.checkpoints.add_or_update(checkpoint)
  ```

- **Faster feedback on invalid Expectation arguments** — Several Expectations now validate their input arguments when you create them, raising an error immediately instead of failing partway through validation. Multicolumn map Expectations also now require at least two entries in `column_list`. ([#10833](https://github.com/fivetran/great_expectations/pull/10833), [#10850](https://github.com/fivetran/great_expectations/pull/10850))

#### Changes

##### Features

- `ExpectTableRowCountToBeBetween` now supports the `strict_min` and `strict_max` parameters. ([#10845](https://github.com/fivetran/great_expectations/pull/10845))
- Added `add_or_update` to the Checkpoint factory so a Checkpoint can be created or replaced in a single call. ([#10856](https://github.com/fivetran/great_expectations/pull/10856))

##### Bug fixes

- Several Expectations now validate their input arguments up front and raise an error immediately rather than failing during validation. ([#10833](https://github.com/fivetran/great_expectations/pull/10833))
- Expectations backed by pandas `Series.between()` now handle all combinations of inclusive bounds correctly across supported pandas versions. ([#10837](https://github.com/fivetran/great_expectations/pull/10837))
- `ExpectColumnUniqueValueCountToBeBetween` now honors `strict_min` and `strict_max`, which were previously ignored. ([#10835](https://github.com/fivetran/great_expectations/pull/10835))

##### Docs

- Updated a documentation screenshot to reflect the current handling of observed values in the validation run history view. ([#10867](https://github.com/fivetran/great_expectations/pull/10867))
- Corrected the documented approach for defining a custom SQL Expectation in GX Cloud. ([#10844](https://github.com/fivetran/great_expectations/pull/10844))
- Added explicit anchor IDs to repeated headings in the documentation so that direct links to a section now land on the intended section. ([#10846](https://github.com/fivetran/great_expectations/pull/10846))
- Corrected typos and removed an outdated reference to suites in the GX Cloud UI from the data quality use case pages. ([#10847](https://github.com/fivetran/great_expectations/pull/10847))
- Documented how to request the GX Agent from within the GX Cloud app on the agent deployment page. ([#10836](https://github.com/fivetran/great_expectations/pull/10836))
- Updated the documented location of the "generate snippet" button in the Airflow connection instructions. ([#10854](https://github.com/fivetran/great_expectations/pull/10854))
- Consolidated the documentation about analytics and usage statistics into a single place. ([#10853](https://github.com/fivetran/great_expectations/pull/10853))
- Corrected the capitalization of admonition titles throughout the documentation. ([#10813](https://github.com/fivetran/great_expectations/pull/10813))
- Reorganized the Expectation selection documentation so Expectations are grouped by the data quality issue they address. ([#10806](https://github.com/fivetran/great_expectations/pull/10806))

<details>
<summary>Maintenance</summary>

- Multicolumn map Expectations now reject a `column_list` with fewer than two columns when the Expectation is created. ([#10850](https://github.com/fivetran/great_expectations/pull/10850))
- Continuous integration now skips the slow quoted-identifier tests that were already expected to fail. ([#10857](https://github.com/fivetran/great_expectations/pull/10857))
- Unpinned `snowflake-sqlalchemy`, excluding only the broken 1.7.0 release. ([#10838](https://github.com/fivetran/great_expectations/pull/10838))
- Applied a temporary fix to get past a failing test schema cleanup step. ([#10860](https://github.com/fivetran/great_expectations/pull/10860))
- Microsoft SQL Server tests now run against the version 18 ODBC driver, with connection strings updated and consolidated accordingly. ([#10868](https://github.com/fivetran/great_expectations/pull/10868))
- Pinned `boto3` to avoid a behavior change in a newer release. ([#10862](https://github.com/fivetran/great_expectations/pull/10862))
- Removed an expected-to-fail Databricks test case for `ExpectColumnValuesToBeInTypeList` from the test suite. ([#10843](https://github.com/fivetran/great_expectations/pull/10843))
- Updated the `responses` version pin to avoid a type-checking error in its latest release. ([#10842](https://github.com/fivetran/great_expectations/pull/10842))
- The `invoke deps` development task now accepts a `--force-reinstall` flag and has clearer help text. ([#10834](https://github.com/fivetran/great_expectations/pull/10834))

</details>

### 1.3.1 (2025-01-08)

Compatibility: `posthog` minimum 2.1.0 removed

#### Highlights

- **Suite parameters in the `mostly` field** — Column map expectations now accept a suite parameter for `mostly`, so the threshold can be supplied at validation time instead of being fixed when the expectation is defined. ([#10829](https://github.com/fivetran/great_expectations/pull/10829))

  ```python
  import great_expectations as gx

  expectation = gx.expectations.ExpectColumnValuesToNotBeNull(
      column="passenger_count",
      mostly={"$PARAMETER": "my_mostly"},
  )
  result = batch.validate(expectation, expectation_parameters={"my_mostly": 0.9})
  ```

- **`add_or_update` for suites and validation definitions** — You can now add a suite or a validation definition if it does not exist, or update it in place if it does, in a single call. ([#10796](https://github.com/fivetran/great_expectations/pull/10796), [#10818](https://github.com/fivetran/great_expectations/pull/10818))

  ```python
  suite = context.suites.add_or_update(suite)
  validation_definition = context.validation_definitions.add_or_update(validation_definition)
  ```

- **Observed values render again for expectations with descriptions** — Validation results in Data Docs and GX Cloud now show the observed value for an expectation that has a description, instead of rendering the description in its place. ([#10826](https://github.com/fivetran/great_expectations/pull/10826))

- **`datetime.time` values serialize to JSON** — Values of type `datetime.time` can now be serialized, and are written out as ISO-format strings rather than raising a serialization error. ([#10795](https://github.com/fivetran/great_expectations/pull/10795))

#### Changes

##### Features

- Column map expectations accept a suite parameter for the `mostly` field, so the threshold can be provided at validation time. ([#10829](https://github.com/fivetran/great_expectations/pull/10829))
- Added `context.suites.add_or_update`, which adds a suite or updates the existing one with the same name. ([#10796](https://github.com/fivetran/great_expectations/pull/10796))

##### Bug fixes

- An expectation's description no longer replaces the observed value in rendered validation results. ([#10826](https://github.com/fivetran/great_expectations/pull/10826))
- `datetime.time` values are now serialized to JSON as ISO-format strings instead of failing. ([#10795](https://github.com/fivetran/great_expectations/pull/10795))

##### Docs

- Reworked the Learn data pipeline tutorial page to present it as a general guide to integrating GX into a data pipeline rather than an Airflow-specific tutorial. ([#10828](https://github.com/fivetran/great_expectations/pull/10828))
- Updated the list of other supported databases in the documentation. ([#10812](https://github.com/fivetran/great_expectations/pull/10812))
- Added the Common Room web tracking snippet to the documentation site. ([#10805](https://github.com/fivetran/great_expectations/pull/10805))
- Admonition titles in the documentation are no longer forced to uppercase. ([#10800](https://github.com/fivetran/great_expectations/pull/10800))
- Updated the buttons in the documentation home page banner. ([#10804](https://github.com/fivetran/great_expectations/pull/10804))
- Added an architecture decision record describing the docstring requirements for public API objects. ([#10798](https://github.com/fivetran/great_expectations/pull/10798))
- Replaced remaining references to `context.sources` with `context.data_sources` across the documentation, code comments, and error messages. ([#10794](https://github.com/fivetran/great_expectations/pull/10794))
- Restored Lychee link checking for the documentation site. ([#10797](https://github.com/fivetran/great_expectations/pull/10797))

<details>
<summary>Maintenance</summary>

- Restored `context.validation_definitions.add_or_update`, which adds a validation definition or updates the existing one. ([#10818](https://github.com/fivetran/great_expectations/pull/10818))
- Improved logging in the BigQuery cleanup job and skipped the cleanup query when there are no stale schemas to remove. ([#10824](https://github.com/fivetran/great_expectations/pull/10824))
- Lowered a noisy SQLAlchemy-related log message from warning to debug when validating column-type expectations. ([#10790](https://github.com/fivetran/great_expectations/pull/10790))
- Suppressed Marshmallow V4 migration warnings. ([#10825](https://github.com/fivetran/great_expectations/pull/10825))
- Added a recent formatting-only commit to the git blame ignore list. ([#10822](https://github.com/fivetran/great_expectations/pull/10822))
- Added a lint check requiring an explanatory comment alongside `# type: ignore` and `# noqa:` suppressions, and annotated existing suppressions. ([#10817](https://github.com/fivetran/great_expectations/pull/10817))
- Fixed the BigQuery test-resource cleanup script. ([#10820](https://github.com/fivetran/great_expectations/pull/10820))
- Installed the BigQuery requirements file when running the BigQuery cleanup script. ([#10819](https://github.com/fivetran/great_expectations/pull/10819))
- Added a check that every object marked as public API carries a docstring. ([#10799](https://github.com/fivetran/great_expectations/pull/10799))
- Added a nightly job that cleans up stray BigQuery schemas left behind by CI. ([#10815](https://github.com/fivetran/great_expectations/pull/10815))
- Updated the remaining expectations to reference the canonical data quality issue names. ([#10807](https://github.com/fivetran/great_expectations/pull/10807))
- Upgraded the `posthog` analytics dependency to version 3. ([#10814](https://github.com/fivetran/great_expectations/pull/10814))

</details>

### 1.3.0 (2024-12-19)

#### Highlights

- **Databricks column type expectations now evaluate correctly** — `ExpectColumnValuesToBeInType` and `ExpectColumnValuesToBeInTypeList` now translate Databricks column types correctly, so type checks against Databricks tables evaluate as expected instead of failing on unrecognized type names. ([#10791](https://github.com/fivetran/great_expectations/pull/10791), [#10787](https://github.com/fivetran/great_expectations/pull/10787))

  ```python
  import great_expectations as gx

  suite.add_expectation(
      gx.expectations.ExpectColumnValuesToBeInTypeList(
          column="passenger_count", type_list=["BIGINT", "INT"]
      )
  )
  ```

- **`table.column_type` resolves correctly on Snowflake and Postgres** — Column type evaluation against Snowflake and Postgres now reports the correct type, so expectations that depend on column types produce accurate results on these backends. ([#10776](https://github.com/fivetran/great_expectations/pull/10776), [#10793](https://github.com/fivetran/great_expectations/pull/10793), [#10786](https://github.com/fivetran/great_expectations/pull/10786))

- **`UnexpectedRowsExpectation` results render in Data Docs** — `UnexpectedRowsExpectation` now renders a readable summary in Data Docs, including an observed value that is reported as an integer count for consistency with other expectations. ([#10758](https://github.com/fivetran/great_expectations/pull/10758), [#10779](https://github.com/fivetran/great_expectations/pull/10779), [#10777](https://github.com/fivetran/great_expectations/pull/10777))

- **Expectation descriptions display correctly in Data Docs** — Custom expectation descriptions now appear as proper table cells in Data Docs validation results rather than rendering as internal renderer keys, and descriptions supplied from GX Cloud are handled as well. ([#10789](https://github.com/fivetran/great_expectations/pull/10789), [#10768](https://github.com/fivetran/great_expectations/pull/10768))

- **Simpler imports for writing custom validation actions** — `CheckpointResult` and `ActionContext` can now be imported directly from the top-level checkpoint module, and the `ValidationAction` building blocks needed to write a custom action are documented as public API alongside a new guide. ([#10788](https://github.com/fivetran/great_expectations/pull/10788), [#10752](https://github.com/fivetran/great_expectations/pull/10752), [#10772](https://github.com/fivetran/great_expectations/pull/10772))

  ```python
  from great_expectations.checkpoint import ActionContext, CheckpointResult
  ```

#### Deprecations

- `DataContext.add_or_update_datasource` is deprecated. Removal in 2.0.0. ([#10784](https://github.com/fivetran/great_expectations/pull/10784))

#### Changes

##### Bug fixes

- The `table.column_type` metric now evaluates correctly against Postgres. ([#10793](https://github.com/fivetran/great_expectations/pull/10793))
- `ExpectColumnValuesToBeInTypeList` and `ExpectColumnValuesToBeInType` now translate column types correctly on Databricks. ([#10791](https://github.com/fivetran/great_expectations/pull/10791))
- Expectation descriptions now render as proper cells in Data Docs validation result tables instead of exposing internal renderer keys. ([#10789](https://github.com/fivetran/great_expectations/pull/10789))
- The `table.column_type` metric now evaluates correctly against Snowflake. ([#10776](https://github.com/fivetran/great_expectations/pull/10776))
- The observed value for `UnexpectedRowsExpectation` is now reported as an integer, consistent with other expectations. ([#10777](https://github.com/fivetran/great_expectations/pull/10777))
- `UnexpectedRowsExpectation` now renders a readable summary in Data Docs. ([#10758](https://github.com/fivetran/great_expectations/pull/10758))
- Expectation descriptions supplied from GX Cloud are now handled when rendering results. ([#10768](https://github.com/fivetran/great_expectations/pull/10768))

##### Docs

- `ValidationAction` and the related components needed to build a custom action are now documented as part of the public API. ([#10752](https://github.com/fivetran/great_expectations/pull/10752))
- Added documentation on detecting schema changes in your data. ([#10755](https://github.com/fivetran/great_expectations/pull/10755))
- Added a guide for creating a custom action that runs based on validation results. ([#10772](https://github.com/fivetran/great_expectations/pull/10772))
- Removed an unnecessary escape character from an Expectation docstring so it renders correctly in the Expectation Gallery. ([#10780](https://github.com/fivetran/great_expectations/pull/10780))
- Fixed the underline styling of links on inline code in the documentation so they are easier to read. ([#10783](https://github.com/fivetran/great_expectations/pull/10783))
- Reorganized and updated the core documentation for setting up and using GX. ([#10665](https://github.com/fivetran/great_expectations/pull/10665))
- Removed a documentation tip that suggested printing `validation_results.result_url`, which is not supported. ([#10760](https://github.com/fivetran/great_expectations/pull/10760))
- Clarified the Connect GX Cloud landing page. ([#10761](https://github.com/fivetran/great_expectations/pull/10761))

<details>
<summary>Maintenance</summary>

- Added Databricks-specific type definitions so Databricks column types are recognized when evaluating expectations. ([#10787](https://github.com/fivetran/great_expectations/pull/10787))
- Cleaned up environment variables used by the cloud test suite. ([#10792](https://github.com/fivetran/great_expectations/pull/10792))
- `CheckpointResult` and `ActionContext` can now be imported directly from the top-level checkpoint module, simplifying custom action code. ([#10788](https://github.com/fivetran/great_expectations/pull/10788))
- `DataContext.add_or_update_datasource` is now marked as deprecated. ([#10784](https://github.com/fivetran/great_expectations/pull/10784))
- Added EventBridge Scheduler service coverage to the cloud test suite. ([#10774](https://github.com/fivetran/great_expectations/pull/10774))
- The public API report tooling now verifies that referenced file paths exist. ([#10754](https://github.com/fivetran/great_expectations/pull/10754))
- Removed the stale `isort` references from the developer task definitions now that linting is handled by `ruff`. ([#10782](https://github.com/fivetran/great_expectations/pull/10782))
- Removed the outdated GX Cloud onboarding script. ([#10785](https://github.com/fivetran/great_expectations/pull/10785))
- Added more test coverage for Snowflake column types. ([#10786](https://github.com/fivetran/great_expectations/pull/10786))
- Core Expectation docstrings and schemas now use a shared set of data quality issue names, with several typos corrected. ([#10759](https://github.com/fivetran/great_expectations/pull/10759))
- Removed the hand-rolled documentation link checker in favor of the existing Lychee-based check. ([#10781](https://github.com/fivetran/great_expectations/pull/10781))
- Added an observed value renderer for `UnexpectedRowsExpectation`. ([#10779](https://github.com/fivetran/great_expectations/pull/10779))
- Added a diagram explaining how the multi-datasource test setup works. ([#10766](https://github.com/fivetran/great_expectations/pull/10766))
- Cleaned up and refactored the code behind column type expectations with no change in behavior. ([#10764](https://github.com/fivetran/great_expectations/pull/10764))
- Reverted the continuous integration change that ran pull request workflows with elevated triggers and an actor permissions check; CI once again runs on standard pull request events, with credentialed jobs restricted to the main repository. ([#10773](https://github.com/fivetran/great_expectations/pull/10773))
- Continuous integration workflows were changed to run on pull request targets with an actor permissions check so that CI can run on pull requests from forks; this change was reverted later in this release. ([#10467](https://github.com/fivetran/great_expectations/pull/10467))

</details>

### 1.2.6 (2024-12-11)

#### Highlights

- **Define your own custom validation actions** — You can now define custom actions and use them in Great Expectations validation workflows. Custom action classes are picked up automatically and serialize and deserialize correctly alongside built-in actions. ([#10743](https://github.com/fivetran/great_expectations/pull/10743))

  ```python
  from great_expectations.checkpoint.actions import ValidationAction


  class MyCustomAction(ValidationAction):
      type: str = "my_custom_action"

      def run(self, checkpoint_result, action_context=None):
          ...
  ```

- **Pattern-matching expectations no longer require optional SQL dependencies** — LikePattern expectations now run in environments where the MySQL, MsSQL, or PostgreSQL SQLAlchemy libraries are not installed, instead of failing on a faulty attribute check. ([#10745](https://github.com/fivetran/great_expectations/pull/10745))

- **ExpectTableColumnsToMatchSet now defaults to exact matching** — The exact_match parameter of ExpectTableColumnsToMatchSet now defaults to True, matching the behavior described in the Expectation Gallery documentation. ([#10746](https://github.com/fivetran/great_expectations/pull/10746))

  ```python
  import great_expectations.expectations as gxe

  # exact_match now defaults to True
  expectation = gxe.ExpectTableColumnsToMatchSet(column_set=["id", "name"])
  ```

#### Changes

##### Features

- You can now define your own custom validation actions; they are registered automatically and serialize and deserialize correctly. ([#10743](https://github.com/fivetran/great_expectations/pull/10743))

##### Bug fixes

- Fetching metrics for multiple data assets in a single call no longer returns metrics from a previously cached asset; the batch is now checked against the incoming batch request. ([#10744](https://github.com/fivetran/great_expectations/pull/10744))
- ExpectTableColumnsToMatchSet now defaults exact_match to True, matching its documented behavior. ([#10746](https://github.com/fivetran/great_expectations/pull/10746))
- LikePattern expectations now work in environments without the MySQL, MsSQL, or PostgreSQL SQLAlchemy libraries installed. ([#10745](https://github.com/fivetran/great_expectations/pull/10745))

##### Docs

- Documented key-pair authentication for connecting to Snowflake. ([#10751](https://github.com/fivetran/great_expectations/pull/10751))
- Updated the content of the documentation site banner. ([#10747](https://github.com/fivetran/great_expectations/pull/10747))
- Refreshed the Row Condition guidance, with consistent punctuation and corrected indentation in the examples. ([#10736](https://github.com/fivetran/great_expectations/pull/10736))

<details>
<summary>Maintenance</summary>

- Loosened a BigQuery test assertion so it tolerates BigQuery's updated error message wording. ([#10750](https://github.com/fivetran/great_expectations/pull/10750))
- Added an atomic diagnostic observed-value renderer for ExpectTableColumnsToMatchSet that highlights unexpected and missing columns whether or not the Expectation passed. ([#10748](https://github.com/fivetran/great_expectations/pull/10748))
- Test schemas are now created with a common prefix so they are easier to identify and clean up manually. ([#10742](https://github.com/fivetran/great_expectations/pull/10742))
- The expectation testing framework now allows developers to override the randomly generated table name when using SQL data sources. ([#10724](https://github.com/fivetran/great_expectations/pull/10724))
- Added integration test coverage for UnexpectedRowsExpectation, including JOIN queries against a second table and partitioned batches, across the supported SQL and Spark data sources. ([#10733](https://github.com/fivetran/great_expectations/pull/10733))

</details>

### 1.2.5 (2024-12-04)

#### Highlights

- **Observed-value rendering for value-set Expectations** — Validation results for value-set Expectations — including expect_column_distinct_values_to_be_in_set, expect_column_distinct_values_to_contain_set, and expect_column_most_common_value_to_be_in_set — now render their observed values as atomic content, with each observed item marked as expected or unexpected so it is clear which values fell outside the configured set. ([#10718](https://github.com/fivetran/great_expectations/pull/10718), [#10697](https://github.com/fivetran/great_expectations/pull/10697))

  ```python
  result = batch.validate(gxe.ExpectColumnDistinctValuesToBeInSet(column="species", value_set=["setosa", "virginica"]))
  rendered = result.render()
  ```

- **Observed-value renderer for expect_table_columns_to_match_ordered_list** — Validation results for expect_table_columns_to_match_ordered_list now include a rendered observed value, so the actual column list is displayed alongside the expected ordered list. ([#10683](https://github.com/fivetran/great_expectations/pull/10683))

- **The \{batch} keyword works with partitioned batches across more backends** — UnexpectedRowsExpectation queries that reference the \{batch} keyword now resolve correctly when the batch comes from a partitioner, including queries that use JOIN clauses, where previously some SQL backends raised errors or produced invalid SQL. ([#10721](https://github.com/fivetran/great_expectations/pull/10721))

  ```python
  gxe.UnexpectedRowsExpectation(unexpected_rows_query="SELECT * FROM {batch} WHERE passenger_count > 7")
  ```

- **Version check no longer fails on network errors** — Great Expectations now handles connection failures while checking for a newer released version instead of surfacing an error to the user, so the library keeps working when there is no network access. ([#10720](https://github.com/fivetran/great_expectations/pull/10720))

#### Changes

##### Features

- Value-set Expectations now render their observed values as atomic content, marking each observed value as expected or unexpected relative to the configured value set. ([#10718](https://github.com/fivetran/great_expectations/pull/10718))
- Validation results for expect_table_columns_to_match_ordered_list now render the observed column list. ([#10683](https://github.com/fivetran/great_expectations/pull/10683))

##### Bug fixes

- UnexpectedRowsExpectation queries using the \{batch} keyword now resolve correctly for partitioned batches on more SQL backends, including queries containing JOIN clauses. ([#10721](https://github.com/fivetran/great_expectations/pull/10721))
- Connection errors raised while checking for the latest released version of Great Expectations are now handled gracefully. ([#10720](https://github.com/fivetran/great_expectations/pull/10720))

##### Docs

- Corrected a typo in the documentation. ([#10725](https://github.com/fivetran/great_expectations/pull/10725))
- Fixed incorrect data types shown in the batch definition examples and removed an unused code snippet from the retrieve-a-batch-of-test-data docs. ([#10723](https://github.com/fivetran/great_expectations/pull/10723))
- Added a data quality article covering freshness. ([#10612](https://github.com/fivetran/great_expectations/pull/10612))
- Corrected the dependency listed in the Set Up a GX Environment documentation. ([#10722](https://github.com/fivetran/great_expectations/pull/10722))
- The documentation site announcement bar can no longer be dismissed. ([#10719](https://github.com/fivetran/great_expectations/pull/10719))
- Fixed a set of broken links throughout the documentation. ([#10716](https://github.com/fivetran/great_expectations/pull/10716))
- Restored the close button on the documentation site announcement bar, which was not displaying on the published site. ([#10717](https://github.com/fivetran/great_expectations/pull/10717))
- Added titles to documentation code blocks so they no longer overlap in display, and removed an unused snippet. ([#10708](https://github.com/fivetran/great_expectations/pull/10708))
- Removed published documentation pages that were no longer reachable from the site navigation. ([#10704](https://github.com/fivetran/great_expectations/pull/10704))
- Added a data quality article covering uniqueness. ([#10584](https://github.com/fivetran/great_expectations/pull/10584))
- Updated the announcement banner on the documentation site. ([#10703](https://github.com/fivetran/great_expectations/pull/10703))
- Updated the Manage Data Assets page to match the current UI and removed duplicated content. ([#10695](https://github.com/fivetran/great_expectations/pull/10695))
- Listed Databricks as a supported data source for the Expectations that support it in the Expectation gallery. ([#10691](https://github.com/fivetran/great_expectations/pull/10691))
- Added documentation redirects and fixed existing redirects that pointed to a retired legacy docs site. ([#10692](https://github.com/fivetran/great_expectations/pull/10692))
- Updated the "Connect GX Cloud to ..." pages to reflect the current workflow. ([#10689](https://github.com/fivetran/great_expectations/pull/10689))
- Applied the non-versioned section styling consistently across the GX Cloud documentation section. ([#10694](https://github.com/fivetran/great_expectations/pull/10694))
- Added documentation for Expectation conditions in GX Cloud. ([#10690](https://github.com/fivetran/great_expectations/pull/10690))

<details>
<summary>Maintenance</summary>

- Added test coverage for Expectation behavior against PostgreSQL column types. ([#10727](https://github.com/fivetran/great_expectations/pull/10727))
- Removed a log message from the datasource store that could include sensitive information. ([#10729](https://github.com/fivetran/great_expectations/pull/10729))
- Added tests for the remaining Expectations that were not yet covered by the new test suite. ([#10715](https://github.com/fivetran/great_expectations/pull/10715))
- Added tests that exercise Expectations against Snowflake column types. ([#10706](https://github.com/fivetran/great_expectations/pull/10706))
- Added tests asserting that misconfigured Expectations fail with informative error messages. ([#10696](https://github.com/fivetran/great_expectations/pull/10696))
- Added a new per-Expectation test suite structure with broader coverage of Expectation behavior. ([#10688](https://github.com/fivetran/great_expectations/pull/10688))
- Added an observed-value renderer for expect_column_most_common_value_to_be_in_set and a render state on rendered content parameters so individual set items can be shown as expected or unexpected. ([#10697](https://github.com/fivetran/great_expectations/pull/10697))
- Pinned snowflake-sqlalchemy to avoid a breaking change in that dependency. ([#10698](https://github.com/fivetran/great_expectations/pull/10698))

</details>

### 1.2.4 (2024-11-20)

#### Highlights

- **Duplicate expectations are no longer added to a suite** — Adding an expectation that already exists in a suite no longer creates a duplicate entry: uniqueness checks now compare the expectation itself, ignoring its identifier and the volatile `notes` and `meta` fields. Suite docstrings also point to suite indexing when deleting an expectation. ([#10662](https://github.com/fivetran/great_expectations/pull/10662))

  ```python
  for _ in range(10):
      suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="passenger_count", min_value=0, max_value=6))

  print(len(suite.expectations))  # 1
  ```

- **Expectation conditions documentation refreshed** — The Expectation conditions documentation has been rewritten with clearer language and separate, runnable examples for pandas, Spark, and SQL in every case. ([#10661](https://github.com/fivetran/great_expectations/pull/10661))

- **Passing a plain string as a condition parser** — Supplying a string where the `ConditionParser` enum was previously required no longer raises a type error. ([#10667](https://github.com/fivetran/great_expectations/pull/10667))

  ```python
  gxe.ExpectColumnValuesToBeBetween(
      column="passenger_count",
      min_value=0,
      row_condition='col("pickup_datetime") > "2019-01-01"',
      condition_parser="great_expectations",
  )
  ```

#### Changes

##### Docs

- Added data quality documentation covering integrity. ([#10583](https://github.com/fivetran/great_expectations/pull/10583))
- Incorporated several community documentation contributions from November 2024. ([#10681](https://github.com/fivetran/great_expectations/pull/10681))
- Rewrote the Expectation conditions documentation with clearer language and separate pandas, Spark, and SQL examples throughout. ([#10661](https://github.com/fivetran/great_expectations/pull/10661))
- Documented an architecture decision record explaining why meta fields are not used. ([#10672](https://github.com/fivetran/great_expectations/pull/10672))

<details>
<summary>Maintenance</summary>

- Adding an expectation that duplicates one already in a suite no longer produces a second entry, expectation equality ignores the `notes` and `meta` metadata fields, and the suite docstring now shows deleting expectations by suite index. ([#10662](https://github.com/fivetran/great_expectations/pull/10662))
- Passing a string in place of the `ConditionParser` enum no longer raises a type error, and row condition coverage was added to the Expectation testing framework. ([#10667](https://github.com/fivetran/great_expectations/pull/10667))
- Removed commented-out code from the codebase. ([#10686](https://github.com/fivetran/great_expectations/pull/10686))
- Added tests confirming that SQLite partitioners behave as expected. ([#10676](https://github.com/fivetran/great_expectations/pull/10676))
- Updated CODEOWNERS to name an owner for requirements files. ([#10684](https://github.com/fivetran/great_expectations/pull/10684))
- Added a fixture that exposes data assets to the Expectation test framework, with an asset property on batch test setups. ([#10673](https://github.com/fivetran/great_expectations/pull/10673))
- Extended the Expectation testing framework to run against BigQuery. ([#10675](https://github.com/fivetran/great_expectations/pull/10675))
- Added BigQuery to the marker-based test suites. ([#10674](https://github.com/fivetran/great_expectations/pull/10674))
- Added datetime type inference to the Expectation test framework and moved shared configuration into constants. ([#10666](https://github.com/fivetran/great_expectations/pull/10666))
- Added Databricks SQL coverage to Expectation testing. ([#10653](https://github.com/fivetran/great_expectations/pull/10653))
- Added Spark integration testing support to the Expectation test framework. ([#10670](https://github.com/fivetran/great_expectations/pull/10670))
- Reduced the workload of a flaky timing test so it fails on its own assertion rather than the CI timeout. ([#10663](https://github.com/fivetran/great_expectations/pull/10663))
- Standardized the atomic diagnostic observed-value renderer to use template strings and parameters like other atomic renderers, with better inference of the observed value's type. ([#10643](https://github.com/fivetran/great_expectations/pull/10643))

</details>

#### Contributors

Thanks to @vovavili (first contribution), @yogabonito (first contribution).

### 1.2.3 (2024-11-14)

#### Highlights

- **Double-sided Z-score expectations render their threshold value** — Expectations using a double-sided Z-score now render the inverse threshold as its numeric value instead of showing the literal placeholder text "$inverse_threshold". ([#10648](https://github.com/fivetran/great_expectations/pull/10648))

- **No more spurious warnings when masking config strings without SQLAlchemy** — Configuration strings are no longer masked, so users without SQLAlchemy support installed (for example, when using Azure Blob Storage) no longer see unnecessary warnings. ([#10625](https://github.com/fivetran/great_expectations/pull/10625))

#### Changes

##### Bug fixes

- Configuration strings are no longer masked, removing warnings for users who do not have SQLAlchemy support installed (for example with Azure Blob Storage). ([#10625](https://github.com/fivetran/great_expectations/pull/10625))
- Double-sided Z-score expectations now render the numeric inverse threshold instead of the literal string "$inverse_threshold". ([#10648](https://github.com/fivetran/great_expectations/pull/10648))

##### Docs

- Removed installation instructions for Redshift and Trino, which are no longer officially supported. ([#10660](https://github.com/fivetran/great_expectations/pull/10660))
- Updated the Microsoft Teams Action documentation. ([#10655](https://github.com/fivetran/great_expectations/pull/10655))
- Documentation now notes that Actions are not currently open for contributions while custom Action support is being restored. ([#10646](https://github.com/fivetran/great_expectations/pull/10646))

<details>
<summary>Maintenance</summary>

- Integration tests now generate randomized schema names, with data sources opting in via a `use_schema` flag. ([#10658](https://github.com/fivetran/great_expectations/pull/10658))
- Added SQLite coverage to integration testing, and test table names no longer include the data source type as a prefix. ([#10657](https://github.com/fivetran/great_expectations/pull/10657))
- Moved Checkpoint utility helpers alongside the actions they support, removing the separate utils module. ([#10649](https://github.com/fivetran/great_expectations/pull/10649))
- Added a shared constant listing all unparameterized data sources used in tests. ([#10654](https://github.com/fivetran/great_expectations/pull/10654))
- Cleaned up the `MicrosoftTeamsNotificationAction` docstring so it no longer references YAML configuration, and made its import patterns consistent. ([#10642](https://github.com/fivetran/great_expectations/pull/10642))
- Added an integration test for `MicrosoftTeamsNotificationAction`. ([#10628](https://github.com/fivetran/great_expectations/pull/10628))
- Bumped ruff to 0.7.2. ([#10629](https://github.com/fivetran/great_expectations/pull/10629))
- Bumped docstring-parser to 0.16. ([#10608](https://github.com/fivetran/great_expectations/pull/10608))
- Added a new maintainer to the teams file. ([#10641](https://github.com/fivetran/great_expectations/pull/10641))
- Cleaned up unused Azure CI configuration. ([#10638](https://github.com/fivetran/great_expectations/pull/10638))

</details>

### 1.2.2 (2024-11-07)

#### Highlights

- **Row conditions accept column names containing spaces** — Row conditions whose column names contain spaces are now parsed correctly instead of raising an exception. ([#10611](https://github.com/fivetran/great_expectations/pull/10611))

  ```python
  gxe.ExpectColumnValuesToNotBeNull(
      column="passenger_count",
      row_condition='col("pickup location")=="A"',
      condition_parser="great_expectations",
  )
  ```

- **Renderer parameters restored when using row_condition** — Expectation keyword arguments are once again included as renderer parameters, so rendered output for Expectations that use a row condition shows the full set of parameters. ([#10632](https://github.com/fivetran/great_expectations/pull/10632))

- **Batch definitions validate the column type they partition on** — Adding a batch definition to a SQL data asset now checks that the named column is a valid date/datetime column and raises a clear error otherwise, instead of failing later at validation time. ([#10590](https://github.com/fivetran/great_expectations/pull/10590))

  ```python
  asset.add_batch_definition_daily(name="daily", column="event_date")
  ```

- **Connection strings masked in configuration output** — The `conn_str` field used by Azure Blob Storage data sources is now masked when configuration is displayed or serialized, keeping credentials out of output. ([#10626](https://github.com/fivetran/great_expectations/pull/10626))

#### Changes

##### Features

- Expectation tests run against SQL backends now infer column types from the test data. ([#10622](https://github.com/fivetran/great_expectations/pull/10622))
- Adding a batch definition to a SQL data asset now validates that the specified column is a supported type and raises an error when it is not. ([#10590](https://github.com/fivetran/great_expectations/pull/10590))

##### Bug fixes

- Expectation keyword arguments are again passed through as renderer parameters, restoring missing parameters when a row condition is used. ([#10632](https://github.com/fivetran/great_expectations/pull/10632))
- The `conn_str` field used by Azure Blob Storage data sources is now masked in configuration output. ([#10626](https://github.com/fivetran/great_expectations/pull/10626))
- Batch Expectations now correctly handle `date` values for minimum and maximum bounds. ([#10613](https://github.com/fivetran/great_expectations/pull/10613))
- Row conditions now parse column names that contain spaces instead of raising an exception. ([#10611](https://github.com/fivetran/great_expectations/pull/10611))

##### Docs

- Removed unsupported actions (Opsgenie, PagerDuty, SNS) from the API documentation. ([#10624](https://github.com/fivetran/great_expectations/pull/10624))
- Fixed an incorrect column name in the failing example for ExpectColumnValuesToBeBetween. ([#10620](https://github.com/fivetran/great_expectations/pull/10620))
- Added documentation for dynamic parameters. ([#10483](https://github.com/fivetran/great_expectations/pull/10483))
- Updated documentation of which actions are supported in GX Cloud to match current behavior. ([#10609](https://github.com/fivetran/great_expectations/pull/10609))

<details>
<summary>Maintenance</summary>

- Added Microsoft SQL Server coverage to the Expectation testing framework. ([#10634](https://github.com/fivetran/great_expectations/pull/10634))
- Hardened the pull request title checker workflow against injection. ([#10636](https://github.com/fivetran/great_expectations/pull/10636))
- Added MySQL coverage to the Expectation testing framework. ([#10633](https://github.com/fivetran/great_expectations/pull/10633))
- Simplified the internal test framework with clearer table lookups and more immutable setup objects. ([#10631](https://github.com/fivetran/great_expectations/pull/10631))
- Extra table names used by tests are now randomly generated, and keys in extra test data are labels for correlation rather than table names. ([#10630](https://github.com/fivetran/great_expectations/pull/10630))
- Test setup and teardown are now reused across compatible test configurations, avoiding unneeded database setup work. ([#10619](https://github.com/fivetran/great_expectations/pull/10619))
- Expectation JSON schemas are now verified against the Draft-7 meta-schema, with `multiple_of` corrected to `multipleOf` and a regression test added. ([#10627](https://github.com/fivetran/great_expectations/pull/10627))
- Added another member to the repository teams configuration. ([#10616](https://github.com/fivetran/great_expectations/pull/10616))
- Mocked Posthog in action tests to stop intermittent CI failures. ([#10615](https://github.com/fivetran/great_expectations/pull/10615))
- Bumped http-proxy-middleware from 2.0.6 to 2.0.7 in the documentation site. ([#10566](https://github.com/fivetran/great_expectations/pull/10566))
- Bumped mermaid from 10.9.0 to 10.9.3 in the documentation site. ([#10549](https://github.com/fivetran/great_expectations/pull/10549))

</details>

### 1.2.1 (2024-10-31)

#### Highlights

- **Microsoft Teams notifications work end to end** — The Microsoft Teams notification action is now functional and supported as a first-class Checkpoint action: notification cards render correctly, Data Docs links are reachable from the card (Teams does not support `file:///` links in buttons, so the results are shown in an expandable card instead), and configuration values such as the webhook can be supplied through config substitution the same way Slack and Email actions allow. ([#10593](https://github.com/fivetran/great_expectations/pull/10593), [#10599](https://github.com/fivetran/great_expectations/pull/10599), [#10606](https://github.com/fivetran/great_expectations/pull/10606), [#10595](https://github.com/fivetran/great_expectations/pull/10595))

  ```python
  import great_expectations as gx
  from great_expectations.checkpoint import MicrosoftTeamsNotificationAction

  context = gx.get_context()
  action = MicrosoftTeamsNotificationAction(
      name="teams_notification",
      teams_webhook="${MY_TEAMS_WEBHOOK}",
      notify_on="all",
  )
  ```

- **Accurate unexpected row counts for UnexpectedRowsExpectation** — `UnexpectedRowsExpectation` now reports the true number of unexpected rows in its `observed_value` even when the query returns more than 200 rows, instead of capping the reported count. ([#10604](https://github.com/fivetran/great_expectations/pull/10604))

- **Email action supports config substitution** — `EmailAction` configuration values now resolve string substitutions (for example `${SMTP_PASSWORD}`), so credentials can be kept out of your configuration files. ([#10600](https://github.com/fivetran/great_expectations/pull/10600), [#10602](https://github.com/fivetran/great_expectations/pull/10602))

- **Expectation integration tests run against PostgreSQL and Snowflake** — The Expectation integration test framework can now exercise Expectations against PostgreSQL and Snowflake backends, broadening the backends covered by Expectation test suites. ([#10582](https://github.com/fivetran/great_expectations/pull/10582), [#10586](https://github.com/fivetran/great_expectations/pull/10586))

#### Changes

##### Features

- Expectations can now be tested against a Snowflake backend in the Expectation integration test framework. ([#10586](https://github.com/fivetran/great_expectations/pull/10586))
- Expectations can now be tested against a PostgreSQL backend in the Expectation integration test framework. ([#10582](https://github.com/fivetran/great_expectations/pull/10582))

##### Bug fixes

- `UnexpectedRowsExpectation` now reports the correct unexpected row count when the query returns more than 200 rows. ([#10604](https://github.com/fivetran/great_expectations/pull/10604))
- Data Docs results are now accessible from Microsoft Teams notifications via an expandable card, since Teams does not support `file:///` links. ([#10599](https://github.com/fivetran/great_expectations/pull/10599))
- `EmailAction` configuration values now support string substitution, so credentials can be referenced instead of inlined. ([#10600](https://github.com/fivetran/great_expectations/pull/10600))
- `MicrosoftTeamsNotificationAction` now works with GX 1.x and sends a redesigned notification card. ([#10593](https://github.com/fivetran/great_expectations/pull/10593))
- Two `ExpectationSuite` objects with the same Expectations in a different order now compare as equal, so suites no longer fail freshness checks because of ordering. ([#10562](https://github.com/fivetran/great_expectations/pull/10562))
- Corrected the type hints for the `mostly` and `value_set` Expectation parameters so plain values such as `mostly=1` type-check cleanly while the generated schemas stay unchanged. ([#10571](https://github.com/fivetran/great_expectations/pull/10571))
- Added a redirect so the deploy-gx-agent documentation URL resolves instead of 404ing. ([#10573](https://github.com/fivetran/great_expectations/pull/10573))

##### Docs

- Documentation builds now check for broken URLs with lychee. ([#10585](https://github.com/fivetran/great_expectations/pull/10585))
- Documentation now lists `MicrosoftTeamsNotificationAction` as a first-class, supported action. ([#10595](https://github.com/fivetran/great_expectations/pull/10595))
- Fixed additional small documentation issues found while following the getting-started material. ([#10598](https://github.com/fivetran/great_expectations/pull/10598))
- Documentation now states Python 3.12 as the highest supported Python version. ([#10596](https://github.com/fivetran/great_expectations/pull/10596))
- Removed duplicated content from the GCP Secret Manager instructions on the Access secrets managers page. ([#10591](https://github.com/fivetran/great_expectations/pull/10591))
- Numerous documentation refinements: more relevant links, corrected list indentation, spelling and grammar fixes, code samples that match their surrounding prose, and clearer wording. ([#10560](https://github.com/fivetran/great_expectations/pull/10560))
- Fixed broken links in the 0.18 changelog and in several API reference pages. ([#10588](https://github.com/fivetran/great_expectations/pull/10588))
- Added a working draft guide on data quality distribution analysis. ([#10440](https://github.com/fivetran/great_expectations/pull/10440))
- Internal links in the API reference now use root-relative URLs, preventing intermittent 404s. ([#10528](https://github.com/fivetran/great_expectations/pull/10528))

<details>
<summary>Maintenance</summary>

- Checkpoint creation and Microsoft Teams action runs now emit analytics events. ([#10597](https://github.com/fivetran/great_expectations/pull/10597))
- Expectation test framework supports data sources with multiple assets by accepting extra tables and their data. ([#10592](https://github.com/fivetran/great_expectations/pull/10592))
- `MicrosoftTeamsNotificationAction` now resolves configuration substitutions, matching the Slack and Email notification actions. ([#10606](https://github.com/fivetran/great_expectations/pull/10606))
- Consolidated the configuration-substitution handling used by Slack notifications. ([#10602](https://github.com/fivetran/great_expectations/pull/10602))
- An in-product docs link for configuring credentials now points at the current Core documentation instead of redirecting to the 0.18 content. ([#10580](https://github.com/fivetran/great_expectations/pull/10580))
- Cleaned up miscellaneous internal utility code. ([#10581](https://github.com/fivetran/great_expectations/pull/10581))
- Added more canonical Expectation test coverage. ([#10578](https://github.com/fivetran/great_expectations/pull/10578))
- Updated the 0.18.x changelog for the 0.18.22 release. ([#10575](https://github.com/fivetran/great_expectations/pull/10575))
- Updated the devrel membership listed in `teams.yml`. ([#10567](https://github.com/fivetran/great_expectations/pull/10567))
- Integration test framework now covers pandas filesystem CSV assets. ([#10556](https://github.com/fivetran/great_expectations/pull/10556))
- Saving an Expectation Suite that cannot be persisted now raises a more informative error. ([#10570](https://github.com/fivetran/great_expectations/pull/10570))
- Bumped the `ruff` and `mypy` development dependencies to 0.7.1 and 1.13.0. ([#10565](https://github.com/fivetran/great_expectations/pull/10565))
- Added a test ensuring that public API methods only appear on classes that are themselves marked public. ([#10529](https://github.com/fivetran/great_expectations/pull/10529))
- Re-enabled previously skipped end-to-end tests and updated them to 1.x syntax. ([#10555](https://github.com/fivetran/great_expectations/pull/10555))

</details>

### 1.2.0 (2024-10-24)

#### Highlights

- **The `great_expectations` row condition parser is no longer experimental** — Row conditions written with the `great_expectations` parser are now a supported, non-experimental way to filter the rows an Expectation evaluates, and the parser now understands `==` comparisons. Documentation has been updated to match. ([#10524](https://github.com/fivetran/great_expectations/pull/10524))

  ```python
  gxe.ExpectColumnValuesToNotBeNull(
      column="passenger_count",
      row_condition='col("vendor_id") == 1',
      condition_parser="great_expectations",
  )
  ```

- **Row conditions rejected on Expectations where they have no effect** — Expectations that operate on table structure rather than rows — `ExpectColumnToExist`, `ExpectTableColumnCountToBeBetween`, `ExpectTableColumnCountToEqual`, `ExpectTableColumnsToMatchOrderedList`, `ExpectTableColumnsToMatchSet`, and `UnexpectedRowsExpectation` — no longer accept a `row_condition`, so a condition can no longer be silently ignored. `condition_parser` is now expressed as an enum of the supported parsers. ([#10519](https://github.com/fivetran/great_expectations/pull/10519))

- **Faster validation result rendering** — Rendering validation results and Data Docs is noticeably faster. ([#10530](https://github.com/fivetran/great_expectations/pull/10530))

- **New Learn page for running GX in an Airflow data pipeline** — The Learn documentation now includes a page pointing to the end-to-end tutorial for using GX inside an Airflow data pipeline, alongside cleaned-up tutorial landing and table-of-contents pages. ([#10534](https://github.com/fivetran/great_expectations/pull/10534))

#### Changes

##### Bug fixes

- Fixed file path Batch Definitions so they are serialized correctly and round-trip as expected. ([#10543](https://github.com/fivetran/great_expectations/pull/10543))
- Ensured file-backed domain objects are persisted in JSON files. ([#10523](https://github.com/fivetran/great_expectations/pull/10523))
- Improved rendering performance of validation results. ([#10530](https://github.com/fivetran/great_expectations/pull/10530))
- Removed `row_condition` from Expectations where it has no effect (`ExpectColumnToExist`, `ExpectTableColumnCountToBeBetween`, `ExpectTableColumnCountToEqual`, `ExpectTableColumnsToMatchOrderedList`, `ExpectTableColumnsToMatchSet`, and `UnexpectedRowsExpectation`), introduced an enum for `condition_parser`, and dropped the special-cased `pandas` default parser for three Expectations. ([#10519](https://github.com/fivetran/great_expectations/pull/10519))

##### Docs

- Added documentation redirects for docs subdomains. ([#10558](https://github.com/fivetran/great_expectations/pull/10558))
- Added references to the community issues board in the Get Support and community resources docs, and removed mention of the GX-supported label from the contributing doc. ([#10548](https://github.com/fivetran/great_expectations/pull/10548))
- Fixed broken documentation links so they point at their current URLs. ([#10541](https://github.com/fivetran/great_expectations/pull/10541))
- Changed dynamically generated links in the 0.18 API reference from relative paths to root-based paths so they resolve correctly. ([#10507](https://github.com/fivetran/great_expectations/pull/10507))
- Added the base `Datasource` class to the public API documentation. ([#10527](https://github.com/fivetran/great_expectations/pull/10527))
- Added a Learn page linking to the GX-in-the-data-pipeline Airflow tutorial, plus tense and wording cleanup on the tutorial landing and table-of-contents pages. ([#10534](https://github.com/fivetran/great_expectations/pull/10534))
- Updated the Data Docs site configuration page to reflect that GX 1.x only supports writing Data Docs sites to a local filesystem. ([#10536](https://github.com/fivetran/great_expectations/pull/10536))
- Added redirects for retired documentation URLs so bookmarked and search-result links land on the corresponding versioned or closest-matching page instead of a 404. ([#10516](https://github.com/fivetran/great_expectations/pull/10516))
- Fixed assorted typos in the documentation. ([#10521](https://github.com/fivetran/great_expectations/pull/10521))
- Bumped the maximum supported Python version stated in the documentation. ([#10522](https://github.com/fivetran/great_expectations/pull/10522))

<details>
<summary>Maintenance</summary>

- Added a testing framework for exercising Expectations against data sources, initially supporting pandas DataFrame data sources. ([#10554](https://github.com/fivetran/great_expectations/pull/10554))
- Removed assorted utility functions from the documented public API surface. ([#10557](https://github.com/fivetran/great_expectations/pull/10557))
- Enabled the AWS/Spark docs tests to run on pull requests, updated the remaining test for GX 1.x, and removed three outdated tests. ([#10550](https://github.com/fivetran/great_expectations/pull/10550))
- Updated the Airflow documentation snippet to look up a Checkpoint by name instead of iterating over all Checkpoints. ([#10551](https://github.com/fivetran/great_expectations/pull/10551))
- Documentation site builds on Netlify now use Python 3.12. ([#10531](https://github.com/fivetran/great_expectations/pull/10531))
- Removed the experimental designation from the `great_expectations` row condition parser, added support for the `==` condition, and updated the related documentation. ([#10524](https://github.com/fivetran/great_expectations/pull/10524))
- Cleaned up redundant try/except blocks flagged by the TRY203 lint rule. ([#10540](https://github.com/fivetran/great_expectations/pull/10540))
- Added `DataAsset.get_batch_definition` to the public API documentation. ([#10533](https://github.com/fivetran/great_expectations/pull/10533))
- Upgraded the project's ruff linter to 0.7.0 and updated the corresponding lint suppression codes. ([#10535](https://github.com/fivetran/great_expectations/pull/10535))
- Updated static analysis tooling: ruff 0.6.8 to 0.6.9 and mypy 1.11.1 to 1.12. ([#10525](https://github.com/fivetran/great_expectations/pull/10525))

</details>

### 1.1.3 (2024-10-15)

Compatibility: Python `<3.12,>=3.9` → `<3.13,>=3.9`; `snapshottest` removed (extra `test`) (`python_version < "3.12"`)

#### Highlights

- **Python 3.12 support** — Great Expectations now supports Python 3.12; the supported range is Python >=3.9,\<3.13. ([#10503](https://github.com/fivetran/great_expectations/pull/10503))

- **Data Docs icons render again** — Icons in Data Docs now load correctly instead of failing to appear, after switching to a working icon source. ([#10511](https://github.com/fivetran/great_expectations/pull/10511))

#### Changes

##### Bug fixes

- Fixed missing icons in Data Docs by serving them from a working CDN source. ([#10511](https://github.com/fivetran/great_expectations/pull/10511))

##### Docs

- Corrected an incorrect label in the migration guide. ([#10518](https://github.com/fivetran/great_expectations/pull/10518))
- Documented object factories as part of the public API reference. ([#10513](https://github.com/fivetran/great_expectations/pull/10513))

<details>
<summary>Maintenance</summary>

- Ran the ClickHouse test suite under its own isolated CI marker, since it is not yet compatible with Python 3.12. ([#10512](https://github.com/fivetran/great_expectations/pull/10512))
- Extended the pact contract test to cover all expectation suites. ([#10506](https://github.com/fivetran/great_expectations/pull/10506))
- Corrected how the release-related GitHub Actions install the release tooling. ([#10509](https://github.com/fivetran/great_expectations/pull/10509))
- Added support for running Great Expectations on Python 3.12. ([#10503](https://github.com/fivetran/great_expectations/pull/10503))
- Added manually triggered GitHub Actions workflows for the release process. ([#10502](https://github.com/fivetran/great_expectations/pull/10502))
- Removed the `snapshottest` test dependency. ([#10498](https://github.com/fivetran/great_expectations/pull/10498))

</details>

### 1.1.2 (2024-10-10)

#### Highlights

- **Turn analytics on or off per project from code** — Data Contexts now expose an `enable_analytics` method that explicitly records whether analytics are enabled in the project config. When the project config holds a value, it takes precedence over the analytics environment variable, so you can keep a global environment default and still override it for a specific project. ([#10385](https://github.com/fivetran/great_expectations/pull/10385))

  ```python
  import great_expectations as gx

  context = gx.get_context()
  context.enable_analytics(False)
  ```

- **Result format dicts are no longer mutated by the Validator** — Passing a result format dict into a Validator no longer modifies the dict you provided, so checkpoints are no longer incorrectly considered stale and their validations run as expected. ([#10496](https://github.com/fivetran/great_expectations/pull/10496))

- **V0 to V1 migration guide** — The documentation now includes a guide for migrating a project from Great Expectations V0 to V1. ([#10477](https://github.com/fivetran/great_expectations/pull/10477))

#### Deprecations

- `context.get_datasource` is deprecated; use `context.data_sources.get`. Removal in 2.0.0. ([#10471](https://github.com/fivetran/great_expectations/pull/10471))

#### Changes

##### Features

- Added `context.enable_analytics` to explicitly enable or disable analytics for a project; a value stored in the project config now takes precedence over the analytics environment variable. ([#10385](https://github.com/fivetran/great_expectations/pull/10385))

##### Bug fixes

- A result format dict passed to a Validator is no longer mutated, fixing checkpoint validations that failed because the checkpoint was treated as stale. ([#10496](https://github.com/fivetran/great_expectations/pull/10496))

##### Docs

- Updated the minimum supported version shown in the documentation. ([#10494](https://github.com/fivetran/great_expectations/pull/10494))
- Added a V0 to V1 migration guide to the documentation. ([#10477](https://github.com/fivetran/great_expectations/pull/10477))

<details>
<summary>Maintenance</summary>

- `context.get_datasource` is deprecated in favor of `context.data_sources.get`; it now delegates to that method while keeping its existing error behavior. ([#10471](https://github.com/fivetran/great_expectations/pull/10471))
- Removed the unused `result_url` attribute from `CheckpointResult`. ([#10493](https://github.com/fivetran/great_expectations/pull/10493))

</details>

### 1.1.1 (2024-10-08)

Compatibility: Python `<3.12,>=3.8` → `<3.12,>=3.9`; `ipython` removed; `ipywidgets` removed; `makefun` removed; `numpy` removed (`python_version == "3.8"`); `pandas` removed (`python_version <= "3.8"`); `pytz` removed; `urllib3` removed; removed extra `test`

#### Highlights

- **Python 3.9 is now the minimum supported Python version** — Python 3.8 reached end of life, so GX Core no longer supports it. Supported versions are now Python 3.9 through 3.11, with experimental support for 3.12 and later available via the GX_PYTHON_EXPERIMENTAL environment variable. The README now states the updated support policy. ([#10441](https://github.com/fivetran/great_expectations/pull/10441), [#10474](https://github.com/fivetran/great_expectations/pull/10474))

- **Leaner install footprint** — Installing great_expectations now pulls in fewer third-party packages: the top-level urllib3, pytz, ipython, ipywidgets, and makefun requirements have been removed, and the requirements files were tidied up. ([#10488](https://github.com/fivetran/great_expectations/pull/10488), [#10489](https://github.com/fivetran/great_expectations/pull/10489), [#10487](https://github.com/fivetran/great_expectations/pull/10487), [#10472](https://github.com/fivetran/great_expectations/pull/10472), [#10485](https://github.com/fivetran/great_expectations/pull/10485))

- **Slack webhook credentials no longer leak into serialized configuration** — SlackNotificationAction now substitutes configured credentials just in time when the action runs, so your token or webhook URL is no longer written out when the action is serialized. ([#10476](https://github.com/fivetran/great_expectations/pull/10476))

  ```python
  import great_expectations as gx
  from great_expectations.checkpoint import SlackNotificationAction

  action = SlackNotificationAction(
      name="notify_slack",
      slack_webhook="${SLACK_WEBHOOK}",
  )
  print(action.json())  # the substituted secret is no longer included
  ```

- **Validation results from GX Cloud carry their backend-assigned IDs** — Validation results produced against a Cloud-backed Data Context now come back with the IDs generated by the Cloud backend, so you can reference and look them up reliably. ([#10478](https://github.com/fivetran/great_expectations/pull/10478))

- **New tutorial for dbt, Airflow, and Postgres with GX** — The documentation now includes an end-to-end tutorial showing how dbt, GX, Airflow, and Postgres work together to validate data in a pipeline. ([#10458](https://github.com/fivetran/great_expectations/pull/10458))

#### Changes

##### Bug fixes

- Validation results generated against a Cloud-backed Data Context now receive the IDs assigned by the Cloud backend. ([#10478](https://github.com/fivetran/great_expectations/pull/10478))
- SlackNotificationAction credentials are no longer serialized: variable substitution now happens when the action runs rather than when it is constructed. ([#10476](https://github.com/fivetran/great_expectations/pull/10476))

##### Docs

- Glossary term links in the 0.18 documentation now point at the versioned URLs instead of returning 404s. ([#10479](https://github.com/fivetran/great_expectations/pull/10479))
- Added a tutorial demonstrating how dbt, GX, Airflow, and Postgres can be used together. ([#10458](https://github.com/fivetran/great_expectations/pull/10458))
- The README integration support policy now states that GX Core supports Python 3.9 through 3.11, dropping the reference to Python 3.8. ([#10474](https://github.com/fivetran/great_expectations/pull/10474))

<details>
<summary>Maintenance</summary>

- The top-level `urllib3` requirement was removed; it is already installed as part of `requests`. ([#10488](https://github.com/fivetran/great_expectations/pull/10488))
- The `pytz` requirement was removed from the installed dependency set. ([#10489](https://github.com/fivetran/great_expectations/pull/10489))
- The experimental metric repository was updated to work with the V1 backend API. ([#10486](https://github.com/fivetran/great_expectations/pull/10486))
- The `ipython` and `ipywidgets` requirements were removed from the installed dependency set. ([#10487](https://github.com/fivetran/great_expectations/pull/10487))
- The requirements files were cleaned up, reducing what gets installed alongside great_expectations. ([#10485](https://github.com/fivetran/great_expectations/pull/10485))
- The public API check runs in CI again, restoring coverage that had previously been turned off. ([#10449](https://github.com/fivetran/great_expectations/pull/10449))
- The outdated `makefun` requirement, used only by the removed data assistants, is no longer installed. ([#10472](https://github.com/fivetran/great_expectations/pull/10472))
- The contrib pipeline was removed from the repository's build tooling. ([#10470](https://github.com/fivetran/great_expectations/pull/10470))
- Stale teams and non-employee entries were removed from the repository's teams.yml ownership file. ([#10469](https://github.com/fivetran/great_expectations/pull/10469))
- Bumped `micromatch` from 4.0.5 to 4.0.8 in the documentation site build, picking up fixes for CVE-2024-4067 and CVE-2024-4068. ([#10466](https://github.com/fivetran/great_expectations/pull/10466))
- Bumped `webpack` from 5.88.2 to 5.94.0 in the documentation site build, including a DOM-clobbering security fix. ([#10463](https://github.com/fivetran/great_expectations/pull/10463))
- Bumped `dompurify` from 3.0.11 to 3.1.7 in the documentation site build, picking up several sanitizer bypass fixes. ([#10465](https://github.com/fivetran/great_expectations/pull/10465))
- Bumped `express` from 4.19.2 to 4.21.0 in the documentation site build. ([#10464](https://github.com/fivetran/great_expectations/pull/10464))
- Python 3.8 is no longer a supported version now that it has reached end of life; Python 3.9 is the minimum supported version and CI no longer tests 3.8. ([#10441](https://github.com/fivetran/great_expectations/pull/10441))

</details>

### 1.1.0 (2024-10-03)

#### Highlights

- **Pass expectation parameters to `Batch.validate()`** — `Batch.validate()` now accepts expectation parameters, so you can supply runtime parameter values when validating a single expectation or an expectation suite against a batch. ([#10456](https://github.com/fivetran/great_expectations/pull/10456))

  ```python
  batch.validate(expectation, expectation_parameters={"min_value": 1})
  ```

- **Better autocomplete for `context.data_sources`** — Additional method signatures are now published for `context.data_sources`, so editors and type checkers offer complete autocomplete and type information for data source methods. ([#10447](https://github.com/fivetran/great_expectations/pull/10447))

  ```python
  context.data_sources.add_snowflake(name="my_ds", connection_string="...")
  ```

- **Environment variable substitution in Slack notifications** — `SlackNotificationAction` now supports `${VAR}` substitution, so Slack webhooks and tokens can be supplied through environment variables or config variables instead of being hard-coded. ([#10443](https://github.com/fivetran/great_expectations/pull/10443))

  ```python
  SlackNotificationAction(name="slack", slack_webhook="${SLACK_WEBHOOK}")
  ```

#### Changes

##### Features

- `Batch.validate()` accepts expectation parameters, letting you pass runtime parameter values when validating against a batch. ([#10456](https://github.com/fivetran/great_expectations/pull/10456))
- Autocomplete and type hints for `context.data_sources` now cover previously missing methods. ([#10447](https://github.com/fivetran/great_expectations/pull/10447))

##### Bug fixes

- `SlackNotificationAction` now resolves `${VAR}`-style substitutions in its configuration values. ([#10443](https://github.com/fivetran/great_expectations/pull/10443))
- Data Sources added, updated, or deleted at runtime are now reflected when you print the Data Context. ([#10438](https://github.com/fivetran/great_expectations/pull/10438))
- Fixed an outdated link in the README that pointed to a page that has moved. ([#10446](https://github.com/fivetran/great_expectations/pull/10446))

##### Docs

- The integration support table now lists Databricks (SQL) as a GX Cloud supported Data Source. ([#10452](https://github.com/fivetran/great_expectations/pull/10452))
- Added a Data Source credential management section with an example of using environment variable substitution. ([#10417](https://github.com/fivetran/great_expectations/pull/10417))
- Documentation now states Python 3.9 as the supported minimum version. ([#10453](https://github.com/fivetran/great_expectations/pull/10453))

<details>
<summary>Maintenance</summary>

- Result format and query-based metrics now return at most 200 unexpected records, and the docs state this limit. ([#10432](https://github.com/fivetran/great_expectations/pull/10432))
- `ExpectColumnUniqueValueCountToBeBetween` no longer accepts the `mostly` parameter, which does not apply to column aggregate expectations. ([#10450](https://github.com/fivetran/great_expectations/pull/10450))
- Expectation `min_value`/`max_value` parameters use a shared comparable type and now accept `date` values. ([#10448](https://github.com/fivetran/great_expectations/pull/10448))
- Great Expectations is now published as a stable release on PyPI. ([#10457](https://github.com/fivetran/great_expectations/pull/10457))
- Added Alena Hutchinson to the core developers team. ([#10459](https://github.com/fivetran/great_expectations/pull/10459))

</details>

### 1.0.6 (2024-10-01)

#### Highlights

- **Clear error when opening Data Docs that haven't been built** — Calling `context.open_data_docs()` when no Data Docs have been built now raises a descriptive `NoDataDocsError` instead of failing opaquely. ([#10439](https://github.com/fivetran/great_expectations/pull/10439))

  ```python
  import great_expectations as gx

  context = gx.get_context()
  context.open_data_docs()  # raises NoDataDocsError if no Data Docs exist
  ```

- **Expectation windows for dynamic parameters** — Expectations accept a new optional `windows` field that describes temporal window definitions, enabling dynamic parameters. When empty, the field is omitted from dict serialization and serialized as `null` in JSON. ([#10402](https://github.com/fivetran/great_expectations/pull/10402))

  ```python
  import great_expectations.expectations as gxe

  expectation = gxe.ExpectColumnValuesToNotBeNull(column="passenger_count", windows=None)
  ```

- **Suites render reliably when loaded** — Suites are now rendered when they are loaded, removing the runtime exceptions that came up when adding a validation definition for a freshly created suite or running checkpoints loaded from GX Cloud. ([#10434](https://github.com/fivetran/great_expectations/pull/10434))

#### Changes

##### Features

- `open_data_docs()` now raises a descriptive `NoDataDocsError` when no Data Docs have been built. ([#10439](https://github.com/fivetran/great_expectations/pull/10439))
- Expectations accept a new optional `windows` field for configuring temporal window definitions used by dynamic parameters. ([#10402](https://github.com/fivetran/great_expectations/pull/10402))

##### Bug fixes

- Fixed runtime errors caused by unrendered suites: suites are now rendered when loaded, so adding a validation definition for a newly created suite and running checkpoints loaded from GX Cloud no longer fail. ([#10434](https://github.com/fivetran/great_expectations/pull/10434))

##### Docs

- Added a data quality technical documentation page covering Volume. ([#10362](https://github.com/fivetran/great_expectations/pull/10362))
- Improved the documentation search bar styling and added a hover border to the color mode toggle for visual consistency. ([#10436](https://github.com/fivetran/great_expectations/pull/10436))
- Reverted the documentation search bar on desktop screens to the previous design after searches dropped with the minimalistic version. ([#10409](https://github.com/fivetran/great_expectations/pull/10409))
- Fixed typos in the GX Cloud overview and deployment pattern documentation. ([#10429](https://github.com/fivetran/great_expectations/pull/10429))
- Reorganized and updated the GX Cloud deployment and architecture pattern content into a single GX Cloud overview page. ([#10345](https://github.com/fivetran/great_expectations/pull/10345))
- Excluded internal template pages from the documentation sitemap so they no longer appear in site search results. ([#10401](https://github.com/fivetran/great_expectations/pull/10401))
- Updated the `UnexpectedRowsExpectation` documentation to clarify that subclassing is not required, that the `{batch}` keyword is optional, and to add a GX Cloud section on Custom SQL Expectations. ([#10391](https://github.com/fivetran/great_expectations/pull/10391))

<details>
<summary>Maintenance</summary>

- Expectation equality comparisons ignore rendered content, so otherwise-identical expectations compare as equal regardless of whether they have been rendered. ([#10444](https://github.com/fivetran/great_expectations/pull/10444))
- Added test coverage for expectation parameters being passed through to checkpoints. ([#10435](https://github.com/fivetran/great_expectations/pull/10435))
- Updated the ruff linter from 0.5.3 to 0.6.8, including formatting and linting of Jupyter notebook files. ([#10442](https://github.com/fivetran/great_expectations/pull/10442))

</details>

#### Contributors

Thanks to @Quantisan, @deborahniesz, @JessSaavedra.

### 1.0.5 (2024-09-19)

Compatibility: `databricks-sql-connector` added (extra `databricks`); removed extra `databricks`; new extra `spark-connect`

#### Highlights

- **Spark Connect DataFrames are now accepted** — You can now pass Spark Connect DataFrames to Great Expectations wherever a Spark DataFrame is expected; previously only classic Spark DataFrames were accepted and Spark Connect DataFrames were rejected. Note that sessions created through the Spark Connect session factory methods are still not supported. ([#10420](https://github.com/fivetran/great_expectations/pull/10420))

- **Regex and LIKE Expectations work on Databricks SQL** — Expectations such as expect_column_values_to_match_regex and expect_column_values_to_match_like_pattern now run correctly against Databricks SQL. ([#10406](https://github.com/fivetran/great_expectations/pull/10406))

  ```python
  batch.validate(
      gxe.ExpectColumnValuesToMatchRegex(column="name", regex=".*")
  )
  ```

- **`{batch}` keyword works in UnexpectedRowsExpectation queries** — Queries that use the `{batch}` keyword now run successfully on Postgres, which requires subquery aliases in SELECT and WHERE clauses, and on all backends when the batch uses a splitter, where batch parameters are now rendered as literal values. ([#10392](https://github.com/fivetran/great_expectations/pull/10392))

  ```python
  gxe.UnexpectedRowsExpectation(
      unexpected_rows_query="SELECT * FROM {batch} WHERE passenger_count > 6"
  )
  ```

- **Documentation for connecting GX Cloud to Databricks SQL** — The GX Cloud documentation now includes a "Connect to Databricks SQL" page, listed in the documentation table of contents. ([#10394](https://github.com/fivetran/great_expectations/pull/10394), [#10423](https://github.com/fivetran/great_expectations/pull/10423))

#### Changes

##### Bug fixes

- Connecting to Databricks SQL no longer fails with an AttributeError when the installed `databricks` package does not provide a `sqlalchemy` sub-module, and the minimum supported `databricks-sql-connector` version has been raised. ([#10424](https://github.com/fivetran/great_expectations/pull/10424))
- Spark Connect DataFrames are now accepted wherever Spark DataFrames are, instead of being rejected as an unsupported type; DataFrames from sessions created via the Spark Connect session factory methods remain unsupported. ([#10420](https://github.com/fivetran/great_expectations/pull/10420))
- Regex- and LIKE-based Expectations, including expect_column_values_to_match_regex and expect_column_values_to_match_like_pattern, now work against Databricks SQL. ([#10406](https://github.com/fivetran/great_expectations/pull/10406))
- Using the `{batch}` keyword in an unexpected-rows query no longer fails on Postgres due to missing subquery aliases, and no longer fails on any backend when the batch uses a splitter, since batch parameters are now rendered as literal values. ([#10392](https://github.com/fivetran/great_expectations/pull/10392))

##### Docs

- The "Connect to Databricks SQL" page is now listed in the GX Cloud documentation table of contents. ([#10423](https://github.com/fivetran/great_expectations/pull/10423))
- The published changelog now includes the 0.18.18 through 0.18.21 releases. ([#10422](https://github.com/fivetran/great_expectations/pull/10422))
- Added a "Connect to Databricks SQL" page to the GX Cloud documentation. ([#10394](https://github.com/fivetran/great_expectations/pull/10394))

<details>
<summary>Maintenance</summary>

- `FabricPowerBIDatasource` now lives outside the `great_expectations.experimental` sub-package, removing confusion with the separate contributor experimental package. ([#10419](https://github.com/fivetran/great_expectations/pull/10419))
- Corrected the type annotations for `SQLAlchemyExecutionEngine.get_connection()` and updated column identifier tests to match fixes carried over from the 0.18.x branch. ([#10399](https://github.com/fivetran/great_expectations/pull/10399))

</details>

#### Contributors

Thanks to @allisongx.

### 1.0.4 (2024-09-16)

#### Highlights

- **Checkpoints with Slack and email actions run again** — Checkpoints configured with Slack or email notification actions no longer fail during setup; these actions now compare as equal when they are configured identically. ([#10393](https://github.com/fivetran/great_expectations/pull/10393))

- **More reliable Data Docs links in checkpoint actions** — Checkpoint actions that reference Data Docs pages now retrieve those pages correctly in additional configurations, so notifications and updates include the expected Data Docs links. ([#10400](https://github.com/fivetran/great_expectations/pull/10400))

#### Changes

##### Bug fixes

- Fixed additional cases where checkpoint actions failed to retrieve the correct Data Docs pages. ([#10400](https://github.com/fivetran/great_expectations/pull/10400))
- Fixed action comparison so checkpoints using Slack or email notification actions can be run. ([#10393](https://github.com/fivetran/great_expectations/pull/10393))

##### Docs

- Added "request a demo" calls to action to the GX Cloud sidebar, the resources dropdown, and the Why GX Cloud and Get Support pages. ([#10389](https://github.com/fivetran/great_expectations/pull/10389))

<details>
<summary>Maintenance</summary>

- Diagnostics for every nested validation definition are now emitted from the parent checkpoint run. ([#10386](https://github.com/fivetran/great_expectations/pull/10386))

</details>

### 1.0.3 (2024-09-12)

Compatibility: `sqlalchemy` minimum set to 1.4.0 (extra `snowflake`)

#### Highlights

- **List available batches without loading data** — `BatchDefinition` now offers a public `get_batch_identifiers_list()` method that returns the batch identifiers available for that batch definition. It replaces the old `get_batch_list_from_batch_request` workflow for inspecting available batches, and because it does not read the underlying data it is considerably faster. ([#10383](https://github.com/fivetran/great_expectations/pull/10383), [#10295](https://github.com/fivetran/great_expectations/pull/10295))

  ```python
  batch_definition = asset.get_batch_definition("daily")
  for identifiers in batch_definition.get_batch_identifiers_list():
      print(identifiers)
  ```

- **Fetch a single batch with `get_batch`** — `get_batch_list_from_batch_request` has been replaced by `get_batch`, which retrieves only the batch you actually need instead of reading every matching batch. For Pandas filesystem datasources in particular, this removes the long-standing cost of loading data for batches that were never used. ([#10295](https://github.com/fivetran/great_expectations/pull/10295))

  ```python
  batch = batch_definition.get_batch()
  result = batch.validate(expectation)
  ```

- **Checkpoint results no longer break Data Docs links in actions** — Checkpoint actions such as the Microsoft Teams notification no longer raise a `TypeError` when building Data Docs links from a checkpoint run; the links are rendered correctly again. ([#10374](https://github.com/fivetran/great_expectations/pull/10374))

#### Changes

##### Features

- `BatchDefinition.get_batch_identifiers_list()` is now available as a public, non-data-reading way to see which batches a batch definition covers. ([#10383](https://github.com/fivetran/great_expectations/pull/10383))
- Running a Checkpoint now emits usage analytics for the run. ([#10382](https://github.com/fivetran/great_expectations/pull/10382))
- `get_batch_list_from_batch_request` is replaced by `get_batch`, which fetches only the batch you need, and by `get_batch_identifiers_list` for inspecting available batch metadata; documentation has been updated to the new methods. ([#10295](https://github.com/fivetran/great_expectations/pull/10295))

##### Bug fixes

- Checkpoint actions no longer fail with `TypeError: list indices must be integers` when rendering Data Docs page links. ([#10374](https://github.com/fivetran/great_expectations/pull/10374))

##### Docs

- The feedback survey is no longer shown on the documentation homepage. ([#10378](https://github.com/fivetran/great_expectations/pull/10378))
- Data quality use case articles in the Learn section now use small text instead of superscript for footnotes. ([#10377](https://github.com/fivetran/great_expectations/pull/10377))
- Documentation now lists BigQuery in the GX Core support posture. ([#10375](https://github.com/fivetran/great_expectations/pull/10375))
- Documentation now describes the support posture for Data Docs. ([#10373](https://github.com/fivetran/great_expectations/pull/10373))
- The GX Core introduction page now includes an embedded overview video. ([#10366](https://github.com/fivetran/great_expectations/pull/10366))
- Changelog attributions for the 1.0 releases now credit external contributors. ([#10348](https://github.com/fivetran/great_expectations/pull/10348))

<details>
<summary>Maintenance</summary>

- Removed unused miscellaneous helper functions from the internal test utilities. ([#10357](https://github.com/fivetran/great_expectations/pull/10357))
- Added test coverage for up-to-date (freshness) checks on validation definitions and checkpoints. ([#10381](https://github.com/fivetran/great_expectations/pull/10381))
- Added test coverage for up-to-date (freshness) checks on batch definitions and expectation suites. ([#10380](https://github.com/fivetran/great_expectations/pull/10380))
- Validation definitions and checkpoints are now checked for being up to date with their stored versions, raising a dedicated error when they are not. ([#10365](https://github.com/fivetran/great_expectations/pull/10365))
- Rendering an expectation's description no longer risks a `KeyError` when configuration or result values are absent. ([#10353](https://github.com/fivetran/great_expectations/pull/10353))
- Errors raised when a resource is not added or not up to date now live in a dedicated module with a clearer class hierarchy. ([#10359](https://github.com/fivetran/great_expectations/pull/10359))
- Cleaned up test fixtures. ([#10358](https://github.com/fivetran/great_expectations/pull/10358))
- Batch definitions and expectation suites are now checked for being up to date before they are saved. ([#10277](https://github.com/fivetran/great_expectations/pull/10277))
- Removed error types left over from legacy versions to simplify the set of exceptions the library raises. ([#10356](https://github.com/fivetran/great_expectations/pull/10356))
- An expectation's `description`, when set, is now always rendered in place of the default rendered text, and it is omitted from serialized expectation suites when unset. ([#10347](https://github.com/fivetran/great_expectations/pull/10347))
- Expectation equality comparison now handles `meta` and `notes` more simply and consistently. ([#10349](https://github.com/fivetran/great_expectations/pull/10349))
- Type checking now runs against SQLAlchemy 2, while both SQLAlchemy 1 and 2 remain supported at runtime. ([#10112](https://github.com/fivetran/great_expectations/pull/10112))

</details>

#### Contributors

Thanks to @deborahniesz, @JessSaavedra, @anthonyburdi.

### 1.0.2 (2024-09-05)

#### Highlights

- **Choose a result format when validating a Batch** — You can now pass a result format when validating a Batch or Expectation directly, so you control how much detail comes back without changing your suite or checkpoint configuration. ([#10281](https://github.com/fivetran/great_expectations/pull/10281))

  ```python
  result = batch.validate(expectation, result_format="COMPLETE")
  ```

- **Value sets are no longer mangled into dictionaries** — Expectations that take a value set now keep lists of strings intact — a value set such as ["HI", "AK"] is no longer coerced into a dictionary like \{"H": "I", "A": "K"}. ([#10325](https://github.com/fivetran/great_expectations/pull/10325))

  ```python
  gxe.ExpectColumnValuesToBeInSet(column="state", value_set=["HI", "AK"])
  ```

- **Data Docs show the Data Asset name for fluent Data Sources** — Data Docs pages now display the Data Asset name for fluent Data Sources, making it clear which asset a set of Validation Results came from. ([#9953](https://github.com/fivetran/great_expectations/pull/9953))

- **Clearer UnexpectedRowsExpectation results and rendering** — UnexpectedRowsExpectation now renders its query as a code block, reports an observed value with contextual information instead of a bare row count, and treats the \{batch} keyword in unexpected_rows_query as optional while telling you when it is missing. ([#10334](https://github.com/fivetran/great_expectations/pull/10334), [#10311](https://github.com/fivetran/great_expectations/pull/10311))

  ```python
  gxe.UnexpectedRowsExpectation(
      unexpected_rows_query="SELECT * FROM {batch} WHERE passenger_count > 6"
  )
  ```

- **Light and dark theme selector in the documentation site** — The documentation site now offers a theme selector so you can read the docs in light or dark mode. ([#10181](https://github.com/fivetran/great_expectations/pull/10181))

#### Changes

##### Features

- You can now set the result format when validating a Batch, and a single result-format type and default constant are available for reuse. ([#10281](https://github.com/fivetran/great_expectations/pull/10281))

##### Bug fixes

- Data Docs now show the Data Asset name for fluent Data Sources. ([#9953](https://github.com/fivetran/great_expectations/pull/9953))
- Slack and email notifications no longer fail when rendering Validation Results that have no active batch definition. ([#10344](https://github.com/fivetran/great_expectations/pull/10344))
- Validation Results no longer carry the queried dataframe in their result payload. ([#10338](https://github.com/fivetran/great_expectations/pull/10338))
- Value sets passed to Expectations are no longer coerced into dictionaries, so lists such as ["HI", "AK"] are preserved as given. ([#10325](https://github.com/fivetran/great_expectations/pull/10325))
- Requesting a Batch from a Fabric Power BI Data Source no longer raises a TypeError about an unexpected 'options' keyword argument. ([#10318](https://github.com/fivetran/great_expectations/pull/10318))

##### Docs

- GX Cloud alerting documentation now covers email alerts instead of Slack alerts. ([#10320](https://github.com/fivetran/great_expectations/pull/10320))
- Superscript footnote markers in the application integration support tables now render consistently. ([#10337](https://github.com/fivetran/great_expectations/pull/10337))
- Added a data quality reference article on missingness. ([#10134](https://github.com/fivetran/great_expectations/pull/10134))
- The configure credentials guide now explains how to persist environment variables in Z Shell. ([#10330](https://github.com/fivetran/great_expectations/pull/10330))
- Removed dead links to older documentation from Expectation docstrings and updated the accompanying schema files. ([#10317](https://github.com/fivetran/great_expectations/pull/10317))
- Fixed a typo in the documentation. ([#10329](https://github.com/fivetran/great_expectations/pull/10329))
- The "Connect to GX Cloud with Python" guide now shows how to list available Data Sources and retrieve a sample Batch of data. ([#10315](https://github.com/fivetran/great_expectations/pull/10315))
- The reference table now includes value types so named parameters are easier to identify. ([#10299](https://github.com/fivetran/great_expectations/pull/10299))
- The Airflow tutorial now works with both GX 0.18.x and GX Core 1.0. ([#10319](https://github.com/fivetran/great_expectations/pull/10319))
- Data Context descriptions now include general use cases for each type of Data Context. ([#10292](https://github.com/fivetran/great_expectations/pull/10292))
- The create a Validation Definition guide now lists a Batch Definition, rather than a Data Asset, as its prerequisite. ([#10288](https://github.com/fivetran/great_expectations/pull/10288))
- Documentation now correctly describes printed Validation Results as JSON rather than YAML. ([#10287](https://github.com/fivetran/great_expectations/pull/10287))
- The documentation site now has a light/dark theme selector, and the navigation bar no longer uses a translucent background. ([#10181](https://github.com/fivetran/great_expectations/pull/10181))
- Removed the legacy version 0.17 documentation files, which are now served from a standalone site. ([#10279](https://github.com/fivetran/great_expectations/pull/10279))
- Documentation feedback tickets now record the page path the feedback came from. ([#10312](https://github.com/fivetran/great_expectations/pull/10312))
- Corrected a typo in the description of the min_value argument for ExpectColumnMaxToBeBetween. ([#10285](https://github.com/fivetran/great_expectations/pull/10285))
- Updated the allow-list IP addresses documented for the fully hosted GX Cloud deployment pattern. ([#10308](https://github.com/fivetran/great_expectations/pull/10308))
- Fixed a failing GX Core documentation build. ([#10300](https://github.com/fivetran/great_expectations/pull/10300))
- The GX Core documentation sidebar and version dropdown now stay consistent and keep the tab highlighted when switching between versions 0.18 and 1.0. ([#10302](https://github.com/fivetran/great_expectations/pull/10302))
- Updated the project README. ([#10294](https://github.com/fivetran/great_expectations/pull/10294))

<details>
<summary>Maintenance</summary>

- UnexpectedRowsExpectation renders its query as a code block, reports a descriptive observed value instead of a row count, and accepts an unexpected_rows_query without the \{batch} keyword while warning when it is missing. ([#10334](https://github.com/fivetran/great_expectations/pull/10334))
- UnexpectedRowsExpectation carries metadata and a docstring consistent with core Expectations, and its description is now an instance attribute. ([#10311](https://github.com/fivetran/great_expectations/pull/10311))

</details>

#### Contributors

Thanks to @masfworld (first contribution).

### 1.0.1 (2024-08-29)

#### Highlights

- **Checkpoints now hold onto the exact Validation Definition you pass in** — A Checkpoint now references the same `ValidationDefinition` instance it was given, so changes you make to that object are reflected when the Checkpoint runs instead of acting on a separate copy. ([#10274](https://github.com/fivetran/great_expectations/pull/10274))

  ```python
  validation_definition = context.validation_definitions.add(
      gx.ValidationDefinition(name="my_vd", data=batch_definition, suite=suite)
  )
  checkpoint = gx.Checkpoint(name="my_checkpoint", validation_definitions=[validation_definition])
  assert checkpoint.validation_definitions[0] is validation_definition
  ```

- **Validation Definition API reference documentation** — `ValidationDefinition` and its methods are now marked as public API, so they appear in the published API reference documentation. ([#10282](https://github.com/fivetran/great_expectations/pull/10282))

- **Docs now show a tested way to check your installed GX Core version** — The documentation's instructions for verifying which version of GX Core is installed have been updated and the example is now covered by tests. ([#10286](https://github.com/fivetran/great_expectations/pull/10286))

  ```python
  import great_expectations as gx

  print(gx.__version__)
  ```

- **Direct links to full code examples in the GX Core docs** — Every procedure and sample-code tab group in the GX Core docs now has a header and a query string, so you can link straight to the full code example for any given procedure. ([#10258](https://github.com/fivetran/great_expectations/pull/10258))

#### Changes

##### Bug fixes

- A Checkpoint now references the same Validation Definition instance that was passed to it rather than a copy, so later edits to that object take effect when the Checkpoint runs. ([#10274](https://github.com/fivetran/great_expectations/pull/10274))

##### Docs

- Removed orphaned documentation pages and leftover content from the previous documentation structure, and updated links that pointed to them. ([#10260](https://github.com/fivetran/great_expectations/pull/10260))
- Updated the documented method for checking the version of the installed GX Core library and put the example under test. ([#10286](https://github.com/fivetran/great_expectations/pull/10286))
- Updated the support and contribution documentation to match the current support posture, clarifying issue prioritization, pointing community discussion to Discourse, and documenting the issue labels. ([#10298](https://github.com/fivetran/great_expectations/pull/10298))
- Removed the examples directory from the repository. ([#10293](https://github.com/fivetran/great_expectations/pull/10293))
- Corrected a typo in the result format documentation, which referred to `results_url` instead of `result_url` when retrieving a GX Cloud result link. ([#10283](https://github.com/fivetran/great_expectations/pull/10283))
- Updated the instructions for adding data assets to reflect the current workflow. ([#10200](https://github.com/fivetran/great_expectations/pull/10200))
- Corrected the Databricks SQL docstring, which incorrectly referred to Postgres. ([#10148](https://github.com/fivetran/great_expectations/pull/10148))
- Removed Redshift from the community-supported integrations listed in the application integration support documentation. ([#10280](https://github.com/fivetran/great_expectations/pull/10280))
- Removed the misleading `/database` path element from Databricks SQL connection strings in the documentation and test examples, since it is ignored by the connector. ([#10273](https://github.com/fivetran/great_expectations/pull/10273))
- Docstrings and some error messages now refer to Expectations by their class names instead of the older validator method names. ([#10268](https://github.com/fivetran/great_expectations/pull/10268))
- Fixed the code block shown in the review Validation Results step of the guide to testing an Expectation. ([#10267](https://github.com/fivetran/great_expectations/pull/10267))
- Replaced references to "GX OSS" and "GX 1.0" throughout the documentation with the current product name, GX Core. ([#10255](https://github.com/fivetran/great_expectations/pull/10255))
- Added headers and query strings to the procedure and sample-code tab groups in the GX Core docs so full code examples can be linked to directly. ([#10258](https://github.com/fivetran/great_expectations/pull/10258))
- Fixed a broken internal link to the available Expectations table in the GX Cloud documentation for v1.0 and v0.18. ([#10247](https://github.com/fivetran/great_expectations/pull/10247))
- Promoted the 1.0 documentation to be the latest published version. ([#10261](https://github.com/fivetran/great_expectations/pull/10261))

<details>
<summary>Maintenance</summary>

- Simplified `ValidationDefinition` construction by removing a custom initializer override; behavior is unchanged. ([#10278](https://github.com/fivetran/great_expectations/pull/10278))
- Upgraded the type checker to mypy 1.11.2 and resolved the new typing errors it surfaced; no runtime behavior changed. ([#10142](https://github.com/fivetran/great_expectations/pull/10142))
- Checkpoint creation analytics events now include the ids of the associated validation definitions. ([#10290](https://github.com/fivetran/great_expectations/pull/10290))
- Analytics events are no longer emitted from Azure CI runs. ([#10291](https://github.com/fivetran/great_expectations/pull/10291))
- Marked `ValidationDefinition` as public API so it is included in the published API reference documentation. ([#10282](https://github.com/fivetran/great_expectations/pull/10282))
- Analytics events are no longer emitted from CI runs. ([#10263](https://github.com/fivetran/great_expectations/pull/10263))
- Loosened the `ruamel` version pin to allow 0.18 or greater, which resolves CVE-2019-20478. ([#10266](https://github.com/fivetran/great_expectations/pull/10266))

</details>

### 1.0.0 (2024-08-22)

#### Highlights

- **Rendered content stays up to date** — Rendered content is now regenerated every time rather than reused from a previous render, so descriptions and rendered output always reflect the current expectations and validation results. ([#10257](https://github.com/fivetran/great_expectations/pull/10257))

#### Changes

##### Bug fixes

- Content is now always re-rendered, so rendered output reflects the latest state instead of stale previously rendered content. ([#10257](https://github.com/fivetran/great_expectations/pull/10257))
- Error messages raised when running a Checkpoint include the diagnostics for all of its child validation definitions, not just the first problem found. This change was subsequently reverted in this release. ([#10250](https://github.com/fivetran/great_expectations/pull/10250))

##### Docs

- Updated the project README to describe GX Core. ([#10252](https://github.com/fivetran/great_expectations/pull/10252))

<details>
<summary>Maintenance</summary>

- Reverted the previous change to Checkpoint and Validation Definition error reporting, restoring the earlier behavior where running an unsaved Checkpoint or Validation Definition is saved automatically when its children are already saved and otherwise raises the prior error message. ([#10256](https://github.com/fivetran/great_expectations/pull/10256))
- Introduced an internal diagnostics helper used by the checks that determine whether a Checkpoint, Validation Definition, Expectation Suite, or Batch Definition has been saved, with no change to expected behavior. ([#10249](https://github.com/fivetran/great_expectations/pull/10249))

</details>

### 1.0.0a6
* [FEATURE] Add the public api to context.data_source and context.data_source.get ([#10180](https://github.com/great-expectations/great_expectations/pull/10180))
* [FEATURE] Remove order_by from Asset API ([#10187](https://github.com/great-expectations/great_expectations/pull/10187))
* [FEATURE] Rename name_* params to name ([#10188](https://github.com/great-expectations/great_expectations/pull/10188))
* [FEATURE] Rename suite_param to expectation_param in validation_definitition ([#10196](https://github.com/great-expectations/great_expectations/pull/10196))
* [FEATURE] Delete batch definition by name. ([#10197](https://github.com/great-expectations/great_expectations/pull/10197))
* [FEATURE] Filter bad validation definitions and checkpoints coming back through stores. ([#10219](https://github.com/great-expectations/great_expectations/pull/10219))
* [BUGFIX] Allow 0 ValidationDefinitions on a Checkpoint ([#10194](https://github.com/great-expectations/great_expectations/pull/10194))
* [BUGFIX] Add directive to control generation of reader methods. ([#10198](https://github.com/great-expectations/great_expectations/pull/10198))
* [BUGFIX] Ensure that data source and nested objects obtain IDs on add for all environments ([#10221](https://github.com/great-expectations/great_expectations/pull/10221))
* [BUGFIX] Add StoreBackendError to missing exception list. ([#10224](https://github.com/great-expectations/great_expectations/pull/10224))
* [BUGFIX] Use `is_added` checks in `identifier_bundle` serialization logic ([#10245](https://github.com/great-expectations/great_expectations/pull/10245))
* [BUGFIX] Filter and log bad expectations when loading a suite ([#10248](https://github.com/great-expectations/great_expectations/pull/10248))
* [DOCS] Updated feedback modal ([#10168](https://github.com/great-expectations/great_expectations/pull/10168))
* [DOCS] Fix syntax around getting batch definitions ([#10189](https://github.com/great-expectations/great_expectations/pull/10189))
* [DOCS] Update file system batch params sample to use strings ([#10190](https://github.com/great-expectations/great_expectations/pull/10190))
* [DOCS] DSB-796: Fix syntax highlighting ([#10192](https://github.com/great-expectations/great_expectations/pull/10192))
* [DOCS] Puts 1.0 connect to SQL data code snippets in the documentation under test. ([#10203](https://github.com/great-expectations/great_expectations/pull/10203))
* [DOCS] cloud UI v0 updates ([#10205](https://github.com/great-expectations/great_expectations/pull/10205))
* [DOCS] Update GX version support in support posture ([#10208](https://github.com/great-expectations/great_expectations/pull/10208))
* [DOCS] Transition feedback Jira tickets to kanban board ([#10212](https://github.com/great-expectations/great_expectations/pull/10212))
* [DOCS] Updated deprecation policy ([#10223](https://github.com/great-expectations/great_expectations/pull/10223))
* [DOCS] GX 1.0: Put documentation code under test for connect to filesystem data guides ([#10186](https://github.com/great-expectations/great_expectations/pull/10186))
* [DOCS] Update README.md to remove out dated info on how to contribute to docs ([#10226](https://github.com/great-expectations/great_expectations/pull/10226))
* [DOCS] Puts 1.0 documentation example code for how to run validations under test ([#10230](https://github.com/great-expectations/great_expectations/pull/10230))
* [DOCS] Puts 1.0 example scripts for connecting to dataframe data under test. ([#10225](https://github.com/great-expectations/great_expectations/pull/10225))
* [DOCS] puts 1.0 code under test for how to define Expectations ([#10229](https://github.com/great-expectations/great_expectations/pull/10229))
* [DOCS] Revises the glossary for 1.0 ([#10209](https://github.com/great-expectations/great_expectations/pull/10209))
* [DOCS] Puts scripts for 1.0 "create a Data Context" docs under test ([#10228](https://github.com/great-expectations/great_expectations/pull/10228))
* [DOCS] Puts 1.0 example code for Checkpoints, Actions, and Result Format under test. ([#10232](https://github.com/great-expectations/great_expectations/pull/10232))
* [DOCS] Puts 1.0 examples for how to customize Expectations under test. ([#10235](https://github.com/great-expectations/great_expectations/pull/10235))
* [DOCS] Puts 1.0 example code for how to configure project settings under test ([#10240](https://github.com/great-expectations/great_expectations/pull/10240))
* [DOCS] Puts 1.0 doc examples for how to configure Data Docs into scripts under test ([#10243](https://github.com/great-expectations/great_expectations/pull/10243))
* [DOCS] Add docs tests step to CI ([#10220](https://github.com/great-expectations/great_expectations/pull/10220))
* [DOCS] DOC-818: Update GX Core Overview and Try GX ([#10237](https://github.com/great-expectations/great_expectations/pull/10237))
* [DOCS] Update README.md to reflect contribution posture ([#10244](https://github.com/great-expectations/great_expectations/pull/10244))
* [MAINTENANCE] Update `teams.yml` ([#10178](https://github.com/great-expectations/great_expectations/pull/10178))
* [MAINTENANCE] Remove `notify_on` from base Action ([#10179](https://github.com/great-expectations/great_expectations/pull/10179))
* [MAINTENANCE] Remove `SuiteParameterStore` ([#10191](https://github.com/great-expectations/great_expectations/pull/10191))
* [MAINTENANCE] Use context manager to close session in CloudDataContext ([#10195](https://github.com/great-expectations/great_expectations/pull/10195))
* [MAINTENANCE] Ensure GXCloudStoreBackend session is closed ([#10204](https://github.com/great-expectations/great_expectations/pull/10204))
* [MAINTENANCE] Delete CloudMigrator and ConfigurationBundle ([#10207](https://github.com/great-expectations/great_expectations/pull/10207))
* [MAINTENANCE] Ensure CloudDataStore session is closed ([#10206](https://github.com/great-expectations/great_expectations/pull/10206))
* [MAINTENANCE] Update Posthog payloads ([#10183](https://github.com/great-expectations/great_expectations/pull/10183))
* [MAINTENANCE] Ensure that `context.validation_definitions.all()` works with Cloud ([#10216](https://github.com/great-expectations/great_expectations/pull/10216))
* [MAINTENANCE] Add required keys to SuiteValidationResult.meta ([#10214](https://github.com/great-expectations/great_expectations/pull/10214))
* [MAINTENANCE] Remove cascading saves within Checkpoint hierarchy ([#10218](https://github.com/great-expectations/great_expectations/pull/10218))
* [MAINTENANCE] Get tests around rendered content passing ([#10215](https://github.com/great-expectations/great_expectations/pull/10215))
* [MAINTENANCE] Raise informative errors if child objects are not persisted before parent ([#10217](https://github.com/great-expectations/great_expectations/pull/10217))
* [MAINTENANCE] Update import path for UnexpectedRowsExpectation ([#10234](https://github.com/great-expectations/great_expectations/pull/10234))
* [MAINTENANCE] Add posthog event for all deserialization error. ([#10239](https://github.com/great-expectations/great_expectations/pull/10239))
* [MAINTENANCE] Enable Codecov Test Result Reporting ([#10211](https://github.com/great-expectations/great_expectations/pull/10211))
* [MAINTENANCE] Add batch_parameters to validation results payload ([#10236](https://github.com/great-expectations/great_expectations/pull/10236))
* [MAINTENANCE] Cut over analytics to prod ([#10241](https://github.com/great-expectations/great_expectations/pull/10241))
* [MAINTENANCE] Add `AddedDiagnostics` helper class to `is_added` flows ([#10249](https://github.com/great-expectations/great_expectations/pull/10249))

### 1.0.0a5

- [FEATURE] add slack analytics for cloud ([#9944](https://github.com/great-expectations/great_expectations/pull/9944))
- [FEATURE] Add serialization logic to Expectation models ([#9949](https://github.com/great-expectations/great_expectations/pull/9949))
- [FEATURE] Add get data context mercury v1 integration test. ([#9978](https://github.com/great-expectations/great_expectations/pull/9978))
- [FEATURE] SnowflakeDatasource update ([#10005](https://github.com/great-expectations/great_expectations/pull/10005))
- [FEATURE] SnowflakeDatasource make `role` + `warehouse` required ([#10021](https://github.com/great-expectations/great_expectations/pull/10021))
- [FEATURE] Experimental Python 3.12 support ([#8862](https://github.com/great-expectations/great_expectations/pull/8862))
- [FEATURE] Add atomic renderer for `ExpectMulticolumnSumToEqual` ([#10076](https://github.com/great-expectations/great_expectations/pull/10076))
- [FEATURE] Add missing atomic renderers to Expectations ([#10079](https://github.com/great-expectations/great_expectations/pull/10079))
- [FEATURE] Snowflake - Key-Pair auth updates from `0.18.x` ([#10095](https://github.com/great-expectations/great_expectations/pull/10095))
- [FEATURE] Add sentence case titles to Expectation schemas ([#10097](https://github.com/great-expectations/great_expectations/pull/10097))
- [FEATURE] Use v1 data context endpoint (cloud) ([#10093](https://github.com/great-expectations/great_expectations/pull/10093))
- [FEATURE] SnowflakeDatasource - AccountIdentifier error improvments ([#10104](https://github.com/great-expectations/great_expectations/pull/10104))
- [FEATURE] use v1 cloud api for data sources ([#10094](https://github.com/great-expectations/great_expectations/pull/10094))
- [FEATURE] Make save method for data context variables public ([#10057](https://github.com/great-expectations/great_expectations/pull/10057))
- [FEATURE] Add context.data_sources.all ([#10116](https://github.com/great-expectations/great_expectations/pull/10116))
- [FEATURE] Misc Data Source cleanup ([#10126](https://github.com/great-expectations/great_expectations/pull/10126))
- [FEATURE] Clean up import structure for gx ([#10146](https://github.com/great-expectations/great_expectations/pull/10146))
- [FEATURE] Turn on remaining v1 endpoints ([#10155](https://github.com/great-expectations/great_expectations/pull/10155))
- [FEATURE] Update dataframe batch.validate workflow ([#10165](https://github.com/great-expectations/great_expectations/pull/10165))
- [BUGFIX] Migrate back to github hosted runners until docker issue is fixed ([#10011](https://github.com/great-expectations/great_expectations/pull/10011))
- [BUGFIX] Fix parsing of account/me response. ([#10015](https://github.com/great-expectations/great_expectations/pull/10015))
- [BUGFIX] Handle OSError during save on read-only file system. ([#10024](https://github.com/great-expectations/great_expectations/pull/10024))
- [BUGFIX] add ecr caching to trino and spark images ([#10037](https://github.com/great-expectations/great_expectations/pull/10037))
- [BUGFIX] Avoid writing to great_expectations.yml during init ([#10038](https://github.com/great-expectations/great_expectations/pull/10038))
- [BUGFIX] Z-score renderer when `double_sided` ([#10084](https://github.com/great-expectations/great_expectations/pull/10084))
- [BUGFIX] SQLDatasource (V1) - lowercase unquoted schema_names for SQLAlchemy case-sensitivity compatibility ([#10109](https://github.com/great-expectations/great_expectations/pull/10109))
- [BUGFIX] Revert package update ([#10118](https://github.com/great-expectations/great_expectations/pull/10118))
- [BUGFIX] Remove illegible duplicate local Data Docs link from Slack renderer ([#10130](https://github.com/great-expectations/great_expectations/pull/10130))
- [BUGFIX] Fix type of StoreBackend.\_manually_initialize_store_backend_id ([#10159](https://github.com/great-expectations/great_expectations/pull/10159))
- [BUGFIX] On store add, add id to input model ([#10167](https://github.com/great-expectations/great_expectations/pull/10167))
- [BUGFIX] Add checkpoint_id to validation result meta ([#10169](https://github.com/great-expectations/great_expectations/pull/10169))
- [BUGFIX] Update binary path in mssql docker image ([#10171](https://github.com/great-expectations/great_expectations/pull/10171))
- [DOCS] Revises and reorganizes content for installing additional dependencies per the GX 1.0 ToC ([#9934](https://github.com/great-expectations/great_expectations/pull/9934))
- [DOCS] Initial revision and reorg of "Create a Data Context" content for revised GX 1.0 ToC ([#9938](https://github.com/great-expectations/great_expectations/pull/9938))
- [DOCS] Removes content for integrating with GCP from the BigQuery SQL connect to data topic in the 0.18.x docs ([#9955](https://github.com/great-expectations/great_expectations/pull/9955))
- [DOCS] Clarify SQL Expectation Support in GX Cloud Docs ([#9951](https://github.com/great-expectations/great_expectations/pull/9951))
- [DOCS] core expectation model metadata ([#9967](https://github.com/great-expectations/great_expectations/pull/9967))
- [DOCS] Update Table and Multi Column Expectation docstrings ([#9990](https://github.com/great-expectations/great_expectations/pull/9990))
- [DOCS] Add Alerts Content to the GX Cloud Documentation ([#9880](https://github.com/great-expectations/great_expectations/pull/9880))
- [DOCS] Updates Expectations docstrings with supported OSS Data Sources for gallery ([#10030](https://github.com/great-expectations/great_expectations/pull/10030))
- [DOCS] Adds GX 1.0 preview docs for Run Validations topic ([#10026](https://github.com/great-expectations/great_expectations/pull/10026))
- [DOCS] Connect to data using SQL for GX 1.0 ([#9971](https://github.com/great-expectations/great_expectations/pull/9971))
- [DOCS] Remove splitter from data asset docs and add batch definition documentation to expectation docs ([#10032](https://github.com/great-expectations/great_expectations/pull/10032))
- [DOCS] Update path to config_variables.yml file in docs. ([#10044](https://github.com/great-expectations/great_expectations/pull/10044))
- [DOCS] Add data quality use case TOC skeleton under Learn ([#10049](https://github.com/great-expectations/great_expectations/pull/10049))
- [DOCS] GX 1.0 updated docs for Expectations ([#10048](https://github.com/great-expectations/great_expectations/pull/10048))
- [DOCS] Updates broken links to code examples in github ([#10059](https://github.com/great-expectations/great_expectations/pull/10059))
- [DOCS] Update feedback modal ([#10054](https://github.com/great-expectations/great_expectations/pull/10054))
- [DOCS] Included all new expectations, grouped by DQ issue ([#10062](https://github.com/great-expectations/great_expectations/pull/10062))
- [DOCS] 0.18.9 -> 0.18.17 changelogs ([#10068](https://github.com/great-expectations/great_expectations/pull/10068))
- [DOCS] GX 1.0 Checkpoint guides ([#10055](https://github.com/great-expectations/great_expectations/pull/10055))
- [DOCS] 1.0 Customize Expectations guides ([#10066](https://github.com/great-expectations/great_expectations/pull/10066))
- [DOCS] Updated integrated support policy for 1.0 ([#10064](https://github.com/great-expectations/great_expectations/pull/10064))
- [DOCS] Fix typo ([#10083](https://github.com/great-expectations/great_expectations/pull/10083))
- [DOCS] Fix styles for hovering button in terminal ([#10090](https://github.com/great-expectations/great_expectations/pull/10090))
- [DOCS] update gx cloud and airflow doc ([#10025](https://github.com/great-expectations/great_expectations/pull/10025))
- [DOCS] Updated documentation for the GX Scheduler ([#10103](https://github.com/great-expectations/great_expectations/pull/10103))
- [DOCS] 1.0 connect to filesystem data guides ([#10115](https://github.com/great-expectations/great_expectations/pull/10115))
- [DOCS] 1.0 guides for connecting to data in dataframes ([#10133](https://github.com/great-expectations/great_expectations/pull/10133))
- [DOCS] 1.0 guide for getting sample data for testing or data exploration ([#10136](https://github.com/great-expectations/great_expectations/pull/10136))
- [DOCS] Added more expectations for Cloud, sorted by DQ issue ([#10137](https://github.com/great-expectations/great_expectations/pull/10137))
- [DOCS] Incorporating review feedback ([#10138](https://github.com/great-expectations/great_expectations/pull/10138))
- [DOCS] first draft for Data Quality: Schema tech doc ([#10022](https://github.com/great-expectations/great_expectations/pull/10022))
- [DOCS] Update docs to include Runner and suppress Agent ([#10139](https://github.com/great-expectations/great_expectations/pull/10139))
- [DOCS] Typo corrections in GX Cloud docs ([#10156](https://github.com/great-expectations/great_expectations/pull/10156))
- [DOCS] Integrate feedback modal with Jira ([#10110](https://github.com/great-expectations/great_expectations/pull/10110))
- [DOCS] DSB-961: Fix table of contents highlighting ([#10152](https://github.com/great-expectations/great_expectations/pull/10152))
- [DOCS] Add dedicated page for scheduler ([#10158](https://github.com/great-expectations/great_expectations/pull/10158))
- [DOCS] 1-0 guide: how to toggle analytics collection ([#10166](https://github.com/great-expectations/great_expectations/pull/10166))
- [DOCS] 1.0 preview docs: Configure project Stores ([#10150](https://github.com/great-expectations/great_expectations/pull/10150))
- [DOCS] 1.0 guide for securely storing and accessing credentials and tokens ([#10157](https://github.com/great-expectations/great_expectations/pull/10157))
- [DOCS] updated older support policy ([#10174](https://github.com/great-expectations/great_expectations/pull/10174))
- [MAINTENANCE] Exclude patterns from codecov reports ([#9941](https://github.com/great-expectations/great_expectations/pull/9941))
- [MAINTENANCE] Temporary: xfail tests that hit fastapi ([#9946](https://github.com/great-expectations/great_expectations/pull/9946))
- [MAINTENANCE] Clean up extraneous GX Cloud enums ([#9947](https://github.com/great-expectations/great_expectations/pull/9947))
- [MAINTENANCE] Add fastapi to docker-compose for mercury ([#9948](https://github.com/great-expectations/great_expectations/pull/9948))
- [MAINTENANCE] Changes to allow local testing using mercury's docker-compose ([#9976](https://github.com/great-expectations/great_expectations/pull/9976))
- [MAINTENANCE] Ensure that validation definitions and checkpoints save before running ([#9963](https://github.com/great-expectations/great_expectations/pull/9963))
- [MAINTENANCE] core expectation metadata ([#9985](https://github.com/great-expectations/great_expectations/pull/9985))
- [MAINTENANCE] Export types for all of GX (V1 pre-release) ([#9987](https://github.com/great-expectations/great_expectations/pull/9987))
- [MAINTENANCE] Add `metadata` property to Expectation schemas ([#9993](https://github.com/great-expectations/great_expectations/pull/9993))
- [MAINTENANCE] Add schemas for Table and Multi-Column Expectations ([#9991](https://github.com/great-expectations/great_expectations/pull/9991))
- [MAINTENANCE] Migrate ci to enterprise-arc runners ([#9757](https://github.com/great-expectations/great_expectations/pull/9757))
- [MAINTENANCE] Upgrade to pytest 8 ([#10006](https://github.com/great-expectations/great_expectations/pull/10006))
- [MAINTENANCE] ruff `0.4.8` ([#10009](https://github.com/great-expectations/great_expectations/pull/10009))
- [MAINTENANCE] Add custom types to Expectation schemas ([#9994](https://github.com/great-expectations/great_expectations/pull/9994))
- [MAINTENANCE] Remove unused properties on single Expectation ([#10004](https://github.com/great-expectations/great_expectations/pull/10004))
- [MAINTENANCE] Patch for CVE-2024-36039 ([#10016](https://github.com/great-expectations/great_expectations/pull/10016))
- [MAINTENANCE] Bump context config version to 4.0 ([#10013](https://github.com/great-expectations/great_expectations/pull/10013))
- [MAINTENANCE] Clean up top-level `conftest.py` ([#10014](https://github.com/great-expectations/great_expectations/pull/10014))
- [MAINTENANCE] Refactor metadata for ColumnAggregate Expectations ([#10019](https://github.com/great-expectations/great_expectations/pull/10019))
- [MAINTENANCE] Rename `ExpectationConfiguration` `expectation_type` to `type` ([#10018](https://github.com/great-expectations/great_expectations/pull/10018))
- [MAINTENANCE] Define JSON Schemas for ColumnAggregate Expectations ([#10020](https://github.com/great-expectations/great_expectations/pull/10020))
- [MAINTENANCE] configure images to pull through our ecr cache ([#10001](https://github.com/great-expectations/great_expectations/pull/10001))
- [MAINTENANCE] Move `mostly` to correct Expectation classes ([#10027](https://github.com/great-expectations/great_expectations/pull/10027))
- [MAINTENANCE] Add metadata to `ColumnMapExpectations` ([#10034](https://github.com/great-expectations/great_expectations/pull/10034))
- [MAINTENANCE] : change expectation kwarg types (breaking change) ([#10051](https://github.com/great-expectations/great_expectations/pull/10051))
- [MAINTENANCE] add json schema field description ([#10065](https://github.com/great-expectations/great_expectations/pull/10065))
- [MAINTENANCE] update ignore panda db client warning ([#10071](https://github.com/great-expectations/great_expectations/pull/10071))
- [MAINTENANCE] Improve Expectation schemas ([#10099](https://github.com/great-expectations/great_expectations/pull/10099))
- [MAINTENANCE] Have DCV point at V1 ([#10102](https://github.com/great-expectations/great_expectations/pull/10102))
- [MAINTENANCE] Update `ConfigStr` + `ConfigUri` json schema definition ([#10023](https://github.com/great-expectations/great_expectations/pull/10023))
- [MAINTENANCE] Parametrize `TestConnectionError` ([#10105](https://github.com/great-expectations/great_expectations/pull/10105))
- [MAINTENANCE] Loosen `ruamel.yaml` pin (v1) ([#10106](https://github.com/great-expectations/great_expectations/pull/10106))
- [MAINTENANCE] Remove public api decorator from non-public V1 code. ([#10111](https://github.com/great-expectations/great_expectations/pull/10111))
- [MAINTENANCE] Update yarn.lock to handle vanta vulnerbilities. ([#10114](https://github.com/great-expectations/great_expectations/pull/10114))
- [MAINTENANCE] Pin setuptools, we error with the latest. ([#10119](https://github.com/great-expectations/great_expectations/pull/10119))
- [MAINTENANCE] Revert "[MAINTENANCE] Pin setuptools, we error with the latest." ([#10123](https://github.com/great-expectations/great_expectations/pull/10123))
- [MAINTENANCE] Allow numpy 2 ([#10122](https://github.com/great-expectations/great_expectations/pull/10122))
- [MAINTENANCE] Ruff `0.5.3` ([#10124](https://github.com/great-expectations/great_expectations/pull/10124))
- [MAINTENANCE] Forbid extra attrs on V1 Pydantic models ([#10127](https://github.com/great-expectations/great_expectations/pull/10127))
- [MAINTENANCE] Add context.data_sources.get ([#10125](https://github.com/great-expectations/great_expectations/pull/10125))
- [MAINTENANCE] mypy - `possibly-undefined` ([#10092](https://github.com/great-expectations/great_expectations/pull/10092))
- [MAINTENANCE] Remove immutability from validation definition ([#10141](https://github.com/great-expectations/great_expectations/pull/10141))
- [MAINTENANCE] Add a clause when we reraise exceptions in tuple_store_backend.py ([#10160](https://github.com/great-expectations/great_expectations/pull/10160))
- [MAINTENANCE] update_datasource returns the updated datasource ([#10170](https://github.com/great-expectations/great_expectations/pull/10170))
- [MAINTENANCE] Temporarily update Pandas pins to unblock V1 prerelease ([#10175](https://github.com/great-expectations/great_expectations/pull/10175))

### 1.0.0a4

- [FEATURE] Remove ExpectationSuite.execution_engine_type ([#9841](https://github.com/great-expectations/great_expectations/pull/9841))
- [FEATURE] Directory Asset BatchDefinition API ([#9874](https://github.com/great-expectations/great_expectations/pull/9874))
- [FEATURE] DirectoryAsset BatchDefinition API ([#9888](https://github.com/great-expectations/great_expectations/pull/9888))
- [FEATURE] update slack renderer to new design ([#9919](https://github.com/great-expectations/great_expectations/pull/9919))
- [BUGFIX] Make column_index optional ([#9860](https://github.com/great-expectations/great_expectations/pull/9860))
- [BUGFIX] fix sqlalchemy import ([#9872](https://github.com/great-expectations/great_expectations/pull/9872))
- [BUGFIX] Ensure that `SlackNotificationAction` renders properly ([#9885](https://github.com/great-expectations/great_expectations/pull/9885))
- [BUGFIX] Patch issue with `SlackNotificationAction` header rendering ([#9903](https://github.com/great-expectations/great_expectations/pull/9903))
- [DOCS] Remove Instances of Test Connection from the GX Cloud Docs ([#9815](https://github.com/great-expectations/great_expectations/pull/9815))
- [DOCS] Remove Query Asset Content from GX Cloud Docs ([#9802](https://github.com/great-expectations/great_expectations/pull/9802))
- [DOCS] added discourse to OSS support ([#9847](https://github.com/great-expectations/great_expectations/pull/9847))
- [DOCS] Update get support ([#9852](https://github.com/great-expectations/great_expectations/pull/9852))
- [DOCS] Minor Updates to GX Cloud Expectations Topics ([#9884](https://github.com/great-expectations/great_expectations/pull/9884))
- [DOCS] Gx 1.0 Introductory content initial reorganization (take 2) ([#9869](https://github.com/great-expectations/great_expectations/pull/9869))
- [DOCS] Minor GX Cloud Docs Fixes ([#9892](https://github.com/great-expectations/great_expectations/pull/9892))
- [DOCS] Revises the GX component overview for GX 1.0 ([#9896](https://github.com/great-expectations/great_expectations/pull/9896))
- [DOCS] Change the texts of the "Was this Helpful?" widget ([#9905](https://github.com/great-expectations/great_expectations/pull/9905))
- [DOCS] Updates to About Great Expectations and Community Resources (OSS) ([#9912](https://github.com/great-expectations/great_expectations/pull/9912))
- [DOCS] Update 0.18 changelog ([#9914](https://github.com/great-expectations/great_expectations/pull/9914))
- [DOCS] Minor Edits to Connect GX Cloud to PostgreSQL (GX Cloud) ([#9927](https://github.com/great-expectations/great_expectations/pull/9927))
- [DOCS] Revise "Try GX" for GX 1.0 ([#9897](https://github.com/great-expectations/great_expectations/pull/9897))
- [DOCS] reorganizes content under the 1.0 Set up a GX environment topic ([#9930](https://github.com/great-expectations/great_expectations/pull/9930))
- [MAINTENANCE] Ruff 0.4.2 ([#9833](https://github.com/great-expectations/great_expectations/pull/9833))
- [MAINTENANCE] Enable SIM110 ([#9836](https://github.com/great-expectations/great_expectations/pull/9836))
- [MAINTENANCE] Enable SIM211 ([#9832](https://github.com/great-expectations/great_expectations/pull/9832))
- [MAINTENANCE] Enable SIM300 ([#9834](https://github.com/great-expectations/great_expectations/pull/9834))
- [MAINTENANCE] Enable SIM201 ([#9835](https://github.com/great-expectations/great_expectations/pull/9835))
- [MAINTENANCE] Delete dataset directory. ([#9842](https://github.com/great-expectations/great_expectations/pull/9842))
- [MAINTENANCE] Finish removing data asset top level package ([#9843](https://github.com/great-expectations/great_expectations/pull/9843))
- [MAINTENANCE] Make `SerializableDataContext.create` private ([#9853](https://github.com/great-expectations/great_expectations/pull/9853))
- [MAINTENANCE] mypy 1.10 ([#9857](https://github.com/great-expectations/great_expectations/pull/9857))
- [MAINTENANCE] Make `ExpectationSuite` importable from the top level GX namespace ([#9854](https://github.com/great-expectations/great_expectations/pull/9854))
- [MAINTENANCE] Remove block style datasource and batch from public api ([#9858](https://github.com/great-expectations/great_expectations/pull/9858))
- [MAINTENANCE] Remove LegacyDatasource ([#9848](https://github.com/great-expectations/great_expectations/pull/9848))
- [MAINTENANCE] set marker tests to not fail fast ([#9862](https://github.com/great-expectations/great_expectations/pull/9862))
- [MAINTENANCE] Ensure Spark can start ([#9866](https://github.com/great-expectations/great_expectations/pull/9866))
- [MAINTENANCE] Remove test_yaml_config and all integration tests that … ([#9861](https://github.com/great-expectations/great_expectations/pull/9861))
- [MAINTENANCE] Actually remove LegacyDatasource ([#9867](https://github.com/great-expectations/great_expectations/pull/9867))
- [MAINTENANCE] Remove `DataAssistants` ([#9859](https://github.com/great-expectations/great_expectations/pull/9859))
- [MAINTENANCE] Remove public decorator from anything BatchRequest related ([#9871](https://github.com/great-expectations/great_expectations/pull/9871))
- [MAINTENANCE] Skip unsupported time metric (1.0) ([#9856](https://github.com/great-expectations/great_expectations/pull/9856))
- [MAINTENANCE] enable tests ([#9865](https://github.com/great-expectations/great_expectations/pull/9865))
- [MAINTENANCE] Integration test around pandas ABS partitioning ([#9837](https://github.com/great-expectations/great_expectations/pull/9837))
- [MAINTENANCE] Integration tests around s3 batches ([#9846](https://github.com/great-expectations/great_expectations/pull/9846))
- [MAINTENANCE] GCS Integration tests around partitioning ([#9839](https://github.com/great-expectations/great_expectations/pull/9839))
- [MAINTENANCE] Update context factories to delete by name ([#9870](https://github.com/great-expectations/great_expectations/pull/9870))
- [MAINTENANCE] `ExpectationSuite` API cleanup ([#9875](https://github.com/great-expectations/great_expectations/pull/9875))
- [MAINTENANCE] Remove yaml config validator again ([#9877](https://github.com/great-expectations/great_expectations/pull/9877))
- [MAINTENANCE] Remove dataconnector tests that reference block style D… ([#9879](https://github.com/great-expectations/great_expectations/pull/9879))
- [MAINTENANCE] Remove some references to block style datasource ([#9868](https://github.com/great-expectations/great_expectations/pull/9868))
- [MAINTENANCE] Remove URN support ([#9886](https://github.com/great-expectations/great_expectations/pull/9886))
- [MAINTENANCE] Rename core partitioners ([#9894](https://github.com/great-expectations/great_expectations/pull/9894))
- [MAINTENANCE] Remove legacy `GeCloudStoreBackend` ([#9893](https://github.com/great-expectations/great_expectations/pull/9893))
- [MAINTENANCE] FileDataAsset BatchDefinition API accepts either `str` or `re.Pattern` ([#9895](https://github.com/great-expectations/great_expectations/pull/9895))
- [MAINTENANCE] Instrument validation workflows ([#9889](https://github.com/great-expectations/great_expectations/pull/9889))
- [MAINTENANCE] Remove remaining references to block style datasources ([#9881](https://github.com/great-expectations/great_expectations/pull/9881))
- [MAINTENANCE] Refactor legacy `anonymous_usage_statistics` into new top-level fields ([#9891](https://github.com/great-expectations/great_expectations/pull/9891))
- [MAINTENANCE] Remove suite CRUD from data_context ([#9890](https://github.com/great-expectations/great_expectations/pull/9890))
- [MAINTENANCE] Ensure that actions have names ([#9902](https://github.com/great-expectations/great_expectations/pull/9902))
- [MAINTENANCE] Remove simple sqlalchemy datasource ([#9900](https://github.com/great-expectations/great_expectations/pull/9900))
- [MAINTENANCE] Remove references to suite crud ([#9907](https://github.com/great-expectations/great_expectations/pull/9907))
- [MAINTENANCE] Improve error message around instantiating and saving s… ([#9908](https://github.com/great-expectations/great_expectations/pull/9908))
- [MAINTENANCE] Remove BaseDatasource ([#9901](https://github.com/great-expectations/great_expectations/pull/9901))
- [MAINTENANCE] Remove DatasourceConfig ([#9916](https://github.com/great-expectations/great_expectations/pull/9916))
- [MAINTENANCE] Ruff `0.4.4` ([#9918](https://github.com/great-expectations/great_expectations/pull/9918))
- [MAINTENANCE] Update packaging pipeline to work on 1.0 ([#9922](https://github.com/great-expectations/great_expectations/pull/9922))
- [MAINTENANCE] Remove legacy DataConnectors ([#9923](https://github.com/great-expectations/great_expectations/pull/9923))
- [MAINTENANCE] Remove batch kwargs ([#9932](https://github.com/great-expectations/great_expectations/pull/9932))
- [MAINTENANCE] Move `convert_to_json_serializable` to top-level utils package ([#9933](https://github.com/great-expectations/great_expectations/pull/9933))
- [MAINTENANCE] Ban future use of `convert_to_json_serializable` ([#9935](https://github.com/great-expectations/great_expectations/pull/9935))
- [MAINTENANCE] Remove batching regex from FilePathDataConnector ([#9898](https://github.com/great-expectations/great_expectations/pull/9898))

### 1.0.0a3

- [FEATURE] Add Regex Partitioner ([#9792](https://github.com/great-expectations/great_expectations/pull/9792))
- [FEATURE] Fluent BatchDefinition API for Pandas Assets ([#9820](https://github.com/great-expectations/great_expectations/pull/9820))
- [FEATURE] Add fluent-style BatchDefinition API to file-backed DataAssets ([#9823](https://github.com/great-expectations/great_expectations/pull/9823))
- [FEATURE] BatchDefinition API for Directory DataAsset ([#9827](https://github.com/great-expectations/great_expectations/pull/9827))
- [FEATURE] Remove [cloud] optional dependency ([#9813](https://github.com/great-expectations/great_expectations/pull/9813))
- [BUGFIX] limit unexpected count if include_unexpected_rows is set ([#9781](https://github.com/great-expectations/great_expectations/pull/9781))
- [BUGFIX] Pass in partitioner + batching_regex when creating batch_def… ([#9798](https://github.com/great-expectations/great_expectations/pull/9798))
- [BUGFIX] Do not persist interactive batch defs ([#9816](https://github.com/great-expectations/great_expectations/pull/9816))
- [BUGFIX] `scrapy` compatibility - handle `dir()` inconsistencies (#9830) ([#9831](https://github.com/great-expectations/great_expectations/pull/9831))
- [DOCS] Link Fix ([#9772](https://github.com/great-expectations/great_expectations/pull/9772))
- [DOCS] Adds clarification of `discard_failed_expectations` to 0.18.x OSS quickstart ([#9782](https://github.com/great-expectations/great_expectations/pull/9782))
- [DOCS] Remove Feedback Widget from Landing Pages ([#9780](https://github.com/great-expectations/great_expectations/pull/9780))
- [DOCS] Learn TOC Updates ([#9784](https://github.com/great-expectations/great_expectations/pull/9784))
- [DOCS] Update About GX Cloud ([#9751](https://github.com/great-expectations/great_expectations/pull/9751))
- [DOCS] Update Docs for GX-Agent Versioning ([#9783](https://github.com/great-expectations/great_expectations/pull/9783))
- [DOCS] Add GX Cloud Logs Content ([#9766](https://github.com/great-expectations/great_expectations/pull/9766))
- [DOCS] Update agent deploy docs to specify imagePullPolicy of Always ([#9805](https://github.com/great-expectations/great_expectations/pull/9805))
- [DOCS] Updates to how to get support ([#9809](https://github.com/great-expectations/great_expectations/pull/9809))
- [DOCS] Update docs for Agent Active icon ([#9808](https://github.com/great-expectations/great_expectations/pull/9808))
- [DOCS] More updates to the how to get support page ([#9818](https://github.com/great-expectations/great_expectations/pull/9818))
- [MAINTENANCE] Update codecov so PRs start passing. ([#9764](https://github.com/great-expectations/great_expectations/pull/9764))
- [MAINTENANCE] Make CheckpointAction Annotated ([#9761](https://github.com/great-expectations/great_expectations/pull/9761))
- [MAINTENANCE] Rename validations -> validation_results ([#9774](https://github.com/great-expectations/great_expectations/pull/9774))
- [MAINTENANCE] Convert QuantileRange from TypedDict to BaseModel ([#9767](https://github.com/great-expectations/great_expectations/pull/9767))
- [MAINTENANCE] Remove add_sorters methods ([#9773](https://github.com/great-expectations/great_expectations/pull/9773))
- [MAINTENANCE] Clean up legacy checkpoint tests and components ([#9749](https://github.com/great-expectations/great_expectations/pull/9749))
- [MAINTENANCE] Generic type for Partitioner ([#9785](https://github.com/great-expectations/great_expectations/pull/9785))
- [MAINTENANCE] Retire ColumnDescriptiveMetrics - Develop ([#9790](https://github.com/great-expectations/great_expectations/pull/9790))
- [MAINTENANCE] Integration tests around SQL validation workflows ([#9788](https://github.com/great-expectations/great_expectations/pull/9788))
- [MAINTENANCE] Remove Spark Partitioners ([#9796](https://github.com/great-expectations/great_expectations/pull/9796))
- [MAINTENANCE] Make codecov informational ([#9797](https://github.com/great-expectations/great_expectations/pull/9797))
- [MAINTENANCE] Delete legacy checkpoint ([#9791](https://github.com/great-expectations/great_expectations/pull/9791))
- [MAINTENANCE] Add unexpected rows expectation code snippet for docs ([#9800](https://github.com/great-expectations/great_expectations/pull/9800))
- [MAINTENANCE] Turn on numpy 2 prerelease tests. ([#9707](https://github.com/great-expectations/great_expectations/pull/9707))
- [MAINTENANCE] Promote V1 Checkpoint objects ([#9803](https://github.com/great-expectations/great_expectations/pull/9803))
- [MAINTENANCE] Remove `include_rendered_content` flag ([#9807](https://github.com/great-expectations/great_expectations/pull/9807))
- [MAINTENANCE] Remove gallery build pipeline ([#9777](https://github.com/great-expectations/great_expectations/pull/9777))
- [MAINTENANCE] Add script to generate public api list. ([#9712](https://github.com/great-expectations/great_expectations/pull/9712))
- [MAINTENANCE] Bring back sql_datasource integration tests for backend… ([#9812](https://github.com/great-expectations/great_expectations/pull/9812))
- [MAINTENANCE] Ensure that V1 Validator works with Cloud rendered content ([#9810](https://github.com/great-expectations/great_expectations/pull/9810))
- [MAINTENANCE] Remove xfail from checkpoint and data docs integration tests ([#9811](https://github.com/great-expectations/great_expectations/pull/9811))
- [MAINTENANCE] Enable SIM103 ([#9801](https://github.com/great-expectations/great_expectations/pull/9801))
- [MAINTENANCE] Prework for implementing fluent batch definition api for file path assets ([#9817](https://github.com/great-expectations/great_expectations/pull/9817))
- [MAINTENANCE] Enable SIM118 ([#9819](https://github.com/great-expectations/great_expectations/pull/9819))
- [MAINTENANCE] Delete legacy checkpoint config and result ([#9824](https://github.com/great-expectations/great_expectations/pull/9824))
- [MAINTENANCE] Rename `sources` to `data_sources` ([#9825](https://github.com/great-expectations/great_expectations/pull/9825))
- [MAINTENANCE] Update Pandas DataAsset type ([#9826](https://github.com/great-expectations/great_expectations/pull/9826))
- [MAINTENANCE] file system integration tests ([#9793](https://github.com/great-expectations/great_expectations/pull/9793))
- [MAINTENANCE] Update Pandas Types ([#9828](https://github.com/great-expectations/great_expectations/pull/9828))
- [MAINTENANCE] Backfill checkpoint ID/PK integration tests ([#9821](https://github.com/great-expectations/great_expectations/pull/9821))
- [MAINTENANCE] SQL backend integration tests ([#9822](https://github.com/great-expectations/great_expectations/pull/9822))

### 1.0.0a2

- [FEATURE] `TableAsset.test_connection()` should fail if table is not queryable. (#9198) ([#9475](https://github.com/great-expectations/great_expectations/pull/9475))
- [FEATURE] Add backend-agnostic partitioners ([#9460](https://github.com/great-expectations/great_expectations/pull/9460))
- [FEATURE] v1 59/suite evaluation parameter options ([#9474](https://github.com/great-expectations/great_expectations/pull/9474))
- [FEATURE] Add Partitioner to BatchRequest ([#9482](https://github.com/great-expectations/great_expectations/pull/9482))
- [FEATURE] `CheckpointFactory` ([#9413](https://github.com/great-expectations/great_expectations/pull/9413))
- [FEATURE] V1 Validation scaffolding ([#9508](https://github.com/great-expectations/great_expectations/pull/9508))
- [FEATURE] DataAsset uses partitioner from BatchConfig ([#9499](https://github.com/great-expectations/great_expectations/pull/9499))
- [FEATURE] `ValidationConfigStore` ([#9523](https://github.com/great-expectations/great_expectations/pull/9523))
- [FEATURE] Add evaluation parameter support to v1 validator ([#9552](https://github.com/great-expectations/great_expectations/pull/9552))
- [FEATURE] Don't break context for invalid datasource configs ([#9486](https://github.com/great-expectations/great_expectations/pull/9486))
- [FEATURE] Add ValidationConfig::run ([#9571](https://github.com/great-expectations/great_expectations/pull/9571))
- [FEATURE] Enable `ValidationConfig` CRUD ([#9566](https://github.com/great-expectations/great_expectations/pull/9566))
- [FEATURE] `ValidationConfig.save()` ([#9579](https://github.com/great-expectations/great_expectations/pull/9579))
- [FEATURE] Save validation results on ValidationDefinition run ([#9599](https://github.com/great-expectations/great_expectations/pull/9599))
- [FEATURE] MetricListMetricRetriever - develop ([#9620](https://github.com/great-expectations/great_expectations/pull/9620))
- [FEATURE] V1 Checkpoint ([#9590](https://github.com/great-expectations/great_expectations/pull/9590))
- [FEATURE] `Checkpoint.save()` ([#9676](https://github.com/great-expectations/great_expectations/pull/9676))
- [FEATURE] Add support for V1 Cloud Backend endpoints ([#9651](https://github.com/great-expectations/great_expectations/pull/9651))
- [FEATURE] Implement TupleFilesystemStoreBackend::get_all ([#9687](https://github.com/great-expectations/great_expectations/pull/9687))
- [FEATURE] Implement TupleS3StoreBackend::get_all ([#9692](https://github.com/great-expectations/great_expectations/pull/9692))
- [FEATURE] Implement InlineStoreBackend::get_all ([#9686](https://github.com/great-expectations/great_expectations/pull/9686))
- [FEATURE] Refactor FilePathDataConnector ([#9704](https://github.com/great-expectations/great_expectations/pull/9704))
- [FEATURE] TupleGCSStoreBackend::get_all ([#9703](https://github.com/great-expectations/great_expectations/pull/9703))
- [FEATURE] TupleAzureBlobStoreBackend::get_all ([#9708](https://github.com/great-expectations/great_expectations/pull/9708))
- [FEATURE] Add BatchRequest.batching_regex ([#9710](https://github.com/great-expectations/great_expectations/pull/9710))
- [FEATURE] Implement LegacyBatchDefinition.batching_regex ([#9717](https://github.com/great-expectations/great_expectations/pull/9717))
- [FEATURE] Update expectations and checkpoints v1 stores to implement gx_cloud_response_json_to_object_collection ([#9718](https://github.com/great-expectations/great_expectations/pull/9718))
- [FEATURE] Add BatchDefinition.batching_regex ([#9721](https://github.com/great-expectations/great_expectations/pull/9721))
- [FEATURE] Factory iterators ([#9682](https://github.com/great-expectations/great_expectations/pull/9682))
- [FEATURE] BatchDefinition fluent API for SQL Assets ([#9732](https://github.com/great-expectations/great_expectations/pull/9732))
- [FEATURE] Batch definition sorting ([#9720](https://github.com/great-expectations/great_expectations/pull/9720))
- [FEATURE] `BatchDefinition.get_batch` ([#9753](https://github.com/great-expectations/great_expectations/pull/9753))
- [FEATURE] Add sort_ascending to BatchDefinition fluent API ([#9756](https://github.com/great-expectations/great_expectations/pull/9756))
- [BUGFIX] Databricks shared compute fix ([#9490](https://github.com/great-expectations/great_expectations/pull/9490))
- [BUGFIX] Fix tabs to reference correct versions for 0.18 and 1.0 ([#9489](https://github.com/great-expectations/great_expectations/pull/9489))
- [BUGFIX] Fix test setup to get ephemeral context ([#9504](https://github.com/great-expectations/great_expectations/pull/9504))
- [BUGFIX] - Prevent duplicate Expectations in Validation Results when Exceptions are triggered ([#9456](https://github.com/great-expectations/great_expectations/pull/9456))
- [BUGFIX] Ensure that `concurrency` is ignored in V1 Cloud contexts ([#9553](https://github.com/great-expectations/great_expectations/pull/9553))
- [BUGFIX] fix ExpectationConfiguration import in snippet ([#9567](https://github.com/great-expectations/great_expectations/pull/9567))
- [BUGFIX] Misconfigured Expectations affecting unassociated Checkpoints ([#9491](https://github.com/great-expectations/great_expectations/pull/9491))
- [BUGFIX] Remove counts when showing a sample ([#9638](https://github.com/great-expectations/great_expectations/pull/9638))
- [BUGFIX] Patch `ValidationDefinition` round trip serialization/deserialization ([#9700](https://github.com/great-expectations/great_expectations/pull/9700))
- [BUGFIX] Ensure that `Checkpoint` deserializes proper action subclass ([#9701](https://github.com/great-expectations/great_expectations/pull/9701))
- [BUGFIX] Exclude batch_definitions from \_EXCLUDE_FROM_READER_OPTIONS ([#9702](https://github.com/great-expectations/great_expectations/pull/9702))
- [DOCS] Update Edit a Checkpoint Configuration ([#9484](https://github.com/great-expectations/great_expectations/pull/9484))
- [DOCS] Add 0.18.9 release to docs versions ([#9488](https://github.com/great-expectations/great_expectations/pull/9488))
- [DOCS] Corrected and simplified CTAs for getting customer support ([#9492](https://github.com/great-expectations/great_expectations/pull/9492))
- [DOCS] Add a Procedure for Adding a Validation to a Checkpoint to the GX Cloud Docs ([#9487](https://github.com/great-expectations/great_expectations/pull/9487))
- [DOCS] Pin sphinx extensions ([#9505](https://github.com/great-expectations/great_expectations/pull/9505))
- [DOCS] Fix links style ([#9503](https://github.com/great-expectations/great_expectations/pull/9503))
- [DOCS] Update the README in the Great Expectations Repository ([#9498](https://github.com/great-expectations/great_expectations/pull/9498))
- [DOCS] updating docs cta for workshops DO NOT MERGE UNTIL 2/1 ([#9497](https://github.com/great-expectations/great_expectations/pull/9497))
- [DOCS] Remove Beta from GX Cloud Account References ([#9506](https://github.com/great-expectations/great_expectations/pull/9506))
- [DOCS] Adds titles to all codeblocks ([#9447](https://github.com/great-expectations/great_expectations/pull/9447))
- [DOCS] Fix regex when checking for snippet names ([#9509](https://github.com/great-expectations/great_expectations/pull/9509))
- [DOCS] Update styles for autogenerated index pages ([#9481](https://github.com/great-expectations/great_expectations/pull/9481))
- [DOCS] Remove GitHub badge for mobile ([#9467](https://github.com/great-expectations/great_expectations/pull/9467))
- [DOCS] Fix interactions with versioning dropdown ([#9493](https://github.com/great-expectations/great_expectations/pull/9493))
- [DOCS] Resources dropdown should be visible at all times ([#9514](https://github.com/great-expectations/great_expectations/pull/9514))
- [DOCS] Highlight section docs in sidebar ([#9417](https://github.com/great-expectations/great_expectations/pull/9417))
- [DOCS] Was This Helpful section ([#9426](https://github.com/great-expectations/great_expectations/pull/9426))
- [DOCS] Archive 0.17 ([#9520](https://github.com/great-expectations/great_expectations/pull/9520))
- [DOCS] Add "Was it Helpful?" section to the Setup overview page ([#9526](https://github.com/great-expectations/great_expectations/pull/9526))
- [DOCS] Update README.md ([#9555](https://github.com/great-expectations/great_expectations/pull/9555))
- [DOCS] Updating breadcrumbs styles ([#9554](https://github.com/great-expectations/great_expectations/pull/9554))
- [DOCS] Feedback Modal ([#9525](https://github.com/great-expectations/great_expectations/pull/9525))
- [DOCS] Update terminal and code snippets style ([#9419](https://github.com/great-expectations/great_expectations/pull/9419))
- [DOCS] Update font size of left navigation ([#9561](https://github.com/great-expectations/great_expectations/pull/9561))
- [DOCS] Adds titles to code blocks in v0.18.x docs ([#9563](https://github.com/great-expectations/great_expectations/pull/9563))
- [DOCS] Add Missing Prerequisites Content ([#9575](https://github.com/great-expectations/great_expectations/pull/9575))
- [DOCS] Build out 1.0 docs ToC with stub pages for sections in progress ([#9564](https://github.com/great-expectations/great_expectations/pull/9564))
- [DOCS] Changes the default ToC when a page match isn't found on version change. ([#9581](https://github.com/great-expectations/great_expectations/pull/9581))
- [DOCS] Update Account Identifier Field Description ([#9583](https://github.com/great-expectations/great_expectations/pull/9583))
- [DOCS] Add Snowflake Connection Syntax Example ([#9588](https://github.com/great-expectations/great_expectations/pull/9588))
- [DOCS] Docs announcement bar copy update ([#9595](https://github.com/great-expectations/great_expectations/pull/9595))
- [DOCS] Posthog Instance ([#9592](https://github.com/great-expectations/great_expectations/pull/9592))
- [DOCS] Revise OSS Installation and Setup Guidance for Google Cloud Storage ([#9600](https://github.com/great-expectations/great_expectations/pull/9600))
- [DOCS] Hide duplicate tabs ([#9570](https://github.com/great-expectations/great_expectations/pull/9570))
- [DOCS] Update Instances of `python title="Jupyter Notebook"` ([#9604](https://github.com/great-expectations/great_expectations/pull/9604))
- [DOCS] Removes remaining OSS docs from the prerelease version ([#9582](https://github.com/great-expectations/great_expectations/pull/9582))
- [DOCS] Revise OSS Installation and Setup Guidance for SQL Data Sources ([#9609](https://github.com/great-expectations/great_expectations/pull/9609))
- [DOCS] Consolidate Install Additional Dependencies Content ([#9611](https://github.com/great-expectations/great_expectations/pull/9611))
- [DOCS] Changes to the docs API page ([#9613](https://github.com/great-expectations/great_expectations/pull/9613))
- [DOCS] Bring back 1.0 changelog ([#9621](https://github.com/great-expectations/great_expectations/pull/9621))
- [DOCS] remove extraneous expectation docs ([#9623](https://github.com/great-expectations/great_expectations/pull/9623))
- [DOCS] Update and Edit Manage Data Contexts ([#9628](https://github.com/great-expectations/great_expectations/pull/9628))
- [DOCS] mdx Error Updates ([#9548](https://github.com/great-expectations/great_expectations/pull/9548))
- [DOCS] Revises the guidance under the 1.0 prerelease Manage Expectation topic ([#9639](https://github.com/great-expectations/great_expectations/pull/9639))
- [DOCS] Update and Edit Manage Credentials ([#9642](https://github.com/great-expectations/great_expectations/pull/9642))
- [DOCS] Move expectations gallery link inside navbar ([#9662](https://github.com/great-expectations/great_expectations/pull/9662))
- [DOCS] Adds 1.0 Validation Definitions guide ([#9663](https://github.com/great-expectations/great_expectations/pull/9663))
- [DOCS] Remove CE templates & examples ([#9672](https://github.com/great-expectations/great_expectations/pull/9672))
- [DOCS] GX Cloud Proof of Concept ([#9635](https://github.com/great-expectations/great_expectations/pull/9635))
- [DOCS] Adds guidance around Checkpoints in 1.0 ([#9675](https://github.com/great-expectations/great_expectations/pull/9675))
- [DOCS] Corrects broken import for prerequisites in v0.18 connect to Filesystem Data Assets page ([#9679](https://github.com/great-expectations/great_expectations/pull/9679))
- [DOCS] Update Core Expectation Docstrings w/ Inline Examples for Gallery ([#9603](https://github.com/great-expectations/great_expectations/pull/9603))
- [DOCS] Update and Revise Manage Data Docs ([#9699](https://github.com/great-expectations/great_expectations/pull/9699))
- [DOCS] Upgrade docusaurus 3.0 ([#9667](https://github.com/great-expectations/great_expectations/pull/9667))
- [DOCS] GX OSS Quickstart Updates ([#9726](https://github.com/great-expectations/great_expectations/pull/9726))
- [DOCS] Update `add_expectation_configuration` method in Create and edit Expectations ([#9728](https://github.com/great-expectations/great_expectations/pull/9728))
- [DOCS] Update Template Link in Create a Custom Batch Expectation ([#9731](https://github.com/great-expectations/great_expectations/pull/9731))
- [DOCS] Update GX Cloud Docs to Reflect UI Updates ([#9729](https://github.com/great-expectations/great_expectations/pull/9729))
- [DOCS] Make left navigation responsive ([#9652](https://github.com/great-expectations/great_expectations/pull/9652))
- [DOCS] Fix Overlay Bug on Desktop ([#9741](https://github.com/great-expectations/great_expectations/pull/9741))
- [DOCS] Update GX Cloud Documentation to Reflect New Data Asset Workflow ([#9694](https://github.com/great-expectations/great_expectations/pull/9694))
- [DOCS] Add Installation and Setup Guidance for Amazon S3 to Install Additional Dependencies ([#9719](https://github.com/great-expectations/great_expectations/pull/9719))
- [DOCS] Adds Changelog to the 1.0 ToC ([#9754](https://github.com/great-expectations/great_expectations/pull/9754))
- [DOCS] GX Cloud Content Adjustments ([#9746](https://github.com/great-expectations/great_expectations/pull/9746))
- [MAINTENANCE] Run marker tests on python 3.11 ([#9455](https://github.com/great-expectations/great_expectations/pull/9455))
- [MAINTENANCE] Customize coderabbit ([#9479](https://github.com/great-expectations/great_expectations/pull/9479))
- [MAINTENANCE] Remove change file dependency for running doc tests ([#9448](https://github.com/great-expectations/great_expectations/pull/9448))
- [MAINTENANCE] Ensure that `DataContextConfig` has a consistent shape when args are omitted ([#9469](https://github.com/great-expectations/great_expectations/pull/9469))
- [MAINTENANCE] Run docs tests on merge queue. ([#9496](https://github.com/great-expectations/great_expectations/pull/9496))
- [MAINTENANCE] Update KlDivergence to KLDivergence. ([#9501](https://github.com/great-expectations/great_expectations/pull/9501))
- [MAINTENANCE] Revert Add batch_configs to context schema ([#9511](https://github.com/great-expectations/great_expectations/pull/9511))
- [MAINTENANCE] Remove hashed column partitioner ([#9510](https://github.com/great-expectations/great_expectations/pull/9510))
- [MAINTENANCE] Remove `context.get_expectation_suite` in favor of factory method ([#9513](https://github.com/great-expectations/great_expectations/pull/9513))
- [MAINTENANCE] Remove `DataContext` dependency from `ExpectationSuite` ([#9512](https://github.com/great-expectations/great_expectations/pull/9512))
- [MAINTENANCE] Start refactoring codebase to use checkpoint factory CRUD ([#9507](https://github.com/great-expectations/great_expectations/pull/9507))
- [MAINTENANCE] Backfill test around validator::validate taking evaluation parameters ([#9516](https://github.com/great-expectations/great_expectations/pull/9516))
- [MAINTENANCE] Turn off publishing pact contracts for 1.0 API ([#9531](https://github.com/great-expectations/great_expectations/pull/9531))
- [MAINTENANCE] Rename `ge_cloud_id` to `id` ([#9529](https://github.com/great-expectations/great_expectations/pull/9529))
- [MAINTENANCE] Sample getting a file passing mdx check ([#9532](https://github.com/great-expectations/great_expectations/pull/9532))
- [MAINTENANCE] Remove experimental concurrency support ([#9519](https://github.com/great-expectations/great_expectations/pull/9519))
- [MAINTENANCE] Improve typing and comment ([#9534](https://github.com/great-expectations/great_expectations/pull/9534))
- [MAINTENANCE] `ruff` `0.2.2` ([#9538](https://github.com/great-expectations/great_expectations/pull/9538))
- [MAINTENANCE] Make Checkpoint's context dependency optional ([#9521](https://github.com/great-expectations/great_expectations/pull/9521))
- [MAINTENANCE] Update referential integrity test so DB is only created once - `develop` ([#9544](https://github.com/great-expectations/great_expectations/pull/9544))
- [MAINTENANCE] Remove fluent partitioner methods from DataAssets ([#9517](https://github.com/great-expectations/great_expectations/pull/9517))
- [MAINTENANCE] Backfill test around BatchConfig partitioners being used by validators ([#9547](https://github.com/great-expectations/great_expectations/pull/9547))
- [MAINTENANCE] Remove context from v1 Validator and add helper to project manager ([#9560](https://github.com/great-expectations/great_expectations/pull/9560))
- [MAINTENANCE] Remove manual validation around evaluation parameters in core expecta… ([#9537](https://github.com/great-expectations/great_expectations/pull/9537))
- [MAINTENANCE] Lower allowed max `C901` `mccabe` complexity score ([#9569](https://github.com/great-expectations/great_expectations/pull/9569))
- [MAINTENANCE] Prettier yaml formatting ([#9562](https://github.com/great-expectations/great_expectations/pull/9562))
- [MAINTENANCE] Rename ExpectationSuite.expectation_suite_name and ExpectationSuiteIdentifier.expectation_suite_name to name ([#9559](https://github.com/great-expectations/great_expectations/pull/9559))
- [MAINTENANCE] Ensure proper `ValidationConfig` serialization ([#9558](https://github.com/great-expectations/great_expectations/pull/9558))
- [MAINTENANCE] CDMs - Metrics as ENUM - `develop` ([#9573](https://github.com/great-expectations/great_expectations/pull/9573))
- [MAINTENANCE] Ensure proper ID support within `ValidationConfigStore` ([#9574](https://github.com/great-expectations/great_expectations/pull/9574))
- [MAINTENANCE] Replace `black` formatter with `ruff format` ([#9536](https://github.com/great-expectations/great_expectations/pull/9536))
- [MAINTENANCE] Formatting, lint ignores `.git-blame-ignore-revs` ([#9578](https://github.com/great-expectations/great_expectations/pull/9578))
- [MAINTENANCE] Delete ExpectationSuite attribute data_asset_type ([#9591](https://github.com/great-expectations/great_expectations/pull/9591))
- [MAINTENANCE] Ban direct `unittest.mock.Mock/MagicMock` usage ([#9586](https://github.com/great-expectations/great_expectations/pull/9586))
- [MAINTENANCE] Temporarily disable public_api check during V1 development ([#9587](https://github.com/great-expectations/great_expectations/pull/9587))
- [MAINTENANCE] Fix cloud e2e test ([#9601](https://github.com/great-expectations/great_expectations/pull/9601))
- [MAINTENANCE] Delete extraneous validation actions ([#9598](https://github.com/great-expectations/great_expectations/pull/9598))
- [MAINTENANCE] Make Validation definitions immutable ([#9606](https://github.com/great-expectations/great_expectations/pull/9606))
- [MAINTENANCE] Refactor `ColumnDescriptiveMetricsMetricRetriever` to parent class (develop) ([#9614](https://github.com/great-expectations/great_expectations/pull/9614))
- [MAINTENANCE] Remove context dependency from Validation Actions ([#9605](https://github.com/great-expectations/great_expectations/pull/9605))
- [MAINTENANCE] Add `asset` and `datasource` properties to `ValidationDefinition` ([#9619](https://github.com/great-expectations/great_expectations/pull/9619))
- [MAINTENANCE] Refactor `ValidationAction` to use Pydantic ([#9617](https://github.com/great-expectations/great_expectations/pull/9617))
- [MAINTENANCE] Rename legacy batch definitions ([#9629](https://github.com/great-expectations/great_expectations/pull/9629))
- [MAINTENANCE] Add invoke docs --clear command. ([#9636](https://github.com/great-expectations/great_expectations/pull/9636))
- [MAINTENANCE] Remove dataset ([#9608](https://github.com/great-expectations/great_expectations/pull/9608))
- [MAINTENANCE] Reduce cyclo complexity in some functions. ([#9634](https://github.com/great-expectations/great_expectations/pull/9634))
- [MAINTENANCE] Delete great_expectations/data_asset/ (except for util.py) ([#9637](https://github.com/great-expectations/great_expectations/pull/9637))
- [MAINTENANCE] Reduce max-complexity from `10->8` ([#9622](https://github.com/great-expectations/great_expectations/pull/9622))
- [MAINTENANCE] Change line-length to 100 ([#9584](https://github.com/great-expectations/great_expectations/pull/9584))
- [MAINTENANCE] TableMetrics - BatchInspector updates (develop) ([#9646](https://github.com/great-expectations/great_expectations/pull/9646))
- [MAINTENANCE] `Checkpoint.run()` ([#9647](https://github.com/great-expectations/great_expectations/pull/9647))
- [MAINTENANCE] Rename batch_definition_options to batch_parameters ([#9653](https://github.com/great-expectations/great_expectations/pull/9653))
- [MAINTENANCE] Rename BatchConfig to BatchDefinition ([#9645](https://github.com/great-expectations/great_expectations/pull/9645))
- [MAINTENANCE] Rename ValidationConfig to ValidationDefinition ([#9654](https://github.com/great-expectations/great_expectations/pull/9654))
- [MAINTENANCE] Add organization ID to analytics payloads ([#9643](https://github.com/great-expectations/great_expectations/pull/9643))
- [MAINTENANCE] Add validation result URL support within V1 Checkpoint ([#9656](https://github.com/great-expectations/great_expectations/pull/9656))
- [MAINTENANCE] V1 Checkpoint Store ([#9659](https://github.com/great-expectations/great_expectations/pull/9659))
- [MAINTENANCE] Rename context.validations to context.validation_definitions ([#9660](https://github.com/great-expectations/great_expectations/pull/9660))
- [MAINTENANCE] Use Codecov for test coverage reports ([#9664](https://github.com/great-expectations/great_expectations/pull/9664))
- [MAINTENANCE] Bump webpack-dev-middleware from 5.3.3 to 5.3.4 in /docs/docusaurus ([#9655](https://github.com/great-expectations/great_expectations/pull/9655))
- [MAINTENANCE] add `.git-blame-ignore-revs` for formatting and noqa additions ([#9668](https://github.com/great-expectations/great_expectations/pull/9668))
- [MAINTENANCE] Decouple checkpoint factory from v0.18 checkpoint ([#9665](https://github.com/great-expectations/great_expectations/pull/9665))
- [MAINTENANCE] Bump express from 4.18.2 to 4.19.2 in /docs/docusaurus ([#9666](https://github.com/great-expectations/great_expectations/pull/9666))
- [MAINTENANCE] Cloud tests - don't error on `GxInvalidDatasourceWarning` - `package_resources` deprecation ([#9673](https://github.com/great-expectations/great_expectations/pull/9673))
- [MAINTENANCE] Wire up V1 Checkpoint with factory ([#9670](https://github.com/great-expectations/great_expectations/pull/9670))
- [MAINTENANCE] Bump follow-redirects from 1.15.4 to 1.15.6 in /docs/docusaurus ([#9631](https://github.com/great-expectations/great_expectations/pull/9631))
- [MAINTENANCE] Add `suite_name` to `ExpectationSuiteValidationResult` ([#9677](https://github.com/great-expectations/great_expectations/pull/9677))
- [MAINTENANCE] Lint Docs ([#8936](https://github.com/great-expectations/great_expectations/pull/8936))
- [MAINTENANCE] `mypy 1.9` + begin wider tests type-checking ([#9678](https://github.com/great-expectations/great_expectations/pull/9678))
- [MAINTENANCE] Typing improvements in `test_metadatasource` ([#9681](https://github.com/great-expectations/great_expectations/pull/9681))
- [MAINTENANCE] Clean up `ValidationAction` API ([#9680](https://github.com/great-expectations/great_expectations/pull/9680))
- [MAINTENANCE] enable TRYceratops linting rules ([#9684](https://github.com/great-expectations/great_expectations/pull/9684))
- [MAINTENANCE] Update git-blame-ignore-revs file to ignore changes in #9684 ([#9688](https://github.com/great-expectations/great_expectations/pull/9688))
- [MAINTENANCE] Add after_n_builds to codecov default rules ([#9691](https://github.com/great-expectations/great_expectations/pull/9691))
- [MAINTENANCE] Cleanup Unused Comments ([#9697](https://github.com/great-expectations/great_expectations/pull/9697))
- [MAINTENANCE] Refactor FilePathDataConnector ([#9706](https://github.com/great-expectations/great_expectations/pull/9706))
- [MAINTENANCE] Provide default empty action list in V1 Checkpoint ([#9709](https://github.com/great-expectations/great_expectations/pull/9709))
- [MAINTENANCE] Migrate misc actions to V1 pattern ([#9689](https://github.com/great-expectations/great_expectations/pull/9689))
- [MAINTENANCE] Migrate `OpsgenieNotificationAction` ([#9716](https://github.com/great-expectations/great_expectations/pull/9716))
- [MAINTENANCE] Refactor `EmailAction` for V1 ([#9725](https://github.com/great-expectations/great_expectations/pull/9725))
- [MAINTENANCE] Bump katex from 0.16.9 to 0.16.10 in /docs/docusaurus ([#9722](https://github.com/great-expectations/great_expectations/pull/9722))
- [MAINTENANCE] Improve mechanism to share results between checkpoint actions ([#9730](https://github.com/great-expectations/great_expectations/pull/9730))
- [MAINTENANCE] Rename BatchRequestOptions to BatchParameters ([#9736](https://github.com/great-expectations/great_expectations/pull/9736))
- [MAINTENANCE] pre-commit autoupdate (ruff 0.3.5) ([#9685](https://github.com/great-expectations/great_expectations/pull/9685))
- [MAINTENANCE] Make actions sortable ([#9733](https://github.com/great-expectations/great_expectations/pull/9733))
- [MAINTENANCE] Pin `snowflake-sqlalchemy` due to `1.5.2` runtime bug ([#9744](https://github.com/great-expectations/great_expectations/pull/9744))
- [MAINTENANCE] ruff `0.3.7` ([#9747](https://github.com/great-expectations/great_expectations/pull/9747))
- [MAINTENANCE] Remove `docs_rtd` ([#9737](https://github.com/great-expectations/great_expectations/pull/9737))
- [MAINTENANCE] Migrate `SlackNotificationAction` to V1 pattern ([#9734](https://github.com/great-expectations/great_expectations/pull/9734))
- [MAINTENANCE] Rename Evaluation Parameter to Suite Parameter ([#9743](https://github.com/great-expectations/great_expectations/pull/9743))
- [MAINTENANCE] Migrate `MicrosoftTeamsNotificationAction` to V1 ([#9745](https://github.com/great-expectations/great_expectations/pull/9745))
- [MAINTENANCE] Enable `SIM101` + `SIM114` ([#9758](https://github.com/great-expectations/great_expectations/pull/9758))
- [MAINTENANCE] Type checking `test_metadataource` ([#9759](https://github.com/great-expectations/great_expectations/pull/9759))
- [MAINTENANCE] Enable `run_id` overrides for `Checkpoint` and `ValidationDefinition` ([#9760](https://github.com/great-expectations/great_expectations/pull/9760))

### 1.0.0a1

- [FEATURE] EVR/SVR describe ([#9277](https://github.com/great-expectations/great_expectations/pull/9277))
- [FEATURE] Update how-to docs to use describe() ([#9280](https://github.com/great-expectations/great_expectations/pull/9280))
- [FEATURE] Handle distinct_id inside analytics config ([#9266](https://github.com/great-expectations/great_expectations/pull/9266))
- [FEATURE] Script to move doc code snippets out of tests and into docs ([#9297](https://github.com/great-expectations/great_expectations/pull/9297))
- [FEATURE] Example run for the SnippetMover (10) ([#9337](https://github.com/great-expectations/great_expectations/pull/9337))
- [FEATURE] ExpectationSuite accepts Expectations on init ([#9364](https://github.com/great-expectations/great_expectations/pull/9364))
- [FEATURE] Use SuiteFactory API in `tests/actions` ([#9353](https://github.com/great-expectations/great_expectations/pull/9353))
- [FEATURE] `UnexpectedRowsExpectation` ([#9377](https://github.com/great-expectations/great_expectations/pull/9377))
- [FEATURE] `unexpected_rows_query.table` metric ([#9412](https://github.com/great-expectations/great_expectations/pull/9412))
- [FEATURE] Allow using EmailAction with email servers that require no authentication (fixes #9379) ([#9388](https://github.com/great-expectations/great_expectations/pull/9388)) (thanks @MarcelBeining)
- [FEATURE] Add Partitioner field to BatchConfig ([#9432](https://github.com/great-expectations/great_expectations/pull/9432))
- [FEATURE] `TableAsset.test_connection()` should fail if table is not queryable. (#9198) ([#9475](https://github.com/great-expectations/great_expectations/pull/9475))
- [BUGFIX] Remove a stray git pull ([#9229](https://github.com/great-expectations/great_expectations/pull/9229))
- [BUGFIX] Fix docs build for 0.17 as a prior version ([#9234](https://github.com/great-expectations/great_expectations/pull/9234))
- [BUGFIX] Remove unneeded and problematic git wrangling in docs build ([#9288](https://github.com/great-expectations/great_expectations/pull/9288))
- [BUGFIX] Close quotes in snippet references ([#9309](https://github.com/great-expectations/great_expectations/pull/9309))
- [BUGFIX] Revert relative links ([#9343](https://github.com/great-expectations/great_expectations/pull/9343))
- [BUGFIX] remove connection log for v1 ([#9135](https://github.com/great-expectations/great_expectations/pull/9135))
- [BUGFIX] Move script_example from 0.17.23 -> 0.17 ([#9403](https://github.com/great-expectations/great_expectations/pull/9403))
- [BUGFIX] Fix algolia facetFilters ([#9415](https://github.com/great-expectations/great_expectations/pull/9415))
- [BUGFIX] Find/replace localhost with path relative to host ([#9429](https://github.com/great-expectations/great_expectations/pull/9429))
- [BUGFIX] Fix sphinx linx ([#9434](https://github.com/great-expectations/great_expectations/pull/9434))
- [BUGFIX] Add 0.17 to docs links for 0.17 ([#9439](https://github.com/great-expectations/great_expectations/pull/9439))
- [BUGFIX] Get docs tests passing ([#9449](https://github.com/great-expectations/great_expectations/pull/9449))
- [BUGFIX] Patch Pandas/SQLAlchemy Snowflake issue ([#9459](https://github.com/great-expectations/great_expectations/pull/9459))
- [BUGFIX] Fix pandas dependency issues for Snowflake and Clickhouse ([#9465](https://github.com/great-expectations/great_expectations/pull/9465))
- [DOCS] Expectation Management Script ([#9213](https://github.com/great-expectations/great_expectations/pull/9213))
- [DOCS] Update docs versioning readme ([#9230](https://github.com/great-expectations/great_expectations/pull/9230))
- [DOCS] Update Connect to Generic SQL Database Data Assets to Include Creating an Asset ([#9240](https://github.com/great-expectations/great_expectations/pull/9240))
- [DOCS] Update README.md for broken links ([#9184](https://github.com/great-expectations/great_expectations/pull/9184)) (thanks @cnabro)
- [DOCS] Remove References to GX_CLOUD_SNOWFLAKE_PASSWORD ([#9251](https://github.com/great-expectations/great_expectations/pull/9251))
- [DOCS] Add CTA announcement bar for public preview to docs ([#9274](https://github.com/great-expectations/great_expectations/pull/9274))
- [DOCS] Update GX Cloud Documentation to Reflect Move to Org Agent ([#9204](https://github.com/great-expectations/great_expectations/pull/9204))
- [DOCS] Reduce Button Text ([#9313](https://github.com/great-expectations/great_expectations/pull/9313))
- [DOCS] Corrects invalid redirects ([#9321](https://github.com/great-expectations/great_expectations/pull/9321))
- [DOCS] Hot fix for docs cta bar ([#9320](https://github.com/great-expectations/great_expectations/pull/9320))
- [DOCS] Add Redirect for GX Cloud Documentation ([#9333](https://github.com/great-expectations/great_expectations/pull/9333))
- [DOCS] update or remove outdated integrations, links; components ([#9307](https://github.com/great-expectations/great_expectations/pull/9307))
- [DOCS] Adds redirect rule for an outdated link ([#9342](https://github.com/great-expectations/great_expectations/pull/9342))
- [DOCS] updates relative href to absolute ([#9344](https://github.com/great-expectations/great_expectations/pull/9344))
- [DOCS] adds additional bulk redirects for `learn` pages ([#9350](https://github.com/great-expectations/great_expectations/pull/9350))
- [DOCS] Remove outdated integrations and links from versioned docs ([#9355](https://github.com/great-expectations/great_expectations/pull/9355))
- [DOCS] adds redirect for outdated glossary path ([#9358](https://github.com/great-expectations/great_expectations/pull/9358))
- [DOCS] DOC-648: Update About GX Cloud to reflect GX Agent running in deployment environment ([#9327](https://github.com/great-expectations/great_expectations/pull/9327))
- [DOCS] Typography updates ([#9236](https://github.com/great-expectations/great_expectations/pull/9236))
- [DOCS] corrects mislabeled element in top navbar ([#9369](https://github.com/great-expectations/great_expectations/pull/9369))
- [DOCS] Quick fix: styles for left navigation ([#9372](https://github.com/great-expectations/great_expectations/pull/9372))
- [DOCS] Remove Missingness Assistant Content from GX Cloud Documentation ([#9315](https://github.com/great-expectations/great_expectations/pull/9315))
- [DOCS] Updating Tabs' Styles ([#9287](https://github.com/great-expectations/great_expectations/pull/9287))
- [DOCS] Consolidate GX Cloud and GX OSS Support Topics ([#9367](https://github.com/great-expectations/great_expectations/pull/9367))
- [DOCS] Cut v 0.18 docs ([#9395](https://github.com/great-expectations/great_expectations/pull/9395))
- [DOCS] Customization of Header ([#9243](https://github.com/great-expectations/great_expectations/pull/9243))
- [DOCS] Add resources dropdown to navbar ([#9349](https://github.com/great-expectations/great_expectations/pull/9349))
- [DOCS] remove explicit facet ([#9416](https://github.com/great-expectations/great_expectations/pull/9416))
- [DOCS] update docs readme ([#9409](https://github.com/great-expectations/great_expectations/pull/9409))
- [DOCS] Convert reference/api to relative links for 0.18.8 ([#9442](https://github.com/great-expectations/great_expectations/pull/9442))
- [DOCS] Remove version prefix from 0.18 docs ([#9443](https://github.com/great-expectations/great_expectations/pull/9443))
- [DOCS] Adds Expectation API guides for GX Core prerelease ([#9424](https://github.com/great-expectations/great_expectations/pull/9424))
- [DOCS] Fix links style in tables ([#9427](https://github.com/great-expectations/great_expectations/pull/9427))
- [DOCS] Update Broken Icon Link ([#9451](https://github.com/great-expectations/great_expectations/pull/9451))
- [DOCS] Add Content for Connecting to a PostgreSQL Data Asset ([#9356](https://github.com/great-expectations/great_expectations/pull/9356))
- [DOCS] Update alerts ([#9407](https://github.com/great-expectations/great_expectations/pull/9407))
- [DOCS] Update overview pages style ([#9418](https://github.com/great-expectations/great_expectations/pull/9418))
- [DOCS] Add Result Format Content to the GX Cloud Docs ([#9461](https://github.com/great-expectations/great_expectations/pull/9461))
- [MAINTENANCE] convert docs build scripts from bash to python ([#9222](https://github.com/great-expectations/great_expectations/pull/9222))
- [MAINTENANCE] Add core Expectations to Public API ([#9232](https://github.com/great-expectations/great_expectations/pull/9232))
- [MAINTENANCE] Remove broken util function ([#9238](https://github.com/great-expectations/great_expectations/pull/9238))
- [MAINTENANCE] Update Expectation Gallery for 1.0 ([#9239](https://github.com/great-expectations/great_expectations/pull/9239))
- [MAINTENANCE] Another docs build fix ([#9235](https://github.com/great-expectations/great_expectations/pull/9235))
- [MAINTENANCE] Update code to use SuiteFactory pt 1 ([#9242](https://github.com/great-expectations/great_expectations/pull/9242))
- [MAINTENANCE] Expectation Gallery only builds from success test cases ([#9247](https://github.com/great-expectations/great_expectations/pull/9247))
- [MAINTENANCE] move prepare_prior_versions to allow one version at a time ([#9246](https://github.com/great-expectations/great_expectations/pull/9246))
- [MAINTENANCE] Sequence diagrams around the docs build ([#9248](https://github.com/great-expectations/great_expectations/pull/9248))
- [MAINTENANCE] BUGFIX Add template_dict to domain_keys: fixes #8998 ([#9249](https://github.com/great-expectations/great_expectations/pull/9249)) (thanks @Chr96er)
- [MAINTENANCE] Bump jinja2 from 2.11.3 to 3.1.3 in /docs_rtd ([#9228](https://github.com/great-expectations/great_expectations/pull/9228))
- [MAINTENANCE] Add upper bound for numpy ([#9256](https://github.com/great-expectations/great_expectations/pull/9256))
- [MAINTENANCE] Add typevar around add_expectation ([#9254](https://github.com/great-expectations/great_expectations/pull/9254))
- [MAINTENANCE] Run docs build file processing during versionsing, rather than build ([#9258](https://github.com/great-expectations/great_expectations/pull/9258))
- [MAINTENANCE] Switch over docs build flow and update readme ([#9261](https://github.com/great-expectations/great_expectations/pull/9261))
- [MAINTENANCE] `ruff` `0.1.14` ([#9271](https://github.com/great-expectations/great_expectations/pull/9271))
- [MAINTENANCE] Enable ruff preview rules ([#9273](https://github.com/great-expectations/great_expectations/pull/9273))
- [MAINTENANCE] Move Markdown rendering logic to top-level notes field in Expectation and ExpectationSuite ([#9270](https://github.com/great-expectations/great_expectations/pull/9270))
- [MAINTENANCE] Numpy 2 compatibility (initial PR) ([#9272](https://github.com/great-expectations/great_expectations/pull/9272))
- [MAINTENANCE] Migrate remaining Expectations to be V1-compatible for Expectation Gallery ([#9275](https://github.com/great-expectations/great_expectations/pull/9275))
- [MAINTENANCE] Add data context group for posthog ([#9284](https://github.com/great-expectations/great_expectations/pull/9284))
- [MAINTENANCE] allow absolute file links ([#9282](https://github.com/great-expectations/great_expectations/pull/9282))
- [MAINTENANCE] fix absolute md links ([#9281](https://github.com/great-expectations/great_expectations/pull/9281))
- [MAINTENANCE] replace absolute hrefs in docs ([#9279](https://github.com/great-expectations/great_expectations/pull/9279))
- [MAINTENANCE] Add instrumentation for V1 Expectation management APIs ([#9241](https://github.com/great-expectations/great_expectations/pull/9241))
- [MAINTENANCE] Revert 1.0 doc changes until we separate out 0.18 and 1.0 doc builds ([#9289](https://github.com/great-expectations/great_expectations/pull/9289))
- [MAINTENANCE] Block gallery build ([#9290](https://github.com/great-expectations/great_expectations/pull/9290))
- [MAINTENANCE] Remove deprecated fixture mark usage ([#9298](https://github.com/great-expectations/great_expectations/pull/9298))
- [MAINTENANCE] Add VersionedLink component ([#9300](https://github.com/great-expectations/great_expectations/pull/9300))
- [MAINTENANCE] Remove stray logging ([#9302](https://github.com/great-expectations/great_expectations/pull/9302))
- [MAINTENANCE] Remove unused mdx file that had an absolute link. ([#9299](https://github.com/great-expectations/great_expectations/pull/9299))
- [MAINTENANCE] Remove salt from V1 analytics anonymizer ([#9306](https://github.com/great-expectations/great_expectations/pull/9306))
- [MAINTENANCE] Use verson safe links ([#9301](https://github.com/great-expectations/great_expectations/pull/9301))
- [MAINTENANCE] Move react imports to be relative ([#9294](https://github.com/great-expectations/great_expectations/pull/9294))
- [MAINTENANCE] Check for snippets in docs ([#9310](https://github.com/great-expectations/great_expectations/pull/9310))
- [MAINTENANCE] Fix python max version ([#9264](https://github.com/great-expectations/great_expectations/pull/9264))
- [MAINTENANCE] Add Cloud user id to analytics calls ([#9260](https://github.com/great-expectations/great_expectations/pull/9260))
- [MAINTENANCE] remove data asset field for exp suite ([#9318](https://github.com/great-expectations/great_expectations/pull/9318))
- [MAINTENANCE] Add redirect for old docs ([#9319](https://github.com/great-expectations/great_expectations/pull/9319))
- [MAINTENANCE] Move redirect to top and add force flag ([#9322](https://github.com/great-expectations/great_expectations/pull/9322))
- [MAINTENANCE] Clean docs before build ([#9323](https://github.com/great-expectations/great_expectations/pull/9323))
- [MAINTENANCE] Add renderer to ignore list for public api ([#9335](https://github.com/great-expectations/great_expectations/pull/9335))
- [MAINTENANCE] version control 0 17 ([#9326](https://github.com/great-expectations/great_expectations/pull/9326))
- [MAINTENANCE] Convert jsx imports to be relative ([#9332](https://github.com/great-expectations/great_expectations/pull/9332))
- [MAINTENANCE] Relative mdx imports ([#9331](https://github.com/great-expectations/great_expectations/pull/9331))
- [MAINTENANCE] Stop using relative path to docs from 0.17 docs ([#9338](https://github.com/great-expectations/great_expectations/pull/9338))
- [MAINTENANCE] Remove unused files ([#9347](https://github.com/great-expectations/great_expectations/pull/9347))
- [MAINTENANCE] Delete tests for legacy usage stats platform ([#9357](https://github.com/great-expectations/great_expectations/pull/9357))
- [MAINTENANCE] Only use @site/src for CardLink and CardLinkGrid ([#9345](https://github.com/great-expectations/great_expectations/pull/9345))
- [MAINTENANCE] Add `description` to `Expectation` to enable simpler renderered content ([#9308](https://github.com/great-expectations/great_expectations/pull/9308))
- [MAINTENANCE] Use consistent snakecase when referencing `ExpectColumnPairValuesAToBeGreaterThanB` ([#9360](https://github.com/great-expectations/great_expectations/pull/9360))
- [MAINTENANCE] Update public api report to show both over- and under- … ([#9348](https://github.com/great-expectations/great_expectations/pull/9348))
- [MAINTENANCE] Rename expectation to match 0.18.x version ([#9362](https://github.com/great-expectations/great_expectations/pull/9362))
- [MAINTENANCE] Fix 2 image links ([#9352](https://github.com/great-expectations/great_expectations/pull/9352))
- [MAINTENANCE] Update LinkCard to wrap VersionedLink ([#9346](https://github.com/great-expectations/great_expectations/pull/9346))
- [MAINTENANCE] Fix /docs/ references in 0.17 ([#9351](https://github.com/great-expectations/great_expectations/pull/9351))
- [MAINTENANCE] Convert 0.17 to use relative imports ([#9354](https://github.com/great-expectations/great_expectations/pull/9354))
- [MAINTENANCE] Use VersionedLink instead of <a /> where appropriate in 0.17 ([#9339](https://github.com/great-expectations/great_expectations/pull/9339))
- [MAINTENANCE] Merge changelog/release updates from v0.18 into `develop` ([#9376](https://github.com/great-expectations/great_expectations/pull/9376))
- [MAINTENANCE] Update snippet script to check versioned_docs ([#9383](https://github.com/great-expectations/great_expectations/pull/9383))
- [MAINTENANCE] update pact test for datasources ([#9380](https://github.com/great-expectations/great_expectations/pull/9380))
- [MAINTENANCE] Log all duplicate snippets at the same time ([#9386](https://github.com/great-expectations/great_expectations/pull/9386))
- [MAINTENANCE] Simplify create_version task ([#9384](https://github.com/great-expectations/great_expectations/pull/9384))
- [MAINTENANCE] Move snippets to snippet directory ([#9385](https://github.com/great-expectations/great_expectations/pull/9385))
- [MAINTENANCE] Enable `ruff` `numpy` linting rules ([#9390](https://github.com/great-expectations/great_expectations/pull/9390))
- [MAINTENANCE] Rename and move V17 snippets to legacy docs dir ([#9374](https://github.com/great-expectations/great_expectations/pull/9374))
- [MAINTENANCE] Copy over snippet that was defined in docs/ but referen… ([#9391](https://github.com/great-expectations/great_expectations/pull/9391))
- [MAINTENANCE] Remove legacy usage statistics ([#9398](https://github.com/great-expectations/great_expectations/pull/9398))
- [MAINTENANCE] Set retry to 0 on CloudDataStore ([#9295](https://github.com/great-expectations/great_expectations/pull/9295))
- [MAINTENANCE] namespace snippets ([#9399](https://github.com/great-expectations/great_expectations/pull/9399))
- [MAINTENANCE] Update versions.json and the docusaurus build to reflect 0.17 ([#9393](https://github.com/great-expectations/great_expectations/pull/9393))
- [MAINTENANCE] Update docs create version script to omit patch ([#9394](https://github.com/great-expectations/great_expectations/pull/9394))
- [MAINTENANCE] Only look for snippets in docs directories ([#9392](https://github.com/great-expectations/great_expectations/pull/9392))
- [MAINTENANCE] block contrib pipeline from deploying on develop. ([#9402](https://github.com/great-expectations/great_expectations/pull/9402))
- [MAINTENANCE] ExpectationSuite.name is source of truth ([#9396](https://github.com/great-expectations/great_expectations/pull/9396))
- [MAINTENANCE] Support Markdown formatting within Expectation description rendering ([#9375](https://github.com/great-expectations/great_expectations/pull/9375))
- [MAINTENANCE] Use `{batch}` instead of `{active_batch}` in SQL-based Expectation queries ([#9411](https://github.com/great-expectations/great_expectations/pull/9411))
- [MAINTENANCE] Remove more refs to usage statistics ([#9401](https://github.com/great-expectations/great_expectations/pull/9401))
- [MAINTENANCE] docs build: throw on broken markdown link ([#9404](https://github.com/great-expectations/great_expectations/pull/9404))
- [MAINTENANCE] Rename Splitter to Partitioner ([#9408](https://github.com/great-expectations/great_expectations/pull/9408))
- [MAINTENANCE] Remove old file-processing code no longer needed for docs build ([#9410](https://github.com/great-expectations/great_expectations/pull/9410))
- [MAINTENANCE] Remove unused docs_pending directory ([#9414](https://github.com/great-expectations/great_expectations/pull/9414))
- [MAINTENANCE] Clean up Checkpoint run API ([#9433](https://github.com/great-expectations/great_expectations/pull/9433))
- [MAINTENANCE] Remove more params from Checkpoint API ([#9435](https://github.com/great-expectations/great_expectations/pull/9435))
- [MAINTENANCE] Remove `context.run_checkpoint` ([#9438](https://github.com/great-expectations/great_expectations/pull/9438))
- [MAINTENANCE] Re-add v1 doc snippet tests (revert 9289) ([#9437](https://github.com/great-expectations/great_expectations/pull/9437))
- [MAINTENANCE] Start deleting uses of `test_yaml_config` ([#9445](https://github.com/great-expectations/great_expectations/pull/9445))
- [MAINTENANCE] Update CI trigger to recognize pre-release candidates ([#9450](https://github.com/great-expectations/great_expectations/pull/9450))
- [MAINTENANCE] Update CI trigger regex again ([#9452](https://github.com/great-expectations/great_expectations/pull/9452))
- [MAINTENANCE] Add Pandas/SQLAlchemy warning to ignores list to unblock V1 prerelease ([#9453](https://github.com/great-expectations/great_expectations/pull/9453))
- [MAINTENANCE] Only do docs checks and build on develop. ([#9454](https://github.com/great-expectations/great_expectations/pull/9454))
- [MAINTENANCE] Ignore pandas `DeprecationWarning` for legacy `PandasDataset` ([#9472](https://github.com/great-expectations/great_expectations/pull/9472))

### Older Changelist

Older changelist can be found at [docs/docusaurus/versioned_docs/version-0.18/oss/changelog.md](https://github.com/great-expectations/great_expectations/blob/develop/docs/docusaurus/versioned_docs/version-0.18/oss/changelog.md)
