from __future__ import annotations

from typing import Any, Literal

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.sql_server_datasource import (
    EntraIDServicePrincipalAuthConnectionDetails,
    SQLServerDatasource,
)


class FabricDatasource(SQLServerDatasource):
    """Adds a Microsoft Fabric datasource to the data context.

    Args:
        name: The name of this Fabric datasource.
        connection_string: Structured connection details using Entra ID
            Service Principal authentication.
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["fabric"] = "fabric"  # type: ignore[assignment]
    connection_string: EntraIDServicePrincipalAuthConnectionDetails

    @override
    @pydantic.root_validator(pre=True)
    def _convert_root_connection_detail_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Pack top-level connection detail kwargs into ``connection_string``."""
        from great_expectations.datasource.fluent.sql_server_datasource import (
            _CONNECTION_DETAIL_FIELDS,
            _MUTUALLY_EXCLUSIVE_MSG,
        )

        connection_string = values.get("connection_string")
        connection_details: dict[str, Any] = {}
        for field_name in list(values.keys()):
            if field_name in _CONNECTION_DETAIL_FIELDS:
                if connection_string is not None:
                    raise ValueError(_MUTUALLY_EXCLUSIVE_MSG)
                connection_details[field_name] = values.pop(field_name)
        if connection_details:
            connection_details.setdefault("authentication", "Entra ID Service Principal")
            values["connection_string"] = connection_details
        return values
