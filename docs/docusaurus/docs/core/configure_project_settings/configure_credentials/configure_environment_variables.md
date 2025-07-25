### MAX_RESULT_RECORDS in util.py

Controls the maximum number of unexpected rows returned in validation results.

- Default: 200
- Type: Integer
- Example: `export GX_MAX_RESULT_RECORDS=500`

This is useful when you need to see more than the default 200 unexpected rows 
during data validation, particularly for debugging data quality issues.

Note: Setting this to a very high value may impact performance and memory usage
when dealing with large datasets that have many unexpected rows.
