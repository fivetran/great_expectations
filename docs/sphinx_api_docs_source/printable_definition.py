from __future__ import annotations

import pathlib
from dataclasses import dataclass


@dataclass(frozen=True)
class PrintableDefinition:
    file: pathlib.Path
    name: str

    def __post_init__(self):
        if not self.file.exists():
            raise FileNotFoundError(f"File {self.file} does not exist.")  # noqa: TRY003

    def __str__(self) -> str:  # type: ignore[explicit-override]
        return f"File: {self.file} Name: {self.name}"

    def __lt__(self, other) -> bool:
        return str(self) < str(other)
