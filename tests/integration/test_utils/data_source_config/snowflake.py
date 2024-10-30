from random import randint
from typing import Dict, List, Type, Union

import pandas as pd
import pytest

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.snowflake import (
    ARRAY as _ARRAY,
)
from great_expectations.compatibility.snowflake import (
    # BYTEINT as _BYTEINT,
    # CHARACTER as _CHARACTER,
    # DEC as _DEC,
    # DOUBLE as _DOUBLE,
    # FIXED as _FIXED,
    # GEOGRAPHY as _GEOGRAPHY,
    # GEOMETRY as _GEOMETRY,
    NUMBER as _NUMBER,
    # OBJECT as _OBJECT,
    # STRING as _STRING,
    # TEXT as _TEXT,
    # TIMESTAMP_LTZ as _TIMESTAMP_LTZ,
    # TIMESTAMP_NTZ as _TIMESTAMP_NTZ,
    # TIMESTAMP_TZ as _TIMESTAMP_TZ,
    # TINYINT as _TINYINT,
    # VARBINARY as _VARBINARY,
    # VARIANT as _,
)
from great_expectations.compatibility.snowflake import (
    SnowflakeType,
)
from great_expectations.compatibility.sqlalchemy import (
    Column,
    MetaData,
    Table,
    create_engine,
    insert,
)
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)


class SnowflakeTypeBase:
    type: type[SnowflakeType]

    def __new__(self, *args, **kwargs) -> SnowflakeType:
        return self.type(*args, **kwargs)


class ARRAY(SnowflakeTypeBase):
    type = _ARRAY


class NUMBER(SnowflakeTypeBase):
    type = _NUMBER


SnowflakeColumnType = Union[
    type[ARRAY],
    # type[BYTEINT],
    # type[CHARACTER],
    # type[DEC],
    # type[DOUBLE],
    # type[FIXED],
    # type[GEOGRAPHY],
    # type[GEOMETRY],
    type[NUMBER],
    # type[OBJECT],
    # type[STRING],
    # type[TEXT],
    # type[TIMESTAMP_LTZ],
    # type[TIMESTAMP_NTZ],
    # type[TIMESTAMP_TZ],
    # type[TINYINT],
    # type[VARBINARY],
    # type[VARIANT],
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


class SnowflakeConnectionConfig(BaseSettings):
    SNOWFLAKE_USER: str
    SNOWFLAKE_PW: str
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_DATABASE: str
    SNOWFLAKE_SCHEMA: str
    SNOWFLAKE_WAREHOUSE: str
    SNOWFLAKE_ROLE: str = "PUBLIC"

    @property
    def connection_string(self) -> str:
        return (
            f"snowflake://{self.SNOWFLAKE_USER}:{self.SNOWFLAKE_PW}"
            f"@{self.SNOWFLAKE_ACCOUNT}/{self.SNOWFLAKE_DATABASE}/{self.SNOWFLAKE_SCHEMA}"
            f"?warehouse={self.SNOWFLAKE_WAREHOUSE}&role={self.SNOWFLAKE_ROLE}"
        )


class SnowflakeBatchTestSetup(BatchTestSetup[SnowflakeDatasourceTestConfig]):
    def __init__(
        self,
        config: SnowflakeDatasourceTestConfig,
        data: pd.DataFrame,
    ) -> None:
        self.table_name = f"snowflake_expectation_test_table_{randint(0, 1000000)}"
        self.snowflake_connection_config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
        self.engine = create_engine(url=self.snowflake_connection_config.connection_string)
        self.metadata = MetaData()
        self.table: Union[Table, None] = None
        super().__init__(config=config, data=data)

    @override
    def make_batch(self) -> Batch:
        name = self._random_resource_name()
        return (
            self._context.data_sources.add_snowflake(
                name=name, connection_string=self.snowflake_connection_config.connection_string
            )
            .add_table_asset(
                name=name,
                table_name=self.table_name,
            )
            .add_batch_definition_whole_table(name=name)
            .get_batch()
        )

    @override
    def setup(self) -> None:
        column_types = self.get_column_types()
        columns: List[Column] = [
            Column(name, column_type) for name, column_type in column_types.items()
        ]
        self.table = Table(
            self.table_name,
            self.metadata,
            *columns,
            schema=self.snowflake_connection_config.SNOWFLAKE_SCHEMA,
        )
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

    def get_column_types(self) -> Dict[str, SnowflakeType]:
        if self.config.column_types is None:
            raise NotImplementedError("Column inference not implemented")
        else:
            # ensure we've filtered out our indirection types
            translated_type_dict: Dict[str, Union[SnowflakeType, Type[SnowflakeType]]] = {}
            for column_name, column_type in self.config.column_types.items():
                if isinstance(column_type, SnowflakeTypeBase):
                    translated_type_dict[column_name] = column_type.type
                else:
                    translated_type_dict[column_name] = column_type

            return translated_type_dict
