from __future__ import annotations

import pytest

from great_expectations.expectations.conditions import (
    AndCondition,
    Column,
    Comparator,
    ComparisonCondition,
    Condition,
    NullityCondition,
    OrCondition,
)

pytestmark = pytest.mark.unit


class TestCondition:
    """Tests for the base Condition class."""

    def test_condition_instantiation(self):
        """Test that Condition can be instantiated."""
        condition = Condition()
        assert isinstance(condition, Condition)

    def test_and_with_two_conditions(sef):
        condition_a = Condition()
        condition_b = Condition()

        result = condition_a & condition_b
        assert result == AndCondition(conditions=[condition_a, condition_b])

    def test_and_with_and_on_left(sef):
        condition_a = Condition()
        condition_b = Condition()
        condition_c = Condition()

        left_condition = AndCondition(conditions=[condition_a, condition_b])

        result = left_condition & condition_c
        assert result == AndCondition(conditions=[condition_a, condition_b, condition_c])

    def test_and_with_and_on_right(sef):
        condition_a = Condition()
        condition_b = Condition()
        condition_c = Condition()

        right_condition = AndCondition(conditions=[condition_b, condition_c])

        result = condition_a & right_condition
        assert result == AndCondition(conditions=[condition_a, condition_b, condition_c])

    def test_or_with_two_conditions(sef):
        condition_a = Condition()
        condition_b = Condition()

        result = condition_a | condition_b
        assert result == OrCondition(conditions=[condition_a, condition_b])

    def test_or_with_or_on_left(sef):
        condition_a = Condition()
        condition_b = Condition()
        condition_c = Condition()

        left_condition = OrCondition(conditions=[condition_a, condition_b])

        result = left_condition | condition_c
        assert result == OrCondition(conditions=[condition_a, condition_b, condition_c])

    def test_or_with_or_on_right(sef):
        condition_a = Condition()
        condition_b = Condition()
        condition_c = Condition()

        right_condition = OrCondition(conditions=[condition_b, condition_c])

        result = condition_a | right_condition
        assert result == OrCondition(conditions=[condition_a, condition_b, condition_c])


class TestAndCondition:
    """Tests for the AndCondition class."""

    def test_repr_single_condition(self):
        """Test __repr__ with a single condition."""
        cond = Condition()
        and_cond = AndCondition(conditions=[cond])
        assert repr(and_cond) == "(Condition())"

    @pytest.mark.unit
    def test_repr_multiple_conditions(self):
        """Test __repr__ with multiple conditions."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        and_cond = AndCondition(conditions=[cond1, cond2, cond3])

        assert repr(and_cond) == "(Condition() AND Condition() AND Condition())"

    def test_flattens_nested_and_conditions(self):
        """Test that AndCondition flattens nested AndConditions."""
        cond1 = Condition()
        cond2 = Condition()
        inner_and = AndCondition(conditions=[cond1, cond2])
        cond3 = Condition()

        # Nested AND should be flattened
        outer_and = AndCondition(conditions=[inner_and, cond3])

        assert outer_and == AndCondition(conditions=[cond1, cond2, cond3])

    def test_flattens_multiple_nested_and_conditions(self):
        """Test that AndCondition flattens multiple levels of nested ANDs."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        cond4 = Condition()

        # Create nested structure: AND(AND(cond1, cond2), AND(cond3, cond4))
        inner_and1 = AndCondition(conditions=[cond1, cond2])
        inner_and2 = AndCondition(conditions=[cond3, cond4])

        outer_and = AndCondition(conditions=[inner_and1, inner_and2])
        assert outer_and == AndCondition(conditions=[cond1, cond2, cond3, cond4])

    def test_flattens_deeply_nested_and_conditions(self):
        """Test that AndCondition flattens deeply nested structures."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        cond4 = Condition()
        cond5 = Condition()

        # Create: AND(AND(AND(cond1, cond2), cond3), AND(cond4, cond5))
        deepest_and = AndCondition(conditions=[cond1, cond2])
        middle_and = AndCondition(conditions=[deepest_and, cond3])
        inner_and = AndCondition(conditions=[cond4, cond5])

        outer_and = AndCondition(conditions=[middle_and, inner_and])

        assert outer_and == AndCondition(conditions=[cond1, cond2, cond3, cond4, cond5])


class TestOrCondition:
    """Tests for the OrCondition class."""

    def test_repr_single_condition(self):
        """Test __repr__ with a single condition."""
        cond = Condition()
        or_cond = OrCondition(conditions=[cond])

        assert repr(or_cond) == "(Condition())"

    def test_repr_multiple_conditions(self):
        """Test __repr__ with multiple conditions."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        or_cond = OrCondition(conditions=[cond1, cond2, cond3])

        assert repr(or_cond) == "(Condition() OR Condition() OR Condition())"

    def test_can_contain_and_conditions(self):
        """Test that OrCondition can contain AndCondition instances."""
        cond1 = Condition()
        cond2 = Condition()
        and_cond = AndCondition(conditions=[cond1, cond2])
        cond3 = Condition()
        or_cond = OrCondition(conditions=[and_cond, cond3])
        expected = f"({and_cond!r} OR {cond3!r})"
        assert repr(or_cond) == expected

    def test_flattens_nested_or_conditions(self):
        """Test that OrCondition flattens nested OrConditions."""
        cond1 = Condition()
        cond2 = Condition()
        inner_or = OrCondition(conditions=[cond1, cond2])
        cond3 = Condition()

        # Nested OR should be flattened
        outer_or = OrCondition(conditions=[inner_or, cond3])

        assert outer_or == OrCondition(conditions=[cond1, cond2, cond3])

    def test_flattens_multiple_nested_or_conditions(self):
        """Test that OrCondition flattens multiple levels of nested ORs."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        cond4 = Condition()

        # Create nested structure: OR(OR(cond1, cond2), OR(cond3, cond4))
        inner_or1 = OrCondition(conditions=[cond1, cond2])
        inner_or2 = OrCondition(conditions=[cond3, cond4])

        outer_or = OrCondition(conditions=[inner_or1, inner_or2])
        assert outer_or == OrCondition(conditions=[cond1, cond2, cond3, cond4])

    def test_flattens_deeply_nested_or_conditions(self):
        """Test that OrCondition flattens deeply nested structures."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        cond4 = Condition()
        cond5 = Condition()

        # Create: OR(OR(OR(cond1, cond2), cond3), OR(cond4, cond5))
        deepest_or = OrCondition(conditions=[cond1, cond2])
        middle_or = OrCondition(conditions=[deepest_or, cond3])
        inner_or = OrCondition(conditions=[cond4, cond5])

        outer_or = OrCondition(conditions=[middle_or, inner_or])

        assert outer_or == OrCondition(conditions=[cond1, cond2, cond3, cond4, cond5])


