import ConnectionStringTable from './_connection_string_reference_table.mdx';

Different types of SQL databases have different formats for their connection details. Most Data Sources use a source-specific consolidated `connection_string` to provide all connection details, while Snowflake uses separate input parameters. In the following table, the text in `<>` corresponds to the values specific to your credentials and connection details.

   :::warning Snowflake password authentication is deprecated
   Snowflake has deprecated password authentication and will remove support for it entirely in the future. Set up new Data Sources with key-pair authentication. If you have older Snowflake Data Sources using password authentication, update them to use key-pair authentication. For more information about the deprecation, see [Snowflake's documentation](https://docs.snowflake.com/en/user-guide/security-mfa-rollout).
   :::

   <ConnectionStringTable/>

   Other connection string formats are valid provided they are for a SQL database that is supported by SQLAlchemy.  You can find more information on the dialects supported by `SQLAlchemy` on their [dialects](https://docs.sqlalchemy.org/en/20/dialects/index.html) page.

   To connect to Snowflake, you will need to supply the following connection details and credentials:

   - `account`: Your Snowflake organization and account name separated by a hyphen (`oraganizationname-accountname`) or your account name and a legacy account locator separated by a period (`accountname.region`). The legacy account locator value must include the geographical region. For example, `us-east-1`. 
    
   To locate your Snowflake organization name, account name, or legacy account locator values see [Finding the Organization and Account Name for an Account](https://docs.snowflake.com/en/user-guide/admin-account-identifier#finding-the-organization-and-account-name-for-an-account) or [Using an Account Locator as an Identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier#using-an-account-locator-as-an-identifier).
    
   - `user`: The username you use to access Snowflake.

   - `database`: The name of the Snowflake database where the data you want to validate is stored. In Snowsight, click **Data** > **Databases**. In the Snowflake Classic Console, click **Databases**.
 
   - `schema`: the name of the Snowflake schema where the data you want to validate is stored.

   - `warehouse`: the name of your Snowflake database warehouse. In Snowsight, click **Admin** > **Warehouses**. In the Snowflake Classic Console, click **Warehouses**.

   - `role`: Your Snowflake role.

   - `private_key`: Your RSA private key value. Do not include the start and end markers `-----BEGIN ENCRYPTED PRIVATE KEY-----` and `-----END ENCRYPTED PRIVATE KEY-----`.