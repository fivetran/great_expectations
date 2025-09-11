---
sidebar_label: 'Manage Data Sources'
title: 'Manage Data Sources'
description: Manage data connections in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

A Data Source is an object that tells GX Cloud how to connect to a specific location of data and provides an entry point for organizing that data into Data Assets which can be validated. Visit the [compatibility reference](/docs/help/compatibility_reference) for a full list of supported Data Sources. [Contact us](mailto:sales@greatexpectations.io) to request support for additional sources.

## Data Source limitations

To connect to the following data locations, you must use the GX Cloud API. These are not available for connection in the GX Cloud UI:
- [Amazon S3](/docs/cloud/connect/connect_s3)
- [Azure Blob Storage](/docs/cloud/connect/python)
- [BigQuery](/docs/cloud/connect/python)
- [Google Cloud Storage](/docs/cloud/connect/python)
- [Pandas](/docs/cloud/connect/python)
- [Spark](/docs/cloud/connect/python)

All of these Data Sources have the following limitations, regardless of your GX Cloud [deployment pattern](/docs/cloud/deploy/deployment_patterns):
- The Data Source configuration cannot be edited in the GX Cloud UI. Use the GX Cloud API if you need to [edit the connection](/cloud/data_sources/manage_data_sources).
- Data Assets cannot be added through the GX Cloud UI. Use the GX Cloud API to add Data Assets.
- ExpectAI is not supported.

Azure Blob Storage, BigQuery, Google Cloud Storage, Pandas, and Spark have the following additional limitations:
- Data Asset metrics are not supported.
- You cannot define a batch in the UI. You can use the GX Cloud API to create a [Batch Definition](/docs/reference/api/core/batch_definition/BatchDefinition_class.mdx).
- Expectations for [Anomaly Detection](/docs/cloud/expectations/expectations_overview.md#anomaly-detection) cannot be automatically generated. You can manually configure Anomaly Detection by adding Expectations with Dynamic Parameters or forecasted ranges.
- Ad hoc Validations cannot be triggered through the GX Cloud UI. Use the UI to [generate a Validation code snippet](/docs/cloud/validations/manage_validations.md) that you can use to run an ad hoc Validation through the GX Cloud API
- Recurring Validations cannot be scheduled in GX Cloud. Use an [orchestrator](/docs/reference/learn/integrations/data_pipeline_tutorial) to run recurring Validations. 

## Edit Data Source settings

You can use the GX Cloud UI to edit settings for Databricks SQL, PostgreSQL, Redshift, and Snowflake Data Sources. You can use the GX Cloud API to edit settings for any Data Source. 

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click **Manage Data Sources**.

3. Click **Edit Data Source** for the Data Source you want to edit.

4. Edit the configuration as needed. Available fields vary by source type. For details, refer to the instructions for [connecting GX Cloud](/cloud/connect/connect_lp.md) to your source type.

6. Click **Save**.

</TabItem>

<TabItem value="api" label="API">

TBD

</TabItem>

</Tabs>

## Data Source credential management
Options for managing credentials depend on whether you are connecting a Data Source in the GX Cloud UI or through the GX Cloud API.

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

Depending on your [deployment pattern](/docs/cloud/deploy/deployment_patterns), you have the following options for managing credentials for Data Sources connected through the GX Cloud UI.

-  **Direct input** is supported for all GX Cloud deployment patterns. You can input credentials directly into the GX Cloud UI. These credentials are stored in GX Cloud and securely encrypted at rest and in transit. 

- **Environment variable substitution** is supported for agent-enabled and read-only deployments. To enhance security, you can use environment variables to manage sensitive connection parameters or strings. For example, instead of directly including your database password in configuration settings, you can use a variable reference like `${MY_DATABASE_PASSWORD}`. When using environment variable substitution, your credentials are not stored or transmitted to GX Cloud. To use environment variable substitution, do the following:

   1. Inject the variable into your GX Agent container or environment.
   
      When running the GX Agent Docker container, include the environment variable in the command. For example:
   
      ```bash title="Terminal input"
      docker run -it -e MY_DATABASE_PASSWORD=<YOUR_DATABASE_PASSWORD> -e GX_CLOUD_ACCESS_TOKEN=<YOUR_ACCESS_TOKEN> -e GX_CLOUD_ORGANIZATION_ID=<YOUR_ORGANIZATION_ID> greatexpectations/agent:stable
      ```

      When running the GX Agent in another container-based service, including Kubernetes, ECS, ACI, and GCE, use the service's instructions to set and provide environment variables to the running container.

      When using environment variable substitution in a read-only deployment, set the environment variable in the environment where the GX Cloud API Python client is running.

   2. In the Data Source setup form in the GX Cloud UI, enter the name of your environment variable, enclosed in `${}`. For example, `${MY_DATABASE_PASSWORD}`.

</TabItem>

<TabItem value="api" label="API">

Credentials you use with the GX Cloud API should be stored securely outside of version control. Whether they are connection strings for your Data Sources or tokens for Actions with third party apps such as Slack, credentials used with the GX Cloud API can be supplied with string substitution. Do the following to store any type of credential as an environment variable on a local system and then reference it by variable name in your version controlled code:

1. Assign the credentials to a reference variable.

   <EnvironmentVariables/>

2. Access your credentials in Python strings.

   <AccessCredentials/>