class TestColumn:
    def test_column_hash_equal(self):
        assert hash(Column(name="age")) == hash(Column(name="age"))

    def test_column_hash_not_equal(self):
        assert hash(Column(name="age")) != hash(Column(name="city"))

    def test_less_than_operator(self):
        col = Column(name="age")
        result = col < 18

        assert result == ComparisonCondition(
            column=col, operator=Comparator.LESS_THAN, parameter=18
        )

    def test_less_than_or_equal_operator(self):
        col = Column(name="age")
        result = col <= 18

        assert result == ComparisonCondition(
            column=col, operator=Comparator.LESS_THAN_OR_EQUAL, parameter=18
        )

    def test_equal_operator(self):
        col = Column(name="status")
        result = col == "active"

        assert result == ComparisonCondition(
            column=col, operator=Comparator.EQUAL, parameter="active"
        )

    def test_not_equal_operator(self):
        col = Column(name="status")
        result = col != "inactive"

        assert result == ComparisonCondition(
            column=col, operator=Comparator.NOT_EQUAL, parameter="inactive"
        )

    def test_greater_than_operator(self):
        col = Column(name="age")
        result = col > 65

        assert result == ComparisonCondition(
            column=col, operator=Comparator.GREATER_THAN, parameter=65
        )

    def test_greater_than_or_equal_operator(self):
        col = Column(name="age")
        result = col >= 65

        assert result == ComparisonCondition(
            column=col, operator=Comparator.GREATER_THAN_OR_EQUAL, parameter=65
        )

    def test_is_in_method(self):
        col = Column(name="status")
        result = col.is_in(["active", "pending", "approved"])

        assert result == ComparisonCondition(
            column=col, operator=Comparator.IN, parameter=["active", "pending", "approved"]
        )

    def test_is_not_in_method(self):
        col = Column(name="status")
        result = col.is_not_in(["inactive", "deleted"])

        assert result == ComparisonCondition(
            column=col, operator=Comparator.NOT_IN, parameter=["inactive", "deleted"]
        )

    def test_is_null_method(self):
        col = Column(name="email")
        result = col.is_null()

        assert result == NullityCondition(column=col, is_null=True)

    def test_is_not_null_method(self):
        col = Column(name="email")
        result = col.is_not_null()

        assert result == NullityCondition(column=col, is_null=False)


