---
title: Define a Multi-source Expectation
description: Query multiple Data Sources and compare the results for equality.
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../_core_components/prerequisites/_preconfigured_data_context.md';

A Multi-source Expectation executes one SQL query for each of two Data Sources and compares their results for equality. This can be helpful for validating consistency between systems during data migration or regular data loading processes. Multi-source Expectations can detect data drift introduced during the ETL process through discrepancies in schemas, counts, time windows, data types, and precision levels between Data Sources. Here are some examples of comparisons you can test:
- Every row in table A matches every row in table B.
- An aggregate metric of table A matches the same aggregate metric of table B.
- An aggregate metric of table A matches a different aggregate metric of table B. (For example, the count of rows where X is true in table A matches the count of rows where Y and Z are true in table B.)

To compare results for equality, each row returned by the query for the base Data Source will be compared to each row returned by the query for the comparison Data Source. When you configure a Multi-source Expectation, you set a failure threshold with `mostly`. The Expectation will fail if the portion of identical rows between your two queries falls below this threshold.

The portion of identical rows is computed by dividing the number of matching rows by the maximum number of rows in either result. Here are some example scenarios:

| Base result row count | Comparison result row count | Matched rows | Portion of identical rows |
| --------------------- | --------------------------- | ------------ | ------------------------- |
| 200                   | 200                         | 200          | 1                         |
| 25                    | 100                         | 25           | .25                       |
| 100                   | 25                          | 1            | .01                       |
| 0                     | 0                           | 0            | 1                         |

## Prerequisites

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.
- <PrereqPreconfiguredDataContext/>.
- Recommended. [Preconfigured Data Sources and Data Assets connected to your data](/core/connect_to_data/connect_to_data.md) for [testing your Multi-source Expectation](/core/define_expectations/test_an_expectation.md).

### Procedure

To create a Multi-source Expectation, add an `ExpectQueryResultsToMatchComparison` Expectation for the base Data Source.

<Tabs 
   queryString="procedure"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

1. Define your comparison Data Source.

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - define comparison Data Source"
   ```

2. Determine your base and comparison SQL queries. Each query should be written in the dialect of the associated Data Source.

   In this example, the queries will both select any rows where the passenger count is greater than `0`:

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - define queries"
   ```

3. Customize how the Expectation renders in Data Docs.

   As with other Expectations, the `description` attribute contains the text describing the Expectation when your results are rendered into Data Docs. You can format the `description` string with Markdown syntax:

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - define description"
   ```

4. Create a new Expectation using the `ExpectQueryResultsToMatchComparison` class and your parameters.
  
   The class name `ExpectQueryResultsToMatchComparison` describes the functionality of the Expectation: it queries multiple Data Sources and compares the results for equality.  When you create your Expectation, you can use a name that is more indicative of your specific use case.  In this example, the multi-source Expectation will be used to validate that two tables both have the same rows with passengers.

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - create Expectation"
   ```

5. Use your Multi-source Expectation.

   Now that you've created a Multi-source Expectation, you can [add it to an Expectation Suite](/core/define_expectations/organize_expectation_suites.md) for the base Data Source and [validate it](/docs/core/run_validations/run_a_validation_definition.md) like any other Expectation.

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - full code example"
```

</TabItem>

</Tabs>

## Limitations

Keep the following limitations in mind when working with Multi-source Expectations:
- The comparison is limited to the first 200 rows of each query result. If you anticipate that a query will return more than 200 rows, use an `ORDER BY` clause to control what is surfaced first for comparison.
- Batches are not supported. To test a time-based interval of data, use timestamp windows in your base and comparison SQL queries.
- The Expectation configuration and validation results are not reflected on the comparison Data Source. The Expectation is always managed on the Data Asset where you initially configure it.
