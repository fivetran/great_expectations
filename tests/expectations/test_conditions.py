from __future__ import annotations

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.expectations.conditions import (
    AndCondition,
    Condition,
    OrCondition,
)


class TestCondition:
    """Tests for the base Condition class."""

    def test_condition_instantiation(self):
        """Test that Condition can be instantiated."""
        condition = Condition()
        assert isinstance(condition, Condition)


class TestAndCondition:
    """Tests for the AndCondition class."""

    def test_repr_single_condition(self):
        """Test __repr__ with a single condition."""
        cond = Condition()
        and_cond = AndCondition(conditions=[cond])
        assert repr(and_cond) == f"({cond!r})"

    def test_repr_multiple_conditions(self):
        """Test __repr__ with multiple conditions."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        and_cond = AndCondition(conditions=[cond1, cond2, cond3])
        expected = f"({cond1!r} AND {cond2!r} AND {cond3!r})"
        assert repr(and_cond) == expected

    def test_flattens_nested_and_conditions(self):
        """Test that AndCondition flattens nested AndConditions."""
        cond1 = Condition()
        cond2 = Condition()
        inner_and = AndCondition(conditions=[cond1, cond2])
        cond3 = Condition()

        # Nested AND should be flattened
        outer_and = AndCondition(conditions=[inner_and, cond3])
        assert isinstance(outer_and, AndCondition)
        # Should be flattened to [cond1, cond2, cond3]
        assert len(outer_and.conditions) == 3
        assert outer_and.conditions[0] == cond1
        assert outer_and.conditions[1] == cond2
        assert outer_and.conditions[2] == cond3

    def test_raises_error_with_or_condition(self):
        """Test that AndCondition raises error when given an OrCondition."""
        cond1 = Condition()
        or_cond = OrCondition(conditions=[cond1])

        with pytest.raises(ValidationError, match="AND groups cannot contain OR conditions"):
            AndCondition(conditions=[or_cond])

    def test_raises_error_with_mixed_conditions_including_or(self):
        """Test that AndCondition raises error when any condition is OrCondition."""
        cond1 = Condition()
        cond2 = Condition()
        or_cond = OrCondition(conditions=[cond1])

        with pytest.raises(ValidationError, match="AND groups cannot contain OR conditions"):
            AndCondition(conditions=[cond1, or_cond, cond2])

    def test_flattens_multiple_nested_and_conditions(self):
        """Test that AndCondition flattens multiple levels of nested ANDs."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        cond4 = Condition()

        # Create nested structure: AND(AND(cond1, cond2), AND(cond3, cond4))
        inner_and1 = AndCondition(conditions=[cond1, cond2])
        inner_and2 = AndCondition(conditions=[cond3, cond4])

        # Should flatten to [cond1, cond2, cond3, cond4]
        outer_and = AndCondition(conditions=[inner_and1, inner_and2])
        assert isinstance(outer_and, AndCondition)
        assert len(outer_and.conditions) == 4
        assert outer_and.conditions == [cond1, cond2, cond3, cond4]

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

        # Should completely flatten to [cond1, cond2, cond3, cond4, cond5]
        outer_and = AndCondition(conditions=[middle_and, inner_and])
        assert isinstance(outer_and, AndCondition)
        assert len(outer_and.conditions) == 5
        assert outer_and.conditions == [cond1, cond2, cond3, cond4, cond5]


class TestOrCondition:
    """Tests for the OrCondition class."""

    def test_repr_single_condition(self):
        """Test __repr__ with a single condition."""
        cond = Condition()
        or_cond = OrCondition(conditions=[cond])
        assert repr(or_cond) == f"({cond!r})"

    def test_repr_multiple_conditions(self):
        """Test __repr__ with multiple conditions."""
        cond1 = Condition()
        cond2 = Condition()
        cond3 = Condition()
        or_cond = OrCondition(conditions=[cond1, cond2, cond3])
        expected = f"({cond1!r} OR {cond2!r} OR {cond3!r})"
        assert repr(or_cond) == expected

    def test_raises_error_with_nested_or_condition(self):
        """Test that OrCondition raises error when given another."""
        cond1 = Condition()
        cond2 = Condition()
        inner_or = OrCondition(conditions=[cond1, cond2])
        cond3 = Condition()

        with pytest.raises(ValidationError, match="OR groups cannot contain nested OR conditions"):
            OrCondition(conditions=[inner_or, cond3])

    def test_can_contain_and_conditions(self):
        """Test that OrCondition can contain AndCondition instances."""
        cond1 = Condition()
        cond2 = Condition()
        and_cond = AndCondition(conditions=[cond1, cond2])
        cond3 = Condition()
        or_cond = OrCondition(conditions=[and_cond, cond3])
        expected = f"({and_cond!r} OR {cond3!r})"
        assert repr(or_cond) == expected
