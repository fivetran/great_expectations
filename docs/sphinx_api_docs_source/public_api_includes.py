"""Methods, classes and files to be included as part of the public API, even if they are not mentioned in docs snippets."""

from __future__ import annotations

import pathlib

from docs.sphinx_api_docs_source.include_exclude_definition import (
    IncludeExcludeDefinition,
)

DEFAULT_INCLUDES: list[IncludeExcludeDefinition] = [
    IncludeExcludeDefinition(
        reason="Referenced via legacy docs, will likely need to be included in the public API. Added here as an example include.",
        name="remove_expectation",
        filepath=pathlib.Path("great_expectations/core/expectation_suite.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="ValidationAction",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="run",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="_run",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="SlackNotificationAction",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="MicrosoftTeamsNotificationAction",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="EmailAction",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="StoreValidationResultAction",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Validation Actions are used within Checkpoints but are part of our Public API and can be overridden via plugins.",
        name="UpdateDataDocsAction",
        filepath=pathlib.Path("great_expectations/checkpoint/actions.py"),
    ),
    IncludeExcludeDefinition(
        reason="Data Context types are part of the public API",
        name="EphemeralDataContext",
        filepath=pathlib.Path(
            "great_expectations/data_context/data_context/ephemeral_data_context.py"
        ),
    ),
    IncludeExcludeDefinition(
        reason="Data Context types are part of the public API",
        name="FileDataContext",
        filepath=pathlib.Path(
            "great_expectations/data_context/data_context/file_data_context.py"
        ),
    ),
    IncludeExcludeDefinition(
        reason="Data Context types are part of the public API",
        name="CloudDataContext",
        filepath=pathlib.Path(
            "great_expectations/data_context/data_context/cloud_data_context.py"
        ),
    ),
    IncludeExcludeDefinition(
        reason="Map metric providers are part of the public API",
        name="MetricProvider",
        filepath=pathlib.Path(
            "great_expectations/expectations/metrics/metric_provider.py"
        ),
    ),
]
