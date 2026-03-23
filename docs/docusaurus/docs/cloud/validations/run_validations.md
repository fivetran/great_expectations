---
sidebar_label: 'Run Validations'
title: 'Run Validations'
description: Create and manage Validations in GX Cloud.
toc_max_heading_level: 3
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To explore your data and fine-tune your Expectations, run an ad hoc Validation as described on this page. To run recurring Validations, use a [schedule](/docs/cloud/schedules/manage_schedules.md) or an [orchestrator](/docs/cloud/integrations/integrate_airflow.md).

## Run an ad hoc Validation

Workflows for ad hoc Validations vary based on the following aspects of what you're validating:
- Expectation type - [GX-managed or API-managed Expectations](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- Data scope - entire Data Asset or a time-based subset of a Data Asset.
- Data Source - for example, Snowflake or Amazon S3.


### Find your workflow

To help you find the right workflow for your particular combination of Expectation type, data scope, and Data Source, the table below provides a summary of the workflow for each possible combination of factors and a link to detailed instructions.

<table class="merged-rows"><thead>
  <tr>
    <th>Expectations</th>
    <th>Scope</th>
    <th>Data Source</th>
    <th>Workflow summary and link to full instructions</th>
  </tr></thead>
<tbody>
  <tr>
    <td rowspan="5">GX-managed</td>
    <td rowspan="2">Entire&nbsp;Data&nbsp;Asset</td>
    <td>AlloyDB<br />Amazon S3<br />Aurora<br />Citus<br />Databricks SQL<br />Microsoft Fabric<br />Microsoft SQL Server<br />Neon<br />PostgreSQL<br />Redshift<br />Snowflake</td>
    <td>Use the UI:<ul><li>Click the **Validate** button.</li></ul><a href="/docs/cloud/validations/run_validations/?validation-interface=ui#gx-managed-expectations-entire-asset">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td>Azure&nbsp;Blob&nbsp;Storage <br />BigQuery<br />Google&nbsp;Cloud&nbsp;Storage </td>
    <td>Use the API:<ul><li>Retrieve your Data Asset’s GX-managed Checkpoint.</li><li>Run the Checkpoint.</li></ul><a href="/docs/cloud/validations/run_validations/?validation-interface=api#gx-managed-expectations-entire-asset">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td rowspan="3">Time interval</td>
    <td>AlloyDB<br />Aurora<br />Citus<br />Databricks SQL<br />Microsoft Fabric<br />Microsoft SQL Server<br />Neon<br />PostgreSQL<br />Redshift<br />Snowflake</td>
    <td>For Table Data Assets, use the UI:<ul><li>Choose a **Batch interval**.</li><li>Click the **Validate** button and select a Batch to validate.</li></ul><a href="/docs/cloud/validations/run_validations/?validation-interface=ui#gx-managed-expectations-time-interval">Jump to full instructions</a><br /><br /><br />For Query Data Assets, use the API:<ul><li>Update your Data Asset’s GX-managed Batch Definition to partition your data based on values in a DATE or DATETIME column.</li><li>Retrieve your Data Asset's GX-managed Checkpoint.</li><li>Run the Checkpoint with Batch Parameters passed as integers.</li></ul><a href="/docs/cloud/validations/run_validations/?validation-interface=api&source-type=sql#gx-managed-expectations-time-interval">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td>Amazon S3<br />Azure&nbsp;Blob&nbsp;Storage <br />Google&nbsp;Cloud&nbsp;Storage </td>
    <td>Use the API:<ul><li>Update your Data Asset’s GX-managed Batch Definition to partition your data based on regex filename matching.</li><li>Retrieve your Data Asset's GX-managed Checkpoint.</li><li>Run the Checkpoint with Batch Parameters passed as strings.</li></ul><a href="/docs/cloud/validations/run_validations/?validation-interface=api&source-type=filesystem#gx-managed-expectations-time-interval">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td>BigQuery</td>
    <td>Use the API:<ul><li>Update your Data Asset’s GX-managed Batch Definition to partition your data based on values in a DATE or DATETIME column.</li><li>Retrieve your Data Asset's GX-managed Checkpoint.</li><li>Run the Checkpoint with Batch Parameters passed as integers.</li></ul><a href="/docs/cloud/validations/run_validations/?validation-interface=api&source-type=sql#gx-managed-expectations-time-interval">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td rowspan="3">API-managed</td>
    <td>Entire&nbsp;Data&nbsp;Asset</td>
    <td>All sources</td>
    <td>Use the API:<ul><li>Retrieve your Data Asset's GX-managed Batch Definition.</li><li>Create a Validation Definition to associate your API-managed Expectations with your Data Asset via its GX-managed Batch Definition.</li><li>Run the Validation Definition.</li></ul><a href="/docs/cloud/validations/run_validations/#api-managed-expectations-entire-asset">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td rowspan="2">Time interval</td>
    <td>AlloyDB<br />Aurora<br />BigQuery<br />Citus<br />Databricks SQL<br />Microsoft Fabric<br />Microsoft SQL Server<br />Neon<br />PostgreSQL<br />Redshift<br />Snowflake</td>
    <td>Use the API:<ul><li>Create a Batch Definition to partition your data based on values in a DATE or DATETIME column.</li><li>Create a Validation Definition to associate your API-managed Expectations with your Data Asset via your Batch Definition.</li><li>Run the Validation Definition  with Batch Parameters passed as integers.</li></ul><a href="/docs/cloud/validations/run_validations/?source-type=sql#api-managed-expectations-time-interval">Jump to full instructions</a></td>
  </tr>
  <tr>
    <td>Amazon S3<br />Azure&nbsp;Blob&nbsp;Storage <br />Google&nbsp;Cloud&nbsp;Storage </td>
    <td>Use the API:<ul><li>Create a Batch Definition to partition your data based on regex filename matching.</li><li>Create a Validation Definition to associate your API-managed Expectations with your Data Asset via your Batch Definition.</li><li>Run the Validation Definition  with Batch Parameters passed as strings.</li></ul><a href="/docs/cloud/validations/run_validations/?source-type=filesystem#api-managed-expectations-time-interval">Jump to full instructions</a></td>
  </tr>
</tbody></table>

No matter how you run your Validations, you can [view historical Validation Results](#view-validation-run-history) in the GX Cloud UI.


### GX-managed Expectations, entire asset

If your Data Source is one of the following, you can use the GX Cloud UI to validate GX-managed Expectations for your entire Data Asset:
- AlloyDB
- Amazon S3
- Aurora
- Citus
- Databricks SQL
- Microsoft Fabric
- Microsoft SQL Server
- Neon
- PostgreSQL
- Redshift
- Snowflake

For all Data Sources, you can use the GX Cloud API to validate GX-managed Expectations for your entire Data Asset.

<Tabs 
   queryString="validation-interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'Validate with the UI'},
      {value: 'api', label: 'Validate with the API'}
   ]}
