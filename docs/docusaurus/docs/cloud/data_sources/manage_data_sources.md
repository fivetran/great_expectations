---
sidebar_label: 'Manage Data Sources'
title: 'Manage Data Sources'
description: Manage data connections in GX Cloud.
toc_max_heading_level: 2
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

A Data Source is an object that tells GX Cloud how to connect to a specific location of data and provides an entry point for organizing that data into Data Assets, which can be validated. Visit the [compatibility reference](/docs/help/compatibility_reference) for a full list of supported Data Sources. Contact us to [request support for additional sources](mailto:sales@greatexpectations.io).

## Workflow and feature support


Depending on your Data Source, GX Cloud supports both no-code UI workflows and programmatic API workflows as indicated in the table below.

| Workflow                                                             | Databricks SQL<br/>Microsoft Fabric<br/>Microsoft SQL Server<br/>PostgreSQL and its derivatives *<br/>Redshift<br/>Snowflake |Trino      | Amazon S3 | Azure Blob Storage<br/>BigQuery<br/>Google Cloud Storage<br/>Pandas<br/>Spark |
|:---------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------|:----------|:----------|:------------------------------------------------------------------------------|
| [Create Data Source](/docs/cloud/connect/connect_lp.md)              | UI / API                                                                                                                     | API       | API       | API                                                                           |
| [Edit Data Source configuration](#edit-data-source-settings)         | UI / API                                                                                                                     | API       | API       | API                                                                           |
| [Add Data Assets](/docs/cloud/data_assets/manage_data_assets.md)     | UI / API                                                                                                                     | API       | API       | API                                                                           |
| [Define Batches](/docs/cloud/validations/run_validations.md)         | UI / API                                                                                                                     | UI / API  | API       | API                                                                           |
| [Run ad hoc Validations](/docs/cloud/validations/run_validations.md) | UI / API                                                                                                                     | UI / API  | UI / API  | API                                                                           |

Some UI-only features are not supported for some Data Sources. Consult the table below to learn more about UI-only feature support for individual sources and, where available, workarounds.

| Feature                                                                                                                                    | Databricks SQL<br/>Microsoft Fabric<br/>Microsoft SQL Server<br/>PostgreSQL and its derivatives *<br/>Redshift<br/>Snowflake | Amazon S3<br/>Trino                         | Azure Blob Storage<br/>BigQuery<br/>Google Cloud Storage<br/>Pandas<br/>Spark | Workaround for unsupported Data Sources                                                              |
|:-------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------|:------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Data Asset metrics](/docs/cloud/data_assets/manage_data_assets.md#view-data-asset-metrics)                                                | <span role="img" aria-label="Yes">✅</span>                                                                                  | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span>                                   | None                                                                                                                                                                           |
| [Column filter](/docs/cloud/overview/data_health#filters) on Data Health dashboard                                                         | <span role="img" aria-label="Yes">✅</span>                                                                                  | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span>                                   | None                                                                                                                                                                           |
| [Generate Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) Expectations when adding a Data Asset   | <span role="img" aria-label="Yes">✅</span>                                                                                  | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span>                                   |[Manually configure Anomaly Detection](/docs/cloud/expectations/expectations_overview.md#anomaly-detection) by adding Expectations with Dynamic Parameters or forecasted ranges |
| [Generate Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) Expectations when adding an Expectation | <span role="img" aria-label="Yes">✅</span>                                                                                  | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span>                                   |[Manually configure Anomaly Detection](/docs/cloud/expectations/expectations_overview.md#anomaly-detection) by adding Expectations with Dynamic Parameters or forecasted ranges |
| [ExpectAI](/docs/cloud/overview/accelerating_test_coverage.md#expectai)                                                                    | <span role="img" aria-label="Yes">✅</span>                                                                                  | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span>                                   | None                                                                                                                                                                           |
| [Schedule recurring Validations](/docs/cloud/schedules/manage_schedules.md)                                                                | <span role="img" aria-label="Yes">✅</span>                                                                                  | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span>                                   |[Use an orchestrator](/docs/reference/learn/integrations/data_pipeline_tutorial) to run recurring Validations                                                                   |

\* AlloyDB, Amazon Aurora PostgreSQL, Citus, and Neon are PostgreSQL-derived systems and have the same support in GX Cloud as PostgreSQL.

:::note Limitations for Query Data Assets
Most SQL Data Sources support validating the records in a single table (as a Table Data Asset) or the records returned by a SQL query (as a Query Data Asset). The tables above reflect GX Cloud support for Table Data Assets.  Note that [Query Data Assets have some limitations](/cloud/data_assets/manage_data_assets.md#data-asset-options-for-sql-data-sources) compared to Table Data Assets.
:::

## Edit Data Source settings

You can use the GX Cloud UI to edit settings for Databricks SQL, Microsoft Fabric, Microsoft SQL Server, PostgreSQL, Redshift, and Snowflake Data Sources. You can use the GX Cloud API to edit settings for any Data Source. 

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

When editing a Data Source in the GX Cloud UI, you can change the name and connection details.

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- A Databricks SQL, Microsoft Fabric, Microsoft SQL Server, PostgreSQL, Redshift, or Snowflake [Data Source](/docs/cloud/connect/connect_lp).

### Procedure

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. Click **Manage Data Sources**.

3. Click **Edit Data Source** for the Data Source you want to edit.

4. Edit the configuration as needed. Available fields vary by source type. For details, refer to the instructions for [connecting GX Cloud](/docs/cloud/connect/connect_lp.md) to your source type.

5. Click **Save**.

</TabItem>

<TabItem value="api" label="API">

When editing a Data Source with the GX Cloud API, you can change the connection details but not the name.

### Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
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

1. Run the following Python code to create a Data Context object. 

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - get cloud context" 	
   ```

   
   The Data Context will detect the previously set environment variables and connect to your GX Cloud account.


2. Get a Data Source to update.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - get source" 	
   ```    

3. Define updates for one or more of the Data Source's parameters.

   Available fields vary by source type. For details, refer to the instructions for [connecting GX Cloud](/docs/cloud/connect/connect_lp.md) to your source type.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - define source updates" 	
   ``` 

4. Update the Data Source. 

   There is a `context.data_sources.update_*` method for each type of Data Source. These mirror the names of the `context.data_sources.add_*` methods for adding Data Sources. This example shows how to update an S3 Data Source with the `update_pandas_s3` method.

   ```python title="Python" name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - update source" 	
   ```   
</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/data_sources/manage_data_sources.py - full sample" 	
```

</TabItem>

</Tabs>


</TabItem>

</Tabs>

## Data Source credential management
Options for managing credentials depend on whether you are connecting a Data Source in the GX Cloud UI or through the GX Cloud API.

<Tabs 
   queryString="interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

Depending on your [deployment pattern](/docs/cloud/deploy/deployment_patterns), you have the following options for managing credentials for Data Sources connected through the GX Cloud UI.

-  **Direct input** is supported for all GX Cloud deployment patterns. You can input credentials directly into the GX Cloud UI. These credentials are stored in GX Cloud and securely encrypted at rest and in transit. 

- **Environment variable substitution** is supported for agent-enabled deployments and Cloud API calls. To enhance security, you can use environment variables to manage sensitive connection parameters or strings. For example, instead of directly including your database password in configuration settings, you can use a variable reference like `${MY_DATABASE_PASSWORD}`. When using environment variable substitution, your credentials are not stored or transmitted to GX Cloud. 

To use environment variable substitution, do the following:

1. Inject the variable into your GX Agent container or environment. 
   
   When running the GX Agent Docker container, include the environment variable in the command. For example:
   
   ```bash title="Terminal input"
   docker run -it -e MY_DATABASE_PASSWORD=<YOUR_DATABASE_PASSWORD> -e GX_CLOUD_ACCESS_TOKEN=<YOUR_ACCESS_TOKEN> -e GX_CLOUD_ORGANIZATION_ID=<YOUR_ORGANIZATION_ID> greatexpectations/agent:stable
   ```

   When running the GX Agent in another container-based service, including Kubernetes, ECS, ACI, and GCE, use the service's instructions to set and provide environment variables to the running container.

   When using environment variable substitution with the GX Cloud API, set the environment variable in the environment where the GX Cloud API Python client is running.

2. In the Data Source setup form in the GX Cloud UI, enter the name of your environment variable, enclosed in `${}`. For example, `${MY_DATABASE_PASSWORD}`.

</TabItem>

<TabItem value="api" label="API">

Credentials you use with the GX Cloud API should be stored securely outside of version control. Whether they are connection strings for your Data Sources or tokens for Actions with third-party apps such as Slack, credentials used with the GX Cloud API can be supplied with string substitution. Do the following to store any type of credential as an environment variable on a local system and then reference it by variable name in your version-controlled code: 

1. Assign the credentials to environment variables.

   Save your credentials as environment variables by entering `export ENV_VAR_NAME=env_var_value` in the terminal or adding the command to your `~/.bashrc` or `~/.zshrc` file. If you use the `export` command from the terminal, the environment variables will not persist beyond the current session.  However, if you add them to your shell config file (`~/.bashrc` for Bash, `~./zshrc` for Z Shell), the variables will be exported each time you log in.

    You can export credentials as individual components or as a complete Data Source connection string.  For example:

    ```bash title="Terminal, ~/.bashrc, or ~/.zshrc"
    export MY_POSTGRES_USERNAME=<USERNAME>
    export MY_POSTGRES_PASSWORD=<PASSWORD>
    ```

    or:

    ```bash title="Terminal or ~/.bashrc"
    export POSTGRES_CONNECTION_STRING=postgresql+psycopg2://<USERNAME>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>
    ```

    You can also reference your stored credentials within a stored connection string by wrapping their corresponding variable in `${` and `}`. For example:

    ```bash title="Terminal or ~/.bashrc"
    export MY_POSTGRES_USERNAME=<USERNAME>
    export MY_POSTGRES_PASSWORD=<PASSWORD>
    export POSTGRES_CONNECTION_STRING=postgresql+psycopg2://${MY_POSTGRES_USERNAME}:${MY_POSTGRES_PASSWORD}@<HOST>:<PORT>/<DATABASE>
    ```

    Because the dollar sign character `$` is used to indicate the start of a string substitution, it should be escaped using a backslash `\` if it is part of your credentials. For example, if your password is `pa$$word`, then in the previous examples you would use the command:

    ```bash title="Terminal or ~/.bashrc"
    export MY_POSTGRES_PASSWORD=pa\$\$word
    ```

2. Use your environment variables in your Python code.

   To use securely stored credentials, reference the variable names they are assigned to wrapped in `${` and `}`.
   
   You can combine individual components into a connection string:

   ```python title="Python"
   my_connection_string="postgresql+psycopg2://${MY_POSTGRES_USERNAME}:${MY_POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE}",
   ```

   Or you can reference a complete string:

   ```python title="Python"
   my_connection_string = "${POSTGRESQL_CONNECTION_STRING}"
   ```

   When you pass the GX Cloud API a parameter that references your environment variables, GX Cloud will use the corresponding stored values.

  </TabItem>

</Tabs>
