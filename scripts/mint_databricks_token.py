"""Mint a short-lived Databricks OAuth machine-to-machine (M2M) access token.

OAuth M2M lets a service principal authenticate with a client ID and secret
via the client-credentials grant; the resulting bearer token is accepted anywhere a
PAT is and is valid for one hour.

This script prints ONLY the access token to stdout so a caller can capture it into
an environment variable (e.g. ``DATABRICKS_TOKEN``) and reuse the existing
token-based connection path unchanged. Callers must register the value for log
masking before use (in GitHub Actions, ``echo "::add-mask::$TOKEN"``) so the token
does not leak into logs.
"""

import sys

import requests

from great_expectations.compatibility.pydantic import BaseSettings

TOKEN_REQUEST_TIMEOUT_SECONDS = 30


class ServicePrincipalConfig(BaseSettings):
    """OAuth M2M credentials.

    Injected via CI, but when running locally you may use your own service
    principal's credentials.
    """

    databricks_host: str
    databricks_client_id: str
    databricks_client_secret: str

    @property
    def token_endpoint(self) -> str:
        host = self.databricks_host.removeprefix("https://").removeprefix("http://").rstrip("/")
        return f"https://{host}/oidc/v1/token"


def mint_access_token(config: ServicePrincipalConfig) -> str:
    """Exchange the service principal's client credentials for an OAuth access token."""
    response = requests.post(
        config.token_endpoint,
        auth=(config.databricks_client_id, config.databricks_client_secret),
        data={"grant_type": "client_credentials", "scope": "all-apis"},
        timeout=TOKEN_REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


def main() -> None:
    config = ServicePrincipalConfig()  # type: ignore[call-arg]  # values come from env
    sys.stdout.write(mint_access_token(config))


if __name__ == "__main__":
    main()
