from datetime import datetime, timezone

import pandas as pd

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import SqliteDatasourceTestConfig

DATE_COL = "date"
VALUE_COL = "value"

LAST_YEAR = "last year"
FIRST_DAY_OF_THE_YEAR = "first day of the year"
FIRST_DAY_OF_THE_MONTH = "first day of the month"
SECOND_DAY_OF_THE_MONTH = "second day of the month"

DATA = pd.DataFrame(
    {
        DATE_COL: [
            datetime(year=2023, month=1, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=1, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=2, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=2, day=2, tzinfo=timezone.utc).date(),
        ],
        VALUE_COL: [
            LAST_YEAR,
            FIRST_DAY_OF_THE_YEAR,
            FIRST_DAY_OF_THE_MONTH,
            SECOND_DAY_OF_THE_MONTH,
        ],
    }
)

JUST_SQLITE = [SqliteDatasourceTestConfig()]


class TestPartitioning:
    """Tests to show that we partition sqlite data sourdces correctly.

    All tests use ExpectColumnDistinctValuesToEqualSet to detect that we are just seeing the
    appropriate rows.
    """

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_SQLITE,
        data=pd.DataFrame(DATA),
    )
    def test_yearly_partitioning(self, asset_for_datasource: TableAsset) -> None:
        batch_def = asset_for_datasource.add_batch_definition_yearly("yearly", column=DATE_COL)
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    # NOT LAST_YEAR
                    FIRST_DAY_OF_THE_YEAR,
                    FIRST_DAY_OF_THE_MONTH,
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_SQLITE,
        data=pd.DataFrame(DATA),
    )
    def test_monthly_partitioning(self, asset_for_datasource: TableAsset) -> None:
        batch_def = asset_for_datasource.add_batch_definition_monthly("monthly", column=DATE_COL)
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    # NOT LAST_YEAR
                    # NOT FIRST_DAY_OF_THE_YEAR,
                    FIRST_DAY_OF_THE_MONTH,
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_SQLITE,
        data=pd.DataFrame(DATA),
    )
    def test_daily_partitioning(self, asset_for_datasource: TableAsset) -> None:
        batch_def = asset_for_datasource.add_batch_definition_daily("daily", column=DATE_COL)
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    # NOT LAST_YEAR
                    # NOT FIRST_DAY_OF_THE_YEAR,
                    # NOT FIRST_DAY_OF_THE_MONTH,
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_SQLITE,
        data=pd.DataFrame(DATA),
    )
    def test_order_ascending__true(self, asset_for_datasource: TableAsset) -> None:
        batch_def = asset_for_datasource.add_batch_definition_daily(
            "daily_ascending", column=DATE_COL, sort_ascending=True
        )
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    SECOND_DAY_OF_THE_MONTH,
                ],
            )
        )
        assert result.success

    @parameterize_batch_for_data_sources(
        data_source_configs=JUST_SQLITE,
        data=pd.DataFrame(DATA),
    )
    def test_order_ascending__false(self, asset_for_datasource: TableAsset) -> None:
        batch_def = asset_for_datasource.add_batch_definition_daily(
            "daily_descending", column=DATE_COL, sort_ascending=False
        )
        batch = batch_def.get_batch()

        result = batch.validate(
            gxe.ExpectColumnDistinctValuesToEqualSet(
                column=VALUE_COL,
                value_set=[
                    LAST_YEAR,
                ],
            )
        )
        assert result.success
