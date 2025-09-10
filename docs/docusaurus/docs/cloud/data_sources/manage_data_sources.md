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

The steps for editing Data Source settings depend on whether the Data Source was created in the GX Cloud UI or with the GX Cloud API.

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

 You can use the UI to edit the settings of Data Sources created in the GX Cloud UI.


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

To connect to your Data Source in the GX Cloud UI, there are two methods for managing credentials:

-  **Direct input**: You can input credentials directly into GX Cloud. These credentials are stored in GX Cloud and securely encrypted at rest and in transit. When Data Source credentials have been directly provided, they can be used to connect to a Data Source in any GX Cloud deployment pattern.

- **Environment variable substitution**: To enhance security, you can use environment variables to manage sensitive connection parameters or strings. For example, instead of directly including your database password in configuration settings, you can use a variable reference like `${MY_DATABASE_PASSWORD}`. When using environment variable substitution, your password is not stored or transmitted to GX Cloud.

   :::warning[Environment variable substitution support]
   Environment variable substitution is not supported in fully-hosted deployments.
   :::

   - **Configure the environment variable**: Enter the name of your environment variable, enclosed in `${}`, into the Data Source setup form. For instance, you might use `${MY_DATABASE_PASSWORD}`.

   - **Inject the variable into your GX Agent container or environment**: When running the GX Agent Docker container, include the environment variable in the command. For example:
   
      ```bash title="Terminal input"
      docker run -it -e MY_DATABASE_PASSWORD=<YOUR_DATABASE_PASSWORD> -e GX_CLOUD_ACCESS_TOKEN=<YOUR_ACCESS_TOKEN> -e GX_CLOUD_ORGANIZATION_ID=<YOUR_ORGANIZATION_ID> greatexpectations/agent:stable
      ```

   When running the GX Agent in another container-based service, including Kubernetes, ECS, ACI, and GCE, use the service's instructions to set and provide environment variables to the running container.

   When using environment variable substitution in a read-only deployment, set the environment variable in the environment where the GX Cloud API Python client is running.

</TabItem>

<TabItem value="api" label="API">

TBD

For API tab, copy environment variable info from https://docs.greatexpectations.io/docs/core/configure_project_settings/configure_credentials/ including bits from intro about not putting tokens under version control 


</TabItem>

</Tabs>