class TestComparisonCondition:
    def test_repr_equal_operator(self):
        col = Column(name="status")
        cond = ComparisonCondition(column=col, operator=Comparator.EQUAL, parameter="active")

        assert repr(cond) == "status == active"

    def test_repr_not_equal_operator(self):
        col = Column(name="status")
        cond = ComparisonCondition(column=col, operator=Comparator.NOT_EQUAL, parameter="inactive")

        assert repr(cond) == "status != inactive"

    def test_repr_less_than_operator(self):
        col = Column(name="age")
        cond = ComparisonCondition(column=col, operator=Comparator.LESS_THAN, parameter=18)

        assert repr(cond) == "age < 18"

    def test_repr_less_than_or_equal_operator(self):
        col = Column(name="age")
        cond = ComparisonCondition(column=col, operator=Comparator.LESS_THAN_OR_EQUAL, parameter=18)

        assert repr(cond) == "age <= 18"

    def test_repr_greater_than_operator(self):
        col = Column(name="age")
        cond = ComparisonCondition(column=col, operator=Comparator.GREATER_THAN, parameter=65)

        assert repr(cond) == "age > 65"

    def test_repr_greater_than_or_equal_operator(self):
        col = Column(name="age")
        cond = ComparisonCondition(
            column=col, operator=Comparator.GREATER_THAN_OR_EQUAL, parameter=65
        )

        assert repr(cond) == "age >= 65"

    def test_repr_in_operator(self):
        col = Column(name="status")
        cond = ComparisonCondition(
            column=col, operator=Comparator.IN, parameter=["active", "pending", "approved"]
        )

        assert repr(cond) == "status IN (active, pending, approved)"

    def test_repr_not_in_operator(self):
        col = Column(name="status")
        cond = ComparisonCondition(
            column=col, operator=Comparator.NOT_IN, parameter=["inactive", "deleted"]
        )

        assert repr(cond) == "status NOT_IN (inactive, deleted)"


class TestNullityCondition:
    """Tests for the NullityCondition class."""

    def test_repr_is_null(self):
        col = Column(name="email")
        cond = NullityCondition(column=col, is_null=True)

        assert repr(cond) == "email IS NULL"

    def test_repr_is_not_null(self):
        col = Column(name="email")
        cond = NullityCondition(column=col, is_null=False)

        assert repr(cond) == "email IS NOT NULL"


class TestComplexExpressions:
    """Tests for complex condition expressions with AND/OR combinations."""

    def test_and_has_precedence_over_or(self):
        """Test that & operator has higher precedence than | operator."""
        col1 = Column(name="age")
        col2 = Column(name="status")
        col3 = Column(name="score")

        cond1 = col1 > 18
        cond2 = col2 == "active"
        cond3 = col3 >= 80

        result = cond1 | cond2 & cond3

        assert result == OrCondition(conditions=[cond1, AndCondition(conditions=[cond2, cond3])])

    def test_parentheses_override_precedence(self):
        """Test that parentheses can override operator precedence for grouping."""
        col1 = Column(name="age")
        col2 = Column(name="status")
        col3 = Column(name="score")

        cond1 = col1 > 18
        cond2 = col2 == "active"
        cond3 = col3 >= 80

        result = (cond1 | cond2) & cond3

        assert result == AndCondition(conditions=[OrCondition(conditions=[cond1, cond2]), cond3])

    def test_complex_nested_expression(self):
        """Test complex expression with multiple levels of nesting."""
        age = Column(name="age")
        status = Column(name="status")
        score = Column(name="score")
        email = Column(name="email")

        adult_and_active = (age > 18) & (status == "active")
        high_score_with_email = (score >= 80) & email.is_not_null()
        result = adult_and_active | high_score_with_email

        cond1 = age > 18
        cond2 = status == "active"
        cond3 = score >= 80
        cond4 = email.is_not_null()

        assert result == OrCondition(
            conditions=[
                AndCondition(conditions=[cond1, cond2]),
                AndCondition(conditions=[cond3, cond4]),
            ]
        )

    def test_multiple_ands_flatten(self):
        """Test that multiple ANDs flatten into a single AndCondition."""
        col1 = Column(name="age")
        col2 = Column(name="status")
        col3 = Column(name="score")
        col4 = Column(name="city")

        cond1 = col1 > 18
        cond2 = col2 == "active"
        cond3 = col3 >= 80
        cond4 = col4 == "NYC"

        result = cond1 & cond2 & cond3 & cond4

        assert result == AndCondition(conditions=[cond1, cond2, cond3, cond4])

    def test_multiple_ors_flatten(self):
        """Test that multiple ORs flatten into a single OrCondition."""
        col1 = Column(name="status")

        cond1 = col1 == "active"
        cond2 = col1 == "pending"
        cond3 = col1 == "approved"
        cond4 = col1 == "verified"

        result = cond1 | cond2 | cond3 | cond4

        assert result == OrCondition(conditions=[cond1, cond2, cond3, cond4])