>

<TabItem value="ui" label="UI">

#### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A [Data Asset](/docs/cloud/data_assets/manage_data_assets.md) from AlloyDB, Amazon S3, Aurora, Citus, Databricks SQL, Microsoft Fabric, Microsoft SQL Server, Neon, PostgreSQL, Redshift, or Snowflake with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).

#### Procedure

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Click **Validate**.

</TabItem>

<TabItem value="api" label="API">

#### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any [Data Asset](/docs/cloud/data_assets/manage_data_assets.md) with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

#### Procedure

To help you validate GX-managed Expectations with the GX Cloud API, GX Cloud provides a GX-managed [Checkpoint](/docs/reference/api/Checkpoint_class) you can run. 

1. Define the Data Asset to validate.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - define asset"
   ```

2. Retrieve the name of the GX-managed Checkpoint for your Data Asset.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - retrieve checkpoint"
   ```

3. Run the Checkpoint.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - run checkpoint"
   ```

</TabItem>
</Tabs>

When the Validation is complete, you can [view the results in the GX Cloud UI](#view-validation-run-history).

### GX-managed Expectations, time interval

If your Data Source is one of the following, you can use the GX Cloud UI to validate GX-managed Expectations for a time-based subset of your Data Asset:
- AlloyDB
- Aurora
- Citus
- Databricks SQL
- Microsoft Fabric
- Microsoft SQL Server
- Neon
- PostgreSQL
- Redshift
- Snowflake

For all Data Sources, you can use the GX Cloud API to validate GX-managed Expectations for a time-based subset of your Data Asset. Note that the code is different for SQL Data Sources vs. filesystem Data Sources.

<Tabs 
   queryString="validation-interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'Partition and validate with the UI'},
      {value: 'api', label: 'Partition and validate with the API'}
   ]}
>

<TabItem value="ui" label="UI">

#### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A [Data Asset](/docs/cloud/data_assets/manage_data_assets.md) from AlloyDB, Aurora, Citus, Databricks SQL, Microsoft Fabric, Microsoft SQL Server, Neon, PostgreSQL, Redshift, or Snowflake with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations) and at least one DATE or DATETIME column.

#### Procedure

To validate your data incrementally, you will first define how to partition your data into Batches and then select a specific time-based Batch to validate.

First, partition your data.

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to the current Batch configuration, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit Batch**.

4. Choose a **Batch interval**.

   - **Year** partitions Data Asset records by year.
   - **Month** partitions Data Asset records by year and month.
   - **Day** partitions Data Asset records by year, month, and day.

5. Under **Validate by**, select the column that contains the DATE or DATETIME data to partition on.

6. Click **Save**.

Then, you can validate a Batch of data.

1. Click **Validate**.

2. Select one of the following options to **Specify a single Batch to validate**:

    - **Latest Batch**. Note that the latest Batch may still be receiving new data. For example, if you are batching by day and have new data arriving every hour, the latest Batch will be any data that has arrived in the current day. The latest daily Batch is not necessarily a full 24 hours worth of data. 

    - **Custom Batch**, which will let you enter a specific period of time to validate based on how you've batched your data. For example, if you've batched your data by month, you'll be prompted to enter a **Year-Month** to identify the records to validate.

3. Click **Run**.


</TabItem>

<TabItem value="api" label="API">

#### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any [Data Asset](/docs/cloud/data_assets/manage_data_assets.md) with at least one [GX-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- Date indicators to partition on.
   - For SQL Data Sources, you need at least one DATE or DATETIME column.
   - For filesystem Data Sources, your filenames must indicate the timeframe using a pattern that can be parsed with regex.
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

#### Procedure

The code for validating GX-managed Expectations on a time-based subset of a Data Asset depends on your Data Source type. For SQL Data Sources, you will partition your data based on values in a DATE or DATETIME column. For filesystem Data Sources, you will partition your data based on regex filename matching.


<Tabs 
   queryString="source-type"
   defaultValue="sql"
   values={[
      {value: 'sql', label: 'SQL sources'},
      {value: 'filesystem', label: 'Filesystem sources'}
   ]}
>


<TabItem value="sql" label="SQL sources">

To validate your data incrementally, you will first define how to partition your data into Batches and then select a specific time-based Batch to validate.

First, partition your data.

1. Define the Data Asset to batch and the DATE or DATETIME column to partition on.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - define asset"
   ```

