---
sidebar_label: 'Manage Validations'
title: 'Manage Validations'
description: Create and manage Validations in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

You can run an ad hoc Validation to explore your data and fine-tune your Expectations. To run recurring Validations, use a [schedule](/docs/cloud/schedules/manage_schedules.md) or an [orchestrator](/cloud/connect/connect_airflow.md).
 
Options for ad hoc Validations depend on your Data Soure type and whether you are validating [GX-managed or API-managed Expectations](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations.). 

- GX-managed Expectations on Data Assets from Databricks SQL, PostgreSQL, Redshift, or Snowflake Data Sources can be validated with the GX Cloud UI. 
- All Expectations and all Data Sources can be validated with the GX Cloud API.

## Validate GX-managed Expectations

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
- A Databricks SQL, PostgreSQL, Redshift, or Snowflake [Data Asset](docs/cloud/data_assets/manage_data_assets) with at least one [GX-managed Expectation](/cloud/expectations/expectations_overview#gx-managed-vs-api-managed-expectations).

### Run a Validation

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

4. When the confirmation message appears, click **See results**, or click the **Validations** tab and select the Validation in the **Batches & run history** pane.

5. Optional. Click **Share** to copy the URL for the Validation Results and share them with other users in your workspace.

### Run a Validation on a time-based subset of a Data Asset

If your Data Asset has at least one DATE or DATETIME column, you can validate your data incrementally. To to this, you will first define how to partition your data and then select a specific time-based interval to validate.

#### Batch your data

First, parition your data into time-based Batches.

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to the current batch configuration, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit batch**.

4. Choose how to **Validate by**. Select the **Entire Asset** tab to provide all Data Asset records to your Expectations and validations, or select one of the **Year**/**Month**/**Day** tabs to use subsets of Data Asset records for your Expectations and validations. **Year** partitions Data Asset records by year, **Month** partitions Data Asset records by year and month, **Day** partitions Data Asset records by year, month, and day.

5. Select the **Batch column** that contains the DATE or DATETIME data to partition on.

6. Click **save**

#### Validate a Batch

After your Data Asset is batched, you can run a Validation on the latest Batch of data, or you can select a specific time period for the Validation. 

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

4. Select one of the following options:

    - **Latest** - Run the Validation on the latest Batch of data.

    - **Custom** - Select the **year**, **month**, or **day** to run the Validation on a Batch of data for a specific period.

5. Click **Run**.

6. When the confirmation message appears, click **See results**, or click the **Validations** tab and select the Validation in the **Batches & run history** pane.

7. Optional. Click **Share** to copy the URL for the Validation Results and share them with other users in your workspace.
</TabItem>

<TabItem value="api" label="API">

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any Data Asset with at least one [GX-managed Expectation](/cloud/expectations/expectations_overview#gx-managed-vs-api-managed-expectations).
- [Python version 3.9 to 3.12](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

### Run a Validation

### Run a Validation on a time-based subset of a Data Asset


</TabItem>

</Tabs>

----------
OLD CONTENT BELOW HERE



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
   - A <img src="/img/calendar.png" alt="calendar icon" width="20" height="20"/> calendar icon indicates a Valdation ran by a GX-managed schedule.
   - **Batch** information is included for any Validation ran on a subset of a Data Asset. 
   :::

5. Optional. Hover over a success or [failure severity](/cloud/expectations/expectations_overview.md#failure-severity) icon in the Validation timeline to view details about a specific Validation run, including the observed values.

    ![Provided details are: success, severity, run time, batch interval, batch column, batch name, and observed value.](/img/view_validation_timeline_detail.png)
