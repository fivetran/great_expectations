---
sidebar_label: 'Manage Validations'
title: 'Manage Validations'
description: Create and manage Validations in GX Cloud.
toc_max_heading_level: 2
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To explore your data and fine-tune your Expectations, run an ad hoc Validation as described in this page. To run recurring Validations, use a [schedule](/docs/cloud/schedules/manage_schedules.md) or an [orchestrator](/docs/cloud/connect/connect_airflow.md).

Workflows for ad hoc Validations vary based on the following factors:
- whether you are validating [GX-managed or API-managed Expectations](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations.)
- whether you are validating your entire Data Asset or a time-based subset of it
- your Data Source type 

- GX-managed Expectations on Data Assets from Databricks SQL, PostgreSQL, Redshift, or Snowflake Data Sources can be validated with the GX Cloud UI. 
- All Expectations and all Data Sources can be validated with the GX Cloud API.


<Tabs 
   queryString="workflow-matrix"
   defaultValue="AlloyDB"
   values={[
      {value: 'AlloyDB', label: 'AlloyDB'},
      {value: 'Aurora', label: 'Aurora'},
      {value: 'S3', label: 'Amazon S3'},
      {value: 'Azure', label: 'Azure Blob Storage'},
      {value: 'BigQuery', label: 'BigQuery'},
      {value: 'Citus', label: 'Citus'},
      {value: 'Databricks', label: 'Databricks'},
      {value: 'GCS', label: 'Google Cloud Storage'},
      {value: 'Neon', label: 'Neon'},
      {value: 'PostgreSQL', label: 'PostgreSQL'},
      {value: 'Redshift', label: 'Redshift'},
      {value: 'Snowflake', label: 'Snowflake'}
   ]}
>

<TabItem value="AlloyDB" label="AlloyDB">
|                          | Entire Data Asset | Time-based subset of a Data Asset |
|--------------------------|-------------------|-----------------------------------|
| GX-managed Expectations  | 1                 | 2                                 |
| API-managed Expectations | 3                 | 4                                 |
</TabItem>

<TabItem value="Aurora" label="Aurora">
a
</TabItem>

<TabItem value="S3" label="Amazon S3">
b
</TabItem>

<TabItem value="Azure" label="Azure Blob Storage">
c
</TabItem>

<TabItem value="BigQuery" label="BigQuery">
d
</TabItem>

<TabItem value="Citus" label="Citus">
e
</TabItem>

<TabItem value="Databricks" label="Databricks">
f
</TabItem>

<TabItem value="GCS" label="Google Cloud Storage">
g
</TabItem>

<TabItem value="Neon" label="Neon">
h
</TabItem>

<TabItem value="PostgreSQL" label="PostgreSQL">
i
</TabItem>

<TabItem value="Redshift" label="Redshift">
j
</TabItem>

<TabItem value="Snowflake" label="Snowflake">
k
</TabItem>

</Tabs>

No matter how you run your validations, historical validation results are available in the GX Cloud UI.

## Validate GX-managed Expectations

If your Data Source is Databricks SQL, PostgreSQL, Redshift, or Snowflake, use the GX Cloud UI for ad hoc validations of GX-managed Expectations. For all other Data Sources, use the GX Cloud API to validate GX-managed Expectations. 

<Tabs 
   queryString="validation-interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'Validate with the UI'},
      {value: 'api', label: 'Validate with the API'}
   ]}
>

<TabItem value="ui" label="UI">

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A Databricks SQL, PostgreSQL, Redshift, or Snowflake [Data Asset](/docs/cloud/data_assets/manage_data_assets.md) with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).

### Validate entire Data Asset

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

