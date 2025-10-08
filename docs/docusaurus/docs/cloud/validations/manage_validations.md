---
sidebar_label: 'Manage Validations'
title: 'Manage Validations'
description: Create and manage Validations in GX Cloud.
toc_max_heading_level: 2
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To explore your data and fine-tune your Expectations, run an ad hoc Validation as described in this page. To run recurring Validations, use a [schedule](/docs/cloud/schedules/manage_schedules.md) or an [orchestrator](/docs/cloud/connect/connect_airflow.md).

Options for ad hoc Validations depend on your Data Soure type and whether you are validating [GX-managed or API-managed Expectations](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations.). 

- GX-managed Expectations on Data Assets from Databricks SQL, PostgreSQL, Redshift, or Snowflake Data Sources can be validated with the GX Cloud UI. 
- All Expectations and all Data Sources can be validated with the GX Cloud API.

No matter how you run your validations, historical validation results are available in the GX Cloud UI.

## Validate GX-managed Expectations

<Tabs 
   queryString="validation-interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'Validate with the UI'},
      {value: 'api', label: 'Validate with the API'}
   ]}
>

<TabItem value="ui" label="UI">

### Prerequisites (UI Validation, GX-managed Expectations)

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A Databricks SQL, PostgreSQL, Redshift, or Snowflake [Data Asset](/docs/cloud/data_assets/manage_data_assets.md) with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).

### Validate entire Data Asset (UI Validation, GX-managed Expectations)

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

