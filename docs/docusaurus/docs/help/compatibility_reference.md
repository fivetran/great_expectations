---
title: Compatibility reference
hide_table_of_contents: true
---

The following table defines integrations and tools supported by GX Cloud and GX Core.


| Service | GX Cloud | GX Core | Notes |
|---|---|---|---|
| Data sources | AlloyDB<br/>Amazon Aurora PostgreSQL<br/>Amazon S3<br/>Azure Blob Storage<br/>BigQuery<br/>Citus<br/>Databricks SQL<br/>Google Cloud Storage<br/>Neon<br/>Pandas<br/>PostgreSQL<br/>Redshift<br/>Snowflake<br/>Spark | AlloyDB<br/>Amazon Aurora PostgreSQL<br/>Amazon S3<br/>Azure Blob Storage<br/>BigQuery<br/>Citus<br/>Databricks SQL<br/>Google Cloud Storage<br/>Neon<br/>Pandas<br/>PostgreSQL<br/>Redshift<br/>Snowflake<br/>Spark<br/>SQLite | We've seen GX Core work with the following data sources in the past, but we don't guarantee ongoing compatibility at this time: Athena, AWS Glue, Clickhouse, Databricks (Spark), Dremio, EMR Spark, Microsoft Fabric, MSSQL, MySQL, Teradata, Trino, and Vertica. |
| Notifications | Email | Email<br/>Microsoft Teams<br/>Slack<br/>Custom | We support the general workflow for creating custom notifications with Actions but cannot help troubleshoot the domain-specific logic within a custom Action. |
| Credential stores | Environment variables | Environment variables<br/>`config_variables.yml` |  |
| Orchestrators | Airflow version 2.9.0+ | Airflow version 2.9.0+ | Although only Airflow is supported, GX Cloud and GX Core should work with any orchestrator that executes Python code. |
| Operating systems | Mac/Linux | Mac/Linux | Though GX does not currently support Windows, we've seen users successfully deploy on Windows. |
| Python versions | 3.9 to 3.12 | 3.9 to 3.12 | GX typically follows the [Python release cycle](https://devguide.python.org/versions/). |
| GX library versions | ≥1.0 | ≥1.0 | Support for 0.18 was deprecated October 25, 2024 and reached end of life on October 1, 2025. |
| Web browsers | [Google Chrome](https://www.google.com/chrome/)<br/>[Mozilla Firefox](https://www.mozilla.org/en-US/firefox/)<br/>[Apple Safari](https://www.apple.com/safari/)<br/>[Microsoft Edge](https://www.microsoft.com/en-us/edge?ep=82&form=MA13KI&es=24) | [Google Chrome](https://www.google.com/chrome/)<br/>[Mozilla Firefox](https://www.mozilla.org/en-US/firefox/)<br/>[Apple Safari](https://www.apple.com/safari/)<br/>[Microsoft Edge](https://www.microsoft.com/en-us/edge?ep=82&form=MA13KI&es=24) | Only the latest version of each browser is supported. |



