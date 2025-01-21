---
sidebar_label: 'Freshness'
title: 'Validate data freshness with GX'
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Data freshness refers to how up-to-date, or current, data is relative to its source system or the real-world events it represents. Freshness is about the recency of data relative to its generation; its primary metric is the time since data was generated or updated.

Data informs many time-sensitive tasks and decision-making processes in today's business environment. Stale data can lead to significant consequences in applications across industries. For example, in e-commerce, outdated inventory data can result in oversold products and frustrated customers. In financial trading, stale market data can lead to missed opportunities and potential compliance issues. These scenarios underscore the critical importance of data freshness validation to ensure accurate insights and timely decision-making.

Great Expectations (GX) can be used to monitor and validate the freshness of your organization's data. Through use of the Expectations and features offered by both GX Cloud and GX Core, you can establish checks that ensure your datasets maintain the expected levels of freshness, catch staleness issues early, and prevent downstream issues in your data workflows. This article will discuss how to effectively manage and validate data freshness using GX, ensuring your organization has high-quality, up-to-date datasets for accurate insights and timely actions.

## Prerequisite knowledge

This article assumes basic familiarity with GX components and workflows. If you're new to GX, start with the [GX Cloud](https://docs.greatexpectations.io/docs/cloud/overview/gx_cloud_overview) and [GX Core](https://docs.greatexpectations.io/docs/core/introduction) overviews to familiarize yourself with key concepts and setup procedures.

## Data preview

The examples presented in this article use a synthetic sensor reading dataset; a sample of this dataset is shown below. The data is available in a public Postgres database table, as described in the examples, and is also available in [CSV format](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/freshness_sensor_readings.csv).

| reading_id | sensor_id | temperature_k | reading_ts          | created_at          |
|:-----------|:----------|:--------------|:--------------------|:--------------------|
| 1001       | factory-1 | 305.00        | 2024-11-22 13:38:07 | 2024-11-22 13:47:00 |
| 1002       | factory-2 | 310.00        | 2024-11-22 13:38:54 | 2024-11-22 13:47:00 |
| 1003       | factory-3 | 308.00        | 2024-11-22 13:39:54 | 2024-11-22 13:47:00 |
| 1004       | factory-1 | 303.75        | 2024-11-22 13:40:10 | 2024-11-22 13:47:00 |
| 1005       | factory-2 | 311.00        | 2024-11-22 13:40:53 | 2024-11-22 13:47:00 |

This dataset is representative of a scenario in which environment readings are captured by remote IOT sensors and reported back through the cloud to a central database. Freshness needs might center on timely reporting of temperature in a factory, to monitor that rooms maintain required ranges for temperature-sensitive manufacturing processes. If fresh sensor data is not received, analysts and machine learning models are not able to determine if action needs to be taken on factory premises. Most notably:
* `reading_ts` captures the timestamp that the reading was taken by the sensor
* `created_at` is the creation timestamp of the row in the database, indicating when data became available for analysis

Freshness checks can be run against both the the `reading_ts` and `created_at` columns to ensure that the sensors are reporting fresh data and that the infrastructure responsible for delivering the readings is functioning in an expected, timely manner.

## Key freshness Expectations

GX Cloud and GX Core provide several options to use Expectations to validate freshness:
1. Built-in Expectations, such as those discussed in this section, can be used on timestamp columns to create freshness checks. Built-in expectations can be added in the GX Cloud UI or when using a GX Core Python workflow.
2. Custom SQL Expectations can be used in [GX Cloud](/cloud/expectations/manage_expectations.md#custom-sql-expectations) or [GX Core](/core/customize_expectations/use_sql_to_define_a_custom_expectation.md) to define and check data freshness based on SQL logic.
3. In GX Core, you can [customize Expectation classes](/core/customize_expectations/define_a_custom_expectation_class.md) to create Expectations that use Python logic to define and validate data freshness.

### Expect column maximum to be between

This Expectation can be used on a timestamp column to expect that the maximum, or the most recent, timestamp, in a column is within an expected range of time.

**Example**: Validate that the most recent timestamp occurred after a specified time.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/freshness_resources/freshness_expectations.py ExpectColumnMaxToBeBetween"
```

<small>View `ExpectColumnMaxToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_max_to_be_between).</small>

### Expect column minimum to be between

Checking for data freshness may also center on validating how old the data is. This Expectation can be used on a timestamp column to validate the minimum, or oldest, timestamp in a column is within an expected range of time.

**Example**: Validate that the oldest data is no older than a certain time.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/freshness_resources/freshness_expectations.py ExpectColumnMinToBeBetween"
```

<small>View `ExpectColumnMinToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_min_to_be_between).</small>