When the Validation is complete, you can [view the results](#view-validation-run-history).

### Validate a time-based subset of a Data Asset (UI Validation, GX-managed Expectations)

If your Data Asset has at least one DATE or DATETIME column, you can validate your data incrementally. To do this, you will first define how to partition your data and then select a specific time-based interval to validate.

First, you partition your data.

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to the current batch configuration, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit batch**.

4. Choose a **Batch interval**.

   - **Year** partitions Data Asset records by year.
   - **Month** partitions Data Asset records by year and month.
   - **Day** partitions Data Asset records by year, month, and day.

5. Under **Validate by**, select the column that contains the DATE or DATETIME data to partition on.

6. Click **Save**.

Then, you can validate a batch of data.

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

4. Select one of the following options to **Specify a single Batch to validate**:

    - **Latest Batch**. Note that the latest Batch may still be recieving new data. For example, if you are batching by day and have new data arriving every hour, the latest batch will be any data that has arrived in the current day. The latest daily batch is not necessarily a full 24 hours worth of data. 

    - **Custom Batch**, which will let you enter a specific period of time to validate based on how you've batched your data. For example, if you've batched your data by month, you'll be prompted to enter a **Year-month** to identify the records to validate.

5. Click **Run**.

</TabItem>

<TabItem value="api" label="API">

### Prerequisites (API Validation, GX-managed Expectations)

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any Data Asset with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- [Python version 3.9 to 3.12](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

### Validate entire Data Asset (API Validation, GX-managed Expectations)

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Go to the **Validations** tab.

4. If you have multiple **Expectation Suites**, make sure the **GX-Managed Expectation Suite** is selected.

5. Click the <img src="/img/snippet.png" alt="code snippet icon" width="20" height="20"/> code snippet icon next to the **Validate** button, and then click **Generate snippet**.

6. Run the generated code in the enviroment where you've saved your Cloud credentials as environment variables. 


When the Validation is complete, you can [view the results in the GX Cloud UI](#view-validation-run-history).

### Validate a time-based subset of a Data Asset (API Validation, GX-managed Expectations)

If your Data Asset has at least one DATE or DATETIME column, you can validate your data incrementally. To do this, you will first define how to partition your data and then select a specific time-based interval to validate.

Options for defining and validating Batches for GX-managed Expectations depend on your Data Source type.

- Data Assets from Databricks SQL, PostgreSQL, Redshift, or Snowflake Data Sources support defining  Batches and validating GX-managed Expectations on batched data in the GX Cloud UI.
- All Data Assets support defining  and validating Batches with the GX Cloud API.

First, you partition your data

1. Define the Data Asset to batch and the DATE or DATETIME column to partition on

   ```Python 
   data_source_name = "my_data_source" 
   data_asset_name = "my_data_asset 
   column_name = "my_date_or_datetime_column"
   ```

2. Decide how you want to batch your data.

   | Goal                                      | partitioner                | method                                |
   |-------------------------------------------|----------------------------|---------------------------------------|
   | Partition records by year                 | `ColumnPartitionerYearly`  | `partition_on_year`                   |
   | Partition records by year and month       | `ColumnPartitionerMonthly` | `partition_on_year_and_month`         |
   | Partition records by year, month, and day | `ColumnPartitionerDaily`   | `partition_on_year_and_month_and_day` |

3. Partition your data. This example demonstrates daily batches with the `ColumnPartitionerDaily` partitioner and `partition_on_year_and_month_and_day` method. Refer to the above table for partitioners and methods for other types of batches.

   ```Python
   import great_expectations as gx
   from great_expectations.core.partitioners import ColumnPartitionerDaily

   context = gx.get_context()
   ds = context.data_sources.get(data_source_name)
   asset = ds.get_asset(data_asset_name)

   for bd in asset.batch_definitions:
       if "GX-Managed" in bd.name:
           bd.partitioner = ColumnPartitionerDaily(
               method_name="partition_on_year_and_month_and_day",
               column_name=column_name,
               sort_ascending=True,
           )

   context.update_datasource(ds)
   ```

Then, you can validate a batch of data.

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Go to the Validations tab.

3. Click **Validate**.

4. Select one of the following options to **Specify a single Batch to validate**:

    - **Latest Batch**. Note that the latest Batch may still be recieving new data. For example, if you are batching by day and have new data arriving every hour, the latest batch will be any data that has arrived in the current day. The latest daily batch is not necessarily a full 24 hours worth of data. 

    - **Custom Batch**, which will let you enter a specific period of time to validate based on how you've batched your data. For example, if you've batched your data by month, you'll be prompted to enter a **Year-month** to identify the records to validate.

6. Select **Code snippet**

7. Run the generated code in the enviroment where you've saved your Cloud credentials as environment variables. 

</TabItem>

</Tabs>


When the Validation is complete, you can [view the results](#view-validation-run-history).


## View Validation run history

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click the **Validations** tab.

4. On the **Validations** page, select one of the following options:

    - To view only run validation failures, click **Failures Only**.

    - To view the run history for specific Validation, select a Validation in the **Batches & run history** pane.
    
    - To view the run history of all Validations, select **All Runs** to view a graph showing the Validation run history for all columns.

       Optional. Hover over a success or [failure severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) icon in the Validation timeline to view details about a specific Validation run, including the observed values.

       ![Provided details are: success, severity, run time, batch interval, batch column, batch name, and observed value.](/img/view_validation_timeline_detail.png)

   :::tip Run history details
   Depending on how your Data Assets are validated, you may find the following information on items in the **Batches & run history** pane.
   - A <img src="/img/calendar.png" alt="calendar icon" width="20" height="20"/> calendar icon indicates a Valdation ran by a GX-managed schedule.
   - **Batch** information is included for any Validation ran on a subset of a Data Asset. 
    :::

5. Optional. Click **Share** to copy the URL for the Validation Results and share them with other users in your workspace.

## PARKING LOT - might be useful later

1. Retrieve your Data Asset.

   Replace the value of `datasource_name` with the name of your Data Source and the value of `asset_name` with the name of your Data Asset in the following code. Then execute it to retrieve an existing Data Source and Data Asset from your GX Cloud organization:

   ```Python
   # Retrieve a Data Source
   datasource_name = "my_datasource"
   data_source = context.data_sources.get(datasource_name)

   # Get the Data Asset from the Data Source
   asset_name = "MY_TABLE_ASSET"
   data_asset = data_source.get_asset(asset_name)
   ```

2. Add one or more Batch Definitions to the Data Asset.

   A partitioned Batch Definition subdivides the records in a Data Asset based on the values in a specified field. GX Cloud currently supports partitioning Data Assets based on DATE or DATETIME fields. The records can be grouped by year, month, or day. A Data Asset can have multiple Batch Definitions as long as each Batch Definition has a unique name within that Data Asset.

   Update the `date_column` variable and `name` parameters in the following snippet, then execute it to create partitioned Batch Definitions:

   ```Python
   date_column = "pickup_datetime"

   daily_batch_definition = data_asset.add_batch_definition_daily(
       name="DAILY", column=date_column
   )

   monthly_batch_definition = data_asset.add_batch_definition_monthly(
       name="MONTHLY", column=date_column
   )

   yearly_batch_definition = data_asset.add_batch_definition_yearly(
      name="YEARLY", column=date_column
   )
   ```

4. Optional. Verify the Batch Definition is valid.

   When retrieving a Batch from a partitioned Batch Definition, you can specify the date of the data to retrieve as shown in the following examples. If you do not specify a date, the most recent date in the data is returned by default.

   ```Python
   daily_batch = daily_batch_definition.get_batch(
       batch_parameters={"year": 2020, "month": 1, "day": 14}
   )
   daily_batch.head()

   monthly_batch = monthly_batch_definition.get_batch(
       batch_parameters={"year": 2020, "month": 1}
   )
   monthly_batch.head()

   yearly_batch = yearly_batch_definition.get_batch(
       batch_parameters={"year": 2020}
   )
   yearly_batch.head()
   ```

5. Find the name of your GX-managed Expectation Suite

   ```Python
   # Get all Expectation Suites
   all_suites = context.suites.all()

   # Define the Data Asset name to match
   asset_name = "my_asset"

   # Find your Data Asset's GX-managed Expectation Suite
   matching_suites = [
      suite for suite in all_suites
      if asset_name in suite.name and "GX-Managed" in suite.name
   ]

   # Print matching suite names
   for suite in matching_suites:
    print(suite.name)
   ```

6. Retrieve your Expectation Suite

   Update the value of `expectation_suite_name` in the following code with the name of your Expectation Suite. Then execute the code to retrieve that Expectation Suite:

   ```
   expectation_suite_name = "my_expectation_suite"
   expectation_suite = context.suites.get(name=expectation_suite_name)
   ```

5. Create a Validation Definition to associate your GX-managed Expectation Suite with your batched data.

   Update the value of `definition_name` with a descriptive name that indicates the purpose of the Validation Definition. Then execute the code to create your Validation Definition:

   ```Python
   definition_name = "my_validation_definition"
   batch_definition = "daily_batch"
   validation_definition = gx.ValidationDefinition(
   data=batch_definition, suite=expectation_suite, name=definition_name
   )
   ```