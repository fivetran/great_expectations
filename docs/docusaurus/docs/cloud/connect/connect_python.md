---
sidebar_label: 'Connect to GX Cloud with Python'
title: 'Connect to GX Cloud with Python'
id: connect_python
description: Connect to a GX Cloud account and validate data from a Python script.
---

Learn how to use GX Cloud from a Python script or interpreter, such as a Jupyter Notebook. You'll install Great Expectations, configure your GX Cloud environment variables, connect to sample data, build your first Expectation, validate data, and review the validation results through Python code.

## Prerequisites

- You have internet access and download permissions.
- You have a GX Cloud user with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.

## Prepare your environment

1. Download and install [Python](https://www.python.org/downloads/). GX supports Python versions 3.9 to 3.13.

2. Download and install pip. See the [pip documentation](https://pip.pypa.io/en/stable/cli/pip/).


## Install GX

1. Run the following command in an empty base directory inside a Python virtual environment:

    ```bash title="Terminal input"
    pip install great_expectations
    ```

    It can take several minutes for the installation to complete.

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

Environment variables securely store your GX Cloud access credentials.

1. Save your credentials as **GX_CLOUD_ACCESS_TOKEN**, **GX_CLOUD_ORGANIZATION_ID**, and **GX_CLOUD_WORKSPACE_ID** environment variables by entering `export ENV_VAR_NAME=env_var_value` in the terminal or adding the command to your `~/.bashrc` or `~/.zshrc` file. For example:

    ```bash title="Terminal input"
    export GX_CLOUD_ACCESS_TOKEN=<user_access_token>
    export GX_CLOUD_ORGANIZATION_ID=<organization_id>
    export GX_CLOUD_WORKSPACE_ID=<workspace_id>
    ```

    :::note Note
   After you save your credentials as environment variables, you can use Python scripts to access GX Cloud and complete other tasks. See the [API reference](/reference/index.md).
    :::

2. Optional. If you created a temporary file to record your credentials, delete it. 

## Create a Data Context

1. Run the following Python code to create a Data Context object:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_python.py - get cloud context"
   ```
   
   The Data Context will detect the previously set environment variables and connect to your GX Cloud account.

   If you are a member of multiple [workspaces](/cloud/access/manage_access.md#workspaces), note that you can pass a workspace ID in the `get_context` call to override the workspace ID set in your environment variables.
   
2. Optional. Verify that you have a GX Cloud Data Context:

    ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_python.py - verify context type"
    ```

## Connect to a Data Asset

:::tip Working with Data Sources

The Data Context you created includes a built-in `pandas_default` Data Source. This Data Source gives access to all of the `read_*(...)` methods available in pandas. This allows you to connect to a pandas Data Asset without adding your own Data Source first as demonstrated in this section.

Cloud API instructions for connecting to other Data Sources such as Azure Blob Storage, Google Cloud Storage, BigQuery, and Spark are under construction. In the meantime, you can refer to the [GX Core docs](/docs/core/connect_to_data/connect_to_data.md) for guidance as the Cloud API uses the same methods for connecting Data Sources.
:::

- Run the following Python code to connect to existing `.csv` data stored in the `great_expectations` GitHub repository and create a Validator object:

    ```python title="Python" name="tutorials/quickstart/quickstart.py connect_to_data"
    ```

    The code example uses the default Data Source for Pandas to access the `.csv` data from the file at the specified URL path.

    Alternatively, if you have already configured your data in GX Cloud you can use it instead.  To see your available Data Sources, run:

    ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_python.py - list data sources"
    ```
  
    Using the printed information, you can get the name of one of your existing Data Sources, one of its Data Assets, and the name of a Batch Definition on the Data Asset.  Then, you can retrieve a Batch of data by updating the values for `data_source_name`, `asset_name`, and `batch_definition_name` in the following code and executing it:

    ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_python.py - retrieve a data asset"
    ```

## Create Expectations

- Run the following Python code to create two Expectations and save them to the Expectation Suite:

    ```python title="Python" name="tutorials/quickstart/quickstart.py create_expectation"
    ```

  The first Expectation uses domain knowledge (the `pickup_datetime` shouldn't be null).

  The second Expectation uses explicit kwargs along with the `passenger_count` column. 

## Validate data

1. Run the following Python code to examine the data and determine if it matches the defined Expectations. This will return Validation Results:

    ```python title="Python" name="tutorials/quickstart/quickstart.py run_checkpoint"
    ```

2. Run the following Python code to view a JSON representation of the Validation Results in the generated Data Docs:

    ```python title="Python" name="tutorials/quickstart/quickstart.py view_results"
    ```
