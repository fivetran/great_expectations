from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Generic, List, Mapping, Type, Union

from typing_extensions import override

from great_expectations.compatibility.sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    insert,
    sqltypes,
)
from tests.integration.test_utils.data_source_config.base import BatchTestSetup, _ConfigT

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.compatibility.sqlalchemy import TypeEngine


@dataclass
class TableData:
    name: str
    df: pd.DataFrame
    column_types: Dict[str, TypeEngine]
    table: Union[Table, None] = None


class SQLBatchTestSetup(BatchTestSetup, ABC, Generic[_ConfigT]):
    @property
    @abstractmethod
    def connection_string(self) -> str:
        """Connection string used to connect to SQL backend."""

    @property
    @abstractmethod
    def schema(self) -> Union[str, None]:
        """Schema -- if any -- to use when connecting to SQL backend."""

    @property
    def inferrable_types_lookup(self) -> Dict[Type, TypeEngine]:
        """Dict of Python type keys mapped to SQL dialect-specific SqlAlchemy types."""
        # implementations of the class can override this if more specific types are required
        return {
            str: sqltypes.VARCHAR,  # type: ignore[dict-item]
            int: sqltypes.INTEGER,  # type: ignore[dict-item]
            float: sqltypes.DECIMAL,  # type: ignore[dict-item]
            bool: sqltypes.BOOLEAN,  # type: ignore[dict-item]
        }

    def __init__(
        self,
        config: _ConfigT,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
    ) -> None:
        self.extra_data = extra_data
        self.table_name = f"{config.label}_expectation_test_table_{self._random_resource_name()}"
        self.engine = create_engine(url=self.connection_string)
        self.metadata = MetaData()
        self.tables: List[Table] = []
        super().__init__(config, data)

    @override
    def setup(self) -> None:
        main_table_data = TableData(
            name=self.table_name, df=self.data, column_types=self.config.column_types or {}
        )
        extra_table_data = [
            TableData(name=name, df=df, column_types=self.config.extra_column_types.get(name, {}))
            for name, df in self.extra_data.items()
        ]
        all_table_data = [main_table_data, *extra_table_data]

        # create tables
        for table_data in all_table_data:
            columns = self.get_column_types(table_data)
            table = self.create_table(table_data.name, columns=columns)
            self.tables.append(table)
            table_data.table = table
        self.metadata.create_all(self.engine)

        # insert data
        with self.engine.connect() as conn, conn.begin():
            for table_data in all_table_data:
                if table_data.table is None:
                    raise RuntimeError("Table must be created before data can be loaded.")
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

    def create_table(self, name: str, columns: Mapping[str, TypeEngine]) -> Table:
        column_list = [Column(col_name, col_type) for col_name, col_type in columns.items()]
        return Table(name, self.metadata, *column_list, schema=self.schema)

    def get_column_types(
        self,
        table_data: TableData,
    ) -> Mapping[str, TypeEngine]:
        column_types = self.infer_column_types(table_data.df)
        # prefer explicit types if they're provided
        column_types.update(table_data.column_types)
        untyped_columns = set(table_data.df.columns) - set(column_types.keys())
        if untyped_columns:
            config_class_name = self.config.__class__.__name__
            message = (
                f"Unable to infer types for the following column(s): "
                f"{', '.join(untyped_columns)}. \n"
                f"Please provide the missing types as the `column_types` "
                f"parameter when \ninstantiating {config_class_name}."
            )
            raise RuntimeError(message)
        return column_types

    def infer_column_types(self, data: pd.DataFrame) -> Dict[str, TypeEngine]:
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
