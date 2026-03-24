---
sidebar_label: 'Integrate GX Cloud with Slack'
title: 'Integrate GX Cloud with Slack'
description: Connect your GX Cloud workspace to Slack so you can configure alerts that @mention stakeholders or yourself in Slack.
---

With GX Cloud's Slack integration and [alerts](/cloud/alerts/alert_about_failures.md), you can notify public [Slack](https://slack.com/) channels about Expectation failures. Connect your GX Cloud workspace to Slack to enable the following alert configuration options:

- **Channel selection.** Your team will be able to use a dropdown in the alert configuration form to select the target channel. 
- **At-mentions to highlight notifications for stakeholders or yourself.** Your team will be able to configure @mentions to include in the notification message in Slack to help bring the notification to the attention of key collaborators and manage noise for other channel members.

Keep the following in mind when integrating Slack:

- The integration is configured at the [workspace](/cloud/access/manage_access.md#workspaces) level. A GX Cloud workspace can connect to only one Slack workspace. Each different workspace in a GX Cloud organization can connect to a different Slack workspace, the same Slack workspace as another GX Cloud workspace, or no Slack workspace.
- You must have [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater to manage the integration.

## Connect to Slack

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Slack** integration and click **Connect**.
3. Follow the prompts to sign in to Slack and **Allow** the connection.

## Reconnect to Slack

Your Slack integration may **Error** if, for example, the GX Cloud Slack app is removed or its bot token is revoked. If this happens, notifications will not be sent to Slack channels, but your existing alert configurations will be kept intact so that Slack notifications will resume when the integration is reconnected. To reconnect the integration, do the following:

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Slack** integration and click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/>  **Edit connection**.
3. Click **Reconnect**.
4. Follow the prompts to sign in to Slack and **Allow** the connection.

## Remove your Slack integration

1. In GX Cloud, select the relevant **Workspace** and then click **Integrations**.
2. Locate the **Slack** integration and click  <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit connection**.
3. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Remove**.
4. Note that removing the integration may impact existing alert configurations. If an alert’s **Recipients** include **Slack channels**, the channel and @mention configuration details will be deleted. If the alert is also configured with **Emails** as recipients, that portion of the alert’s configuration will be left as-is, and notifications will continue to be sent to those email addresses. Click **Remove** to confirm you understand the impact to existing alert configurations and finalize deleting the connection.

