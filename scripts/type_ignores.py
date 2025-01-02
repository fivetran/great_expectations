from __future__ import annotations

import pathlib
import re
import sys
from collections.abc import Iterator

TYPE_IGNORE_COMMENT_REGEX: re.Pattern[str] = re.compile(
    r" # type: ignore(?P<code>\[.*?\])?(?P<comment>\s*# .*)?$"
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
    all_ignores: list[tuple[pathlib.Path, int, str]] = []
    for path in paths[:]:
        for lineno, ignore in get_type_ignores(path):
            all_ignores.append((path, lineno, ignore))

    return all_ignores


NOQA_IGNORE_COMMENT_REGEX: re.Pattern[str] = re.compile(
    r" # noqa: (?P<code>.*?)?(?P<comment>\s*# .*)?$"
)


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
    all_ignores: list[tuple[pathlib.Path, int, str]] = []
    for path in paths[:]:
        for lineno, ignore in get_noqa_ignores(path):
            all_ignores.append((path, lineno, ignore))

    return all_ignores


if __name__ == "__main__":
    paths: list[pathlib.Path] = [pathlib.Path(p) for p in sys.argv[1:]]
    checks = {"type": check_type_ignores(paths), "noqa": check_noqa_ignores(paths)}
    should_fail = False
    total_errors = 0
    for key, all_ignores in checks.items():
        if all_ignores:
            should_fail = True
            total_errors += len(all_ignores)
            print(f"{len(all_ignores)} errors must be fixed before merging.")
            print(f"Found {key} ignores without explanatory comments:")
            for path, lineno, ignore in all_ignores:
                print(f" {path}:{lineno}\n {ignore}")
    if should_fail:
        print(f"Found {total_errors} ignores without comments that need to be fixed before merging")
        sys.exit(1)
    else:
        sys.exit(0)
