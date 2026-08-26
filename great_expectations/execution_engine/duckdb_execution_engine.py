from __future__ import annotations

import datetime
import logging
import uuid
from typing import TYPE_CHECKING, Any, Optional, Tuple, cast

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility.duckdb import duckdb
from great_expectations.compatibility.pandas import pandas as pd
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.batch import BatchMarkers
from great_expectations.core.batch_spec import (
    BatchSpec,
    PathBatchSpec,
    RuntimeDataBatchSpec,
)
from great_expectations.core.id_dict import IDDict
from great_expectations.execution_engine.duckdb_batch_data import DuckDBBatchData
from great_expectations.execution_engine.duckdb_sql_utils import (
    quote_ident,
    sql_literal,
    sql_literal_list,
)
from great_expectations.execution_engine.execution_engine import ExecutionEngine
from great_expectations.expectations.row_conditions import (
    AndCondition,
    ComparisonCondition,
    Condition,
    NullityCondition,
    Operator,
    OrCondition,
    PassThroughCondition,
    deserialize_row_condition,
)
from great_expectations.util import convert_to_json_serializable  # noqa: TID251 # FIXME CoP

if TYPE_CHECKING:
    from great_expectations.execution_engine.execution_engine import (
        MetricComputationConfiguration,
    )
    from great_expectations.validator.computed_metric import MetricValue
    from great_expectations.validator.metric_configuration import MetricConfigurationID

logger = logging.getLogger(__name__)

_COMPARISON_OPERATOR_TO_SQL = {
    Operator.EQUAL: "=",
    Operator.NOT_EQUAL: "!=",
    Operator.LESS_THAN: "<",
    Operator.LESS_THAN_OR_EQUAL: "<=",
    Operator.GREATER_THAN: ">",
    Operator.GREATER_THAN_OR_EQUAL: ">=",
}


