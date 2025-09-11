---
sidebar_label: 'Manage Validations'
title: 'Manage Validations'
description: Create and manage Validations in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

You can manually run a Validation to explore your data and fine-tune your Expectations. To run recurring Validations, use a [schedule](/docs/cloud/schedules/manage_schedules.md) or an [orchestrator](/cloud/connect/connect_airflow.md).


## Run a Validation

Note that the following cannot be validated with the GX Cloud UI. Use the GX Cloud API to validate the following:
- [API-managed Expectations](/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations)
- Data Assets from Azure Blob Storage, BigQuery, Google Cloud Storage, Pandas, or Spark Data Sources

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- An Amazon S3, Databricks SQL, PostgreSQL, Redshift, or Snowflake [Data Asset](docs/cloud/data_assets/manage_data_assets) with at least one [GX-managed Expectation](/cloud/expectations/expectations_overview#gx-managed-vs-api-managed-expectations).

### Procedure

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

4. If you've [defined a Batch](/cloud/expectations/manage_expectations.md#optional-define-a-batch), you can run a Validation on the latest Batch of data, or you can select a specific year, year and month, or year, month, and day period for the Validation. 

   If you've defined a Batch, select one of the following options:

    - **Latest** - Run the Validation on the latest Batch of data.

    - **Custom** - Select the **year**, **month**, or **day** to run the Validation on a Batch of data for a specific period.

    Then click **Run**.

5. When the confirmation message appears, click **See results**, or click the **Validations** tab and select the Validation in the **Batches & run history** pane.

6. Optional. Click **Share** to copy the URL for the Validation Results and share them with other users in your workspace.
</TabItem>

<TabItem value="api" label="API">

</TabItem>

</Tabs>



## View Validation run history

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click the **Validations** tab.

4. On the **Validations** page, select one of the following options:

    - To view only run validation failures, click **Failures Only**.

    - To view the run history for specific Validation, select a Validation in the **Batches & run history** pane.
    
    - To view the run history of all Validations, select **All Runs** to view a graph showing the Validation run history for all columns.

   :::tip Run history details
   Depending on how your Data Assets are validated, you may find the following information on items in the **Batches & run history** pane.
   - A <img src="/img/calendar.png" alt="pencil icon" width="20" height="20"/> calendar icon indicates a Valdation ran by a GX-managed schedule.
   - **Batch** information is included for any Validation ran on a subset of a Data Asset. 
   :::

5. Optional. Hover over a circle in the Validation timeline to view details about a specific Validation run, including the observed values.

    ![Validation timeline detail](/img/view_validation_timeline_detail.png)
