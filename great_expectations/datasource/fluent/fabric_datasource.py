from __future__ import annotations

from typing import Any, Literal

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.sql_server_datasource import (
    _CONNECTION_DETAIL_FIELDS,
    _MUTUALLY_EXCLUSIVE_MSG,
    EntraIDServicePrincipalAuthConnectionDetails,
    SQLServerDatasource,
)


class UnsupportedAuthenticationError(ValueError):
    """Raised when a non-Entra ID authentication method is used with FabricDatasource."""

    def __init__(self, authentication: str) -> None:
        super().__init__(
            f"FabricDatasource only supports Entra ID Service Principal "
            f"authentication, got {authentication!r}."
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
        connection_string = values.get("connection_string")
        connection_details: dict[str, Any] = {}
        for field_name in list(values.keys()):
            if field_name in _CONNECTION_DETAIL_FIELDS:
                if connection_string is not None:
                    raise ValueError(_MUTUALLY_EXCLUSIVE_MSG)
                connection_details[field_name] = values.pop(field_name)
        if connection_details:
            auth = connection_details.get("authentication", "Entra ID Service Principal")
            if auth != "Entra ID Service Principal":
                raise UnsupportedAuthenticationError(auth)
            connection_details["authentication"] = auth
            values["connection_string"] = connection_details
        return values
