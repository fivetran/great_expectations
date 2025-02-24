import Tabs from '@theme/Tabs'
import TabItem from '@theme/TabItem'

import GxData from '../../../_core_components/_data.jsx'
import PreReqPython from '../../../_core_components/prerequisites/_python_installation.md'
import PreReqGxInstalledWithSqlDependecies from '../../../_core_components/prerequisites/_gx_installation_with_sql_dependencies.md'
import PreReqDataContext from '../../../_core_components/prerequisites/_preconfigured_data_context.md'
import PreReqCredentials from '../../../_core_components/prerequisites/_securely_configured_credentials.md'

import DatasourceMethodReferenceTable from './_datasource_method_reference_table.md'

### Prerequisites {#prerequisites-data-source}
- <PreReqPython/>.
- <PreReqGxInstalledWithSqlDependecies/>
- <PreReqDataContext/>.
- <PreReqCredentials/>.

### Procedure {#procedure-data-source}

<Tabs 
   queryString="procedure"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

1. Import GX and instantiate a Data Context:

   ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py imports"
   ```

2. Define a name and connection string for your Data Source.

   You can assign any name to a Data Source as long as it is unique within your Data Context.

   Your connection string or credentials should not be saved in plain text in your code.  Instead, you should reference a securely stored connection string or credentials through string substitution.  The guidance on how to [Configure your credentials](#configure-credentials) covers how to determine the format of your connection string, securely store your connection string or credentials, and how to reference your connection string or credentials in Python.

   The following code defines a Data Source name and references a PostgreSQL connection string that has been securely stored in its entirety:

    ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py name and connection string"
   ```

3. Create a Data Source.
   
   GX Core provides specific methods for creating Data Sources that correspond to supported SQL dialects.  All of these methods are accessible from the `data_sources` attribute of your Data Context.  Reference the following table to determine the method used for your data's SQL dialect:

   <DatasourceMethodReferenceTable/>

   Once you have the method for your data's SQL dialect, you can call it with the previously defined Data Source name and connection string to create your Data Source.  The following example creates a PostgreSQL Data Source:

   ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py create data source"
   ```
4. Optional. If you're connecting to Snowflake and want to use key-pair authentication instead of a password, pass the private key with `kwargs`. Note that a placeholder password is still required to pass the configuration validation, but the password will not be used if a `private_key` is provided.

   ```python title="Python"
   # For details on how to access your private key, refer to "Configure credentials" above 
   connect_args = {"private_key": pkb} 

   connection_details={
      "account": "accountname.region",
      "user": "my_user",
      "role": "my_role",
      "password": "placeholder_value", # must be provided to pass validation but will be ignored
      "warehouse": "my_wh",
      "database": "my_db",
      "schema": "my_schema"
   }

   data_source = context.data_sources.add_snowflake(
      name=datasource_name,
      connection_string=connection_details,
      kwargs={"connect_args": connect_args}
   )
   ```
   
   :::warning Private key serialized in File Data Context
   If you're using a [File Data Context](/core/set_up_a_gx_environment/create_a_data_context.md), `kwargs` will be serialized to `great_expectations.yml`, including the private key.
   :::


5. Optional. Verify the Data Source is connected:

   ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py verify data source"
   ```
   
   The details of your Data Source are retrieved from the Data Context and displayed.

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Sample code" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py full sample code"
```

</TabItem>

</Tabs>