2. Decide how you want to batch your data. Reference the table below to determine the partitioner and method to use to achieve your goal.

   | Goal                                      | partitioner                | method                                |
   |-------------------------------------------|----------------------------|---------------------------------------|
   | Partition records by year                 | `ColumnPartitionerYearly`  | `partition_on_year`                   |
   | Partition records by year and month       | `ColumnPartitionerMonthly` | `partition_on_year_and_month`         |
   | Partition records by year, month, and day | `ColumnPartitionerDaily`   | `partition_on_year_and_month_and_day` |

3. Partition your data. This example demonstrates daily Batches with the `ColumnPartitionerDaily` partitioner and the `partition_on_year_and_month_and_day` method. Refer to the above table for partitioners and methods for other types of Batches.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - partition data"
   ```

Then, you can validate a Batch of data. To help you validate GX-managed Expectations with the Cloud API, GX Cloud provides a GX-managed [Checkpoint](/docs/reference/api/Checkpoint_class) you can run. 

1. Retrieve the name of the GX-managed Checkpoint for your Data Asset.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - retrieve checkpoint name"
   ```

2. Run the Checkpoint with Batch Parameters passed as integers.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - run checkpoint"
   ```

</TabItem>

<TabItem value="filesystem" label="Filesystem sources">

To validate your data incrementally, you will first define how to partition your data into Batches and then select a specific time-based Batch to validate.

First, partition your data.

1. Define the Data Asset to batch.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - define asset"
   ```

