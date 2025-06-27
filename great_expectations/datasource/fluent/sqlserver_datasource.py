from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Final, Literal, Optional

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.sql_datasource import (
    SQLDatasource,
    TableAsset,
    to_lower_if_not_quoted,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import BatchMetadata

LOGGER: Final[logging.Logger] = logging.getLogger(__name__)

MISSING: Final = object()  # sentinel value to indicate missing values


@public_api
class SQLServerDatasource(SQLDatasource):
    """Adds a SQL Server datasource to the data context with automatic schema detection.

    For datasources named with pattern "Database.Schema" (like "TransformedDataDnA.CR"), 
    automatically scopes table discovery and asset creation to that specific schema.

    Args:
        name: The name of this SQL Server datasource. Use "Database.Schema" pattern for automatic schema detection.
        connection_string: The SQLAlchemy connection string used to connect to the SQL Server database.
            For example: "mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"
        create_temp_table: Whether to leverage temporary tables during metric computation.
        kwargs: Extra SQLAlchemy keyword arguments to pass to `create_engine()`.
        assets: An optional dictionary whose keys are SQL DataAsset names and whose values
            are SQL DataAsset objects.
    """

    type: Literal["sqlserver"] = "sqlserver"  # type: ignore[assignment] # FIXME CoP

    @property
    def schema_(self) -> str | None:
        """
        Convenience property to get the `schema` from datasource name pattern.
        
        Parses schema from datasource names like "Database.Schema" (e.g., "TransformedDataDnA.CR" → "CR").
        Returns None if the datasource name doesn't follow the pattern.
        """
        if not self.name:
            return None
            
        # Check for "Database.Schema" pattern
        if "." in self.name:
            parts = self.name.split(".")
            if len(parts) == 2:
                database_part, schema_part = parts
                # Validate that both parts look reasonable (not empty, reasonable length)
                if (database_part 
                    and schema_part 
                    and len(schema_part) <= 128  # SQL Server schema name limit
                    and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', schema_part)):  # Valid SQL identifier
                    return to_lower_if_not_quoted(schema_part)
        
        return None

    @public_api
    @override
    def add_table_asset(
        self,
        name: str,
        table_name: str = "",
        schema_name: Optional[str] = MISSING,  # type: ignore[assignment] # sentinel value
        batch_metadata: Optional[BatchMetadata] = None,
    ) -> TableAsset:
        """Adds a table asset to this datasource.

        Args:
            name: The name of this table asset.
            table_name: The table where the data resides.
            schema_name: The schema that holds the table. Will use the datasource schema if not provided.
            batch_metadata: BatchMetadata we want to associate with this DataAsset and all batches derived from it.

        Returns:
            The table asset that is added to the datasource.
        """
        if schema_name is MISSING:
            # using MISSING to indicate that the user did not provide a value
            schema_name = self.schema_
            if schema_name:
                LOGGER.debug(f"Auto-detected schema '{schema_name}' from datasource name '{self.name}' for table asset '{name}'")

        return super().add_table_asset(
            name=name,
            table_name=table_name,
            schema_name=schema_name,
            batch_metadata=batch_metadata,
        )