When the Validation is complete, you can [view the results](#view-validation-run-history).

### Validate a time-based subset of a Data Asset

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

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any Data Asset with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).
   :::note Minimum version for row conditions
   GX Cloud library versions prior to 1.8.1 do not support the following [row conditions](/cloud/expectations/expectations_overview.md#row-conditions) options. If you use any of these aspects of row conditions, make sure your GX Cloud library is version 1.8.1 or later.
      - multiple condition statements
      - **is in**, **is not in**, or **is null** operators
   :::

### Validate entire Data Asset

To allow you to validate GX-managed Expectations with the Cloud API, GX Cloud provides a GX-managed Checkpoint you can run. 

1. Retrieve the GX-managed Checkpoint name. Replace `my data asset name` in the code sample below with your Data Asset's name.

   ```Python 
   import great_expectations as gx
   context = gx.get_context()

   checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
   for name in checkpoint_names:
       if "GX-Managed" in name and "my Data Asset name" in name:
           my_checkpoint=name
    ```

2. Run the checkpoint.

   ```Python
   checkpoint = context.checkpoints.get(my_checkpoint)

   checkpoint.run()
   ```



When the Validation is complete, you can [view the results in the GX Cloud UI](#view-validation-run-history).

### Validate a time-based subset of a Data Asset

Options for validating a time-based subset of a Data Asset depend on your Data Source type.


<Tabs 
   queryString="source-type"
   defaultValue="sql"
   values={[
      {value: 'sql', label: 'SQL sources'},
      {value: 'filesystem', label: 'Filesystem sources'}
   ]}
>

<TabItem value="sql" label="SQL sources">

If your SQL Data Asset has at least one DATE or DATETIME column, you can validate your data incrementally. To do this, you will first define how to partition your data and then select a specific time-based interval to validate.

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

Then, you can validate a batch of data. To allow you to validate GX-managed Expectations with the Cloud API, GX Cloud provides a GX-managed Checkpoint you can run. 

1. Retrieve the GX-managed Checkpoint name. Replace `my data asset name` in the code sample below with your Data Asset's name.

   ```Python 
   import great_expectations as gx
   context = gx.get_context()

   checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
   for name in checkpoint_names:
       if "GX-Managed" in name and "my Data Asset name" in name:
           my_checkpoint=name
    ```

2. Run the checkpoint with batch parameters passed as integers.

   ```Python
   checkpoint = context.checkpoints.get(my_checkpoint)
   batch_parameters_daily = {"year": 2019, "month": 1, "day": 30}

   checkpoint.run(batch_parameters=batch_parameters_daily)
   ```

</TabItem>

<TabItem value="filesystem" label="Filesystem sources">

If your filesystem Data Asset has date-based filenames, you can validate your data incrementally. To do this, you will first define how to partition your data and then select a specific time-based interval to validate.

First, you partition your data

1. Define the Data Asset to batch.

   ```Python 
   data_source_name = "my_data_source" 
   data_asset_name = "my_data_asset" 
   ```

2. Decide how you want to batch your data.

   | Goal                                      | partitioner                  | parameter names        |
   |-------------------------------------------|------------------------------|------------------------|
   | Partition records by year                 | `FileNamePartitionerYearly`  | `year`                 |
   | Partition records by year and month       | `FileNamePartitionerMonthly` | `year`, `month`        |
   | Partition records by year, month, and day | `FileNamePartitionerDaily`   | `year`, `month`, `day` |

3. Partition your data. This example demonstrates daily batches with the `FileNamePartitionerDaily` partitioner and `year`, `month`, and `day` parameter names. Refer to the above table for partitioners and parameters for other types of batches.

   ```Python
   import re
   batching_regex = re.compile(r"my_file_name_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).csv")

   import great_expectations as gx
   from great_expectations.core.partitioners import FileNamePartitionerDaily

   context = gx.get_context()
   ds = context.data_sources.get(data_source_name)
   asset = ds.get_asset(data_asset_name)

   for bd in asset.batch_definitions:
       if "GX-Managed" in bd.name:
           bd.partitioner = FileNamePartitionerDaily(
               regex=batching_regex,
               sort_ascending=True,
               param_names=("year", "month", "day")
           )

   context.update_datasource(ds)
   ```

Then, you can validate a batch of data. To allow you to validate GX-managed Expectations with the Cloud API, GX Cloud provides a GX-managed Checkpoint you can run. 

1. Retrieve the GX-managed Checkpoint name. Replace `my data asset name` in the code sample below with your Data Asset's name.

   ```Python 
   import great_expectations as gx
   context = gx.get_context()

   checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
   for name in checkpoint_names:
       if "GX-Managed" in name and "my Data Asset name" in name:
           my_checkpoint=name
    ```

2. Run the checkpoint with batch parameters passed as strings.

   ```Python
   checkpoint = context.checkpoints.get(my_checkpoint)
   batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

   checkpoint.run(batch_parameters=batch_parameters_daily)
   ```

</TabItem>
</Tabs>


</TabItem>

</Tabs>


When the Validation is complete, you can [view the results](#view-validation-run-history).

## Validate API-managed Expectations

For all types of Data Sources, use the GX Cloud API to validate API-managed Expectations. 

To do this you will first create a Validation Definition that links your data to your Expectations. Then you can run the Validation Definition to validate the referenced data against the associated Expectations for testing or data exploration. If you want to [trigger Actions](/docs/cloud/alerts/trigger_actions) based on the Validation Results, you will add your Validation Defintion to a Checkpoint that associates your tests with conditional logic for responding to results. 

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any Data Asset with at least one [API-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).
   :::note Minimum version for row conditions
   GX Cloud library versions prior to 1.8.1 do not support the following [row conditions](/cloud/expectations/expectations_overview.md#row-conditions) options. If you use any of these aspects of row conditions, make sure your GX Cloud library is version 1.8.1 or later.
      - multiple condition statements
      - **is in**, **is not in**, or **is null** operators
   :::

### Validate entire Data Asset

To help you to validate API-managed Expectations on an entire Data Asset with the Cloud API, GX Cloud provides a GX-managed Batch Definition you can use to identify your data.

1. Retrieve your Data Asset’s GX-managed Batch Definition.

   ```Python
   import great_expectations as gx

   data_source_name = "my_data_source" 
   data_asset_name = "my_data_asset" 
   batch_definition_name = "my data asset - GX-Managed Batch Definition"

   batch_definition = (
       context.data_sources.get(data_source_name)
       .get_asset(data_asset_name)
       .get_batch_definition(batch_definition_name)
   )
   ```
2. Retrieve your API-managed Expectation Suite.

   ```Python
   suite_name = "my_expectation_suite"
   suite = context.suites.get(name=suite_name)
   ```

3. Create a Validation Definition that associates the Batch Definition with the Expectation Suite.

   ```Python
   definition_name = "my_validation_definition"
   validation_definition = gx.ValidationDefinition(
       data=batch_definition, suite=suite, name=definition_name
   )
   ```
4. Run the validation definition.

   ```Python
   validation_definition.run()
   ```

5. Optional. Create a checkpoint so you can [trigger actions](/docs/cloud/alerts/trigger_actions) based on the validation results of your API-managed Expectations.  

    ```Python
    # Retrieve the validation definition
    validation_definition = context.validation_definitions.get("my_validation_definition")

    # Create a checkpoint
    checkpoint_name = "my_checkpoint"
    checkpoint_config = gx.Checkpoint(name=checkpoint_name, validation_definitions=[validation_definition])

    # Save the checkpoint to the data context
    checkpoint = context.checkpoints.add(checkpoint_config)
    ```

### Validate a time-based subset of a Data Asset


Options for validating a time-based subset of a Data Asset depend on your Data Source type.


<Tabs 
   queryString="source-type"
   defaultValue="sql"
   values={[
      {value: 'sql', label: 'SQL sources'},
      {value: 'filesystem', label: 'Filesystem sources'}
   ]}
>

<TabItem value="sql" label="SQL sources">

If your SQL Data Asset has at least one DATE or DATETIME column, you can validate your data incrementally. To do this, you will first define how to partition your data and then select a specific time-based interval to validate.

First, you partition your data

1. Retrieve the data asset.

   ```Python 
   data_source_name = "my_data_source" 
   data_asset_name = "my_data_asset 

   import great_expectations as gx

   context = gx.get_context()
   ds = context.data_sources.get(data_source_name)
   asset = ds.get_asset(data_asset_name)
   ```

2. Decide how you want to batch your data.

   | Goal                                      | method                         |
   |-------------------------------------------|--------------------------------|
   | Partition records by year                 | `add_batch_definition_yearly`  |
   | Partition records by year and month       | `add_batch_definition_monthly` |
   | Partition records by year, month, and day | `add_batch_definition_daily`   |

3. Partition your data. This example demonstrates daily batches with the `add_batch_definition_daily` method. Refer to the above table for partitioners and methods for other types of batches.

   ```Python
   date_column = "pickup_datetime"
   daily_batch_definition = data_asset.add_batch_definition_daily(
       name="DAILY", column=date_column
   )
   ```

4. Retrieve your API-managed Expectation Suite.

   ```Python
   suite_name = "my_expectation_suite"
   suite = context.suites.get(name=suite_name)
   ```

5. Create Validation definition that associates your time-based Batch Definition with your API-managed Expectation Suite.

   ```Python
   definition_name = "my_validation_definition"
   validation_definition = gx.ValidationDefinition(
       data=batch_definition, suite=suite, name=definition_name
   )

   validation_definition = context.validation_definitions.add(validation_definition)
   ``` 


6. Run the validation definition with batch parameters passed as integers.

   ```Python 
   batch_parameters_yearly = {"year": 2019, "month": 1, "day": 30}

   validation_definition.run(batch_parameters=batch_parameters_yearly)
    ```

7. Optional. Create a checkpoint so you can [trigger actions](/docs/cloud/alerts/trigger_actions) based on the validation results of your API-managed Expectations.  

    ```Python
    # Retrieve the validation definition
    validation_definition = context.validation_definitions.get("my_validation_definition")

    # Create a checkpoint
    checkpoint_name = "my_checkpoint"
    checkpoint_config = gx.Checkpoint(name=checkpoint_name, validation_definitions=[validation_definition])

    # Save the checkpoint to the data context
    checkpoint = context.checkpoints.add(checkpoint_config)

    # When you run the checkpoint, pass batch parameters as integers
    batch_parameters_yearly = {"year": 2019, "month": 1, "day": 30}

    checkpoint.run(batch_parameters=batch_parameters_yearly)
    ```

</TabItem>

<TabItem value="filesystem" label="Filesystem sources">

If your filesystem Data Asset has date-based filenames, you can validate your data incrementally. To do this, you will first define how to partition your data and then select a specific time-based interval to validate.

First, you partition your data

1. Retrieve the data asset.

   ```Python 
   data_source_name = "my_data_source" 
   data_asset_name = "my_data_asset 

   import great_expectations as gx

   context = gx.get_context()
   ds = context.data_sources.get(data_source_name)
   asset = ds.get_asset(data_asset_name)
   ```

2. Decide how you want to batch your data.

   | Goal                                      | method                         | parameter names        |
   |-------------------------------------------|--------------------------------|------------------------|
   | Partition records by year                 | `add_batch_definition_yearly`  | `year`                 |
   | Partition records by year and month       | `add_batch_definition_monthly` | `year`, `month`        |
   | Partition records by year, month, and day | `add_batch_definition_daily`   | `year`, `month`, `day` |

3. Partition your data. This example demonstrates daily batches with the `add_batch_definition_daily` method. Refer to the above table for methods and parameters for other types of batches.

   ```Python
   batch_definition_name = "daily_yellow_tripdata_sample"
   batch_definition_regex = r"folder_with_data/yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\.csv"

   batch_definition = file_data_asset.add_batch_definition_daily(
       name=batch_definition_name, regex=batch_definition_regex
   )
   ```

4. Retrieve your API-managed Expectation Suite.

   ```Python
   suite_name = "my_expectation_suite"
   suite = context.suites.get(name=suite_name)
   ```

5. Create Validation definition that associates your time-based Batch Definition with your API-managed Expectation Suite.

   ```Python
   definition_name = "my_validation_definition"
   validation_definition = gx.ValidationDefinition(
       data=batch_definition, suite=suite, name=definition_name
   )

   validation_definition = context.validation_definitions.add(validation_definition)
   ``` 

6. Run validation definition with batch parameters passed as strings

   ```Python 
   batch_parameters_daily = {"year": "2019", "month": "1", "day": "30"}

   validation_definition.run(batch_parameters=batch_parameters_daily)
    ```
   ```

7. Optional. Create a checkpoint so you can [trigger actions](/docs/cloud/alerts/trigger_actions) based on the validation results of your API-managed Expectations.  

    ```Python
    # Retrieve the validation definition
    validation_definition = context.validation_definitions.get("my_validation_definition")

    # Create a checkpoint
    checkpoint_name = "my_checkpoint"
    checkpoint_config = gx.Checkpoint(name=checkpoint_name, validation_definitions=[validation_definition])

    # Save the checkpoint to the data context
    checkpoint = context.checkpoints.add(checkpoint_config)

    # When you run the checkpoint, pass batch parameters as strings
    batch_parameters_monthly = {"year": "2019", "month": "01"}

    checkpoint.run(batch_parameters=batch_parameters_monthly)
    ```
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
