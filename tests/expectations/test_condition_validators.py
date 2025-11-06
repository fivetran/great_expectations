"""Tests for condition validators on row_condition in Expectations."""

from datetime import datetime, timezone

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.expectations.core import (
    ExpectColumnValuesToBeInSet,
    ExpectTableRowCountToEqual,
)
from great_expectations.expectations.row_conditions import (
    Column,
    ComparisonCondition,
    Operator,
)

pytestmark = pytest.mark.unit


class TestAndConditionValidator:
    """Tests for AndCondition validator when passed to Expectation."""

    def test_flatten_nested_and_conditions(self):
        """Test that nested AndConditions are flattened when passed to Expectation."""
        column_1 = Column("column_1")
        column_2 = Column("column_2")
        column_3 = Column("column_3")

        row_condition = (column_1 < 8) & ((column_2 > 8) & (column_3 == 8))

        # Pass to an Expectation - should flatten
        expectation = ExpectColumnValuesToBeInSet(
            column="test_column", value_set=["a", "b"], row_condition=row_condition
        )

        # Verify flattening occurred - should have 3 conditions instead of nested structure
        assert len(expectation.row_condition.conditions) == 3

    def test_error_on_or_within_and(self):
        """Test that OrConditions nested within AndConditions raise error in Expectation."""
        column_1 = Column("column_1")
        column_2 = Column("column_2")
        column_3 = Column("column_3")

        # OR within AND
        row_condition = (column_1 < 8) & ((column_2 > 8) | (column_3 == 8))

        with pytest.raises(ValueError, match="AND groups cannot contain OR conditions"):
            ExpectColumnValuesToBeInSet(
                column="test_column", value_set=["a", "b"], row_condition=row_condition
            )


class TestOrConditionValidator:
    """Tests for OrCondition validator when passed to Expectation."""

    def test_error_on_nested_or_within_or_within_and(self):
        """Test that nested OR structures are caught by validation."""
        column_1 = Column("column_1")
        column_2 = Column("column_2")
        column_3 = Column("column_3")

        nested_or = (column_1 > 8) | ((column_2 == 8) | (column_3 == 9))

        with pytest.raises(ValueError, match="OR groups cannot contain nested OR conditions"):
            ExpectColumnValuesToBeInSet(
                column="test_column", value_set=["a", "b"], row_condition=nested_or
            )


class TestTotalConditionCountValidator:
    """Tests for total condition count validator when passed to Expectation."""

    def test_error_on_more_than_100_conditions(self):
        """Test that more than 100 conditions raises error in Expectation."""
        column = Column("column_1")

        # Create 101 conditions
        row_condition = column == 0
        for i in range(1, 101):
            row_condition = row_condition & (column == i)

        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            ExpectColumnValuesToBeInSet(
                column="test_column", value_set=["a", "b"], row_condition=row_condition
            )

    def test_exactly_100_conditions_allowed(self):
        """Test that exactly 100 conditions is allowed in Expectation."""
        column = Column("column_1")

        # Create exactly 100 condition
        row_condition = column == 0
        for i in range(1, 100):
            row_condition = row_condition & (column == i)

        # This should not raise an error
        expectation = ExpectColumnValuesToBeInSet(
            column="test_column", value_set=["a", "b"], row_condition=row_condition
        )
        assert len(expectation.row_condition.conditions) == 100

    def test_nested_and_conditions_count_towards_limit(self):
        """Test that nested AndConditions within OR are counted towards the 100 limit."""
        column = Column("column_1")

        # Create first AND group with 50 conditions
        first_and_group = column == 0
        for i in range(1, 50):
            first_and_group = first_and_group & (column == i)

        # Create second AND group with 51 conditions
        second_and_group = column == 50
        for i in range(51, 101):
            second_and_group = second_and_group & (column == i)

        # Combine with OR - total: 50 + 51 = 101 conditions
        row_condition = first_and_group | second_and_group

        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            ExpectColumnValuesToBeInSet(
                column="test_column", value_set=["a", "b"], row_condition=row_condition
            )


class TestValidatorAppliesAcrossExpectations:
    """Test that the validator applies to all BatchExpectation subclasses with row_condition."""

    def test_validator_applies_to_core_expectations(self):
        """Test that expectations in core/ directory also get validated."""
        column_1 = Column("column_1")
        column_2 = Column("column_2")
        column_3 = Column("column_3")

        row_condition = (column_1 < 8) & ((column_2 > 8) | (column_3 == 8))

        # This should raise ValueError even for ExpectTableRowCountToEqual
        with pytest.raises(ValueError, match="AND groups cannot contain OR conditions"):
            ExpectTableRowCountToEqual(value=10, row_condition=row_condition)


