from random import randint
from typing import Dict, Union

import pandas as pd
import pytest
from sqlalchemy import Column, MetaData, Table, create_engine, insert

# commented out types are present in SqlAlchemy 2.x but not 1.4
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    BIGINT,
    BIT,
    BOOLEAN,
    BYTEA,
    CHAR,
    CIDR,
    # CITEXT,
    DATE,
    # DATEMULTIRANGE,
    DATERANGE,
    # DOMAIN,
    DOUBLE_PRECISION,
    ENUM,
    FLOAT,
    HSTORE,
    INET,
    # INT4MULTIRANGE,
    INT4RANGE,
    # INT8MULTIRANGE,
    INT8RANGE,
    INTEGER,
    INTERVAL,
    JSON,
    JSONB,
    # JSONPATH,
    MACADDR,
    # MACADDR8,
    MONEY,
    NUMERIC,
    # NUMMULTIRANGE,
    NUMRANGE,
    OID,
    REAL,
    REGCLASS,
    # REGCONFIG,
    SMALLINT,
    TEXT,
    TIME,
    TIMESTAMP,
    # TSMULTIRANGE,
    # TSQUERY,
    # TSRANGE,
    # TSTZMULTIRANGE,
    TSTZRANGE,
    TSVECTOR,
    UUID,
    VARCHAR,
)

from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.test_utils.data_source_config.base import (
    BatchTestSetup,
    DataSourceTestConfig,
)

# Sqlalchemy follows the convention of exporting all known valid types for a given dialect
# as uppercase types from the namespace `sqlalchemy.dialects.<dialect>
# commented out types are present in SqlAlchemy 2.x but not 1.4
PostgresColumnType = Union[
    type[ARRAY],
    type[BIGINT],
    type[BIT],
    type[BOOLEAN],
    type[BYTEA],
    type[CHAR],
    type[CIDR],
    # type[CITEXT],
    type[DATE],
    # type[DATEMULTIRANGE],
    type[DATERANGE],
    # type[DOMAIN],
    type[DOUBLE_PRECISION],
    type[ENUM],
    type[FLOAT],
    type[HSTORE],
    type[INET],
    # type[INT4MULTIRANGE],
    type[INT4RANGE],
    # type[INT8MULTIRANGE],
    type[INT8RANGE],
    type[INTEGER],
    type[INTERVAL],
    type[JSON],
    type[JSONB],
    # type[JSONPATH],
    type[MACADDR],
    # type[MACADDR8],
    type[MONEY],
    type[NUMERIC],
    # type[NUMMULTIRANGE],
    type[NUMRANGE],
    type[OID],
    type[REAL],
    type[REGCLASS],
    # type[REGCONFIG],
    type[SMALLINT],
    type[TEXT],
    type[TIME],
    type[TIMESTAMP],
    # type[TSMULTIRANGE],
    # type[TSQUERY],
    # type[TSRANGE],
    # type[TSTZMULTIRANGE],
    type[TSTZRANGE],
    type[TSVECTOR],
    type[UUID],
    type[VARCHAR],
]


class PostgreSQLDatasourceTestConfig(DataSourceTestConfig[PostgresColumnType]):
    @property
    @override
    def label(self) -> str:
        return "postgresql"

    @property
    @override
    def pytest_mark(self) -> pytest.MarkDecorator:
        return pytest.mark.postgresql

    @override
    def create_batch_setup(
        self, data: pd.DataFrame, request: pytest.FixtureRequest
    ) -> BatchTestSetup:
        return PostgresBatchTestSetup(
            data=data,
            config=self,
        )


class PostgresBatchTestSetup(BatchTestSetup[PostgreSQLDatasourceTestConfig]):
    def __init__(
        self,
        config: PostgreSQLDatasourceTestConfig,
        data: pd.DataFrame,
    ) -> None:
        self.table_name = f"postgres_expectation_test_table_{randint(0, 1000000)}"
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
            self._context.data_sources.add_postgres(
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
        columns = [Column(name, type) for name, type in self.get_column_types().items()]
        self.table = Table(self.table_name, self.metadata, *columns, schema=self.schema)
        self.metadata.create_all(self.engine)
        with self.engine.begin() as conn:
            # pd.DataFrame(...).to_dict("index") returns a dictionary where the keys are the row
            # index and the values are a dict of column names mapped to column values.
            # Then we pass that list of dicts in as parameters to our insert statement.
            #   INSERT INTO test_table (my_int_column, my_str_column) VALUES (?, ?)
            #   [...] [('1', 'foo'), ('2', 'bar')]
            conn.execute(insert(self.table), list(self.data.to_dict("index").values()))

    @override
    def teardown(self) -> None:
        if self.table is not None:
            self.table.drop(self.engine)

    def get_column_types(self) -> Dict[str, PostgresColumnType]:
        if self.config.column_types is None:
            return {}
        return self.config.column_types
