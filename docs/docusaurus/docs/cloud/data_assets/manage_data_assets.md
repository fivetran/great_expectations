---
sidebar_label: 'Manage Data Assets'
title: 'Manage Data Assets'
description: Create and manage Data Assets in GX Cloud.
toc_min_heading_level: 2
toc_max_heading_level: 2
---

A Data Asset is a collection of records from a Data Source. You can validate the whole Data Asset or a time-based subset of it. When you first connect to a Data Source, you define a minimum of one Data Asset. You can add more Data Assets from that same Data Source later. 

## Add a Data Asset from a new Data Source

To add a Data Asset from a new Data Source, refer to [Connect GX Cloud](/cloud/connect/connect_lp.md).

## Add a Data Asset from an existing Data Source

To add a Data Asset from an existing Data Source, complete the following steps:

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset**.

2. In the **Existing Data Source** tab, select the relevant Data Source.

3. Select one or more tables or views to import as Data Assets.

4. Click **Add x Asset(s)**.

5. Decide which [Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema**, **Volume**, and **Completeness** anomalies. You can de-select recommendations you’d like to opt out of.

6. Click **Start monitoring** or **Finish**.

Then you can [add an Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation) for your new Data Asset.

## View Data Asset metrics

Data Asset metrics provide you with insight into the data you can use for your data validations. When you create a new Data Asset, schema data is automatically fetched.

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

## Delete a Data Asset


1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.
2. In the Data Assets list, click **Delete Data Asset** for the Data Asset you want to remove.
3. Review the warning and click **Delete** to confirm.

## Edit Data Source settings

Edit Data Source settings to update Data Source connection information or access credentials. You can only edit the settings of Data Sources created in GX Cloud.


1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click **Manage Data Sources**.

3. Click **Edit Data Source** for the Data Source you want to edit.

4. Edit the configuration as needed. Available fields vary by source type. For details, refer to the instructions for [connecting GX Cloud](/cloud/connect/connect_lp.md) to your source type.

6. Click **Save**.


## Data Source credential management

To connect to your Data Source in GX Cloud, there are two methods for managing credentials:

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

## View GX Cloud logs

If you encounter an issue performing a GX Cloud task, review log information to troubleshoot the cause and determine a fix.

1. In GX Cloud, select the relevant **Workspace** and then click **Logs**.

2. Click **Show log** next to a log entry to display additional log details.

3. Optional. Click **Hide log** to close the log details view.