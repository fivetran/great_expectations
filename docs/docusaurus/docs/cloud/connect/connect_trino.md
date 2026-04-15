---
sidebar_label: 'Connect GX Cloud to Trino'
title: 'Connect GX Cloud to Trino'
description: Add a Trino Data Source in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To connect GX Cloud to data stored in Trino, use the GX Cloud API.

## Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A Trino catalog with a schema that has a table or view.
- [Python](https://www.python.org/downloads/) version 3.10 to 3.13.
- Recommended. A [Python virtual environment](https://docs.python.org/3/library/venv.html).


## Install GX Cloud

Run the following terminal command to install the GX Cloud library with support for Trino dependencies:

```bash title="Terminal input"
pip install 'great_expectations[trino]'
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

## Connect a Trino Data Source and add a Data Asset

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

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_trino.py - get cloud context" 
   ```

   The Data Context will detect the previously set environment variables and connect to your GX Cloud account.


2. Define the Data Source's parameters.

   The following information is required when you create a Trino Data Source:

   - `name`: A descriptive name used to reference the Data Source. This should be unique within your workspace.
   - `connection_string`: The connection string used to connect to the database. The format for this is `trino://<USER>:@<HOST>:<PORT>/<CATALOG>/<DATABASE>`.

   Replace the variable values with your own and run the following Python code:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_trino.py - define source" 
   ```

3. Add a Trino Data Source to your Data Context by executing the following code:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_trino.py - add source" 
   ```

4. Define your Data Asset's parameters.

   The following information is required when you create a Trino Data Asset:

   - `name`: A name by which you can reference the Data Asset in the future. This should be unique within the Data Source.
   - `table_name`: The name of the SQL table that the Data Asset will retrieve records from.

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_trino.py - define asset" 
   ```


5. Add the Data Asset to your Data Source. A new Data Asset is created and added to a Data Source simultaneously:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_trino.py - add asset" 
   ```

</TabItem>


<TabItem value="sample_code" label="Sample code">
```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_trino.py - full code example" 
```

</TabItem>

</Tabs>

## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)


## Limitations

Keep the following limitations in mind when working with Trino Data Sources.

- Trino Data Source connections cannot be edited in the GX Cloud UI. Use the GX Cloud API if you need to [edit the connection](/cloud/data_sources/manage_data_sources.md#edit-data-source-settings).
- Trino Data Assets cannot be added through the GX Cloud UI. Use the GX Cloud API to [add more Data Assets](/docs/cloud/data_assets/manage_data_assets.md?interface=api#add-a-data-asset-from-an-existing-data-source) from your Trino Data Source.
- Only Table Data Assets are supported. You cannot make a [Query Data Asset](/cloud/data_assets/manage_data_assets.md#data-asset-options-for-sql-data-sources) with a Trino Data Source.
- [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai) is not supported.
- Data Asset metrics are not automatically fetched. You can [manually profile data](/docs/cloud/data_assets/manage_data_assets.md#view-data-asset-metrics) to return all available metrics for a Trino Data Asset.
- When you add a Trino Data Asset, Expectations for Anomaly Detection are not automatically generated. You can [generate Anomaly Detection Expectations](/docs/cloud/expectations/manage_expectations.md#create-an-expectation) after the Data Asset is created and profiled.