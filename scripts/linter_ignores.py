"""
Check for instances of linter directive ignores without comments.

In order to keep code quality high, we want to avoid future additions of
noqa or type: ignore directives without comments explaining why they are
necessary.
"""

from __future__ import annotations

import pathlib
import re
import sys
from collections.abc import Iterator

TYPE_IGNORE_COMMENT_REGEX: re.Pattern[str] = re.compile(
    r" # type: ignore(?P<code>\[.*?\])?(?P<comment>\s*# .*)?$"
)
NOQA_IGNORE_COMMENT_REGEX: re.Pattern[str] = re.compile(
    r" # noqa: (?P<code>.*?)*(?P<comment>\s*# .*)?$"
)


def get_type_ignores(path: pathlib.Path) -> Iterator[tuple[int, str]]:
    """Get all type-ignores from a file."""
    with open(path) as f_in:
        for lineno, line in enumerate(f_in, start=1):
            match = TYPE_IGNORE_COMMENT_REGEX.search(line)
            if not match:
                continue
            if not match.group("comment"):
                yield lineno, line


def check_type_ignores(paths: list[pathlib.Path]) -> list[tuple[str, str, str]]:
    """Collect list of type ignores without comments."""
    return [(path, lineno, ignore) for path in paths for lineno, ignore in get_type_ignores(path)]


def get_noqa_ignores(path: pathlib.Path) -> Iterator[tuple[int, str]]:
    """Get all noqa-ignores from a file."""
    with open(path) as f_in:
        for lineno, line in enumerate(f_in, start=1):
            match = NOQA_IGNORE_COMMENT_REGEX.search(line)
            if not match:
                continue
            if not match.group("comment"):
                yield lineno, line


def check_noqa_ignores(paths: list[pathlib.Path]) -> list[tuple[str, str, str]]:
    """Collect list of noqa ignores without comments."""
    return [(path, lineno, ignore) for path in paths for lineno, ignore in get_noqa_ignores(path)]


if __name__ == "__main__":
    paths = [pathlib.Path(p) for p in sys.argv[1:]]
    checks = {"type": check_type_ignores(paths), "noqa": check_noqa_ignores(paths)}

    total_errors = 0
    for key, all_ignores in checks.items():
        if all_ignores:
            total_errors += len(all_ignores)
            print(f"{len(all_ignores)} errors must be fixed before merging.")
            print(f"Found {key} ignores without explanatory comments:")
            for path, lineno, ignore in all_ignores:
                print(f" {path}:{lineno}\n {ignore}")

    if total_errors:
        print(
            f"Found {total_errors} ignores without comments that need to be fixed before merging."
        )
        sys.exit(1)
