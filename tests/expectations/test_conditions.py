from __future__ import annotations

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.expectations.row_conditions import (
    AndCondition,
    Column,
    ComparisonCondition,
    Condition,
    ConditionParserError,
    InvalidConditionTypeError,
    NullityCondition,
    Operator,
    OrCondition,
    PassThroughCondition,
    deserialize_row_condition,
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

    def test_or_with_two_conditions(sef):
        condition_a = Condition()
        condition_b = Condition()

        result = condition_a | condition_b
        assert result == OrCondition(conditions=[condition_a, condition_b])


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


class TestColumn:
    def test_column_hash_equal(self):
        assert hash(Column("age")) == hash(Column("age"))

    def test_column_hash_not_equal(self):
        assert hash(Column("age")) != hash(Column("city"))

    def test_less_than_operator(self):
        col = Column("age")
        result = col < 18

        assert result == ComparisonCondition(column=col, operator=Operator.LESS_THAN, parameter=18)

    def test_less_than_or_equal_operator(self):
        col = Column("age")
        result = col <= 18

        assert result == ComparisonCondition(
            column=col, operator=Operator.LESS_THAN_OR_EQUAL, parameter=18
        )

    def test_equal_operator(self):
        col = Column("status")
        result = col == "active"

        assert result == ComparisonCondition(
            column=col, operator=Operator.EQUAL, parameter="active"
        )

    def test_not_equal_operator(self):
        col = Column("status")
        result = col != "inactive"

        assert result == ComparisonCondition(
            column=col, operator=Operator.NOT_EQUAL, parameter="inactive"
        )

    def test_greater_than_operator(self):
        col = Column("age")
        result = col > 65

        assert result == ComparisonCondition(
            column=col, operator=Operator.GREATER_THAN, parameter=65
        )

    def test_greater_than_or_equal_operator(self):
        col = Column("age")
        result = col >= 65

        assert result == ComparisonCondition(
            column=col, operator=Operator.GREATER_THAN_OR_EQUAL, parameter=65
        )

    def test_is_in_method(self):
        col = Column("status")
        result = col.is_in(["active", "pending", "approved"])

        assert result == ComparisonCondition(
            column=col, operator=Operator.IN, parameter=["active", "pending", "approved"]
        )

    def test_is_not_in_method(self):
        col = Column("status")
        result = col.is_not_in(["inactive", "deleted"])

        assert result == ComparisonCondition(
            column=col, operator=Operator.NOT_IN, parameter=["inactive", "deleted"]
        )

    def test_is_null_method(self):
        col = Column("email")
        result = col.is_null()

        assert result == NullityCondition(column=col, is_null=True)

    def test_is_not_null_method(self):
        col = Column("email")
        result = col.is_not_null()

        assert result == NullityCondition(column=col, is_null=False)


class TestComparisonCondition:
    def test_repr_equal_operator(self):
        col = Column("status")
        cond = ComparisonCondition(column=col, operator=Operator.EQUAL, parameter="active")

        assert repr(cond) == "status == active"

    def test_repr_not_equal_operator(self):
        col = Column("status")
        cond = ComparisonCondition(column=col, operator=Operator.NOT_EQUAL, parameter="inactive")

        assert repr(cond) == "status != inactive"

    def test_repr_less_than_operator(self):
        col = Column("age")
        cond = ComparisonCondition(column=col, operator=Operator.LESS_THAN, parameter=18)

        assert repr(cond) == "age < 18"

    def test_repr_less_than_or_equal_operator(self):
        col = Column("age")
        cond = ComparisonCondition(column=col, operator=Operator.LESS_THAN_OR_EQUAL, parameter=18)

        assert repr(cond) == "age <= 18"

    def test_repr_greater_than_operator(self):
        col = Column("age")
        cond = ComparisonCondition(column=col, operator=Operator.GREATER_THAN, parameter=65)

        assert repr(cond) == "age > 65"

    def test_repr_greater_than_or_equal_operator(self):
        col = Column("age")
        cond = ComparisonCondition(
            column=col, operator=Operator.GREATER_THAN_OR_EQUAL, parameter=65
        )

        assert repr(cond) == "age >= 65"

    def test_repr_in_operator(self):
        col = Column("status")
        cond = ComparisonCondition(
            column=col, operator=Operator.IN, parameter=["active", "pending", "approved"]
        )

        assert repr(cond) == "status IN (active, pending, approved)"

    def test_repr_not_in_operator(self):
        col = Column("status")
        cond = ComparisonCondition(
            column=col, operator=Operator.NOT_IN, parameter=["inactive", "deleted"]
        )

        assert repr(cond) == "status NOT_IN (inactive, deleted)"

    def test_comparison_condition_with_none_parameter_raises_error(self):
        col = Column("status")

        with pytest.raises(ValidationError):
            ComparisonCondition(column=col, operator=Operator.NOT_EQUAL, parameter=None)


class TestNullityCondition:
    """Tests for the NullityCondition class."""

    def test_repr_is_null(self):
        col = Column("email")
        cond = NullityCondition(column=col, is_null=True)

        assert repr(cond) == "email IS NULL"

    def test_repr_is_not_null(self):
        col = Column("email")
        cond = NullityCondition(column=col, is_null=False)

        assert repr(cond) == "email IS NOT NULL"


class TestComplexExpressions:
    """Tests for complex condition expressions with AND/OR combinations."""

    def test_and_has_precedence_over_or(self):
        """Test that & operator has higher precedence than | operator."""
        col1 = Column("age")
        col2 = Column("status")
        col3 = Column("score")

        cond1 = col1 > 18
        cond2 = col2 == "active"
        cond3 = col3 >= 80

        result = cond1 | cond2 & cond3

        assert result == OrCondition(conditions=[cond1, AndCondition(conditions=[cond2, cond3])])

    def test_parentheses_override_precedence(self):
        """Test that parentheses can override operator precedence for grouping."""
        col1 = Column("age")
        col2 = Column("status")
        col3 = Column("score")

        cond1 = col1 > 18
        cond2 = col2 == "active"
        cond3 = col3 >= 80

        result = (cond1 | cond2) & cond3

        assert result == AndCondition(conditions=[OrCondition(conditions=[cond1, cond2]), cond3])

    def test_complex_nested_expression(self):
        """Test complex expression with multiple levels of nesting."""
        age = Column("age")
        status = Column("status")
        score = Column("score")
        email = Column("email")

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


class TestConditionSerialization:
    """Tests for serialization (converting Condition objects to dicts)."""

    def test_comparison_condition_serialization(self):
        """Test that ComparisonCondition serializes to the expected dict."""
        col = Column("age")
        cond = ComparisonCondition(column=col, operator=Operator.LESS_THAN, parameter=18)

        result = cond.dict(exclude_defaults=True)

        assert result == {
            "type": "comparison",
            "column": {"name": "age"},
            "operator": "<",
            "parameter": 18,
        }

    def test_nullity_condition_serialization(self):
        """Test that NullityCondition serializes to the expected dict."""
        col = Column("email")
        cond = NullityCondition(column=col, is_null=True)

        result = cond.dict(exclude_defaults=True)

        assert result == {
            "type": "nullity",
            "column": {"name": "email"},
            "is_null": True,
        }

    def test_and_condition_serialization(self):
        """Test that AndCondition serializes to the expected dict with nested conditions."""
        col = Column("quantity")
        cond1 = ComparisonCondition(column=col, operator=Operator.GREATER_THAN, parameter=0)
        cond2 = ComparisonCondition(column=col, operator=Operator.LESS_THAN, parameter=10)
        and_cond = AndCondition(conditions=[cond1, cond2])

        result = and_cond.dict(exclude_defaults=True)

        assert result == {
            "type": "and",
            "conditions": [
                {
                    "type": "comparison",
                    "column": {"name": "quantity"},
                    "operator": ">",
                    "parameter": 0,
                },
                {
                    "type": "comparison",
                    "column": {"name": "quantity"},
                    "operator": "<",
                    "parameter": 10,
                },
            ],
        }

    def test_or_condition_serialization(self):
        """Test that OrCondition serializes to the expected dict with nested conditions."""
        col = Column("status")
        cond1 = ComparisonCondition(column=col, operator=Operator.EQUAL, parameter="active")
        cond2 = ComparisonCondition(column=col, operator=Operator.EQUAL, parameter="pending")
        or_cond = OrCondition(conditions=[cond1, cond2])

        result = or_cond.dict(exclude_defaults=True)

        assert result == {
            "type": "or",
            "conditions": [
                {
                    "type": "comparison",
                    "column": {"name": "status"},
                    "operator": "==",
                    "parameter": "active",
                },
                {
                    "type": "comparison",
                    "column": {"name": "status"},
                    "operator": "==",
                    "parameter": "pending",
                },
            ],
        }


class TestConditionDeserialization:
    """Tests for deserialization (converting dicts back to Condition objects)."""

    def test_deserialize_comparison_condition(self):
        """Test deserializing a ComparisonCondition from a dict."""
        cond_dict = {
            "type": "comparison",
            "column": {"name": "age"},
            "operator": "<",
            "parameter": 18,
        }

        result = deserialize_row_condition(cond_dict)

        expected = ComparisonCondition(
            column=Column("age"), operator=Operator.LESS_THAN, parameter=18
        )
        assert result == expected

    def test_deserialize_nullity_condition_is_null(self):
        """Test deserializing a NullityCondition with is_null=True from a dict."""
        cond_dict = {
            "type": "nullity",
            "column": {"name": "email"},
            "is_null": True,
        }

        result = deserialize_row_condition(cond_dict)

        expected = NullityCondition(column=Column("email"), is_null=True)
        assert result == expected

    def test_deserialize_nullity_condition_is_not_null(self):
        """Test deserializing a NullityCondition with is_null=False from a dict."""
        cond_dict = {
            "type": "nullity",
            "column": {"name": "email"},
            "is_null": False,
        }

        result = deserialize_row_condition(cond_dict)

        expected = NullityCondition(column=Column("email"), is_null=False)
        assert result == expected

    def test_deserialize_and_condition(self):
        """Test deserializing an AndCondition from a dict."""
        cond_dict = {
            "type": "and",
            "conditions": [
                {
                    "type": "comparison",
                    "column": {"name": "quantity"},
                    "operator": ">",
                    "parameter": 0,
                },
                {
                    "type": "comparison",
                    "column": {"name": "quantity"},
                    "operator": "<",
                    "parameter": 10,
                },
            ],
        }

        result = deserialize_row_condition(cond_dict)

        col = Column("quantity")
        expected = AndCondition(
            conditions=[
                ComparisonCondition(column=col, operator=Operator.GREATER_THAN, parameter=0),
                ComparisonCondition(column=col, operator=Operator.LESS_THAN, parameter=10),
            ]
        )
        assert result == expected

    def test_deserialize_or_condition(self):
        """Test deserializing an OrCondition from a dict."""
        cond_dict = {
            "type": "or",
            "conditions": [
                {
                    "type": "comparison",
                    "column": {"name": "status"},
                    "operator": "==",
                    "parameter": "active",
                },
                {
                    "type": "comparison",
                    "column": {"name": "status"},
                    "operator": "==",
                    "parameter": "pending",
                },
            ],
        }

        result = deserialize_row_condition(cond_dict)

        col = Column("status")
        expected = OrCondition(
            conditions=[
                ComparisonCondition(column=col, operator=Operator.EQUAL, parameter="active"),
                ComparisonCondition(column=col, operator=Operator.EQUAL, parameter="pending"),
            ]
        )
        assert result == expected

    def test_deserialize_nested_and_or_condition(self):
        """Test deserializing nested AND/OR conditions from a dict."""
        cond_dict = {
            "type": "or",
            "conditions": [
                {
                    "type": "and",
                    "conditions": [
                        {
                            "type": "comparison",
                            "column": {"name": "age"},
                            "operator": ">",
                            "parameter": 18,
                        },
                        {
                            "type": "comparison",
                            "column": {"name": "status"},
                            "operator": "==",
                            "parameter": "active",
                        },
                    ],
                },
                {
                    "type": "comparison",
                    "column": {"name": "age"},
                    "operator": "<",
                    "parameter": 65,
                },
            ],
        }

        result = deserialize_row_condition(cond_dict)

        age = Column("age")
        status = Column("status")
        expected = OrCondition(
            conditions=[
                AndCondition(
                    conditions=[
                        ComparisonCondition(
                            column=age, operator=Operator.GREATER_THAN, parameter=18
                        ),
                        ComparisonCondition(
                            column=status, operator=Operator.EQUAL, parameter="active"
                        ),
                    ]
                ),
                ComparisonCondition(column=age, operator=Operator.LESS_THAN, parameter=65),
            ]
        )
        assert result == expected

    def test_deserialize_string_returns_string(self):
        """Test that deserializing a string returns the string unchanged."""
        result = deserialize_row_condition("some_condition")

        assert result == "some_condition"
        assert isinstance(result, str)

    def test_deserialize_none_returns_none(self):
        """Test that deserializing None returns None."""
        result = deserialize_row_condition(None)

        assert result is None

    def test_deserialize_invalid_type_raises_error(self):
        """Test that deserializing an invalid type raises InvalidConditionTypeError."""
        with pytest.raises(InvalidConditionTypeError):
            deserialize_row_condition(12345)

    def test_deserialize_dict_without_type_raises_error(self):
        """Test that deserializing a dict without a type field raises ConditionParserError."""
        cond_dict = {
            "column": {"name": "age"},
            "some_field": "value",
        }

        with pytest.raises(ConditionParserError):
            deserialize_row_condition(cond_dict)

    def test_deserialize_dict_with_unknown_type_raises_error(self):
        """Test that deserializing a dict with unknown type raises ConditionParserError."""
        cond_dict = {
            "type": "unknown_type",
            "column": {"name": "age"},
        }

        with pytest.raises(ConditionParserError):
            deserialize_row_condition(cond_dict)


class TestConditionRoundTrip:
    """Tests for round-trip serialization and deserialization."""

    def test_and_condition_round_trip(self):
        """Test round-trip serialization/deserialization preserves condition structure."""
        col = Column("quantity")
        original = AndCondition(
            conditions=[
                ComparisonCondition(column=col, operator=Operator.GREATER_THAN, parameter=0),
                ComparisonCondition(column=col, operator=Operator.LESS_THAN, parameter=10),
            ]
        )

        serialized = original.dict()
        deserialized = deserialize_row_condition(serialized)

        assert deserialized == original


class TestPassThroughCondition:
    def test_pass_through_condition_creation(self):
        condition = PassThroughCondition(pass_through_filter='col("age") > 18')

        assert condition.pass_through_filter == 'col("age") > 18'
        assert condition.type == "pass_through"

    def test_pass_through_condition_repr(self):
        condition = PassThroughCondition(pass_through_filter='col("age") > 18')

        assert repr(condition) == "PassThrough('col(\"age\") > 18')"

    def test_pass_through_condition_serialization(self):
        condition = PassThroughCondition(pass_through_filter="PClass=='1st'")

        result = condition.dict()

        assert result == {"type": "pass_through", "pass_through_filter": "PClass=='1st'"}

    def test_pass_through_condition_deserialization(self):
        cond_dict = {"type": "pass_through", "pass_through_filter": "quantity > 0"}

        result = deserialize_row_condition(cond_dict)

        expected = PassThroughCondition(pass_through_filter="quantity > 0")
        assert result == expected

    def test_pass_through_condition_round_trip(self):
        original = PassThroughCondition(pass_through_filter="col > 100")

        serialized = original.dict()
        deserialized = deserialize_row_condition(serialized)

        assert deserialized == original
