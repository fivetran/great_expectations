---
title: 'GX Cloud overview'
id: gx_cloud_overview
description: Explore GX Cloud integration, concepts, workflows, and architecture.
toc_min_heading_level: 2
toc_max_heading_level: 2
---

GX Cloud is a fully managed SaaS platform that simplifies data quality management and monitoring. With GX Cloud, you and your team can work collaboratively to define and maintain shared understanding of your data.

## GX Cloud in your environment

You can integrate GX Cloud at any point in your data pipeline to manage and monitor data quality. Common integration points include but are not limited to the following:

- **[Ingestion](/reference/learn/gx_in_your_data_pipeline/ingestion.md):** validate raw data before writing it to your data warehouse so that you can quarantine bad records and identify bugs in your source system.

- **[Transformation](reference/learn/gx_in_your_data_pipeline/transformation.md):** check the results of transformations in your warehouse and condition pipeline steps based on validation success or failure.

- **[Delivery](reference/learn/gx_in_your_data_pipeline/delivery.md):** ensure unexpected patterns reveal business insights rather than data quality issues.

Here’s an example of where these three common integration points fit in a generic data pipeline:

![Raw data from Square, Mailchimp, and Salesforce are validated by GX Cloud before being written to a Snowflake data warehouse. Transformations are validated within the Snowflake data pipeline. Finalized data is validated before being served by BI tools such as Tableau, Power BI, and Looker.](./overview_images/gx_cloud_pipeline.png)

You can also integrate GX Cloud with version control systems and with data at rest. Common workflows that validate data outside the data pipeline include:

- **CI/CD:** test changes to your transformation code before merging it to production so that code changes don’t have negative downstream impacts on data.

- **Exploration:** enable your stakeholders to create and run ad hoc tests to get a better understanding of the data they’re consuming.

For a full list of data sources and other tools supported by GX Cloud, visit the [compatibility reference](/help/compatibility_reference.md).

## GX Cloud concepts

The key GX Cloud concepts described below provide a data validation vocabulary that represents your data, your data validation criteria, and the results of data validation. Within GX Cloud, these concepts are applied to define components and implement data validation workflows.

|  |  |
| :--: | :--- |
| <img src="/img/database_icon.svg" alt="Data Source" width="84px"/> | **Data Source**<br/>A Data Source is the GX representation of a database or data store. |
| <img src="/img/table_icon.svg" alt="Data Asset" width="84px"/> | **Data Asset**<br/>A Data Asset is a collection of records within a Data Source.  |
| <img src="/img/magnify_data_icon.svg" alt="Expectation" width="96px"/> | **Expectation**<br/>An Expectation is a declarative, verifiable assumption about your data. Expectations serve as unit tests for your data. |
| <img src="/img/gear_icon.svg" alt="Validation" width="84px"/> | **Validation**<br/>A Validation runs selected Expectations against a Data Asset to validate the data defined by that Data Asset. |
| <img src="/img/checklist_icon.svg" alt="Validation Result" width="84px"/> | **Validation Result**<br/>A Validation Result captures the outcome of a Validation and related metadata that describes passing and failing data. |

## GX Cloud workflow

GX Cloud data validation workflows are created using GX Cloud components, entities that represent GX Cloud data validation concepts.

### Standard data validation workflow

A GX Cloud data validation workflow can be implemented using the following steps:

![Standard GX Cloud workflow](./overview_images/gx_cloud_workflow.png)

1. Connect to your data.
2. Create a Data Asset.
3. Define Expectations.
4. Validate your data.
5. Review and share your Validation Results with your business.


### Additional workflow features
There are a variety of GX Cloud features that support additional enhancements to your GX Cloud data validation workflow.

![GX Cloud workflow enhanced with product features](./overview_images/gx_cloud_workflow_enhanced.png)

* **GX Cloud user management.** GX Cloud functions as a shared portal to manage and monitor your business's data quality. Users can be invited to your GX Cloud organization and assigned a role that governs their ability to view and edit components and workflows in GX Cloud. Enterprise organizations can use workspaces for more control over what users can access and do. See [Manage access](/cloud/access/manage_access.md) for more details.

* **Data Asset profiling.** GX Cloud introspects your data schema by default on Data Asset creation, and also offers one-click fetching of additional descriptive metrics including column type and statistical summaries. Data profiling results are used to suggest parameters for Expectations that you create.

* **Automate rules for Anomaly Detection.** GX Cloud can automatically generate Expectations that detect column changes, volume changes that deviate from historical patterns, and changes to the proportion of null values in each column. This option is available in the GX Cloud UI when you [create new Data Assets](/cloud/data_assets/manage_data_assets.md#add-a-data-asset-from-an-existing-data-source) or [add Expectations](/cloud/expectations/manage_expectations.md#create-an-expectation) for an existing Data Asset.

* **Personalize rules with ExpectAI.** GX Cloud can generate [AI-recommended Expectations](/cloud/expectations/manage_expectations.md#generate-expectations) for a Data Asset. These will be personalized based on an analysis of a sample of your data.

* **Generate code for custom SQL Expectations with ExpectAI.** To simplify working with [custom SQL Expectations](/cloud/expectations/expectations_overview.md#custom-sql-expectations), you can use ExpectAI to generate a SQL query based on a natural language prompt you provide and a data profile GX Cloud automatically provides.

* **Schedule Validations.** GX Cloud enables you to schedule validations, so that you can test and assess your data on a regular cadence and monitor data quality over time. See [Manage schedules](/cloud/schedules/manage_schedules.md) for more detail.

* **Alerting.** GX Cloud provides the ability to send alerts when validations fail, enabling your business to remain proactively aware of the health of your Data Assets. See [Respond to results](/cloud/alerts/alerts_lp.md) for more detail.

* **Monitor Data Health.** GX Cloud provides metric summaries and trends to help you understand and improve test coverage and success across your business. See [Data Health](/cloud/overview/data_health.md) for more detail.

* **Integrations.** GX Cloud integrates with a variety of third-party tools to help you get the most out of your data quality efforts. For example, you can integrate GX Cloud with data catalogs to bring data quality insights into your data governance workflows. Or, you can integrate GX Cloud with orchestrators to quarantine and backfill bad records. See [Integrations](/cloud/integrations/integrations_lp.md) for more information.

:::note Data Source support
Some features aren't supported for some Data Sources. See [Manage Data Sources](/docs/cloud/data_sources/manage_data_sources.md#workflow-and-feature-support) for details.
:::

## GX Cloud architecture

GX Cloud architecture comprises a frontend web UI, storage for entity configuration and metadata, a backend application, and a Python API.

![You interact using the UI, API, or both. How GX Cloud connects to your data depends on your deployment pattern.](./overview_images/gx_cloud_architecture.png)

* **GX Cloud frontend web UI**. Enables you to manage and validate your business's data quality without running code and provides shared visibility into your team's Validation Results history.

* **GX Cloud data storage**. Stores the configurations for your Data Sources, Data Assets, Expectations, and Validations alongside your Validation Result histories and Data Asset descriptive metrics.

* **GX Cloud backend application**. Contains the necessary logic and compute to connect to data and run queries. The specifics of how the GX Cloud backend connects to your data is described in [Deployment patterns](/cloud/deploy/deployment_patterns.md).

* **GX Cloud API**. Enables you to [interact programmatically](/reference/index.md) with GX Cloud entities and workflows using Python scripts. 