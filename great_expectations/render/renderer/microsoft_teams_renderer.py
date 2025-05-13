from __future__ import annotations

import datetime as dt
import logging
from typing import TYPE_CHECKING

from great_expectations.compatibility.typing_extensions import override
from great_expectations.render.renderer.renderer import Renderer

if TYPE_CHECKING:
    from great_expectations.checkpoint.checkpoint import CheckpointResult
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
    )
    from great_expectations.data_context.types.resource_identifiers import (
        ValidationResultIdentifier,
    )

logger = logging.getLogger(__name__)


class MicrosoftTeamsRenderer(Renderer):
    """
    Responsible for formatting validation results and data docs links into a Microsoft Teams webhook
    message payload.

    Relevant links/documentation:
        * Payload schema: https://adaptivecards.io/explorer/
        * Interactive UI editor: https://adaptivecards.io/designer/

    """

    _MICROSOFT_TEAMS_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"
    _MICROSOFT_TEAMS_SCHEMA_URL = "http://adaptivecards.io/schemas/adaptive-card.json"
    _MICROSOFT_TEAMS_SCHEMA_VERSION = "1.5"
    _GX_LOGO_URL = "https://www.greatexpectations.io/image/gx-logo-mark-400"
    _SUCCESS_EMOJI = "✅"
    _FAILURE_EMOJI = "❌"
    _NO_VALUE_PLACEHOLDER = "--"

    @override
    def render(
        self,
        checkpoint_result: CheckpointResult,
        data_docs_pages: dict[ValidationResultIdentifier, dict[str, str]] | None = None,
    ) -> dict:
        blocks: list[dict] = []

        blocks.append(
            self._build_header_block(
                checkpoint_name=checkpoint_result.name,
                success=checkpoint_result.success or False,
                run_time=checkpoint_result.run_id.run_time,
            )
        )

        for idx, (validation_result_identifier, validation_result) in enumerate(
            checkpoint_result.run_results.items(), start=1
        ):
            validation_blocks = self._build_validation_result_blocks(
                idx=idx,
                total_validation_count=len(checkpoint_result.run_results),
                validation_result_identifier=validation_result_identifier,
                validation_result=validation_result,
            )
            blocks.extend(validation_blocks)

        return self._build_payload(blocks=blocks, data_docs_pages=data_docs_pages)

    def _build_header_block(
        self, checkpoint_name: str, success: bool, run_time: dt.datetime
    ) -> dict:
        success_text = (
            f"Success {self._SUCCESS_EMOJI}" if success else f"Failure {self._FAILURE_EMOJI}"
        )
        return {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "items": [
                        {
                            "type": "Image",
                            "url": self._GX_LOGO_URL,
                            "altText": checkpoint_name,
                            "size": "small",
                        }
                    ],
                    "width": "auto",
                },
                {
                    "type": "Column",
                    "items": [
                        {
                            "type": "TextBlock",
                            "weight": "bolder",
                            "text": f"{checkpoint_name} - {success_text}",
                            "wrap": True,
                        },
                        {
                            "type": "TextBlock",
                            "spacing": "None",
                            "text": f"Ran {run_time}",
                            "isSubtle": True,
                            "wrap": True,
                        },
                    ],
                    "width": "stretch",
                },
            ],
        }

    def _build_validation_result_blocks(
        self,
        idx: int,
        total_validation_count: int,
        validation_result_identifier: ValidationResultIdentifier,
        validation_result: ExpectationSuiteValidationResult,
    ) -> list[dict]:
        success = validation_result.success
        success_text = self._SUCCESS_EMOJI if success else self._FAILURE_EMOJI
        color = "Good" if success else "Attention"

        blocks = [
            {
                "type": "TextBlock",
                "text": f"Validation Result ({idx} of {total_validation_count}) {success_text}",
                "wrap": True,
                "weight": "Bolder",
                "style": "columnHeader",
                "isSubtle": True,
                "color": color,
            },
            {
                "type": "FactSet",
                "facts": self._build_validation_result_facts(
                    validation_result_identifier=validation_result_identifier,
                    validation_result=validation_result,
                ),
                "separator": True,
            },
        ]

        if validation_result.result_url:
            blocks.append(
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View Result",
                            "url": validation_result.result_url,
                        }
                    ],
                }
            )

        return blocks

    def _build_validation_result_facts(
        self,
        validation_result_identifier: ValidationResultIdentifier,
        validation_result: ExpectationSuiteValidationResult,
    ) -> list[dict]:
        asset_name = validation_result.asset_name or self._NO_VALUE_PLACEHOLDER
        suite_name = validation_result.suite_name
        run_name = validation_result_identifier.run_id.run_name or self._NO_VALUE_PLACEHOLDER
        n_checks_succeeded = validation_result.statistics["successful_expectations"]
        n_checks = validation_result.statistics["evaluated_expectations"]
        check_details_text = f"*{n_checks_succeeded}* of *{n_checks}* Expectations were met"

        return [
            {"title": "Data Asset name: ", "value": asset_name},
            {"title": "Suite name: ", "value": suite_name},
            {"title": "Run name: ", "value": run_name},
            {"title": "Summary:", "value": check_details_text},
        ]

    def _get_data_docs_page_links(
        self, data_docs_pages: dict[ValidationResultIdentifier, dict[str, str]] | None
    ) -> list[str]:
        links: list[str] = []

        if not data_docs_pages:
            return links

        for data_docs_page in data_docs_pages.values():
            for docs_link_key, docs_link in data_docs_page.items():
                if docs_link_key == "class":
                    continue

                links.append(docs_link)

        return links

    def _build_payload(
        self,
        blocks: list[dict],
        data_docs_pages: dict[ValidationResultIdentifier, dict[str, str]] | None,
    ) -> dict:
        data_docs_page_links = self._get_data_docs_page_links(data_docs_pages)
        actions = [
            # We would normally use Action.OpenUrl here, but Teams does not support
            # non HTTP/HTTPS URI schemes. As Data Docs utilze file:///, we use Action.ShowCard
            # to display the link in a card.
            {
                "type": "Action.ShowCard",
                "title": "View Data Docs URL",
                "card": {
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": link,
                            "wrap": True,
                        },
                    ],
                    "$schema": self._MICROSOFT_TEAMS_SCHEMA_URL,
                },
            }
            for link in data_docs_page_links
        ]

        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": self._MICROSOFT_TEAMS_CONTENT_TYPE,
                    "content": {
                        "type": "AdaptiveCard",
                        "$schema": self._MICROSOFT_TEAMS_SCHEMA_URL,
                        "version": self._MICROSOFT_TEAMS_SCHEMA_VERSION,
                        "body": blocks,
                        "actions": actions,
                    },
                }
            ],
        }
