---
sidebar_label: 'Alert about failures'
title: 'Alert about failures'
description: Create and manage alerts in GX Cloud.
---

Keep yourself and your stakeholders informed about the health of Data Assets and Expectations by configuring alerts in GX Cloud.

Alerts are configured at the Data Asset level. A single Data Asset can have multiple alerts configured. An alert can be configured to notify about all Expectation failures or only failures of certain [severities](/cloud/expectations/expectations_overview.md#failure-severity).

Alerts can send basic notifications to email addresses or notifications with @mentions to public Slack channels. Note that to enable @mentions for Slack, your GX Cloud workspace must be [integrated with Slack](/cloud/integrations/integrate_slack.md).

:::note More integrations are coming soon
Integrations for rich notifications and incident management in Jira, Microsoft Teams, PagerDuty, and ServiceNow are coming soon.
:::

To keep your email alerts secure, your GX Cloud organization has an allowlist of email domains that all alert recipient email addresses must belong to. By default, this includes the email domain of the Organization Owner who created the organization and domains for sending emails to the following third-party services: [Microsoft Teams](https://support.microsoft.com/en-us/office/send-an-email-to-a-channel-in-microsoft-teams-d91db004-d9d7-4a47-82e6-fb1b16dfd51e), [PagerDuty](https://support.pagerduty.com/main/docs/email-integration-guide), and [ServiceNow](https://www.servicenow.com/docs/r/washingtondc/build-workflows/create-inbound-email-flow.html).

Here is an example of how a team might configure alerts on their Data Assets to make sure the right people get the right information at the right time.

![Silver Data Asset has 3 alerts configured - "Data team awareness" sends notifications about info and warning failures to data@my-company.com, "Data team urgent" sends notifications about critical failures to the slack channel #data-team pinging @data-engineers, and "Sales" sends notifications about warning and critical failures to sales-managers@my-company.com. Gold Data Asset has 2 alerts confirgured - "Rapid response" sends notifcations about all failures to the slack channel #data-team pinging @on-call-data and to the #analytics channel pinging @alex and @bela; meanwhile "Marketing" alert sends notifications about critical failures to marketing@my-company.com, contractors@contractor-company.com, and slack channel #campaign-alerts](/img/alerts.png)

Note that you must have [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater to manage alerts.

## Create an alert

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, click **+ ADD**.
5. In the **Alert name** field, enter a name for the alert that will help you quickly identify it later.
6. Under **Severity**, select one or more failure severities for the alert to notify about. 
7. Decide if you want to notify **Emails** or **Slack channels**.
    - If you want to notify an email address, note that the domain of the email address must belong to your organization’s [email domain allowlist](#update-your-organizations-email-domain-allowlist). By default, the following third-party domains are allowed for basic notifications to third-party services.
      - [Microsoft Teams](https://support.microsoft.com/en-us/office/send-an-email-to-a-channel-in-microsoft-teams-d91db004-d9d7-4a47-82e6-fb1b16dfd51e) - `*.teams.ms`
      - [PagerDuty](https://support.pagerduty.com/main/docs/email-integration-guide) - `*.pagerduty.com`
      - [ServiceNow](https://www.servicenow.com/docs/r/washingtondc/build-workflows/create-inbound-email-flow.html) - `*.service-now.com`
   - If you want to send notifications with user @mentions to Slack, note that your GX Cloud workspace must be [integrated with Slack](/cloud/integrations/integrate_slack.md). 
8. To alert an email address, under **Recipients**, next to **Emails**, click **+** and enter an email address for the alert to send notifications to.
9. To alert a Slack channel, under **Recipients**, next to **Slack channels**, click **+** and select a channel for the alert to send notifications to. After selecting the channel, you will have the option to specify @mentions to include in the notification message. You can mention any user in the channel or any user group.
10. Optional. To send the same notification to another recipient, click **+** and enter another email address or Slack channel. Repeat as needed.
11. Click Save.

## Edit an alert

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, find the alert that you want to edit.
5. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit alert** for the alert that you want to edit.
6. Edit the alert configuration.
7. Click **Save**.

## Disable or enable an alert

If you want to temporarily stop an alert from sending notifications, you can disable it instead of deleting it. This makes it easier to restore the alert when you’re ready for it to start sending notifications again. 

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, find the alert that you want to disable or enable.
5. Click the **ON** / **OFF** toggle switch to disable or enable the alert.

## Delete an alert

1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. In the **Alerts** section, find the alert that you want to delete.
5. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete alert** for the alert that you want to delete.
6. Click **Delete**.

## Update your organization’s email domain allowlist 

By default, your organization’s email domain allowlist includes the following:

- The email domain of the Organization Owner who created the organization
- `*.teams.ms`
- `*.pagerduty.com`
- `*.service-now.com`


To request changes to your organization’s email domain allowlist, have an Organization Owner [contact support](mailto:support@greatexpectations.io).