---
sidebar_label: 'Connect GX Cloud to Microsoft SQL Server'
title: 'Connect GX Cloud to Microsoft SQL Server'
description: Connect GX Cloud to a Microsoft SQL Server Data Source.
hide_table_of_contents: true
---
   
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

To connect GX Cloud to data stored in Microsoft SQL Server, you can use the GX Cloud UI or the GX Cloud API.

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
     {value: 'ui', label: 'UI'},
     {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

## Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A Microsoft SQL Server database, schema, and table or view.
- Credentials that authorize read access to Microsoft SQL Server. You can use [SQL Server Authentication](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/create-a-login?view=sql-server-ver17) or [Entra ID](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-create-new-tenant).

## Connect to a Microsoft SQL Server Data Source and add a Data Asset

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset** > **New Data Source** > **Microsoft SQL Server**.
2. Enter a meaningful name for the Data Source in the **Data Source name** field.
3. Supply your connection details.

   - **Host**: Enter the environment where the Microsoft SQL Server engine is installed and running, for example `sql-server.example.com` for a self-hosted Microsoft SQL Server instance.
   - **Database**: Enter the name of the Microsoft SQL Server database where the data you want to validate is stored.
   - **Schema**: Enter the name of the Microsoft SQL Server schema where the data you want to validate is stored.
   - **Port**:  Enter the port configured for your Microsoft SQL Server instance, typically `1433`.
   - **Encrypt**: Select a TLS encryption protocol:
     - **Optional**: Establish an encrypted connection if your Microsoft SQL Server instance is configured to force encryption. Otherwise, establish an unencrypted connection.
     - **Mandatory**: Require the connection to be encrypted. Validate the server certificate unless **Trust server certificate** is checked. Connection will fail if your Microsoft SQL Server instance does not support TLS. If **Trust server certificate** is not checked, connection will fail if the certificate is not valid and publicly trusted.
     - **Strict**: Use TDS 8.0 where encryption begins before the TLS handshake. Require the connection to be encrypted and validate the server certificate. Connection will fail if your Microsoft SQL Server instance does not support TLS or the certificate is not valid and publicly trusted.
   - **Trust server certificate**: If you set **Encrypt** to **Mandatory**, you can select **Trust server certificate** to enable using an encrypted connection without a valid publicly trusted server certificate. This lets you, for example, use a self-signed certificate with an encrypted connection. 
   - **Driver**: If you are using an [agent-enabled deployment](/cloud/deploy/deployment_patterns.md) of GX Cloud, enter the name of the ODBC driver your environment uses to connect to Microsoft SQL Server. Common values include the following:
     - `ODBC Driver 18 for SQL Server`
     - `ODBC Driver 17 for SQL Server` 
     - `FreeTDS` 
   - **Authentication method**:  Select **SQL Server** or **Entra ID Service Principal**. Depending on your selection, the following credential fields will be required:
     - [SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/create-a-login?view=sql-server-ver17):
       - **Username**: Enter the username you use to access Microsoft SQL Server.
       - **Password**: Enter the password you use to access Microsoft SQL Server.
     - [Entra ID Service Principal](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-create-new-tenant):
       - **Tenant ID**: Enter the unique identifier for your organization's instance of Microsoft Entra ID.
       - **Client ID**: Enter the application ID for your new or existing app registration.
       - **Client secret**: Enter a new secret key from your app registration.

4. Click **Connect**.
5. Select one or more tables or views to import as Data Assets.
6. Click **Add x Asset(s)**.
7. Decide which [Anomaly Detection](/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema** and **Volume** anomalies. You can de-select recommendations you’d like to opt out of. You can choose to generate Expectations to detect **Completeness** anomalies.
8. Click **Start monitoring** or **Finish**.

</TabItem>

<TabItem value="api" label="API">

## Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A Microsoft SQL Server database, schema, and table or view.
- Credentials that authorize read access to Microsoft SQL Server. You can use [SQL Server Authentication](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/create-a-login?view=sql-server-ver17) or [Entra ID](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-create-new-tenant).
- [Python](https://www.python.org/downloads/) version 3.10 to 3.13.
- Recommended. A [Python virtual environment](https://docs.python.org/3/library/venv.html).

## Install GX Cloud 
Run the following terminal command to install the GX Cloud library with support for Microsoft SQL Server dependencies:

```bash title="Terminal input"
pip install 'great_expectations[sql-server]'
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

Environment variables securely store your GX Cloud and Microsoft SQL Server credentials.

1. Save your GX Cloud and Microsoft SQL Server credentials as environment variables by entering `export ENV_VAR_NAME=env_var_value` in the terminal or adding the command to your `~/.bashrc` or `~/.zshrc` file. For example:

   ```bash title="Terminal input"
   export GX_CLOUD_ACCESS_TOKEN=<user_access_token>
   export GX_CLOUD_ORGANIZATION_ID=<organization_id>
   export GX_CLOUD_WORKSPACE_ID=<workspace_id>
   export SQL_SERVER_USER=<username>
   export SQL_SERVER_PASSWORD=<password>
   ```

2. Optional. If you created a temporary file to record your credentials, delete it. 

## Connect a Microsoft SQL Server Data Source and add a Data Asset

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

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - get cloud context" 
   ```

   The Data Context will detect the previously set environment variables and connect to your GX Cloud account.

2. Define the Data Source's parameters.

   The following information is required when you create a Microsoft SQL Server Data Source:

   - `name`: A descriptive name used to reference the Data Source. This should be unique within your workspace.
   - `host`: The environment where the Microsoft SQL Server engine is installed and running, for example `sql-server.example.com` for a self-hosted Microsoft SQL Server instance.
   - `database`: The name of the Microsoft SQL Server database where the data you want to validate is stored.
   - `schema`: The name of the Microsoft SQL Server schema where the data you want to validate is stored.
   - `port`:  The port configured for your Microsoft SQL Server instance, typically `1433`.
   - `encrypt`: The TLS encryption protocol to use. Accepts the following:
     - `Optional`: Establish an encrypted connection if your Microsoft SQL Server instance is configured to force encryption. Otherwise, establish an unencrypted connection.
     - `Mandatory`: Require the connection to be encrypted. Validate the server certificate unless `trust_server_certificate` is set to `True`. Connection will fail if your Microsoft SQL Server instance does not support TLS. If `trust_server_certificate` is set to `False`, connection will fail if the certificate is not valid and publicly trusted.
     - `Strict`: Use TDS 8.0 where encryption begins before the TLS handshake. Require the connection to be encrypted and validate the server certificate. Connection will fail if your Microsoft SQL Server instance does not support TLS or the certificate is not valid and publicly trusted.
   - `trust_server_certificate`: If you set `encrypt` to `Mandatory`, you can set `trust_server_certificate` to `True` to enable using an encrypted connection without a valid publicly trusted server certificate (default is `False`). This lets you, for example, use a self-signed certificate with an encrypted connection. 
   - `driver`: If you are using an [agent-enabled deployment](/cloud/deploy/deployment_patterns.md) of GX Cloud, provide the name of the ODBC driver your environment uses to connect to Microsoft SQL Server. Common values include the following:
     - `ODBC Driver 18 for SQL Server`
     - `ODBC Driver 17 for SQL Server` 
     - `FreeTDS` 
   - `authentication`:  Accepts `SQL Server` or `Entra ID`. Depending on your selection, the following credential parameters will be required:
     - [SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/create-a-login?view=sql-server-ver17):
       - `username`: The username you use to access Microsoft SQL Server.
       - `password`: The password you use to access Microsoft SQL Server.
     - [Entra ID](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-create-new-tenant):
       - `tenant_id`: The unique identifier for your organization's instance of Microsoft Entra ID.
       - `client_id`: The application ID for your new or existing app registration.
       - `client_secret`: A new secret key from your app registration.

   Replace the variable values with your own and run the following Python code. In this example, the strings `"${SQL_SERVER_USER}"` and `"${SQL_SERVER_PASSWORD}"` will be replaced with the values of the environment variables you set earlier:

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - define source" 
   ```

3. Add a Microsoft SQL Server Data Source to your Data Context by executing the following code: 

   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - add source" 
   ```

4. Decide whether you want to validate the records in a single table or the records returned by a SQL query.

   - To validate the records in a single table, you will create a Table Data Asset.
   - To validate the records returned by a SQL query, you will create a Query Data Asset. Note that [Query Data Assets have some limitations](/cloud/data_assets/manage_data_assets.md#data-asset-options-for-sql-data-sources) compared to Table Data Assets.
<br />

<Tabs
   queryString="asset"
   defaultValue="table"
   values={[
     {value: 'table', label: 'Table Data Asset'},
     {value: 'query', label: 'Query Data Asset'}
   ]}
>

<TabItem value="table" label="Table Data Asset">

5. Define your Table Data Asset's parameters.

   The following information is required when you create a Microsoft SQL Server Table Data Asset:

   - `name`: A name by which you can reference the Data Asset in the future. This should be unique within the Data Source.
   - `table_name`: The name of the SQL table that the Table Data Asset will retrieve records from.
   
   
   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - define table data asset" 
   ```

 6. Add the Data Asset to your Data Source. A new Data Asset is created and added to a Data Source simultaneously.
 

      ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - add table data asset" 
      ```


</TabItem>

<TabItem value="query" label="Query Data Asset">

5. Define your Query Data Asset's parameters.

   The following information is required when you create a Microsoft SQL Server Query Data Asset:

   - `name`: A name by which you can reference the Data Asset in the future. This should be unique within the Data Source.
   - `query`: The SQL query that the Data Asset will retrieve records from.
   
   
   ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - define query data asset"
   ```

 6. Add the Data Asset to your Data Source. A new Data Asset is created and added to a Data Source simultaneously.
 
 
      ```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - add query data asset" 
      ```


</TabItem>

</Tabs>

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - full code example" 
```
</TabItem>

</Tabs>

</TabItem>

</Tabs>

## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)