class DuckDBExecutionEngine(ExecutionEngine):
    """An ExecutionEngine backed directly by the `duckdb` Python package.

    Unlike `SqlAlchemyExecutionEngine`, this engine does not go through SQLAlchemy at all:
    batches are `duckdb.DuckDBPyRelation` objects, and metrics are computed by building raw
    SQL expression strings that are executed via the relation's `.filter()`/`.aggregate()`
    API. This trades SQLAlchemy's automatic quoting/escaping for a dependency-light engine,
    so every SQL fragment built here or in a `_duckdb` metric partial must be constructed via
    `great_expectations.expectations.metrics.duckdb_sql_utils` rather than raw f-strings of
    user-controlled values (column names, `in_set` members, regex patterns, etc.).
    """

    def __init__(self, *args, connection_string: Optional[str] = None, **kwargs) -> None:
        self._connection: duckdb.DuckDBPyConnection = duckdb.connect(
            connection_string or ":memory:"
        )
        super().__init__(*args, **kwargs)

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        return self._connection

    def close(self) -> None:
        self._connection.close()

    @override
    def load_batch_data(self, batch_id: str, batch_data) -> None:
        if pd and isinstance(batch_data, pd.DataFrame):
            batch_data = DuckDBBatchData(self, self.connection.from_df(batch_data))
        elif isinstance(batch_data, duckdb.DuckDBPyRelation):
            batch_data = DuckDBBatchData(self, batch_data)
        elif not isinstance(batch_data, DuckDBBatchData):
            raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                "DuckDBExecutionEngine requires batch data that is a pandas DataFrame, a "
                "duckdb.DuckDBPyRelation, or a DuckDBBatchData object."
            )
        super().load_batch_data(batch_id=batch_id, batch_data=batch_data)

    @override
    def get_batch_data_and_markers(
        self, batch_spec: BatchSpec
    ) -> Tuple[DuckDBBatchData, BatchMarkers]:
        batch_markers = BatchMarkers(
            {
                "ge_load_time": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y%m%dT%H%M%S.%fZ"
                )
            }
        )

        relation: duckdb.DuckDBPyRelation
        if isinstance(batch_spec, RuntimeDataBatchSpec):
            batch_data = batch_spec.batch_data
            if isinstance(batch_data, str):
                raise gx_exceptions.ExecutionEngineError(  # noqa: TRY003 # FIXME CoP
                    f'DuckDBExecutionEngine has been passed a string type batch_data, "{batch_data}", '  # noqa: E501 # FIXME CoP
                    "which is illegal. Please check your config."
                )
            if isinstance(batch_data, DuckDBBatchData):
                relation = batch_data.relation
            elif pd and isinstance(batch_data, pd.DataFrame):
                relation = self.connection.from_df(batch_data)
            else:
                raise gx_exceptions.ExecutionEngineError(  # noqa: TRY003 # FIXME CoP
                    "RuntimeDataBatchSpec must provide a pandas DataFrame or DuckDBBatchData "
                    "object for DuckDBExecutionEngine."
                )
            batch_spec.batch_data = "DuckDBRelation"
        elif isinstance(batch_spec, PathBatchSpec):
            path = batch_spec.path
            reader_options = dict(batch_spec.reader_options or {})
            reader_method = batch_spec.reader_method
            if reader_method == "read_parquet" or str(path).lower().endswith((".parquet", ".pq")):
                scan_relation = self.connection.read_parquet(path, **reader_options)
            else:
                scan_relation = self.connection.read_csv(path, **reader_options)  # noqa: F841 # FIXME CoP
            # Materialize the scan into a real table rather than keeping the lazy
            # file-scan relation: every bundled metric query and condition lookup
            # calls .aggregate()/.filter() on this batch independently, and without
            # materializing, DuckDB re-parses the source file from scratch on each
            # one. A one-time materialization here means every later query hits an
            # in-memory columnar table instead. Using a TEMP table (rather than
            # scan_relation.create(), which is permanent) scopes it to this
            # connection's session -- it's dropped automatically on self.close(),
            # never touches an on-disk connection_string database, and works even
            # when that database is opened read-only.
            table_name = f"_gx_batch_{uuid.uuid4().hex}"
            self.connection.execute(
                f"CREATE TEMP TABLE {quote_ident(table_name)} AS SELECT * FROM scan_relation"
            )
            relation = self.connection.table(table_name)
        else:
            raise gx_exceptions.BatchSpecError(  # noqa: TRY003 # FIXME CoP
                "batch_spec must be of type RuntimeDataBatchSpec or PathBatchSpec for "
                f"DuckDBExecutionEngine, not {batch_spec.__class__.__name__}"
            )

        typed_batch_data = DuckDBBatchData(execution_engine=self, relation=relation)
        return typed_batch_data, batch_markers

    @override
    def get_domain_records(self, domain_kwargs: dict) -> duckdb.DuckDBPyRelation:  # noqa: C901, PLR0912 # FIXME CoP
        batch_id: Optional[str] = domain_kwargs.get("batch_id")
        data_object: DuckDBBatchData
        if batch_id is None:
            if self.batch_manager.active_batch_data:
                data_object = cast("DuckDBBatchData", self.batch_manager.active_batch_data)
            else:
                raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                    "No batch is specified, but could not identify a loaded batch."
                )
        elif batch_id in self.batch_manager.batch_data_cache:
            data_object = cast("DuckDBBatchData", self.batch_manager.batch_data_cache[batch_id])
        else:
            raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                f"Unable to find batch with batch_id {batch_id}"
            )

        relation: duckdb.DuckDBPyRelation = data_object.relation

        row_condition = domain_kwargs.get("row_condition")
        if row_condition is not None:
            if isinstance(row_condition, dict):
                row_condition = deserialize_row_condition(row_condition)

            if isinstance(row_condition, PassThroughCondition):
                raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                    "PassThroughCondition (pandas/spark syntax) is not supported for "
                    "DuckDBExecutionEngine. Please use the latest documented row_condition "
                    "syntax, which does not require condition_parser."
                )
            if not isinstance(row_condition, Condition):
                raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                    "DuckDBExecutionEngine only supports the structured row_condition syntax."
                )

            relation = relation.filter(self.condition_to_filter_clause(row_condition))

        if "column" in domain_kwargs:
            return relation

        if (
            "column_A" in domain_kwargs
            and "column_B" in domain_kwargs
            and "ignore_row_if" in domain_kwargs
        ):
            column_a = quote_ident(domain_kwargs["column_A"])
            column_b = quote_ident(domain_kwargs["column_B"])
            ignore_row_if = domain_kwargs["ignore_row_if"]
            if ignore_row_if == "both_values_are_missing":
                relation = relation.filter(f"NOT ({column_a} IS NULL AND {column_b} IS NULL)")
            elif ignore_row_if == "either_value_is_missing":
                relation = relation.filter(f"NOT ({column_a} IS NULL OR {column_b} IS NULL)")
            elif ignore_row_if != "neither":
                raise ValueError(f'Unrecognized value of ignore_row_if ("{ignore_row_if}").')  # noqa: TRY003 # FIXME CoP
            return relation

        if "column_list" in domain_kwargs and "ignore_row_if" in domain_kwargs:
            column_list = [quote_ident(name) for name in domain_kwargs["column_list"]]
            ignore_row_if = domain_kwargs["ignore_row_if"]
            if ignore_row_if == "all_values_are_missing":
                all_null = " AND ".join(f"{col} IS NULL" for col in column_list)
                relation = relation.filter(f"NOT ({all_null})")
            elif ignore_row_if == "any_value_is_missing":
                any_null = " OR ".join(f"{col} IS NULL" for col in column_list)
                relation = relation.filter(f"NOT ({any_null})")
            elif ignore_row_if != "never":
                raise ValueError(f'Unrecognized value of ignore_row_if ("{ignore_row_if}").')  # noqa: TRY003 # FIXME CoP
            return relation

        return relation

    @override
    def get_compute_domain(
        self,
        domain_kwargs: dict,
        domain_type,
        accessor_keys=None,
    ) -> Tuple[Any, dict, dict]:
        partitioned_domain_kwargs = self._partition_domain_kwargs(
            domain_kwargs, domain_type, accessor_keys
        )
        relation = self.get_domain_records(domain_kwargs=domain_kwargs)
        return (
            relation,
            partitioned_domain_kwargs.compute,
            partitioned_domain_kwargs.accessor,
        )

    @override
    def resolve_metric_bundle(
        self,
        metric_fn_bundle,
    ) -> dict[MetricConfigurationID, MetricValue]:
        resolved_metrics: dict[MetricConfigurationID, MetricValue] = {}

        domain_groups: dict[Any, dict] = {}
        bundled_metric_configuration: MetricComputationConfiguration
        for bundled_metric_configuration in metric_fn_bundle:
            domain_kwargs = bundled_metric_configuration.compute_domain_kwargs or {}
            if not isinstance(domain_kwargs, IDDict):
                domain_kwargs = IDDict(domain_kwargs)
            domain_id = domain_kwargs.to_id()

            group = domain_groups.setdefault(
                domain_id, {"domain_kwargs": domain_kwargs, "exprs": []}
            )
            alias = f"m{len(group['exprs'])}"
            group["exprs"].append(
                (bundled_metric_configuration.metric_fn, alias, bundled_metric_configuration)
            )

        for group in domain_groups.values():
            relation = self.get_domain_records(domain_kwargs=group["domain_kwargs"])
            aggregate_expr = ", ".join(f"({expr}) AS {alias}" for expr, alias, _ in group["exprs"])

            try:
                result_relation = relation.aggregate(aggregate_expr)
                row = result_relation.fetchone()
            except Exception as e:
                raise gx_exceptions.ExecutionEngineError(  # FIXME CoP
                    message=f"Error while executing DuckDB aggregate query: {e!s}"
                ) from e

            if row is None:
                raise gx_exceptions.ExecutionEngineError(  # FIXME CoP
                    message="DuckDB aggregate query unexpectedly returned no rows."
                )

            for idx, (_, _, bundled_metric_configuration) in enumerate(group["exprs"]):
                metric_id = bundled_metric_configuration.metric_configuration.id
                resolved_metrics[metric_id] = convert_to_json_serializable(data=row[idx])

        return resolved_metrics

    @override
    def condition_to_filter_clause(self, condition: Condition) -> str:
        output = super().condition_to_filter_clause(condition)
        if not isinstance(output, str):
            raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                f"Expected a SQL filter clause string, but got {output!r}"
            )
        return output

    @override
    def _comparison_condition_to_filter_clause(self, condition: ComparisonCondition) -> str:
        col = quote_ident(condition.column.name)
        op = condition.operator
        if op == Operator.IN:
            return f"{col} IN {sql_literal_list(condition.parameter)}"
        if op == Operator.NOT_IN:
            return f"{col} NOT IN {sql_literal_list(condition.parameter)}"

        sql_op = _COMPARISON_OPERATOR_TO_SQL.get(op)
        if sql_op is None:
            raise gx_exceptions.GreatExpectationsError(  # noqa: TRY003 # FIXME CoP
                f"Unsupported operator for DuckDBExecutionEngine: {op}"
            )
        return f"{col} {sql_op} {sql_literal(condition.parameter)}"

    @override
    def _nullity_condition_to_filter_clause(self, condition: NullityCondition) -> str:
        col = quote_ident(condition.column.name)
        return f"{col} IS NULL" if condition.is_null else f"{col} IS NOT NULL"

    @override
    def _and_condition_to_filter_clause(self, condition: AndCondition) -> str:
        clauses = [self.condition_to_filter_clause(c) for c in condition.conditions]
        return "(" + " AND ".join(clauses) + ")"

    @override
    def _or_condition_to_filter_clause(self, condition: OrCondition) -> str:
        clauses = [self.condition_to_filter_clause(c) for c in condition.conditions]
        return "(" + " OR ".join(clauses) + ")"
