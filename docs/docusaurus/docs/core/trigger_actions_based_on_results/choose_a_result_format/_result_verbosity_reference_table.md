The following table lists the fields that can be found in the `result` dictionary of a Validation Result and the `result_format` levels that return that field. An * indicates the field is not returned by default but can be enabled through an additional setting. Meanwhile, ** indicates that the field is returned by default but can be disabled.

| Fields within `result`                |BOOLEAN_ONLY    |BASIC           |SUMMARY         |COMPLETE        |
----------------------------------------|----------------|----------------|----------------|-----------------
|    element_count                      |no              |yes             |yes             |yes             |
|    missing_count                      |no              |yes             |yes             |yes             |
|    missing_percent                    |no              |yes             |yes             |yes             |
|    unexpected_count                   |no              |yes             |yes             |yes             |
|    unexpected_percent                 |no              |yes             |yes             |yes             |
|    unexpected_percent_nonmissing      |no              |yes             |yes             |yes             |
|    observed_value                     |no              |yes             |yes             |yes             |
|    partial_missing_list               |no              |yes **          |yes **          |yes **          |
|    partial_unexpected_list            |no              |yes **          |yes **          |yes **          |
|    partial_unexpected_index_list      |no              |no              |yes **          |yes **          |
|    partial_unexpected_counts          |no              |no              |yes **          |yes **          |
|    unexpected_index_list              |no              |no              |no              |yes             |
|    unexpected_index_query             |yes *           |yes *           |yes *           |yes             |
|    unexpected_list                    |no              |no              |no              |yes             |
|    unexpected_rows                    |no              |yes *           |yes *           |yes *           |
