from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from functools import cached_property
from typing import TYPE_CHECKING, Dict, Generic, Mapping, Optional, Sequence, Type, Union

from typing_extensions import override

from great_expectations.compatibility.sqlalchemy import (
    Column,
    MetaData,
    Table,
    TextClause,
    create_engine,
    insert,
    sqltypes,
)
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.test_utils.data_source_config.base import BatchTestSetup, _ConfigT

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.compatibility.sqlalchemy import TypeEngine


@dataclass(frozen=True)
class _TableData:
    name: str
    df: pd.DataFrame
    table: Table


class SQLBatchTestSetup(BatchTestSetup[_ConfigT, TableAsset], ABC, Generic[_ConfigT]):
    @property
    @abstractmethod
    def connection_string(self) -> str:
        """Connection string used to connect to SQL backend."""

    @property
    @abstractmethod
    def use_schema(self) -> bool:
        """Whether to use a schema when connecting to SQL backend.

        If `True`, a schema will be automatically created.
        """

    @property
    def inferrable_types_lookup(self) -> Dict[Type, TypeEngine]:
        """Dict of Python type keys mapped to SQL dialect-specific SqlAlchemy types."""
        # implementations of the class can override this if more specific types are required
        return {
            str: sqltypes.VARCHAR,  # type: ignore[dict-item]
            int: sqltypes.INTEGER,  # type: ignore[dict-item]
            float: sqltypes.DECIMAL,  # type: ignore[dict-item]
            bool: sqltypes.BOOLEAN,  # type: ignore[dict-item]
            date: sqltypes.DATE,  # type: ignore[dict-item]
            datetime: sqltypes.DATETIME,  # type: ignore[dict-item]
        }

    def __init__(
        self,
        config: _ConfigT,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> None:
        self.engine = create_engine(url=self.connection_string)
        self.extra_data = extra_data
        self.metadata = MetaData()
        super().__init__(config, data)

    @override
    def make_batch(self) -> Batch:
        return self.asset.add_batch_definition_whole_table(
            name=self._random_resource_name()
        ).get_batch()

    @cached_property
    def table_name(self) -> str:
        return self.main_table_data.name

    @cached_property
    def main_table_data(self) -> _TableData:
        return self._create_table_data(
            name=self._create_table_name(),
            df=self.data,
            column_types=self.config.column_types or {},
        )

    @cached_property
    def extra_table_data(self) -> Mapping[str, _TableData]:
        return {
            label: self._create_table_data(
                name=self._create_table_name(label),
                df=df,
                column_types=self.config.extra_column_types.get(label, {}),
            )
            for label, df in self.extra_data.items()
        }

    @cached_property
    def tables(self) -> Sequence[Table]:
        extra_tables = [td.table for td in self.extra_table_data.values()]
        return [self.main_table_data.table, *extra_tables]

    @cached_property
    def schema(self) -> Union[str, None]:
        if self.use_schema:
            return self._random_resource_name()
        else:
            return None

    @override
    def setup(self) -> None:
        with self.engine.connect() as conn, conn.begin():
            # create schema if needed

            if self.schema:
                conn.execute(TextClause(f"CREATE SCHEMA {self.schema}"))

            # create tables
            all_table_data = self._ensure_all_table_data_created()
            self.metadata.create_all(self.engine)

            # insert data
            for table_data in all_table_data:
                # pd.DataFrame(...).to_dict("index") returns a dictionary where the keys are the row
                # index and the values are a dict of column names mapped to column values.
                # Then we pass that list of dicts in as parameters to our insert statement.
                #   INSERT INTO test_table (my_int_column, my_str_column) VALUES (?, ?)
                #   [...] [('1', 'foo'), ('2', 'bar')]
                conn.execute(
                    insert(table_data.table), list(table_data.df.to_dict("index").values())
                )

    @override
    def teardown(self) -> None:
        for table in self.tables:
            table.drop(self.engine)
        if self.schema:
            with self.engine.connect() as conn, conn.begin():
                conn.execute(TextClause(f"DROP SCHEMA {self.schema}"))

    def _create_table_name(self, label: Optional[str] = None) -> str:
        parts = ["expectation_test_table", label, self._random_resource_name()]
        return "_".join([part for part in parts if part])

    def _ensure_all_table_data_created(self) -> Sequence[_TableData]:
        return [self.main_table_data, *self.extra_table_data.values()]

    def _create_table_data(
        self, name: str, df: pd.DataFrame, column_types: Mapping[str, TypeEngine]
    ) -> _TableData:
        columns = self._get_column_types(df=df, column_types=column_types)
        table = self._create_table(name, columns=columns)
        return _TableData(
            name=name,
            df=df,
            table=table,
        )

    def _create_table(self, name: str, columns: Mapping[str, TypeEngine]) -> Table:
        column_list = [Column(col_name, col_type) for col_name, col_type in columns.items()]
        return Table(name, self.metadata, *column_list, schema=self.schema)

    def _get_column_types(
        self,
        df: pd.DataFrame,
        column_types: Mapping[str, TypeEngine],
    ) -> Mapping[str, TypeEngine]:
        all_column_types = self._infer_column_types(df)
        # prefer explicit types if they're provided
        all_column_types.update(column_types)
        untyped_columns = set(df.columns) - set(all_column_types.keys())
        if untyped_columns:
            config_class_name = self.config.__class__.__name__
            message = (
                f"Unable to infer types for the following column(s): "
                f"{', '.join(untyped_columns)}. \n"
                f"Please provide the missing types as the `column_types` "
                f"parameter when \ninstantiating {config_class_name}."
            )
            raise RuntimeError(message)
        return all_column_types

    def _infer_column_types(self, data: pd.DataFrame) -> Dict[str, TypeEngine]:
        inferred_column_types: Dict[str, TypeEngine] = {}
        for column, value_list in data.to_dict("list").items():
            python_type = type(value_list[0])
            if not all(isinstance(val, python_type) for val in value_list):
                raise RuntimeError(
                    f"Cannot infer type of column {column}. "
                    "Please provide an explicit column type in the test config."
                )
            inferred_type = self.inferrable_types_lookup.get(python_type)
            if inferred_type:
                inferred_column_types[str(column)] = inferred_type
        return inferred_column_types
