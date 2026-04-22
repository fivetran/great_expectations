---
sidebar_label: 'Integrate GX Cloud with Jira'
title: 'Integrate GX Cloud with Jira'
description: Connect your GX Cloud workspace to Jira Cloud so you can link Expectation failures to Jira issues for incident management.
---

With GX Cloud's Jira integration and [incidents](/cloud/alerts/manage_incidents.md), you can link Expectation failures to Jira issues to triage, prioritize, assign, and track the resolution of data quality problems. Linked issues are made accessible at the Data Asset level and in Validation Results for visibility. 

Keep the following in mind when integrating Jira:
- The integration is configured between a [GX Cloud workspace](/cloud/access/manage_access.md#workspaces) and a Jira site (for example, `my-company.atlassian.net`). A GX Cloud workspace can connect to only one Jira site. Each different workspace in a GX Cloud organization can connect to a different Jira site, the same Jira site as another GX Cloud workspace, or no Jira site.
- You must have [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater to manage the integration.

## Prerequisites
To connect or reconnect a Jira integration, you must have the following prerequisites fulfilled:
- You have an [Atlassian service account](https://support.atlassian.com/user-management/docs/understand-service-accounts/#Create-a-service-account).
- You have [credentials for the service account](https://support.atlassian.com/user-management/docs/create-oauth-2-0-credential-for-service-accounts/#Create-an-OAuth-2.0-credential-for-a-service-account).

Follow the steps below to create an Atlassian service account:
1. Go to [Atlassian Administration](https://admin.atlassian.com/).
2. If you have more than one Atlassian organization, select the one that owns the Jira site you want to connect.
3. Select **Directory** > **Service accounts**.
4. Select **Create a service account**.
5. For the **Name**, enter `GX Cloud` or something similar.
6. For the optional **Description**, enter `GX Cloud integration authorizing user` or something similar.
7. Click **Next**.
8. On the **Select app roles** screen, find your **Jira** app, and under **Roles** select **User**. 
   :::note Want to restrict the integration to specific Jira spaces?
   By default, the GX Cloud Jira integration lets your team link Expectation failures to Jira issues in any space of your Jira site. To restrict the integration to specific Jira spaces, you can add [Groups](https://www.atlassian.com/software/jira/guides/permissions/overview#what-are-users-and-groups) for your service account’s app roles instead of granting User permissions for your whole Jira app.
   :::
9. Click **Create**.


Follow the steps below to add credentials for the Atlassian service account:
1. In [Atlassian Administration](https://admin.atlassian.com/) for your organization, go to **Directory** > **Service accounts** and select the service account you created earlier.
2. Select **Create credentials**.
3. Select **OAuth 2.0**.
4. Click **Next**.
5. For the **Name**, enter `gx_cloud_user_token` or something similar.
6. Click **Next**.
7. Select all of the following scopes:
   - `read:jira-work`
   - `read:jira-user`
   - `write:jira-work`
   - `manage:jira-webhook`
8. Click **Next**.
9. Review your OAuth information, then click **Create**.
10. Copy your **Client ID** and **Client secret** and save them somewhere safe. You’ll need these when you connect or reconnect the Jira integration for your GX Cloud workspace. You can't recover the ID or secret after you finish creating the credentials. We recommend you save the ID and secret in a password manager.
11. Click **Done**.

## Connect to Jira

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Jira** integration and click **Connect**.
3. Enter the **Client ID** and **Client secret** from your Atlassian service account.
3. Click **Connect**.
4. Click **Finish**.

Now you can link Expectation failures and Jira work items to [manage incidents](/docs/cloud/alerts/manage_incidents.md#create-an-incident). 

## Reconnect to Jira

Your Jira integration may **Error** if, for example, the user who created the authorizing Atlassian service account leaves your Atlassian organization. If this happens, you won’t be able to link issues, but your existing issue links will be kept intact. To reconnect the integration, do the following:

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Jira** integration and click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/>  **Edit connection**.
3. Click **Reconnect**.
4. Enter the **Client ID** and **Client secret** from an active Atlassian service account with permissions for your Jira site.
5. Click **Connect**.
6. Click **Finish**.

## Remove your Jira integration

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Jira** integration and click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/>  **Edit connection**.
3. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Remove**.
4. Note that removing the integration will remove all Jira issue links from the **Incidents** and **Validations** tabs for all of the Data Assets in your workspace. Click **Remove** to confirm you understand the impact to incident management and finalize deleting the connection.