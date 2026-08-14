from __future__ import annotations

import logging

from scipy import stats

from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnAggregateMetricProvider,
    column_aggregate_value,
)
from great_expectations.expectations.metrics.util import (
    _scipy_distribution_positional_args_from_dict,
    validate_distribution_parameters,
)

logger = logging.getLogger(__name__)


class ColumnParameterizedDistributionKSTestPValue(ColumnAggregateMetricProvider):
    """MetricProvider Class for Aggregate Standard Deviation metric"""

    metric_name = "column.parameterized_distribution_ks_test_p_value"
    value_keys = ("distribution", "p_value", "params")

    @column_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column, distribution, p_value=0.05, params=None, **kwargs):
        if p_value <= 0 or p_value >= 1:
            raise ValueError("p_value must be between 0 and 1 exclusive")  # noqa: TRY003 # FIXME CoP

        validate_distribution_parameters(distribution=distribution, params=params)

        # Format arguments for scipy.kstest
        if isinstance(params, dict):
            positional_parameters = _scipy_distribution_positional_args_from_dict(
                distribution, params
            )
        else:
            positional_parameters = params

        # K-S Test. Build a frozen distribution from the requested parameters and test against
        # its CDF. Passing a distribution name with `args=` is no longer supported by scipy for
        # parameterless CDFs (e.g. ``norm``), so freeze the distribution explicitly instead.
        frozen_distribution = getattr(stats, distribution)(*(positional_parameters or ()))
        ks_result = stats.kstest(column, frozen_distribution.cdf)

        return ks_result
