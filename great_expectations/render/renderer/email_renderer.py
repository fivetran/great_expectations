from __future__ import annotations

import logging
import textwrap
import urllib
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

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


class EmailRenderer(Renderer):
    @override
    def render(
        self,
        checkpoint_result: CheckpointResult,
        data_docs_pages: dict[ValidationResultIdentifier, dict[str, str]] | None = None,
    ) -> tuple[str, str]:
        data_docs_pages = data_docs_pages or {}
        blocks: list[str] = []

        for (
            validation_result_identifier,
            validation_result,
        ) in checkpoint_result.run_results.items():
            description_block = self._build_description_block(validation_result)

            data_docs_page = data_docs_pages.get(validation_result_identifier, {})
            data_docs_link_block = self._build_data_docs_link_block(data_docs_page)
            if data_docs_link_block:
                description_block += "\n" + data_docs_link_block

            blocks.append(description_block)

        status = "Success ✅" if checkpoint_result.success else "Failed ❌"
        title = f"{checkpoint_result.name} - {status}"

        return title, self._concatenate_blocks(blocks)

    def _build_description_block(self, result: ExpectationSuiteValidationResult) -> str:
        suite_name = result.suite_name
        asset_name = result.asset_name or "__no_asset_name__"
        n_checks_succeeded = result.statistics["successful_expectations"]
        n_checks = result.statistics["evaluated_expectations"]
        run_id = result.meta.get("run_id", "__no_run_id__")
        batch_id = result.batch_id
        check_details_text = f"<strong>{n_checks_succeeded}</strong> of <strong>{n_checks}</strong> expectations were met"  # noqa: E501 # FIXME CoP
        status = "Success 🎉" if result.success else "Failed ❌"

        title = f"<h3><u>{suite_name}</u></h3>"
        html = textwrap.dedent(
            f"""\
            <p><strong>{title}</strong></p>
            <p><strong>Batch Validation Status</strong>: {status}</p>
            <p><strong>Expectation Suite Name</strong>: {suite_name}</p>
            <p><strong>Data Asset Name</strong>: {asset_name}</p>
            <p><strong>Run ID</strong>: {run_id}</p>
            <p><strong>Batch ID</strong>: {batch_id}</p>
            <p><strong>Summary</strong>: {check_details_text}</p>"""
        )

        return html

    def _concatenate_blocks(self, text_blocks: list[str]) -> str:
        return "\n<br>".join(text_blocks)

    def _get_report_element(self, docs_link: str) -> str | None:
        report_element = None
        if docs_link:
            try:
                docs_link = urllib.parse.unquote(docs_link)
                if "file:/" in docs_link:
                    # handle special case since the email does not render these links
                    report_element = str(
                        f'<p><strong>DataDocs</strong> can be found here: <a href="{docs_link}">{docs_link}</a>.</br>'  # noqa: E501 # FIXME CoP
                        "(Please copy and paste link into a browser to view)</p>",
                    )
                else:
                    report_element = f'<p><strong>DataDocs</strong> can be found here: <a href="{docs_link}">{docs_link}</a>.</p>'  # noqa: E501 # FIXME CoP
            except Exception as e:
                logger.warning(
                    f"""EmailRenderer had a problem with generating the docs link.
                    link used to generate the docs link is: {docs_link} and is of type: {type(docs_link)}.
                    Error: {e}"""  # noqa: E501 # FIXME CoP
                )
        else:
            logger.warning("No docs link found. Skipping data docs link in the email message.")
        return report_element

    def _build_data_docs_link_block(self, data_docs_page: dict[str, str]) -> str:
        docs_link_blocks: list[str] = []
        for docs_link_key, docs_link in data_docs_page.items():
            if docs_link_key == "class":
                continue

            report_element = self._get_report_element(docs_link)
            if report_element:
                docs_link_blocks.append(report_element)

        return "\n".join(docs_link_blocks)
