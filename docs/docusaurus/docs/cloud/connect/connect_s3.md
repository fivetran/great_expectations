---
sidebar_label: 'Connect GX Cloud to Amazon S3'
title: 'Connect GX Cloud to Amazon S3'
description: Add an Amazon S3 Data Source in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To connect GX Cloud to filesystem data stored in Amazon S3, use the GX Cloud API.

## Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- AWS credentials with read access to a data file on an S3 bucket.
- [Python](https://www.python.org/downloads/) version 3.10 to 3.13.
- Recommended. A [Python virtual environment](https://docs.python.org/3/library/venv.html).


## Install GX Cloud

Run the following terminal command to install the GX Cloud library with support for Amazon S3 dependencies:

```bash title="Terminal input"
pip install 'great_expectations[s3]'
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

Environment variables securely store your GX Cloud and AWS credentials.

1. Save your GX Cloud and AWS credentials as environment variables by entering `export ENV_VAR_NAME=env_var_value` in the terminal or adding the command to your `~/.bashrc` or `~/.zshrc` file. For example:

    ```bash title="Terminal input"
    export GX_CLOUD_ACCESS_TOKEN=<user_access_token>
    export GX_CLOUD_ORGANIZATION_ID=<organization_id>
    export GX_CLOUD_WORKSPACE_ID=<workspace_id>
    export S3_KEY_ID=<key_id>
    export S3_SECRET_KEY=<secret_key>
    ```

2. Optional. If you created a temporary file to record your credentials, delete it. 

## Connect an Amazon S3 Data Source and add a Data Asset

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


   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - get cloud context" 
   ```
   
   The Data Context will detect the previously set environment variables and connect to your GX Cloud account.

2. Verify that you have a GX Cloud Data Context:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - verify context type" 
   ```

3. Define the Data Source's parameters.
   
   The following information is required when you create an Amazon S3 Data Source:

   - `name`: A descriptive name used to reference the Data Source. This should be unique within your workspace.
   - `bucket`: The Amazon S3 bucket name.
   - `boto3_options`: Your AWS credentials passed as `aws_access_key_id` and `aws_secret_access_key`.
     
   Replace the `data_source_name` and `bucket_name` variable values with your own and run the following Python code. In this example, the strings `"${S3_KEY_ID}"` and `"${S3_SECRET_KEY}"` will be replaced with the values of the environment variables you set earlier:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - define source" 
   ```


4. Add an S3 Data Source to your Data Context by executing the following code:
   
   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - add source" 
   ```
   
   GX Cloud uses pandas as the backend for your S3 Data Source.  

5. Define your Data Asset's parameters.
   
   The following information is required when you create an Amazon S3 Data Asset:

   - `name`: A name by which you can reference the Data Asset in the future. This should be unique within the Data Source.
   - `s3_prefix`: The path to the folder containing the data file for the Data Asset, relative to the root of the S3 bucket.
   
   With S3 Data Sources, Data Assets are used to retrieve data from individual files in formats such as `.csv` or `.parquet`. The file format that can be read by an S3 Data Asset is determined when the Data Asset is created. 

   This example uses taxi trip data stored in a `.csv` file in the `data/taxi_yellow_tripdata/` folder within the Data Source’s S3 bucket.

   Replace the variable values with your own and run the following Python code to define your Data Asset's parameters:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - define asset" 
   ```

6. Add the Data Asset to your Data Source.

   A new Data Asset is created and added to a Data Source simultaneously. The file format that the Data Asset can read is determined by the method used when the Data Asset is added to the Data Source. To see the file formats supported by an S3 Data Source, refer to the `.add_*_asset(...)` methods in the [PandasFilesystemDatasource reference page](/reference/api/datasource/fluent/PandasFilesystemDatasource_class.mdx).

   The following example creates a Data Asset that can read `.csv` file data:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - add asset" 
   ```

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_s3.py - full code example" 
```

</TabItem>

</Tabs>

## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)

## Limitations

Keep the following limitations in mind when working with S3 Data Sources.

- S3 Data Source connections cannot be edited in the GX Cloud UI. Use the GX Cloud API if you need to [edit the connection](/cloud/data_sources/manage_data_sources.md#edit-data-source-settings).
- S3 Data Assets cannot be added through the GX Cloud UI. Use the GX Cloud API to [add more Data Assets](/docs/cloud/data_assets/manage_data_assets.md?interface=api#add-a-data-asset-from-an-existing-data-source) from your S3 Data Source.
- When you add an S3 Data Asset, Expectations for Anomaly Detection are not automatically generated. You can [generate Anomaly Detection Expectations](/docs/cloud/expectations/manage_expectations#create-an-expectation) after the Data Asset is created.
- ExpectAI is not supported.
- Data Asset metrics are not automatically fetched. You can [manually profile data](/docs/cloud/data_assets/manage_data_assets.md#view-data-asset-metrics) to return all available metrics for an S3 Data Asset.
- Custom SQL and multi-source Expectations are not supported.