<br/>
<br/>

:::tip[GX tips for freshness Expectations]
Use `ExpectColumnMaxToBeBetween` to validate the most recent data point, ensuring your dataset is up-to-date. Use `ExpectColumnMinToBeBetween` to check the oldest data point, which is useful for verifying data retention policies or identifying unexpectedly old records. Using both in combination can provide a comprehensive freshness check.
:::

## Examples

Data freshness is often calculated relative to the current point in time. For instance, using the sample data shown above, a baseline freshness check might be to validate that data has arrived in the database within the last 5 minutes.

Data freshness might also be validated relative to multiple events. For instance, using the sample data above, another freshness check might be that sensor readings are available in the database no later than 10 minutes after they are captured by the sensor.

The examples in this section showcase how to use available features in GX Cloud and GX Core to create and run Expectations that accommodate the dynamic nature of nature of freshness checks, including the use of `now()`-type functions and timestamp differences.

### Create a freshness custom SQL Expectation using GX Cloud

**Goal**: Create custom SQL Expectations in GX Cloud to validate data freshness and schedule data validation to run hourly.

Use the GX Cloud UI to walk through the following steps:

1. Using the following connection string to create a Postgres Data Source, create a Data Asset for the `freshness_sensor_readings` table:
   ```
   postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
   ```

2. Using the query below, create a custom SQL Expectation on the `freshness_sensor_readings` Data Asset which expects that sensor readings are available in the database no more than 10 minutes after they are initially captured on the sensor.
   ```sql
   select *
   from {batch}
   where extract(epoch from (age(created_at, reading_ts))) > 10*60
   ```

3. Add a second custom SQL Expectation on the same Data Asset which expects that new sensor readings have arrived in the database within the last 5 minutes.
   ```sql
   select *
   from (
      select max(created_at) as most_recent_reading
      from {batch}
   ) t
   where extract(epoch from (age(current_timestamp, most_recent_reading))) > 5*60
   ```

5. Edit the active Validation schedule to modify the frequency of recurring data validation. Select a **Frequency** of *Every 1 hour* to run recurring freshness checks each hour.

6. Inspect the Validation Results on the `freshness_sensor_readings` Data Asset once validation has run.

**Result**: One freshness Expectation passes, and the other fails.

* The freshness Expectation that sensor readings are available in the database no more than 10 minutes after initial capture passes, as this condition holds true for all sensor readings accumulated in the database.

* The freshness Expectation that new sensor readings have arrived in the database within the last 5 minutes fails, as the sample data represents readings from a past point in time and readings are not being continually refreshed in the Postgres database. However, if sensor readings were to be arriving regularly, this Expectation would be able to validate whether or not fresh data was arriving in the required time frame.

**GX solution**: GX enables dynamic data freshness validation, relative to the current point in time, through the use of custom SQL Expectations. Though this example showcased use of a custom SQL Expectation in GX Cloud, this feature is also available in GX Core.


### Create a freshness custom Expectation class using GX Core

**Goal**: Create a custom Expectation class in GX Core to validate data freshness relative to the current point in time.

