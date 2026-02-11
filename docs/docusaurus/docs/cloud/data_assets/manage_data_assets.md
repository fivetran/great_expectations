---
sidebar_label: 'Manage Data Assets'
title: 'Manage Data Assets'
description: Create and manage Data Assets in GX Cloud.
toc_min_heading_level: 2
toc_max_heading_level: 2
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

A Data Asset is a collection of records from a Data Source. You can validate the whole Data Asset or a time-based subset of it. When you first connect to a Data Source, you define a minimum of one Data Asset. You can add more Data Assets from that same Data Source later. 

## Add a Data Asset from a new Data Source

To add a Data Asset from a new Data Source, refer to [Connect GX Cloud](/cloud/connect/connect_lp.md).

## Add a Data Asset from an existing Data Source

You can use the GX Cloud UI to add a Data Asset from an existing Databricks SQL, PostgreSQL, Redshift, or Snowflake Data Source. You can use the GX Cloud API to add a Data Asset from any Data Source. 

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
- A Databricks SQL, PostgreSQL, Redshift, or Snowflake [Data Source](/docs/cloud/connect/connect_lp).

### Procedure

To add a Data Asset from an existing Data Source using the GX Cloud UI, complete the following steps:

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset**.

2. In the **Existing Data Source** tab, select the relevant Data Source.

3. Select one or more tables or views to import as Data Assets.

4. Click **Add x Asset(s)**.

5. Decide which [Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema** and **Volume** anomalies. You can de-select recommendations you’d like to opt out of. You can choose to generate Expectations to detect **Completeness** anomalies.

6. Click **Start monitoring** or **Finish**.


</TabItem>

<TabItem value="api" label="API">

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- A [Data Source](/docs/cloud/connect/connect_lp).
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).
- Recommended. A [Python virtual environment](https://docs.python.org/3/library/venv.html).

### Procedure

<Tabs 
   queryString="verbosity"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

To add a Data Asset from an existing Data Source using the GX Cloud API, complete the following steps:

1. Create a Data Context object.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - get cloud context" 
   ```

2. Fetch the Data Source.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - get data source" 
   ```

3. Define your Data Asset's parameters. Refer to the [API reference](/docs/reference/) for your Data Source for details on required and optional parameters. Here’s an example for a Data Asset on an S3 Data Source.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - define asset" 
   ```

4. Add the Data Asset to your Data Source. Refer to the  [API reference](/docs/reference/) for your Data Source for method details. Here’s an example for a `.csv` file Data Asset on an S3 Data Source.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - add asset" 
   ```

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/data_assets/manage_data_assets.py - full sample" 
```

</TabItem>

</Tabs>

</TabItem>

</Tabs>

Now you can [add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation) for your new Data Asset.

## View Data Asset metrics

Data Asset metrics provide insights into your data that you can use to inform your Expectations. Schema data is automatically fetched when you create a new Databricks SQL, PostgreSQL, Redshift, or Snowflake Data Asset. For Amazon S3 Data Assets, you can manually fetch metrics.

To view Data Asset metrics, do the following:

1. In GX Cloud, select the relevant **Workspace**, click **Data Assets**, and then select a Data Asset in the **Data Assets** list.

2. Click the **Metrics** tab.

3. Optional. Select one of the following options:

    - Click **Profile Data** if you have not previously returned all available metrics for a Data Asset.

    - Click **Refresh** to refresh the Data Asset metrics.

### Available Data Asset metrics

The following table lists the available Data Asset metrics.

| Column                                   | Description                                               | 
|------------------------------------------|-----------------------------------------------------------|
| **Row Count**                            | The number of rows within a Data Asset.                   | 
| **Column**                               | A column within your Data Asset.                          | 
| **Type**                                 | The data storage type in the Data Asset column.           | 
| **Min**                                  | For numeric columns, the lowest value in the column.       | 
| **Max**                                  | For numeric columns, the highest value in the column.     | 
| **Mean**                                 | For numeric columns, the average value in the column.<br/> This is determined by dividing the sum of all values in the column by the number of values.  |
| **Median**                                 | For numeric columns, the value in the middle of a data set.<br/> 50% of the data within the Data Asset has a value smaller or equal to the median, and 50% of the data within the Data Asset has a value that is higher or equal to the median.  |
| **Null %**                                | The percentage of missing values in a column.             |

## View Data Asset history

For an audit trail of who added or removed which Expectations and when, visit a Data Asset’s **History** tab.

1. In GX Cloud, select the relevant **Workspace**, click **Data Assets**, and then select a Data Asset in the **Data Assets** list.
2. Click the **History** tab.

Note that the report is limited to the last 100 changes. 

## Delete a Data Asset


1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.
2. In the Data Assets list, click **Delete Data Asset** for the Data Asset you want to remove.
3. Review the warning and click **Delete** to confirm.


## View GX Cloud logs

If you encounter an issue performing a GX Cloud task, review log information to troubleshoot the cause and determine a fix.

1. In GX Cloud, select the relevant **Workspace** and then click **Logs**.

2. Click **Show log** next to a log entry to display additional log details.

3. Optional. Click **Hide log** to close the log details view.