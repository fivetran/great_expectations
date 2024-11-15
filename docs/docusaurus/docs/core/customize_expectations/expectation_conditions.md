---
title: Apply Expectation conditions to specific rows within a Batch
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../_core_components/prerequisites/_preconfigured_data_context.md';
import PrereqPreconfiguredDataSourceAndAsset from '../_core_components/prerequisites/_data_source_and_asset_connected_to_data.md';

By default, Expectations apply to the entire dataset retrieved in a Batch. However, there are instances when an Expectation may not be relevant for every row. Validating every row could lead to false positives or false negatives in the Validation Results.

For example, you might define an Expectation that a column indicating the country of origin for a product should not be null. If this Expectation is only applicable when the product is an import, applying it to every row in the Batch could result in many false negatives when the country of origin column is null for products produced locally.

To address this issue, GX allows you to define Expectation conditions that apply only to a subset of the data retrieved in a Batch.

## Create an Expectation condition

Great Expectations allows you to specify conditions for validating rows using the `row_condition` argument, which can be applied to all Expectations that assess rows within a Dataset. The `row_condition` argument should be a string that represents a boolean expression. Rows will be validated when the `row_condition` expression evaluates to `True`. Conversely, if the `row_condition` evaluates to `False`, the corresponding row will not be validated by the Expectation.
### Prerequisites

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.
- <PrereqPreconfiguredDataContext/>.
- Recommended. <PrereqPreconfiguredDataSourceAndAsset/> for [testing your customized Expectation](/core/define_expectations/test_an_expectation.md).

### Procedure

   <Tabs queryString="condition_parser" groupId="condition_parser" defaultValue='pandas' values={[{label: 'pandas', value:'pandas'}, {label: 'Spark', value:'spark'}, {label: 'SQL', value:'sql'}]}>

   <TabItem value="pandas" label="pandas">

      In this procedure, it is assumed that your Data Context is stored in the variable `context`, and your Expectation Suite is stored in the variable `suite`. The `suite` can either be a newly created and empty Expectation Suite or an existing Expectation Suite retrieved from the Data Context.
      
      The examples in this procedure use passenger data from the Titanic, which includes details about the class of ticket held by the passenger and whether or not they survived the journey.
      
      1. Determine the `condition_parser` for your `row_condition`.

      The `condition_parser` defines the syntax of `row_condition` strings. When implementing Expectation conditions with pandas, set this argument to `"pandas"`.

   </TabItem>

   <TabItem value="spark" label="Spark">

      In this procedure, it is assumed that your Data Context is stored in the variable `context`, and your Expectation Suite is stored in the variable `suite`. The `suite` can either be a newly created and empty Expectation Suite or an existing Expectation Suite retrieved from the Data Context.
      
      The examples in this procedure use passenger data from the Titanic, which includes details about the class of ticket held by the passenger and whether or not they survived the journey.
      
      1. Determine the `condition_parser` for your `row_condition`.

      The `condition_parser` defines the syntax of `row_condition` strings. When implementing Expectation conditions with Spark, set this argument to `"great_expectations"`.

   </TabItem>

   <TabItem value="sql" label="SQL">

      In this procedure, it is assumed that your Data Context is stored in the variable `context`, and your Expectation Suite is stored in the variable `suite`. The `suite` can either be a newly created and empty Expectation Suite or an existing Expectation Suite retrieved from the Data Context.
      
      The examples in this procedure use passenger data from the Titanic, which includes details about the class of ticket held by the passenger and whether or not they survived the journey.
      
      1. Determine the `condition_parser` for your `row_condition`.

      The `condition_parser` defines the syntax of `row_condition` strings. When implementing Expectation conditions with SQL, set this argument to `"great_expectations"`.

   </TabItem>

   </Tabs>

   Note that the Expectation with conditions will fail if the Batch being validated is from a different type of Data Source than indicated by the `condition_parser`.

2. Determine the `row_condition` expression.

   The `row_condition` argument should be a boolean expression string that is evaluated for each row in the Batch that the Expectation validates. If the `row_condition` evaluates to `True`, the row will be included in the Expectation's validations. If it evaluates to `False`, the Expectation will be skipped for that row.

   The syntax of the `row_condition` argument is based on the `condition_parser` specified earlier.

