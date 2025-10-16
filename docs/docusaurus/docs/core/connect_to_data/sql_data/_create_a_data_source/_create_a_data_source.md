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

2. Define a name and connection details for your Data Source.

   You can assign any name to a Data Source as long as it is unique within your Data Context.

   Your connection details and credentials should not be saved in plain text in your code.  Instead, you should reference securely stored values through string substitution.  The guidance on how to [Configure your credentials](#configure-credentials) covers how to determine the format of your connection details, securely store your connection details and credentials, and how to reference the stored values in Python.

   The following code defines a Data Source name and references a PostgreSQL connection string that has been securely stored in its entirety:

    ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py name and connection string"
   ```

3. Create a Data Source.
   
   GX Core provides specific methods for creating Data Sources that correspond to supported SQL dialects.  All of these methods are accessible from the `data_sources` attribute of your Data Context.  Reference the following table to determine the method used for your data's SQL dialect:

   <DatasourceMethodReferenceTable/>

   Once you have the method for your data's SQL dialect, you can call it with the previously defined Data Source name and connection details to create your Data Source.
   
   The following example creates a PostgreSQL Data Source using a connection string. This is the pattern most Data Sources follow:

   ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py create data source"
   ```

   Here is an example of creating a Snowflake Data Source using separate parameters for each connection detail and credential.

   ```python title="Python"
   datasource_name = "my_new_snowflake_datasource"
   account = "accountname.region"
   user = "my_user"
   database = "my_db"
   schema = "my_schema"
   warehouse = "my_wh"
   role = "my_role"
   private_key = "my_private_key"

   data_source = context.data_sources.add_snowflake(
      name=datasource_name,
      account=account,
      user=user,
      database=database,
      schema=schema,
      warehouse=warehouse,
      role=role,
      private_key=private_key
   }
   )
   ```


4. Optional. Verify the Data Source is connected:

   ```python title="Python" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py verify data source"
   ```
   
   The details of your Data Source are retrieved from the Data Context and displayed.

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Sample code" name="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py full sample code"
```

</TabItem>

</Tabs>