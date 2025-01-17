---
title: Use SQL to define a custom Expectation
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../_core_components/prerequisites/_preconfigured_data_context.md';
import PrereqPreconfiguredDataSourceAndAsset from '../_core_components/prerequisites/_data_source_and_asset_connected_to_data.md';

Among the available Expectations, the `UnexpectedRowsExpectation` is designed to facilitate the execution of SQL queries as the core logic for an Expectation.  By default, `UnexpectedRowsExpectation` considers validation successful when no rows are returned by the provided SQL query.

<!-- TODO: Do we want to discuss custom `_validate(...)` logic here, or should that be held for a future topic on building custom Expectation classes from scratch? -->

<!-- Additionally, the `UnexpectedRowsExpectation`'s use of SQL or Spark-SQL queries makes it uniquely suitable for customized validation logic.  Although the default behavior of an `UnexpectedRowsExpectation` is to treat returned rows as having failed validation, you can override this default by providing a custom `_validate(...)` method for your customized subclass of `UnexpectedRowsExpectation`. -->

## Prerequisites

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.
- <PrereqPreconfiguredDataContext/>.
- Recommended. <PrereqPreconfiguredDataSourceAndAsset/> for [testing your customized Expectation](/core/define_expectations/test_an_expectation.md).

### Procedure

<Tabs 
   queryString="procedure"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

1. Determine your custom SQL query.

   The `UnexpectedRowsExpectation` class takes an `unexpected_rows_query` attribute, which is a SQL or Spark-SQL query that returns a selection of rows from the Batch of data being validated. By default, rows that are returned have failed the validation check.

   The custom SQL query should be written in the SQL dialect your database uses, except that it can also contain the special `{batch}` named query.  When the Expectation is evaluated, the `{batch}` keyword will be replaced with the Batch of data that is configured for your Data Asset.

   In this example, the custom query will select any rows where the passenger count is greater than `6` or less than `0`:

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - define query"
   ```

2. Customize how the Expectation renders in Data Docs.

   As with other Expectations, the `description` attribute contains the text describing the Expectation when your results are rendered into Data Docs. You can format the `description` string with Markdown syntax:

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - define description"
   ```

3. Create a new Expectation using the `UnexpectedRowsExpectation` class and your parameters.
  
   The class name `UnexpectedRowsExpectation` describes the functionality of the Expectation: it finds rows with unexpected values.  When you create your Expectation, you can use a name that is more indicative of your specific use case.  In this example, the customized Expectation will be used to find invalid passenger counts in taxi trip data:

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - create Expectation"
   ```

4. Use your custom SQL Expectation.

   Now that you've created a custom SQL Expectation, you can [add it to an Expectation Suite](/core/define_expectations/organize_expectation_suites.md) and [validate it](/docs/core/run_validations/run_a_validation_definition.md) like any other Expectation.

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - full code example"
```

</TabItem>

</Tabs>