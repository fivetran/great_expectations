import pytest

from great_expectations.compatibility.pydantic import ValidationError, errors
from great_expectations.metrics.domain import (
    AbstractClassInstantiationError,
    Batch,
    ColumnValues,
    Domain,
    Values,
)

BATCH_ID = "my_data_source-my_data_asset-year_2025"
COLUMN = "my_column"


class TestAbstractClasses:
    @pytest.mark.unit
    def test_domain_instantiation_raises(self):
        with pytest.raises(AbstractClassInstantiationError):
            Domain(batch_id=BATCH_ID)

    @pytest.mark.unit
    def test_values_instantiation_raises(self):
        with pytest.raises(AbstractClassInstantiationError):
            Values(batch_id=BATCH_ID)


class TestColumnValues:
    @pytest.mark.unit
    def test_instantiation(self):
        ColumnValues(batch_id=BATCH_ID, column=COLUMN)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "kwargs",
        [
            {"batch_id": "", "column": COLUMN},
            {"batch_id": BATCH_ID, "column": ""},
        ],
    )
    def test_arguments_empty_string_raises(self, kwargs: dict):
        with pytest.raises(ValidationError) as e:
            ColumnValues(**kwargs)
        all_errors = e.value.raw_errors
        assert any(
            True
            if hasattr(error, "exc") and isinstance(error.exc, errors.AnyStrMinLengthError)
            else False
            for error in all_errors
        )


class TestBatch:
    @pytest.mark.unit
    def test_instantiation(self):
        Batch(batch_id=BATCH_ID, row_condition='PClass=="1st"', condition_parser="pandas")
