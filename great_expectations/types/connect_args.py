from typing import Optional, TypedDict


class ConnectArgs(TypedDict, total=False):
    """Type definition for connection arguments."""

    private_key: Optional[str]
