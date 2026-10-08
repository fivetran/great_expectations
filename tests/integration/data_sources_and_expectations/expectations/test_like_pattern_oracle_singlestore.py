from __future__ import annotations

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    OracleDatasourceTestConfig,
    SingleStoreDatasourceTestConfig,
)

PREFIXED_PATTERNS = "prefixed_patterns"
DATA = pd.DataFrame({PREFIXED_PATTERNS: ["foo_abc", "foo_def", "foo_ghi"]})


@parameterize_batch_for_data_sources(
    data_source_configs=[OracleDatasourceTestConfig(), SingleStoreDatasourceTestConfig()],
    data=DATA,
)
def test_like_pattern_expectations_evaluate_on_oracle_and_singlestore(
    batch_for_datasource: Batch,
) -> None:
    """Both dialects support LIKE natively, so each expectation must return a verdict."""
    match = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToMatchLikePattern(column=PREFIXED_PATTERNS, like_pattern="foo%")
    )
    assert match.success, match.exception_info

    match_list = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToMatchLikePatternList(
            column=PREFIXED_PATTERNS, like_pattern_list=["foo%"], match_on="any"
        )
    )
    assert match_list.success, match_list.exception_info

    not_match = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToNotMatchLikePattern(column=PREFIXED_PATTERNS, like_pattern="zz%")
    )
    assert not_match.success, not_match.exception_info

    not_match_list = batch_for_datasource.validate(
        gxe.ExpectColumnValuesToNotMatchLikePatternList(
            column=PREFIXED_PATTERNS, like_pattern_list=["zz%"]
        )
    )
    assert not_match_list.success, not_match_list.exception_info
