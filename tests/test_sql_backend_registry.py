from __future__ import annotations

import pytest

from tests.integration.test_utils.data_source_config.backend_spec import (
    BackendProvisioning,
    BackendTier,
    CiLaneRef,
    SqlBackendSpec,
)

pytestmark = pytest.mark.project


def _make_spec(**overrides: object) -> SqlBackendSpec:
    defaults: dict[str, object] = dict(
        label="throwaway",
        marker="throwaway",
        provisioning=BackendProvisioning.LOCAL_FILE,
        ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="throwaway"),
        uses_schema=False,
    )
    defaults.update(overrides)
    return SqlBackendSpec(**defaults)  # type: ignore[arg-type]


class TestSqlBackendSpecMarkRoundTrip:
    def test_pytest_mark_round_trips_marker_name_to_literal_mark(self) -> None:
        spec = _make_spec(marker="mysql")

        assert spec.pytest_mark == pytest.mark.mysql

    def test_pytest_mark_round_trips_a_different_marker_name(self) -> None:
        spec = _make_spec(marker="singlestore", tiers=frozenset({BackendTier.CURATED_SQL}))

        assert spec.pytest_mark == pytest.mark.singlestore


class TestSqlBackendSpecTableSchemaItemsDefault:
    def test_spec_with_no_table_schema_item_factory_reports_it_as_absent(self) -> None:
        spec = _make_spec()

        assert spec.table_schema_items is None