3. Create the Expectation.

   An Expectation with conditions is created like a regular Expectation, with the addition of the `row_condition` and `condition_parser` parameters alongside the Expectation's other arguments.
   
   <Tabs  className="hidden" queryString="condition_parser" groupId="condition_parser" defaultValue='pandas' values={[{label: 'pandas', value:'pandas'}, {label: 'Spark', value:'spark'}, {label: 'SQL', value:'sql'}]}>

   <TabItem value="pandas" label="pandas">
   
      In pandas, the `row_condition` value is passed to `pandas.DataFrame.query()` prior to Expectation Validation, and the resulting rows from the evaluated Batch will undergo validation by the Expectation.

      ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - pandas example row_condition"
      ```
   
      Do not use single quotes, newlines, or `\n` in the specified `row_condition` as shown in the following examples:

      ```python title="Python" 
      row_condition = "PClass=='1st'"  # Don't do this. Single quotes aren't valid!
   
      row_condition="""
      PClass=="1st"
      """  # Don't do this.  Newlines and \n aren't valid!
   
      row_condition = 'PClass=="1st"'  # Do this instead.
      ```

   </TabItem>

   <TabItem value="spark" label="Spark">

      In Spark, the `row_condition` uses custom syntax, which is parsed as a data filter or query prior to Expectation Validation.

      ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - spark example row_condition"
      ```
   
      Do not use single quotes, newlines, or `\n` in the specified `row_condition` as shown in the following examples:

      ```python title="Python" 
      row_condition = "col('PClass')=='1st'"  # Don't do this. Single quotes aren't valid!
   
      row_condition="""
      col("PClass")=="1st"
      """  # Don't do this.  Newlines and \n aren't valid!
   
      row_condition = 'col("PClass")=="1st"'  # Do this instead.
      ```

   </TabItem>

   <TabItem value="sql" label="SQL">

      In SQL, the `row_condition` uses custom syntax, which is parsed as a data filter or query prior to Expectation Validation.

      ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - sql example row_condition"
      ```
   
      Do not use single quotes, newlines, or `\n` in the specified `row_condition` as shown in the following examples:
   
      ```python title="Python" 
      row_condition = "col('PClass')=='1st'"  # Don't do this. Single quotes aren't valid!
   
      row_condition="""
      col("PClass")=="1st"
      """  # Don't do this.  Newlines and \n aren't valid!
   
      row_condition = 'col("PClass")=="1st"'  # Do this instead.
      ```

   </TabItem>

   </Tabs>

   <Tabs className="hidden" queryString="condition_parser" groupId="condition_parser" defaultValue='pandas' values={[{label: 'pandas', value:'pandas'}, {label: 'Spark', value:'spark'}, {label: 'SQL', value:'sql'}]}>
   
   <TabItem value="pandas" label="pandas">

      In pandas, you can reference variables from the environment by prefixing them with `@`. Additionally, when a column name contains spaces, you can specify it by enclosing the name in backticks: `` ` ``.

      Some examples of valid `row_condition` values for pandas include:

      ```python title="Python"
      row_condition = '`foo foo`=="bar bar"'  # The value of the column "foo foo" is "bar bar"
   
      row_condition = 'foo==@bar'  # the value of the foo field is equal to the value of the bar environment variable
      ```

      For more information on the syntax accepted by pandas `row_condition` values see [pandas.DataFrame.query](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.query.html).

   </TabItem>

   <TabItem value="spark" label="Spark">

      For Spark, you should specify your columns using the `col()` function.

      Some examples of valid `row_condition` values for Spark include: 
    
      ```python title="Python"
      row_condition='col("foo") == "Two  Two"'  # foo is 'Two Two'
    
      row_condition='col("foo").notNull()'  # foo is not null
    
      row_condition='col("foo") > 5'  # foo is greater than 5
    
      row_condition='col("foo") <= 3.14'  # foo is less than 3.14
    
      row_condition='col("foo") <= date("2023-03-13")'  # foo is earlier than 2023-03-13
    
      ```

   </TabItem>

   <TabItem value="sql" label="SQL">

      For SQL, you should specify your columns using the `col()` function.

      Some examples of valid `row_condition` values for SQL include: 
    
      ```python title="Python"
      row_condition='col("foo") == "Two  Two"'  # foo is 'Two Two'
    
      row_condition='col("foo").notNull()'  # foo is not null
    
      row_condition='col("foo") > 5'  # foo is greater than 5
    
      row_condition='col("foo") <= 3.14'  # foo is less than 3.14
    
      row_condition='col("foo") <= date("2023-03-13")'  # foo is earlier than 2023-03-13
    
      ```

   </TabItem>

   </Tabs>

4. Optional. Create additional Expectation conditions

   Expectations that have different conditions are treated as unique, even if they belong to the same type and apply to the same column within an Expectation Suite. This approach allows you to create one unconditional Expectation and an unlimited number of Conditional Expectations, each with a distinct condition.

   For instance, the following code establishes an Expectation that the value in the `"Survived"` column is either 0 or 1:

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - example Expectation without conditions"
   ```
   
   And this code adds a condition to the Expectation that specifies the value of the `"Survived"` column is `1` if the individual was a first class passenger:
   
   <Tabs className="hidden" queryString="condition_parser" groupId="condition_parser" defaultValue='pandas' values={[{label: 'pandas', value:'pandas'}, {label: 'Spark', value:'spark'}, {label: 'SQL', value:'sql'}]}>

   <TabItem value="pandas" label="pandas">

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - pandas example Expectation with conditions"
   ```
   </TabItem>

   <TabItem value="spark" label="Spark">

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - spark example Expectation with conditions"
   ```
   </TabItem>

   <TabItem value="sql" label="SQL">

   ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - sql example Expectation with conditions"
   ```
   </TabItem>

   </Tabs>

## Data Docs and Expectation conditions

Expectations with conditions are presented differently from standard Expectations in the Data Docs. Each Expectation with conditions is prefaced with *if 'row_condition_string', then values must be...* as illustrated in the following image:

![Image](/docs/oss/images/conditional_data_docs_screenshot.png)

If the *'row_condition_string'* is a complex expression, it will be divided into several components to enhance readability.

## Scope and limitations

While conditions can be applied to most Expectations, the following Expectations cannot be conditioned and do not accept the `row_condition` argument:

* `expect_column_to_exist`
* `expect_table_columns_to_match_ordered_list`
* `expect_table_columns_to_match_set`
* `expect_table_column_count_to_be_between`
* `expect_table_column_count_to_equal`
* `unexpected_rows_expectation`
