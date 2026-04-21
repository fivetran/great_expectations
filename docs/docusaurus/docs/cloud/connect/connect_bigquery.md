---
sidebar_label: 'Connect GX Cloud to BigQuery'
title: 'Connect GX Cloud to BigQuery'
description: Add a BigQuery Data Source in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To connect GX Cloud to data stored in BigQuery, use the GX Cloud API.

## Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A GCP project with a BigQuery dataset that has a table or view.
- BigQuery credentials stored securely in a `credentials.json` file outside of version control. 
- [Python](https://www.python.org/downloads/) version 3.10 to 3.13.
- Recommended. A [Python virtual environment](https://docs.python.org/3/library/venv.html).


## Install GX Cloud

Run the following terminal command to install the GX Cloud library with support for BigQuery dependencies:

```bash title="Terminal input"
pip install 'great_expectations[bigquery]'
```

## Get your credentials

You'll need your user access token, organization ID, and workspace ID to set your environment variables. Don't commit your access token to your version control software.


1. In GX Cloud, click **Tokens**.

2. In the **User access tokens** pane, click **Create user access token**.

3. In the **Token name** field, enter a name for the token that will help you quickly identify it.

4. Click **Create**.

5. Copy and then paste the user access token into a temporary file. The token can't be retrieved after you close the dialog.

6. Click **Close**.

7. Copy the value in the **Organization ID** field into the temporary file with your user access token. 

8. In the **Workspace ID** pane, find the relevant **Workspace name**, then copy the associated **ID** into the temporary file with your other credentials and save the file. 

GX recommends deleting the temporary file after you set the environment variables.

## Set your credentials as environment variables

Environment variables securely store your GX Cloud credentials.

1. Save your GX Cloud credentials as environment variables by entering `export ENV_VAR_NAME=env_var_value` in the terminal or adding the command to your `~/.bashrc` or `~/.zshrc` file. For example:

    ```bash title="Terminal input"
    export GX_CLOUD_ACCESS_TOKEN=<user_access_token>
    export GX_CLOUD_ORGANIZATION_ID=<organization_id>
    export GX_CLOUD_WORKSPACE_ID=<workspace_id>
    ```

2. Optional. If you created a temporary file to record your credentials, delete it. 

## Connect a BigQuery Data Source and add a Data Asset

<Tabs 
   queryString="verbosity"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

1. Run the following Python code to create a Data Context object:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - get cloud context" 
   ```

   The Data Context will detect the previously set environment variables and connect to your GX Cloud account.


2. Define the Data Source's parameters.

   The following information is required when you create a BigQuery Data Source:

   - `name`: A descriptive name used to reference the Data Source. This should be unique within your workspace.
   - `connection_string`: The connection string used to connect to the database. The format for this is `bigquery://<GCP_PROJECT>/<BIGQUERY_DATASET>?credentials_path=/path/to/your/credentials.json`.

   Replace the variable values with your own and run the following Python code:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define source" 
   ```

3. Add a BigQuery Data Source to your Data Context by executing the following code:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add source" 
   ```


4. Decide whether you want to validate the records in a single table or the records returned by a SQL query.

   - To validate the records in a single table, you will create a Table Data Asset.
   - To validate the records returned by a SQL query, you will create a Query Data Asset. Note that [Query Data Assets have some limitations](/cloud/data_assets/manage_data_assets.md#data-asset-options-for-sql-data-sources) compared to Table Data Assets.

<Tabs 
   queryString="asset_type"
   defaultValue="table"
   values={[
      {value: 'table', label: 'Table Data Asset'},
      {value: 'query', label: 'Query Data Asset'}
   ]}
>

<TabItem value="table" label="Table Data Asset">
5. Define your Table Data Asset's parameters.

   The following information is required when you create a Table Data Asset:

   - `name`: A name by which you can reference the Data Asset in the future. This should be unique within the Data Source.
   - `table_name`: The name of the SQL table that the Table Data Asset will retrieve records from.

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define table asset" 
   ```

6. Add the Data Asset to your Data Source. A new Data Asset is created and added to a Data Source simultaneously:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add table asset" 
   ```
</TabItem>

<TabItem value="query" label="Query Data Asset">
5. Define your Query Data Asset's parameters.

   The following information is required when you create a Query Data Asset:

   - `name`: A name by which you can reference the Data Asset in the future. This should be unique within the Data Source.
   - `query`: The SQL query that the Data Asset will retrieve records from.

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define query asset" 
   ```

6. Add the Data Asset to your Data Source. A new Data Asset is created and added to a Data Source simultaneously:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add query asset" 
   ```
</TabItem>

</Tabs>

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - full code example" 
```

</TabItem>

</Tabs>

## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)


## Limitations

Keep the following limitations in mind when working with BigQuery Data Sources.

- BigQuery Data Source connections cannot be edited in the GX Cloud UI. Use the GX Cloud API if you need to [edit the connection](/cloud/data_sources/manage_data_sources.md#edit-data-source-settings).
- BigQuery Data Assets cannot be added through the GX Cloud UI. Use the GX Cloud API to [add more Data Assets](/docs/cloud/data_assets/manage_data_assets.md?interface=api#add-a-data-asset-from-an-existing-data-source) from your BigQuery Data Source.
- [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai) is not supported.
- [Data Asset metrics](/cloud/data_assets/manage_data_assets.md#view-data-asset-metrics) are not supported.
- The [Data Health](/cloud/overview/data_health.md) dashboard entity filter cannot detect the Data Asset’s columns.
- Expectations for Anomaly Detection cannot be automatically generated. You can [manually configure Anomaly Detection](/docs/cloud/expectations/expectations_overview.md#anomaly-detection) by adding Expectations with Dynamic Parameters or forecasted ranges.
- Ad hoc Validations cannot be triggered through the GX Cloud UI. Use the API to [run an ad hoc Validation](/cloud/validations/run_validations.md).
- Recurring Validations cannot be scheduled in GX Cloud. Use an [orchestrator to run recurring Validations](/cloud/integrations/integrate_airflow.md).