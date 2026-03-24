---
sidebar_label: 'Responses overview'
title: 'Responses overview'
description: When Expectations fail, you can notify stakeholders to raise awareness, open an incident to track resolution, or trigger programmatic actions for custom business logic.
---

When your Expectations for your data fail, you may want to respond in a variety of ways depending on what the Expectation failure means for your business. For example, you might do one or more of the following:

- Let stakeholders know so they can avoid making decisions based on bad data.
- Engage collaborators so they can begin assessing and resolving the issue.             
- Quarantine and backfill bad records.

GX Cloud provides the following to support these kinds of responses to results.

- [**Alerts**](/cloud/alerts/alert_about_failures.md): You can configure alerts to notify email addresses and Slack channels about Expectation failures as soon as they happen. The notifications provide high-level information about how many Expectations failed and include a link to detailed Validation Results.
- [**Incidents**](/cloud/alerts/manage_incidents.md): You can link Expectation failures to Jira issues to triage, prioritize, assign, and track the resolution of data quality problems. Linked issues are made accessible at the Data Asset level and in Validation Results for visibility.
- [**Actions**](/cloud/alerts/custom_actions.md): You can programmatically apply custom business logic that does anything that can be done with Python code. For example, you might trigger different webhooks depending on which Expectations fail or run follow-up ETL jobs to fill in missing values.

Here’s an example of how an organization might use alerts, incidents, and Actions together to ensure data quality. Actions handle problems where the solution can be automated. Meanwhile, alerts and incidents help make sure the right people have the right info at the right time to address important problems that need human intervention.

![A critical Expectation failure triggers an alert that sends a Slack notification. A team member reviews the Validation Results and decides to link the Expectation failure to a Jira issue to open an incident. A warning Expectation failure triggers a Custom Action that backfills null values.](/img/responses.png)