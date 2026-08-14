from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Type, Union

import numpy as np
import pandas as pd
from scipy import stats

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.suite_parameters import (
    SuiteParameterDict,  # noqa: TC001 # FIXME CoP
)
from great_expectations.expectations.expectation import (
    BatchExpectation,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import (
    FAILURE_SEVERITY_DESCRIPTION,
)
from great_expectations.render import (
    LegacyRendererType,
    RenderedStringTemplateContent,
)
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    RendererConfiguration,
    RendererValueType,
)
from great_expectations.render.util import substitute_none_for_missing
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationValidationResult,
    )
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )
    from great_expectations.render.renderer_configuration import AddParamArgs
    from great_expectations.validator.validator import ValidationDependencies

EXPECTATION_SHORT_DESCRIPTION = (
    "Expect the Cramér's phi (V) measure of association between two columns to be less than or "
    "equal to a threshold."
)
COLUMN_A_DESCRIPTION = "The first column name."
COLUMN_B_DESCRIPTION = "The second column name."
THRESHOLD_DESCRIPTION = (
    "The maximum Cramér's phi value for which to return success=True. Cramér's phi ranges from 0 "
    "(no association / independent) to 1 (perfect association). Defaults to 0.1."
)
BINS_A_DESCRIPTION = (
    "Explicit bin edges (numeric column) or groups of values (categorical column) used to "
    "discretize column_A before building the contingency table."
)
BINS_B_DESCRIPTION = "As bins_A, but for column_B."
N_BINS_A_DESCRIPTION = (
    "The number of bins to use for column_A when bins_A is not provided. Defaults to 10."
)
N_BINS_B_DESCRIPTION = "As n_bins_A, but for column_B."
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.PANDAS.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.NUMERIC.value]


def _get_binned_values(  # noqa: C901, PLR0912 # FIXME CoP
    series: pd.Series, bins: Optional[list], n_bins: Optional[int]
):
    """Get binned values of a series, binning numeric data into intervals and collapsing rare
    categorical values, so that a contingency table can be built.
    """
    if n_bins is None:
        n_bins = 10

    # Bin any real-valued numeric column into intervals. Use is_numeric_dtype so that width-specific
    # dtypes (int32/float32) and pandas nullable dtypes (Int64/Float64) are treated as numeric too;
    # a hardcoded dtype list silently routed those to the categorical branch. Booleans are excluded
    # so they stay categorical (a two-value column is more meaningful ungrouped than binned).
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        if bins is not None:
            sorted_bins = sorted(np.unique(bins))
            if np.min(series) < sorted_bins[0]:
                sorted_bins = [np.min(series), *sorted_bins]
            if np.max(series) > sorted_bins[-1]:
                sorted_bins = [*sorted_bins, np.max(series)]
            edges = np.array(sorted_bins, dtype=float)
        else:
            edges = np.array(
                np.histogram_bin_edges(series[series.notnull()], bins=n_bins), dtype=float
            )

        # Make sure max of series is included in rightmost bin
        edges[-1] = np.nextafter(edges[-1], edges[-1] + 1)

        # Create labels for the returned series. Round each edge to enough decimal places that
        # narrow bins stay distinguishable: the smaller the bin width, the more decimals we need.
        # (A naive int(log10(width)) + 2 inverts this and collapses sub-0.01 bins to identical
        # labels, which makes Categorical.from_codes raise on duplicate categories.)
        min_width = float(min(edges[1:] - edges[:-1]))
        precision = max(2, 2 - int(np.floor(np.log10(min_width))))
        labels = [
            f"[{round(lower, precision)}, {round(upper, precision)})"
            for lower, upper in itertools.pairwise(edges)
        ]
        if series.isnull().any():
            # Missing get digitized into bin = n_bins + 1
            labels += ["(missing)"]

        return pd.Categorical.from_codes(
            codes=np.digitize(series, bins=edges) - 1,
            categories=pd.Index(labels),
            ordered=True,
        )

    else:
        # Cast to object first: fillna/replace below introduce the "(missing)" and "(other)"
        # sentinels, and adding a value that isn't an existing category to a categorical-dtype
        # series in place raises. Casting to object (a no-op for string/object columns) lets the
        # sentinels through; we re-cast to category at the end.
        series = series.astype(object)
        if bins is None:
            value_counts = series.value_counts(sort=True)
            if len(value_counts) < n_bins + 1:
                return series.fillna("(missing)").astype("category")
            else:
                other_values = sorted(value_counts.index[n_bins:])
                replace = dict.fromkeys(other_values, "(other)")
        else:
            replace = {}
            for x in bins:
                replace.update({value: ", ".join(x) for value in x})
        return series.replace(to_replace=replace).fillna("(missing)").astype("category")