2. Decide how you want to batch your data. Reference the table below to determine the partitioner and parameters to use to achieve your goal.

   | Goal                                      | partitioner                  | parameter names        |
   |-------------------------------------------|------------------------------|------------------------|
   | Partition records by year                 | `FileNamePartitionerYearly`  | `year`                 |
   | Partition records by year and month       | `FileNamePartitionerMonthly` | `year`, `month`        |
   | Partition records by year, month, and day | `FileNamePartitionerDaily`   | `year`, `month`, `day` |

3. Partition your data. This example demonstrates daily Batches with the `FileNamePartitionerDaily` partitioner and the `year`, `month`, and `day` parameter names. Refer to the above table for partitioners and parameters for other types of Batches.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - partition data"
   ```

Then, you can validate a Batch of data. To help you validate GX-managed Expectations with the Cloud API, GX Cloud provides a GX-managed [Checkpoint](/docs/reference/api/Checkpoint_class) you can run. 

1. Retrieve the name of the GX-managed Checkpoint for your Data Asset.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - retrieve checkpoint name"
    ```

2. Run the Checkpoint with Batch Parameters passed as strings.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_filesystem.py - run checkpoint"
   ```

</TabItem>

</Tabs>

</TabItem>

</Tabs>

When the Validation is complete, you can [view the results in the GX Cloud UI](#view-validation-run-history).

### API-managed Expectations, entire asset

To validate API-managed Expectations for your entire Data Asset, use the GX Cloud API. The process is the same regardless of your Data Source. You will first create a Validation Definition that links your data to your Expectations. Then you can run the Validation Definition to validate the referenced data against the associated Expectations for testing or data exploration. If you want to [trigger Actions](/docs/cloud/alerts/trigger_actions) based on the Validation Results, you will add your Validation Definition to a Checkpoint that associates your tests with conditional logic for responding to results. 

#### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any [Data Asset](/docs/cloud/data_assets/manage_data_assets.md).
- At least one [API-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations) in an API-managed Expectation Suite.
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

#### Procedure

To help you validate API-managed Expectations on an entire Data Asset with the Cloud API, GX Cloud provides a GX-managed Batch Definition you can use to identify your data.

1. Retrieve your Data Asset’s GX-managed Batch Definition.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - retrieve batch definition"
   ```

2. Retrieve your API-managed Expectation Suite.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - retrieve suite"
   ```

3. Create a Validation Definition that associates the Batch Definition with the Expectation Suite.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - create validation definition"
   ```
4. Run the Validation Definition.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - run validation definition"
   ```

5. Optional. Create a Checkpoint so you can [trigger Actions](/docs/cloud/alerts/trigger_actions) based on the Validation Results of your API-managed Expectations.  

    ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - create checkpoint"
    ```


When the Validation is complete, you can [view the results in the GX Cloud UI](#view-validation-run-history).

### API-managed Expectations, time interval

To validate API-managed Expectations for a time-based subset of a Data Asset, use the GX Cloud API. Note that the code is different for SQL Data Sources vs. filesystem Data Sources. You will first partition your data and create a Validation Definition that links your partitioned data to your Expectations. Then you can run the Validation Definition to validate the referenced data against the associated Expectations for testing or data exploration. If you want to [trigger Actions](/docs/cloud/alerts/trigger_actions) based on the Validation Results, you will add your Validation Definition to a Checkpoint that associates your tests with conditional logic for responding to results. 

#### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- Any [Data Asset](/docs/cloud/data_assets/manage_data_assets.md).
- Date indicators to partition on.
   - For SQL Data Sources, you need at least one DATE or DATETIME column.
   - For filesystem Data Sources, your filenames must indicate the timeframe using a pattern that can be parsed with regex.
- At least one [API-managed Expectation](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations) in an API-managed Expectation Suite.
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).


#### Procedure 

The code for validating API-managed Expectations on a time-based subset of a Data Asset depends on your Data Source type. For SQL Data Sources, you will partition your data based on values in a DATE or DATETIME column. For filesystem Data Sources, you will partition your data based on regex filename matching.



<Tabs 
   queryString="source-type"
   defaultValue="sql"
   values={[
      {value: 'sql', label: 'SQL sources'},
      {value: 'filesystem', label: 'Filesystem sources'}
   ]}
>

<TabItem value="sql" label="SQL sources">

