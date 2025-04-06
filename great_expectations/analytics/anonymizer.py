from __future__ import annotations

from hashlib import sha256


def anonymize(string: str) -> str:
    return sha256(string.encode("utf-8")).hexdigest()
