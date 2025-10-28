import ConnectionStringTable from './_connection_string_reference_table.mdx';

Different types of SQL databases have different formats for their connection details. Most Data Sources use a source-specific consolidated `connection_string` to provide all connection details, while Snowflake uses separate input parameters. In the following table, the text in `<>` corresponds to the values specific to your credentials and connection details.


   <ConnectionStringTable/>

   Other connection string formats are valid provided they are for a SQL database that is supported by SQLAlchemy.  You can find more information on the dialects supported by `SQLAlchemy` on their [dialects](https://docs.sqlalchemy.org/en/20/dialects/index.html) page.

   To connect to Snowflake, you will pass your connection details and credentials as the following parameters: `account`,  `user`, `database`, `schema`, `warehouse`, `role`, and `private_key`. When setting your `private_key` value, do not include the start and end markers `-----BEGIN/END ENCRYPTED PRIVATE KEY-----`.

      :::warning Snowflake password authentication is deprecated
      Snowflake has deprecated password authentication and will remove support for it entirely in the future. Set up new Data Sources with key-pair authentication. If you have older Snowflake Data Sources using password authentication, update them to use key-pair authentication. For more information about the deprecation, see [Snowflake's documentation](https://docs.snowflake.com/en/user-guide/security-mfa-rollout).
      :::