class TestComparisonConditionValidators:
    @pytest.mark.parametrize(
        "operator_func",
        [
            pytest.param(
                lambda col: col == None,  # noqa: E711  # testing invalid syntax
                id="eq - Linting error - `is None` is pythonic, "
                "but that only compares to singleton instance",
            ),
            pytest.param(
                lambda col: col != None,  # noqa: E711  # testing invalid syntax
                id="ne - Linting error - `is None` is pythonic, "
                "but that only compares to singleton instance",
            ),
            pytest.param(lambda col: col < None, id="lt - Nonsense"),
            pytest.param(lambda col: col <= None, id="le - Nonsense"),
            pytest.param(lambda col: col > None, id="gt - Nonsense"),
            pytest.param(lambda col: col >= None, id="ge - Nonsense"),
        ],
    )
    def test_column_operators_with_none_raises_error(self, operator_func):
        """Test that Column operators with None parameter raise InvalidParameterTypeError."""
        col = Column("status")

        with pytest.raises(ValidationError):
            operator_func(col)


class TestInSetOperatorParameterValidator:
    """Tests for IN and NOT_IN operator parameter validation."""

    @pytest.mark.parametrize(
        "parameter",
        [
            pytest.param([1, 2, 3], id="list of ints"),
            pytest.param([1.0, 2.5, 3.14], id="list of floats"),
            pytest.param([1, 2.5, 3], id="mixed ints and floats"),
            pytest.param(["a", "b", "c"], id="list of strings"),
            pytest.param((1, 2, 3), id="tuple of ints"),
            pytest.param({1, 2, 3}, id="set of ints"),
            pytest.param([], id="empty list"),
        ],
    )
    def test_valid_parameter_types(self, parameter):
        """Test that valid parameter types for IN/NOT_IN operators are accepted."""
        col = Column(name="status")
        condition = ComparisonCondition(column=col, operator=Operator.IN, parameter=parameter)
        assert condition.parameter == parameter

        condition = ComparisonCondition(column=col, operator=Operator.NOT_IN, parameter=parameter)
        assert condition.parameter == parameter

    @pytest.mark.parametrize(
        "operator",
        [
            pytest.param(Operator.IN, id="IN"),
            pytest.param(Operator.NOT_IN, id="NOT_IN"),
        ],
    )
    def test_string_parameter_raises_error(self, operator):
        """Test that string parameter raises error for IN/NOT_IN operators."""
        col = Column(name="status")

        with pytest.raises(ValidationError):
            ComparisonCondition(column=col, operator=operator, parameter="abc")

    @pytest.mark.parametrize(
        "operator",
        [
            pytest.param(Operator.IN, id="IN"),
            pytest.param(Operator.NOT_IN, id="NOT_IN"),
        ],
    )
    def test_non_iterable_parameter_raises_error(self, operator):
        """Test that non-iterable parameter raises error for IN/NOT_IN operators."""
        col = Column(name="status")

        with pytest.raises(ValidationError):
            ComparisonCondition(column=col, operator=operator, parameter=42)

    @pytest.mark.parametrize(
        "parameter",
        [
            pytest.param([1, 2, [3, 4]], id="nested list"),
            pytest.param([1, {"a": 2}], id="dict"),
            pytest.param([1, None], id="None"),
            pytest.param([1, datetime.now(tz=timezone.utc)], id="datetime"),
            pytest.param([1, True], id="bool values not allowed"),
        ],
    )
    def test_invalid_element_types_raise_error(self, parameter):
        """Test that invalid element types in parameter raise error."""
        col = Column(name="status")

        with pytest.raises(ValidationError):
            ComparisonCondition(column=col, operator=Operator.IN, parameter=parameter)

    @pytest.mark.parametrize(
        "parameter",
        [
            pytest.param([1, "a"], id="int and string"),
        ],
    )
    def test_mixed_types_raise_error(self, parameter):
        """Test that mixed types in parameter raise error."""
        col = Column(name="status")

        with pytest.raises(ValidationError):
            ComparisonCondition(column=col, operator=Operator.IN, parameter=parameter)
