from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource
from great_expectations.execution_engine.redshift_execution_engine import RedshiftExecutionEngine

if TYPE_CHECKING:
    from great_expectations.execution_engine.sqlalchemy_execution_engine import (
        SqlAlchemyExecutionEngine,
    )


class RedshiftDsn(pydantic.AnyUrl):
    allowed_schemes = {
        "redshift+psycopg2",
    }


class RedshiftDatasource(SQLDatasource):
    """Adds a redshift datasource to the data context using psycopg2.

    Args:
        name: The name of this redshift datasource.
        connection_string: The SQLAlchemy connection string used to connect to the redshift
            database. This will use a redshift with psycopg2. For example:
            "redshift+psycopg2://username@host.amazonaws.com:5439/database"
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["redshift"] = "redshift"  # type: ignore[assignment] # This is a hardcoded constant
    connection_string: Union[ConfigStr, RedshiftDsn]

    @property
    @override
    def execution_engine_type(self) -> Type[SqlAlchemyExecutionEngine]:
        """Returns the default execution engine type."""
        return RedshiftExecutionEngine
