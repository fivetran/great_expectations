from typing import Final

DATAFRAME_REPLACEMENT_STR = "<DATAFRAME>"

# Maximum number of distinct values to return in expectation results
# to prevent payload size issues (e.g., HTTP 413 errors with GX Cloud)
MAX_DISTINCT_VALUES: Final[int] = 500
