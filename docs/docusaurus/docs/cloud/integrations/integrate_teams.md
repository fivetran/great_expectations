---
sidebar_label: 'Integrate GX Cloud with Microsoft Teams'
title: 'Integrate GX Cloud with Microsoft Teams'
description: Connect your GX Cloud workspace to Microsoft Teams so you can configure alerts that @mention stakeholders or yourself in Microsoft Teams.
---


With GX Cloud's [Microsoft Teams](https://www.microsoft.com/en-us/microsoft-teams/group-chat-software) integration and [alerts](/cloud/alerts/alert_about_failures.md), you can notify standard channels in public teams about Expectation failures. Connect your GX Cloud workspace to Microsoft Teams to enable the following alert configuration options:

- **Channel selection**. Your team will be able to use a dropdown in the alert configuration form to select the target channel.
- **At-mentions to highlight notifications for stakeholders or yourself**. Your team will be able to configure @mentions to include in the notification message in Microsoft Teams to help bring the notification to the attention of key collaborators and manage noise for other channel members.

Keep the following in mind when integrating Microsoft Teams:

- The integration is configured at the [workspace](/cloud/access/manage_access.md#workspaces) level. A GX Cloud workspace can connect to only one Microsoft Teams tenant. Each different workspace in a GX Cloud organization can connect to a different Teams tenant, the same Teams tenant as another workspace, or no Teams tenant. 
- The integration will connect to all of the public teams that are in the Microsoft Teams tenant at the time the connection is authorized. If more teams are added to the tenant after the integration is connected, you can [reconnect](#reconnect-to-microsoft-teams) to authorize the connection for the new teams. 
- You must have [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater to manage the integration.



## Prerequisites

To connect or reconnect a Microsoft Teams integration, you must have the following prerequisites fulfilled:
- In Microsoft Entra ID, you have [Global Administrator](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-administrator) permissions or a role that includes the `microsoft.directory/servicePrincipals/managePermissionGrantsForAll` permission and can grant tenant-wide admin consent for the following delegated permissions:
   - `AppCatalog.ReadWrite.All`
   - `ChannelMember.Read.All`
   - `TeamMember.Read.All`
   - `TeamsAppInstallation.ReadWriteForTeam`
   - `TeamworkTag.Read`
- You have the [Microsoft Entra ID tenant ID](https://learn.microsoft.com/en-us/entra/fundamentals/how-to-find-tenant) for your Microsoft Teams tenant.


## Connect to Microsoft Teams

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Microsoft Teams** integration and click **Connect**.
3. Follow the prompts to sign in to Microsoft Teams, provide your **Tenant ID**, grant permissions, and connect.

The integration will be **Pending** while the GX Cloud app is installed for your Microsoft Teams tenant. When the installation completes, the integration will be **Connected** and you can start [configuring alerts](/docs/cloud/alerts/alert_about_failures.md#create-an-alert) for Teams.

## Reconnect to Microsoft Teams

You can reconnect to authorize the connection for new teams that were added after you initially connected to Microsoft Teams, or to resolve an error. Your integration may **Error** if, for example, the user who configured it has their Microsoft account deactivated, or if the authorization is no longer valid because permissions changed or access was revoked. If the integration experiences an error, notifications might not be sent to Teams channels, but alert configurations will be kept intact so that Teams notifications will resume when the integration is reconnected.

To reconnect the integration, do the following.

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Microsoft Teams** integration and click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit connection**.
3. Click **Reconnect**.
4. Follow the prompts to sign in to Microsoft Teams, provide your **Tenant ID**, grant permissions, and connect.

The integration will be **Pending** while the GX Cloud app is installed for your Microsoft Teams tenant. When the installation completes, the integration will be **Connected** and you can start configuring alerts for Teams.

## Remove your Microsoft Teams integration

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Microsoft Teams** integration and click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/>  **Edit connection**.
3. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Remove**.
4. Note that removing the integration may impact existing alert configurations. If an alert’s **Recipients** include **Microsoft Teams channels**, then the team, channel, and @mention configuration details will be deleted. If the alert is also configured with **Emails** or **Slack channels** as recipients, those portions of the alert’s configuration will be left as-is, and notifications will continue to be sent to those destinations. Click **Remove** to confirm you understand the impact to existing alert configurations and finalize deleting the connection.

