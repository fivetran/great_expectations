# Great Expectations Contrib Packages.

Welcome to Great Expectations contrib--the place we store experimental and domain-specific contributions to the Great Expectations repository.

Note that we do not guarantee that Expectations in the `experimental` package are semantically correct and we do not plan to maintain them independently. However, Expectations that the community finds valuable can move into domain-specific or core packages in the future.

## Using Contrib

`pip install --upgrade great-expectations-experimental` and import the Expectation you'd like. Because each Expectation is modular and not imported until you declare you'd like to use it, you're in complete control of dependencies for contrib expectations.

For example:

```python
from great_expectations_contrib.expectations import ExpectNelsonsColumnToExist

# ... obtain Validator

validator.expect_nelsons_column_to_exist()
```
