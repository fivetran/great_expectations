---
sidebar_label: 'Integrate GX Cloud with Atlan'
title: 'Integrate GX Cloud with Atlan'
description: Surface data quality insights directly in Atlan’s metadata layer, and make Atlan’s data catalog and lineage information accessible from your GX Cloud Data Assets.
---

[Atlan](https://atlan.com/) is a centralized catalog and collaboration hub for data governance that helps teams understand what data they have and how it flows. Meanwhile, Great Expectations Cloud enables teams to define, validate, and monitor data quality. You can integrate GX Cloud with Atlan to surface data quality insights directly in Atlan’s metadata layer, and make Atlan’s data catalog and lineage information accessible from your GX Cloud Data Assets.

To integrate GX Cloud with Atlan, you will first get your GX Cloud credentials and then configure the [Great Expectations Cloud workflow in Atlan](https://docs.atlan.com/apps/connectors/observability/great-expectations-cloud).


## Get your credentials

Prerequisites:
- A [GX Cloud account](https://greatexpectations.io/cloud) with [Organization Owner](/cloud/access/manage_access.md#roles-and-permissions) permissions.

Get an organization access token, your organization ID, and your workspace ID so you can set your GX Cloud credentials in Atlan.

1. In GX Cloud, click **Tokens**.
2. In the **Organization access tokens** pane, click **Create organization access token**.
3. In the **Token name** field, enter a name for the token that will help you quickly identify it.
4. Click **Create**.
5. Copy and then paste the organization access token into a temporary file. The token can't be retrieved after you close the dialog.
6. Click **Close**.
7. Copy the value in the **Organization ID** field into the temporary file with your organization access token.
8. In the **Workspace ID** pane, find the relevant **Workspace name**, then copy the associated **ID** into the temporary file with your other credentials and save the file.

GX recommends deleting the temporary file after you set your credentials in Atlan.

## Next steps

Configure the Great Expectations workflow in Atlan.

1. Go to the Great Expectations connector in your company's Atlan workflow center.
2. Enter the GX Cloud credentials you saved above.
3. Delete the temporary file you saved your credentials in.
4. [Configure your Data Source mapping](https://docs.atlan.com/apps/connectors/observability/great-expectations-cloud/how-tos/integrate-great-expectations-cloud#configure-connection) in Atlan.

## Limitations

Filesystem Data Sources, such as Amazon S3, cannot be mapped from GX Cloud to Atlan.