Run the following GX Core workflow:

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/freshness_resources/freshness_workflow.py full workflow"
```

**Result**:
```python title="Python output"
Freshness check passed: False
Most recent reading timestamp: 2024-11-22 14:49:00
```

The Expectation fails because the sample data represents readings from a past point in time, the sample data is not being continually refreshed in Postgres. However, were new sensor readings to be arriving in the database, the custom Expectation could be used to check that new readings had arrived within the desired time frame.

**GX solution**: GX Core enables using custom, Python-based logic to define and validate data freshness. Custom Expectation classes in GX Core can be used to complement and extend GX Cloud workflows.

## Identifying and setting freshness thresholds

Effective data freshness validation requires an understanding of appropriate thresholds based on usage of the delivered data. Use the following steps to guide the process for identifying and codifying freshness thresholds.

1. **Start with business requirements**: Identify downstream data consumers, assess impact of stale data, and define acceptable freshness levels with stakeholders.

2. **Evaluate data source characteristics**: Determine expected update frequency, identify sources with inherent delays, and align thresholds with source capabilities.

3. **Analyze pipeline complexity**: Map data flow through pipeline, estimate processing time per stage, and account for total pipeline lag.

4. **Incorporate temporal patterns**: Identify cyclical patterns (daily, weekly, etc.), determine expected gaps or inactivity, and adjust for known patterns.

5. **Ensure regulatory compliance**: Research industry-specific freshness and timeliness regulations and verify that thresholds meet mandatory requirements.

For example, consider a case of validating freshness for sales transaction data generated by a hypothetical retail store. The business impact of stale data is high—it can lead to stockouts and lost revenue. The source systems (in-store point of sales terminals and an e-commerce platform) provide near real-time data. The data pipeline has moderate complexity with several transformation steps. There are clear daily and weekly sales cycles, with lower volumes sold overnight and on Sundays.

Balancing these factors, appropriate freshness thresholds for this retail sales data could be:
- During peak hours: The latest transaction timestamp occurred within the last 30 minutes.
- During off-hours: The latest transaction timestamp occurred within the last 2 hours.

The thresholds are aggressive enough to quickly detect stale data that could impact the business, while accommodating source system realities and known temporal patterns. Thresholds could be set using the GX `ExpectColumnMaxToBeBetween` Expectation on the transaction timestamp column, and scheduled to run in GX Cloud on an hourly basis.

By systematically working through the above steps and considering a holistic set of factors, you can define optimal freshness thresholds for your specific data assets and use cases. GX enables codifying these thresholds through data freshness validation to consistently to drive high data quality.

## Scenarios

To further understand the wide-ranging impact of data freshness validation across different industries, consider the following scenarios, and how GX can be used to monitor data freshness.

### Social media analytics

**Context**: A marketing agency provides social media monitoring and analytics services to its clients. They collect real-time data from various social media platforms to track brand mentions, sentiment, and engagement metrics.

**GX Solution**: By applying freshness Expectations like `ExpectColumnMaxToBeBetween` and `ExpectColumnMinToBeBetween` to the timestamp columns in the social media data, the agency can verify that they are capturing and analyzing the most recent interactions and conversations. GX enables the agency to set appropriate freshness thresholds based on their clients' needs and the dynamic nature of social media.

### Smart manufacturing and predictive maintenance

**Context**: A manufacturing company has implemented IoT sensors on its production lines to collect real-time data on machine performance, vibration levels, temperature, and other parameters. This data is used to monitor equipment health, predict maintenance needs, and prevent unplanned downtime.

**GX Solution**: GX allows the company to validate the freshness of the sensor data using Expectations like `ExpectColumnMaxToBeBetween` and `ExpectColumnMinToBeBetween`. By setting up these Expectations in their data pipelines, the company can ensure that the data accurately reflects the current state of the machines, enabling predictive maintenance models to identify potential issues early and schedule maintenance proactively.

### Connected vehicles and real-time fleet management

**Context**: A fleet management company equips its vehicles with IoT devices that collect data on location, speed, fuel consumption, and driver behavior. This data is used to optimize routes, monitor vehicle performance, and ensure driver safety.

**GX Solution**: GX empowers the company to set up Expectations like `ExpectColumnMinToBeBetween` and `ExpectColumnMaxToBeBetween` on the timestamp columns in the vehicle data. By incorporating these Expectations into their data pipelines, the company can verify that the data from the connected vehicles is consistently fresh, enabling real-time fleet tracking and quick response to deviations from planned routes or aggressive driving patterns.

## Avoid common freshness validation pitfalls

While data freshness is critical across various domains, teams often encounter common pitfalls when implementing freshness validation:

- **Not defining clear SLAs for data freshness**: Teams should establish and document clear service level agreements (SLAs) for how fresh different datasets need to be. Without clear targets, freshness can degrade over time.

- **Not considering end-to-end pipeline freshness**: Data can become stale at any stage, from ingestion through transformation. Account for total pipeline lag, not just source system freshness. Add validation checks after key processing steps.

- **Averaging timestamps can conceal issues**: Calculating the average timestamp can make the overall data appear misleadingly fresh. Instead, use minimum and maximum values instead to bound the full range.

- **Sampling data inappropriately for freshness checks**: When validating freshness, check the full dataset or use a statistically valid sampling method. Cherry-picking rows can mask staleness issues.

## The path forward

By adhering to best practices and understanding common freshness validation pitfalls, you can ensure that your data pipelines consistently deliver fresh data to drive insights and timely decision-making. Implementing freshness validation using GX empowers you to catch staleness issues early, prevent downstream problems, and maintain the high standards of data quality.

As you progress on your data quality journey, remember that freshness is just one critical aspect of a comprehensive data quality strategy. By exploring our broader [data quality series](/reference/learn/data_quality_use_cases/dq_use_cases_lp.md), you'll gain valuable insights into how other essential dimensions of data quality, such as integrity, completeness, distribution, and schema, can be seamlessly integrated into your workflows using GX.