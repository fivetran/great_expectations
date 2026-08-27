#!/bin/bash

# Scans Python files changed relative to origin/develop under great_expectations/ and
# tests/ for linter/type ignore directives (e.g. noqa, type: ignore) that lack an
# explanatory comment. This does not run mypy and does not affect its exclusion config;
# it is a separate, narrower check on why an ignore was added.

cd "$(git rev-parse --show-toplevel)" || exit 1

git fetch --quiet
# Get a list of modified python scripts
# https://git-scm.com/docs/git-diff#Documentation/git-diff.txt---diff-filterACDMRTUXB82308203
diff_modules=$(\
    git diff --diff-filter=MA --name-only origin/develop \
    | grep -E "^(great_expectations|tests)\/.+\.py$" || true \
)
echo "Force running on files diff'd with origin/develop: $diff_modules"
# Omitting double quotes bc need to unpack the filenames
# shellcheck disable=SC2086
python scripts/linter_ignores.py $diff_modules
echo "Make sure your branch is up to date"
