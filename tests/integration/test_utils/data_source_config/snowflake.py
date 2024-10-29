from random import randint
from typing import Union, Dict

import pandas as pd
import pytest
from sqlalchemy import Column, MetaData, Table, create_engine, insert

from great_expectations.compatibility.snowflake.snowflaketypes import (
    TEXT,
    CHARACTER,
    DEC,
    DOUBLE,
    FIXED,
    NUMBER,
    BYTEINT,
    STRING,
    TINYINT,
    VARBINARY,
    VARIANT,
    OBJECT,
    ARRAY,
    TIMESTAMP_TZ,
    TIMESTAMP_LTZ,
    TIMESTAMP_NTZ,
    GEOGRAPHY,
    GEOMETRY,
)

from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


SnowflakeColumnType = Union[
    type[TEXT],
    type[CHARACTER],
    type[DEC],
    type[DOUBLE],
    type[FIXED],
    type[NUMBER],
    type[BYTEINT],
    type[STRING],
    type[TINYINT],
    type[VARBINARY],
    type[VARIANT],
    type[OBJECT],
    type[ARRAY],
    type[TIMESTAMP_TZ],
    type[TIMESTAMP_LTZ],
    type[TIMESTAMP_NTZ],
    type[GEOGRAPHY],
    type[GEOMETRY],
]


class SnowflakeDatasourceTestConfig(DataSourceTestConfig[SnowflakeColumnType]):

    @property
    @override
    def label(self) -> str:
        return "snowflake"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.snowflake

    @override
    def create_batch_setup(
        self, data: pd.DataFrame, request: pytest.FixtureRequest
    ) -> BatchTestSetup:
        return SnowflakeBatchTestSetup(
            data=data,
            config=self,
        )


class SnowflakeBatchTestSetup(BatchTestSetup[SnowflakeDatasourceTestConfig]):
    def __init__(
        self,
        config: SnowflakeDatasourceTestConfig,
        data: pd.DataFrame,
    ) -> None:
        self.table_name = f"snowflake_expectation_test_table_{randint(0, 1000000)}"
        self.connection_string = "postgresql+psycopg2://postgres@localhost:5432/test_ci"
        self.engine = create_engine(url=self.connection_string)
        self.metadata = MetaData()
        self.table: Union[Table, None] = None
        self.schema = "public"
        super().__init__(config=config, data=data)

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self._context.data_sources.add_snowflake(
                name=name, connection_string=self.connection_string
            )
            .add_table_asset(
                name=name,
                table_name=self.table_name,
                schema_name=self.schema,
            )
            .add_batch_definition_whole_table(name=name)
            .get_batch()
        )

    @override
    def setup(self) -> None:
        column_types = self.get_column_types()
        columns = [
            Column(name, column_type) for name, column_type in column_types.items()
        ]
        self.table = Table(self.table_name, self.metadata, *columns, schema=self.schema)
        self.metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            # pd.DataFrame(...).to_dict("index") returns a dictionary where the keys are the row
            # index and the values are a dict of column names mapped to column values.
            # Then we pass that list of dicts in as parameters to our insert statement.
            #   INSERT INTO test_table (my_int_column, my_str_column) VALUES (?, ?)
            #   [...] [('1', 'foo'), ('2', 'bar')]
            conn.execute(insert(self.table), list(self.data.to_dict("index").values()))
            conn.commit()

    @override
    def teardown(self) -> None:
        if self.table is not None:
            self.table.drop(self.engine)

    def get_column_types(self) -> Dict[str, SnowflakeColumnType]:
        if self.config.column_types is None:
            raise NotImplementedError("Column inference not implemented")
        else:
            return self.config.column_types
