from __future__ import annotations

from typing import Any, Literal

from great_expectations._docs_decorators import public_api
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


@public_api
class FabricDatasource(SQLServerDatasource):
    """Adds a Microsoft Fabric datasource to the data context.

    Args:
        name: The name of this Fabric datasource.
        host: Your Microsoft Fabric workload endpoint,
            for example "myworkspace.datawarehouse.fabric.microsoft.com"
            or "abc123.database.fabric.microsoft.com".
        database: The name of the Microsoft Fabric database
            where the data you want to validate is stored.
        schema: The name of the Microsoft Fabric schema
            where the data you want to validate is stored.
        port: The port configured for your Microsoft Fabric instance,
            typically 1433.
        encrypt: The TLS encryption protocol to use.
            Accepts the following.
            - "Optional" - Establish an encrypted connection if your
            Microsoft Fabric instance is configured to force encryption.
            Otherwise, establish an unencrypted connection.
            - "Mandatory" - Require the connection to be encrypted.
            Validate the server certificate unless "trust_server_certificate" is set to "True".
            Connection will fail if your Microsoft Fabric instance does not support TLS.
            If "trust_server_certificate" is set to "False", connection will fail if
            the certificate is not valid and publicly trusted.
            - "Strict" - Use TDS 8.0 where encryption begins before the TLS handshake.
            Require the connection to be encrypted and validate the server certificate.
            Connection will fail if your Microsoft Fabric instance does not support TLS
            or the certificate is not valid and publicly trusted.
        trust_server_certificate: If you set "encrypt" to "Mandatory", you can set
            "trust_server_certificate" to "True" to enable using an encrypted connection
            without a valid publicly trusted server certificate (default is "False"). This
            lets you, for example, use a self-signed certificate with an encrypted connection.
        driver: The name of the ODBC driver your environment uses to
            connect to Microsoft Fabric. Common values include:
            - "ODBC Driver 18 for SQL Server"
            - "ODBC Driver 17 for SQL Server"
            - "FreeTDS"
        tenant_id: The unique identifier for your organization's
            instance of Microsoft Entra ID.
        client_id: The application ID for your new or existing
            Entra ID app registration.
        client_secret: A new secret key from your Entra ID app registration.
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
