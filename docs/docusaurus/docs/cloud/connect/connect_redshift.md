---
sidebar_label: 'Connect GX Cloud to Redshift'
title: 'Connect GX Cloud to Redshift'
description: Connect GX Cloud to a Redshift Data Source.
---

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.

- A Redshift database, schema, and table or view.

- If you are using a [fully-hosted deployment of GX Cloud](/docs/cloud/deploy/deployment_patterns.md), your Redshift cluster or workgroup must be [publicly accessible](https://docs.aws.amazon.com/redshift/latest/mgmt/rs-security-group-public-private.html#rs-security-group-public-default).

- A Redshift user with the following permissions:

   - `USAGE` privileges on the schema.

   - `SELECT` privileges on the table or view.


## Connect to a Redshift Data Source and add a Data Asset


1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset** > **New Data Source** > **Redshift**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Select whether you will enter your connection details as either separate **Input parameters** or a consolidated **Connection string**.

4. Supply your connection details depending on the method you chose in the previous step.  If you created a separate Redshift user for your GX Cloud connection as recommended above, use those credentials in your connection details.

   - If you chose **Input parameters**, complete the following fields:
    
      - **Username**: Enter the username you use to access Redshift.

      - **Password**: Enter the password you use to access Redshift.

      - **Host**: Enter the host of your Redshift database. The location of this information in Redshift depends on whether you are using a provisioned cluster or Redshift serverless.
         - If you're using a provisioned cluster, go to the **Provisioned clusters dashboard**, select your **Cluster**, and find the **Endpoint**. Copy the endpoint up to the `:`. The host has a format of `cluster-name.abc123.us-east-2.redshift.amazonaws.com`. 
         - If you're using Redshift serverless, go to the **Serverless dashboard**, select your **Workgroup**, and find the **Endpoint**. Copy the endpoint up to the `:`. The host has a format of `workgroup-name.123.us-east-2.redshift-serverless.amazonaws.com`. 

      - **Port**: Enter the port of your Redshift database. The location of this information in Redshift depends on whether you are using a provisioned cluster or Redshift serverless.
         - If you're using a provisioned cluster, go to the **Provisioned clusters dashboard**, select your **Cluster**, and find the **Endpoint**. Copy the number after the `:`. This is usually the default of `5439`. 
         - If you're using Redshift serverless, go to the **Serverless dashboard**, select your **Workgroup**, and find the **Endpoint**. Copy the number after the `:`. This is usually the default of `5439`.  

      - **Database**: Enter the name of the Redshift database where the data you want to validate is stored. 

      - **Schema**: Enter the name of the Redshift schema where the data you want to validate is stored.

      - **SSL mode**:  Select how to handle encryption for client connections and server certificate verification. We recommend selecting `require` since GX Cloud supports SSL connections. See [Redshift's SSL docs](https://docs.aws.amazon.com/redshift/latest/mgmt/connecting-ssl-support.html) for more information on the available options. 

   - If you chose **Connection string**, enter it with a format of:

      ```python title="Redshift connection string"
      redshift+psycopg2://<USER>:<PASSWORD>@<HOST>:<PORT>/<DATABASE>?sslmode=<SSLMODE>&options=-csearch_path%3D<SCHEMA>
      ```

      For guidance on replacing each placeholder in the connection string, see the above input parameter definitions. 

   
5. Click **Connect**.

6. Select one or more tables or views to import as Data Assets.

7. Click **Add x Asset(s)**.

8. Decide which [Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema** and **Volume** anomalies. You can de-select recommendations you’d like to opt out of. You can choose to generate Expectations to detect **Completeness** anomalies.

9. Click **Start monitoring** or **Finish**.


## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)

