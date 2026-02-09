---
sidebar_label: 'Manage email alerts'
title: 'Manage email alerts'
description: Create and manage email alerts in GX Cloud.
---

Keep yourself and your stakeholders informed about the health of Data Assets and Expectations by configuring alerts in GX Cloud.

Alerts are configured at the Data Asset level. A single Data Asset can have multiple alerts configured. An alert can be configured to notify about all Expectation failures or only failures of certain [severities](/cloud/expectations/expectations_overview.md#failure-severity).

To keep your email alerts secure,  your GX Cloud organization has an allowlist of email domains that all alert recipient email addresses must belong to. By default, this includes the email domain of the Organization Owner who created the organization and domains for sending emails to the following third-party services: [Slack](https://slack.com/help/articles/206819278-Send-emails-to-Slack), [Microsoft Teams](https://support.microsoft.com/en-us/office/send-an-email-to-a-channel-in-microsoft-teams-d91db004-d9d7-4a47-82e6-fb1b16dfd51e), and [PagerDuty](https://support.pagerduty.com/main/docs/email-integration-guide).

Note that you must have [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater to manage email alerts.

## Create an email alert

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, click **+ ADD**.
5. In the **Alert name** field, enter a name for the alert that will help you quickly identify it later.
6. Under **Severity**, select one or more failure severities for the alert to notify about. 
7. Under **Recipients**, click **+** and enter an email address for the alert to send notifications to. Note that the domain of the email address must belong to your organization’s [email domain allowlist](#update-your-organizations-email-domain-allowlist). By default, the following third-party domains are allowed for integrations with third-party services.

   - [Slack](https://slack.com/help/articles/206819278-Send-emails-to-Slack) - `*.slack.com`
   - [Microsoft Teams](https://support.microsoft.com/en-us/office/send-an-email-to-a-channel-in-microsoft-teams-d91db004-d9d7-4a47-82e6-fb1b16dfd51e) - `*.teams.ms`
   - [PagerDuty](https://support.pagerduty.com/main/docs/email-integration-guide) - `*.pagerduty.com`


8. Optional. To send the same notification to another recipient, click **+** and enter another email address. Repeat as needed. 
9. Click **Save**.

## Edit an email alert

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, find the alert that you want to edit.
5. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit alert** for the alert that you want to edit.
6. Edit the alert configuration.
7. Click **Save**.

## Disable or enable an email alert

If you want to temporarily stop an alert from sending emails, you can disable it instead of deleting it. This makes it easier to restore the alert when you’re ready for it to start sending emails again. 

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, find the alert that you want to disable or enable.
5. Click the **ON** / **OFF** toggle switch to disable or enable the alert.

## Delete an email alert

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, find the alert that you want to delete.
5. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete alert** for the alert that you want to delete.
6. Click **Delete**.

## Update your organization’s email domain allowlist 

By default, your organization’s email domain allowlist includes the following:

- The email domain of the Organization Owner who created the organization
- `*.slack.com`
- `*.teams.ms`
- `*.pagerduty.com`


To request changes to your organization’s email domain allowlist, have an Organization Owner [contact support](mailto:support@greatexpectations.io).