import GxData from '../../_core_components/_data.jsx'
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

import EnvironmentVariables from './_environment_variables.md';
import ConfigYml from './_config_yml.md';
import AccessCredentials from './_access_credentials.md'



To connect GX Core to your SQL data, you will need your connection details and corresponding credentials. Because your connection details and credentials provide access to your data they should be stored securely outside of version control.  GX Core allows you to securely store credentials and connection details as environment variables or in an uncommitted config file.  These variables are then accessed through string substitution in your version controlled code.

### Prerequisites

- The ability to set environment variables or a File Data Context.

GX Core also supports referencing credentials that have been stored in the AWS Secrets Manager, Google Cloud Secret Manager, and Azure Key Vault secrets managers.  To set up GX Core to access one of these secrets managers you will additionally require:

- The ability to install Python modules with `pip`.

### Procedure

1. Determine the format for your connection details.

   Different types of SQL databases have different formats for their connection details. Most Data Sources use a source-specific consolidated `connection_string` to provide all connection details, while Snowflake uses separate input parameters. In the following table, the text in `<>` corresponds to the values specific to your credentials and connection details.

   :::warning Snowflake password authentication is deprecated
   Snowflake has deprecated password authentication and will remove support for it entirely in the future. Set up new Data Sources with key-pair authentication. If you have older Snowflake Data Sources using password authentication, update them to use key-pair authentication. For more information about the deprecation, see [Snowflake's documentation](https://docs.snowflake.com/en/user-guide/security-mfa-rollout).
   :::

   | Database type   | Connection string                                                                                                                                                |
   |-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
   | BigQuery SQL    | `bigquery://<GCP_PROJECT>/<BIGQUERY_DATASET>?credentials_path=/path/to/your/credentials.json`                                                                    |
   | Databricks SQL  | `databricks://token:<TOKEN>@<HOST>:<PORT>?http_path=<HTTP_PATH>&catalog=<CATALOG>&schema=<SCHEMA>`                                                               |
   | PostgreSQL      | `postgresql+psycopg2://<USER_NAME>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>`                                                                                          |
   | Redshift        | `redshift+psycopg2://<USER_NAME>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>?sslmode=<SSLMODE>`                                                                          |
   | SQLite          | `sqlite:///<PATH_TO_DB_FILE>`                                                                                                                                    |

   Other connection string formats are valid provided they are for a SQL database that is supported by SQLAlchemy.  You can find more information on the dialects supported by `SQLAlchemy` on their [dialects](https://docs.sqlalchemy.org/en/20/dialects/index.html) page.

   To connect to Snowflake, you will need supply the following connection details and credentials:

   - `account`: Your Snowflake organization and account name separated by a hyphen (`oraganizationname-accountname`) or your account name and a legacy account locator separated by a period (`accountname.region`). The legacy account locator value must include the geographical region. For example, `us-east-1`. 
    
   To locate your Snowflake organization name, account name, or legacy account locator values see [Finding the Organization and Account Name for an Account](https://docs.snowflake.com/en/user-guide/admin-account-identifier#finding-the-organization-and-account-name-for-an-account) or [Using an Account Locator as an Identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier#using-an-account-locator-as-an-identifier).
    
   - `user`: The username you use to access Snowflake.

   - `database`: The name of the Snowflake database where the data you want to validate is stored. In Snowsight, click **Data** > **Databases**. In the Snowflake Classic Console, click **Databases**.
 
   - `schema`: the name of the Snowflake schema where the data you want to validate is stored.

   - `warehouse`: the name of your Snowflake database warehouse. In Snowsight, click **Admin** > **Warehouses**. In the Snowflake Classic Console, click **Warehouses**.

   - `role`: Your Snowflake role.

   - `private_key`: Your RSA private key value. Do not include the start and end markers `-----BEGIN ENCRYPTED PRIVATE KEY-----` and `-----END ENCRYPTED PRIVATE KEY-----`.

2. Store the credentials required for your connection.

   GX supports the following methods of securely storing credentials.  Chose one to implement for your connection:

   <Tabs queryString="storage_type" groupId="storage_type" defaultValue='environment_variables' values={[{label: 'Environment Variables', value:'environment_variables'}, {label: 'config.yml', value:'config_yml'}, {label: 'Key pair (Snowflake only)', value:'key_pair'}]}>

   <TabItem value="environment_variables">
      <EnvironmentVariables/>
   </TabItem>

   <TabItem value="config_yml">
      <ConfigYml/>
   </TabItem>

   <TabItem value="key_pair">
   Follow Snowflake's docs to [configure and store the private and public keys](https://docs.snowflake.com/en/user-guide/key-pair-auth). 
   </TabItem>

   </Tabs>

3. Access your credentials in Python strings.

   <Tabs className="hidden" queryString="storage_typet" groupId="storage_type" defaultValue='environment_variables'>

      <TabItem value="environment_variables">
         <AccessCredentials/>
      </TabItem>

      <TabItem value="config_yml">
         <AccessCredentials/>
      </TabItem>

      <TabItem value="key_pair">
      
      Here's an example of how to access your Snowflake private key in Python.

      ```python title="Python"
      import pathlib

      from cryptography.hazmat.backends import default_backend
      from cryptography.hazmat.primitives import serialization

      PRIVATE_KEY_FILE = pathlib.Path("path/to/my/rsa_key.p8").resolve(strict=True)

      p_key = serialization.load_pem_private_key(
              PRIVATE_KEY_FILE.read_bytes(),
              password=b"my_password",
              backend=default_backend()
          )

      pkb = p_key.private_bytes(
          encoding=serialization.Encoding.DER,
          format=serialization.PrivateFormat.PKCS8,
          encryption_algorithm=serialization.NoEncryption())

      connect_args = {"private_key": pkb}
      ```
      </TabItem>

   </Tabs>

4. Optional. Access credentials stored in a secret manager.

   GX Core supports the AWS Secrets Manager, Google Cloud Secret Manager, and Azure Key Vault secrets managers.  For more information on how to set up string substitutions that pull credentials from these sources, see [Access secrets managers](core/configure_project_settings/access_secrets_managers/access_secrets_managers.md).