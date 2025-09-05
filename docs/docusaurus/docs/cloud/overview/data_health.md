---
title: 'Data Health'
description: Understand and improve data quality test coverage and success across your business.
---

To understand the health of your data, you need to know whether tests are passing or failing as well as what you're testing and how often.

## Metrics
To give you these insights into the health of your data, GX Cloud provides the following workspace-level metrics on the **Data Health** page:

![Example metrics: Data Health 71%, Daily distinct Expectations 9167, Active Coverage 98%, Total Data Assets 390. Daily Data Health rollover details include date, Data Health percentage, count of Expectations validated, and count of successful Expectations. Metrics default to overall data and can be filtered to a specific data quality issue, such as schema.](/img/data_health.png)

- **Data Health:** A 30-day average of the following daily percentage: the number of successful distinct Expectations in a day divided by the number of distinct Expectations validated in that day. Here are some scenarios to help you understand the concepts of distinct Expectation validations and successful distinct Expectations as used in calculating data health metrics.
   - If an Expectation is validated multiple times for a given Data Asset in a single day, it will be counted as one distinct Expectation validation.
   - If an Expectation fails near the start of the day and succeeds near the end of the day, it will be counted as a successful distinct Expectation.
   - If an Expectation succeeds near the start of the day and fails near the end of the day, it will not count as a successful distinct Expectation.

- **Daily distinct Expectations:** A 30-day average of the number of distinct Expectations validated each day. 

- **Daily Data Health:** The number of successful distinct Expectations in a day divided by the number of distinct Expectations validated in that day.

- **Active Coverage:** The percentage of Data Assets that have been validated in the last 30 days.

- **Total Data Assets:** The current number of Data Assets in your GX Cloud workspace.

Days as used in these metrics are segmented by midnight UTC.

Only current Data Assets are considered in these metrics. Deleted Data Assets are excluded from the calculations even if they've had Validations within the last 30 days.

## Data quality issue filters

For a more nuanced understanding of what you’re testing, you can filter the **Data Health** dashboard to focus on different data quality issues such as **Schema** or **Volume**. When you apply a filter, the metrics shown are impacted as follows:

- For **Data Health**, **Daily distinct Expectations**, and **Daily Data Health**, only Expectations belonging to the selected data quality issue will be considered when counting both successful distinct Expectations and distinct Expectation validations.

- The **Active Coverage** percentage will be scoped to Data Assets that have been validated with at least one Expectation for the selected data quality issue in the last 30 days.

- The number of **Total Data Assets** will not change. This always shows the current number of Data Assets in your GX Cloud workspace regardless of what if any Expectations they have.

## Next steps for improving data health

If **Active Coverage** is low, drill into it for a list of **Inactive Data Assets**. Then [schedule recurring Validations](/docs/cloud/schedules/manage_schedules.md) and/or [add Expectations](/docs/cloud/expectations/manage_expectations.md#add-an-expectation) for those Data Assets to improve your coverage both overall and for specific data quality issues.