def _get_crosstab(  # noqa: PLR0913 # FIXME CoP
    series_A: pd.Series,
    series_B: pd.Series,
    bins_A: Optional[list],
    bins_B: Optional[list],
    n_bins_A: Optional[int],
    n_bins_B: Optional[int],
) -> pd.DataFrame:
    """Get the contingency table (crosstab) of two series, binning values if necessary."""
    binned_A = _get_binned_values(series_A, bins_A, n_bins_A)
    binned_B = _get_binned_values(series_B, bins_B, n_bins_B)
    return pd.crosstab(binned_A, columns=binned_B)


class ExpectColumnPairCramersPhiValueToBeLessThan(BatchExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectColumnPairCramersPhiValueToBeLessThan is a \
    Batch Expectation.

    BatchExpectations are one of the most common types of Expectation.
    They are evaluated for an entire Batch, and answer a semantic question about the Batch itself.

    Cramér's phi (also written Cramér's V) measures the strength of association between two \
    categorical variables, derived from the Chi-square statistic of their contingency table. \
    A value near 0 indicates the columns are (close to) independent; larger values indicate \
    stronger association. Numeric columns are discretized into bins before the table is built.

    Args:
        column_A (str): \
            {COLUMN_A_DESCRIPTION}
        column_B (str): \
            {COLUMN_B_DESCRIPTION}
        threshold (float): \
            {THRESHOLD_DESCRIPTION}
        bins_A (list or None): \
            {BINS_A_DESCRIPTION}
        bins_B (list or None): \
            {BINS_B_DESCRIPTION}
        n_bins_A (int or None): \
            {N_BINS_A_DESCRIPTION}
        n_bins_B (int or None): \
            {N_BINS_B_DESCRIPTION}

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
            For more detail, see [result_format](https://docs.greatexpectations.io/docs/reference/expectations/result_format).
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see [catch_exceptions](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#catch_exceptions).
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without \
            modification. For more detail, see [meta](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#meta).
        severity (str or None): \
            {FAILURE_SEVERITY_DESCRIPTION} \
            For more detail, see [failure severity](https://docs.greatexpectations.io/docs/cloud/expectations/expectations_overview/#failure-severity).

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

        Exact fields vary depending on the values passed to result_format, catch_exceptions, and meta.

    Notes:
        * observed_value field in the result object is customized for this expectation to be the \
          Cramér's phi (V) value.
        * details.crosstab is customized for this expectation to be a serializable representation \
          of the contingency table between column_A and column_B.
        * The Expectation succeeds when the observed Cramér's phi is less than or equal to threshold.

    Supported Data Sources:
        [{SUPPORTED_DATA_SOURCES[0]}](https://docs.greatexpectations.io/docs/application_integration_support/)

    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}

    Example Data:
                test 	test2
            0 	"A"     "X"
            1 	"A"     "Y"
            2 	"B"     "X"
            3   "B"     "Y"

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnPairCramersPhiValueToBeLessThan(
                    column_A="test",
                    column_B="test2",
                    threshold=0.1
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.0
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input (test2 is fully determined by test, so the columns are perfectly associated):
                test 	test2
            0 	"A"     "X"
            1 	"A"     "X"
            2 	"B"     "Y"
            3   "B"     "Y"

                ExpectColumnPairCramersPhiValueToBeLessThan(
                    column_A="test",
                    column_B="test2",
                    threshold=0.1
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 1.0
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """  # noqa: E501 # FIXME CoP

    column_A: str = pydantic.Field(min_length=1, description=COLUMN_A_DESCRIPTION)
    column_B: str = pydantic.Field(min_length=1, description=COLUMN_B_DESCRIPTION)
    threshold: Union[float, SuiteParameterDict] = pydantic.Field(
        default=0.1, description=THRESHOLD_DESCRIPTION
    )
    bins_A: Optional[List[Any]] = pydantic.Field(default=None, description=BINS_A_DESCRIPTION)
    bins_B: Optional[List[Any]] = pydantic.Field(default=None, description=BINS_B_DESCRIPTION)
    n_bins_A: Optional[int] = pydantic.Field(default=None, description=N_BINS_A_DESCRIPTION)
    n_bins_B: Optional[int] = pydantic.Field(default=None, description=N_BINS_B_DESCRIPTION)

    library_metadata: ClassVar[Dict[str, Union[str, list, bool]]] = {
        "maturity": "production",
        "tags": [
            "core expectation",
            "multi-column expectation",
            "distributional expectation",
        ],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }
    _library_metadata = library_metadata

    success_keys = (
        "column_A",
        "column_B",
        "threshold",
        "bins_A",
        "bins_B",
        "n_bins_A",
        "n_bins_B",
    )
    args_keys = (
        "column_A",
        "column_B",
    )

    class Config:
        title = "Expect column pair Cramér's phi value to be less than"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any],
            model: Type[ExpectColumnPairCramersPhiValueToBeLessThan],
        ) -> None:
            BatchExpectation.Config.schema_extra(schema, model)
            schema["properties"]["metadata"]["properties"].update(
                {
                    "data_quality_issues": {
                        "title": "Data Quality Issues",
                        "type": "array",
                        "const": DATA_QUALITY_ISSUES,
                    },
                    "library_metadata": {
                        "title": "Library Metadata",
                        "type": "object",
                        "const": model._library_metadata,
                    },
                    "short_description": {
                        "title": "Short Description",
                        "type": "string",
                        "const": EXPECTATION_SHORT_DESCRIPTION,
                    },
                    "supported_data_sources": {
                        "title": "Supported Data Sources",
                        "type": "array",
                        "const": SUPPORTED_DATA_SOURCES,
                    },
                }
            )

    @classmethod
    @override
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration:
        add_param_args: AddParamArgs = (
            ("column_A", RendererValueType.STRING),
            ("column_B", RendererValueType.STRING),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        params = renderer_configuration.params
        if not params.column_A or not params.column_B:
            renderer_configuration.template_str = (
                "Cramér's phi association requires two columns: missing column."
            )
        else:
            renderer_configuration.template_str = (
                "Values in $column_A and $column_B must be independent."
            )
        return renderer_configuration

    @classmethod
    @override
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_suite_parameter_string
    def _prescriptive_renderer(  # type: ignore[override] # TODO: Fix this type ignore
        cls,
        configuration: ExpectationConfiguration,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(configuration.kwargs, ["column_A", "column_B"])
        if (params["column_A"] is None) or (params["column_B"] is None):
            template_str = "Cramér's phi association requires two columns: missing column."
        else:
            template_str = "Values in $column_A and $column_B must be independent."

        return [
            RenderedStringTemplateContent(
                content_block_type="string_template",
                string_template={
                    "template": template_str,
                    "params": params,
                    "styling": styling,
                },
            )
        ]

    @override
    def get_validation_dependencies(
        self,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> ValidationDependencies:
        validation_dependencies: ValidationDependencies = super().get_validation_dependencies(
            execution_engine, runtime_configuration
        )
        domain_kwargs = self.configuration.get_domain_kwargs()
        validation_dependencies.set_metric_configuration(
            metric_name="table.head",
            metric_configuration=MetricConfiguration(
                metric_name="table.head",
                metric_domain_kwargs=domain_kwargs,
                metric_value_kwargs={"n_rows": None, "fetch_all": True},
            ),
        )
        return validation_dependencies

    @override
    def _validate(
        self,
        metrics: Dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        configuration = self.configuration
        column_A = configuration.kwargs.get("column_A", self._get_default_value("column_A"))
        column_B = configuration.kwargs.get("column_B", self._get_default_value("column_B"))
        threshold = configuration.kwargs.get("threshold", self._get_default_value("threshold"))
        bins_A = configuration.kwargs.get("bins_A", self._get_default_value("bins_A"))
        bins_B = configuration.kwargs.get("bins_B", self._get_default_value("bins_B"))
        n_bins_A = configuration.kwargs.get("n_bins_A", self._get_default_value("n_bins_A"))
        n_bins_B = configuration.kwargs.get("n_bins_B", self._get_default_value("n_bins_B"))

        df: pd.DataFrame = metrics["table.head"]
        for column in (column_A, column_B):
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in batch.")  # noqa: TRY003 # FIXME CoP

        crosstab = _get_crosstab(df[column_A], df[column_B], bins_A, bins_B, n_bins_A, n_bins_B)

        counts = crosstab.to_numpy()
        n = float(counts.sum())
        min_dimension = min(crosstab.shape)

        if n == 0 or min_dimension < 2:  # noqa: PLR2004 # FIXME CoP
            # Association is undefined / cannot exceed threshold when one variable is constant.
            cramers_phi = 0.0
        else:
            chi2_statistic = stats.chi2_contingency(counts)[0]
            # See e.g. https://en.wikipedia.org/wiki/Cram%C3%A9r%27s_V
            cramers_phi = float(max(min(np.sqrt(chi2_statistic / n / (min_dimension - 1)), 1), 0))

        # Success is inclusive at the boundary (phi == threshold passes), matching the legacy V2
        # behavior of this expectation and the sibling ExpectColumnKlDivergenceToBeLessThan. This is
        # deliberate: phi is clamped to exactly 0.0 for degenerate tables (n == 0 or a constant
        # column), and threshold=0 must still succeed in that case.
        return {
            "success": bool(cramers_phi <= threshold),
            "result": {
                "observed_value": cramers_phi,
                "details": {
                    "crosstab": {
                        "row_variable": column_A,
                        "column_variable": column_B,
                        "rows": [str(idx) for idx in crosstab.index],
                        "columns": [str(col) for col in crosstab.columns],
                        "counts": counts.astype(int).tolist(),
                    },
                },
            },
        }