To validate your data incrementally, you will first define how to partition your data into Batches and then select a specific time-based Batch to validate.

1. Retrieve your Data Asset.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - retrieve data asset" 
   ```

2. Decide how you want to batch your data. Reference the table below to determine the method to use to achieve your goal.

   | Goal                                      | method                         |
   |-------------------------------------------|--------------------------------|
   | Partition records by year                 | `add_batch_definition_yearly`  |
   | Partition records by year and month       | `add_batch_definition_monthly` |
   | Partition records by year, month, and day | `add_batch_definition_daily`   |

3. Partition your data. This example demonstrates daily Batches with the `add_batch_definition_daily` method. Refer to the above table for methods for other types of Batches.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - partition data" 
   ```

4. Retrieve your API-managed Expectation Suite.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - retrieve suite"
   ```

5. Create a Validation Definition that associates your time-based Batch Definition with your API-managed Expectation Suite.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - create validation definition"
   ``` 


6. Run the Validation Definition with Batch Parameters passed as integers.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - run validation definition" 
    ```

7. Optional. Create a Checkpoint so you can [trigger Actions](/docs/cloud/alerts/trigger_actions) based on the Validation Results of your API-managed Expectations.  

    ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - create checkpoint" 
    ```

</TabItem>

<TabItem value="filesystem" label="Filesystem sources">

To validate your data incrementally, you will first define how to partition your data into Batches and then select a specific time-based Batch to validate.

1. Retrieve your Data Asset.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - retrieve data asset" 
   ```

2. Decide how you want to batch your data. Reference the table below to determine the method and parameters to use to achieve your goal.

   | Goal                                      | method                         | parameter names        |
   |-------------------------------------------|--------------------------------|------------------------|
   | Partition records by year                 | `add_batch_definition_yearly`  | `year`                 |
   | Partition records by year and month       | `add_batch_definition_monthly` | `year`, `month`        |
   | Partition records by year, month, and day | `add_batch_definition_daily`   | `year`, `month`, `day` |

3. Partition your data. This example demonstrates daily Batches with the `add_batch_definition_daily` method. Refer to the above table for methods and parameters for other types of Batches.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - partition data" 
   ```

4. Retrieve your API-managed Expectation Suite.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - retrieve suite"
   ```

5. Create a Validation Definition that associates your time-based Batch Definition with your API-managed Expectation Suite.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - create validation definition" 
   ``` 

6. Run the Validation Definition with Batch Parameters passed as strings.

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - run validation definition"" 
   ```

7. Optional. Create a Checkpoint so you can [trigger Actions](/docs/cloud/alerts/trigger_actions) based on the Validation Results of your API-managed Expectations.

    ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - checkpoint" 
    ```
</TabItem>
</Tabs>

When the Validation is complete, you can [view the results in the GX Cloud UI](#view-validation-run-history).

## View Validation run history

All workspace members can view Validation Results.

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Click the **Validations** tab.

4. If you have multiple **Expectation Suites**, select the suite of interest.

5. Do one or more of the following:

    - To view results for a specific Validation run, select an entry in the **Batches & run history** pane.

       - To view only Expectations that failed in the selected run, click **Failures only**.

       - To view a SQL query that will retrieve the full set of unexpected results, select <img src="/img/search_file_icon.png" alt="search file icon" width="20" height="20"/> **Unexpected rows query**. Note that the unexpected results query may not be available depending on the type of Expectation and your configured [result format](/docs/cloud/validations/format_results.md).

    - To view the run history of all Validations, select **All Runs** to view a graph showing the Validation run history for all columns.

       - To view details about a specific Validation run in the Validation timeline, hover over a success or [failure severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) icon. Note that observed values may not be available depending on the type of Expectation and your configured [result format](/docs/cloud/validations/format_results.md).

      ![Provided details are: success, severity, run time, batch interval, batch column, batch name, and observed value.](/img/view_validation_timeline_detail.png)

   :::tip Run history details
   Depending on how your Data Assets are validated, you may find the following information on entries in the **Batches & run history** pane.
   - A <img src="/img/calendar.png" alt="calendar icon" width="20" height="20"/> calendar icon indicates a Validation ran by a GX-managed schedule.
   - **Batch** information is included for any Validation ran on a subset of a Data Asset. 
    :::
