from __future__ import annotations

import importlib
from operator import eq, ge, gt, le, lt, ne

import pytest

from great_expectations.compatibility.pydantic import BaseModel, ValidationError
from great_expectations.expectations.row_conditions import (
    AndCondition,
    Column,
    ColumnComparisonCondition,
    ComparisonCondition,
    Condition,
    ConditionParserError,
    InvalidConditionTypeError,
    InvalidParameterTypeError,
    NullityCondition,
    Operator,
    OrCondition,
    PassThroughCondition,
    RowConditionType,
    UnsupportedColumnComparisonOperatorError,
    deserialize_row_condition,
    find_column_comparisons,
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


COMPARISON_OPERATORS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.LESS_THAN,
    Operator.LESS_THAN_OR_EQUAL,
    Operator.GREATER_THAN,
    Operator.GREATER_THAN_OR_EQUAL,
]
SET_OPERATORS = [Operator.IN, Operator.NOT_IN]


class TestColumnComparisonCondition:
    """Tests for the condition that compares the values of two columns in the same row."""

    @pytest.mark.parametrize("operator", COMPARISON_OPERATORS)
    def test_construction_records_both_columns_and_the_operator(self, operator: Operator):
        cond = ColumnComparisonCondition(
            column=Column("end_date"), operator=operator, other_column=Column("start_date")
        )

        assert cond.type == "column_comparison"
        assert cond.column.name == "end_date"
        assert cond.operator == operator.value
        assert cond.other_column.name == "start_date"

    @pytest.mark.parametrize("operator", COMPARISON_OPERATORS)
    def test_parsing_accepts_the_operator_as_a_plain_string(self, operator: Operator):
        cond = ColumnComparisonCondition.parse_obj(
            {
                "column": {"name": "a"},
                "operator": operator.value,
                "other_column": {"name": "b"},
            }
        )

        assert cond.type == "column_comparison"
        assert cond.operator == operator.value

    def test_is_a_condition(self):
        cond = ColumnComparisonCondition(
            column=Column("a"), operator=Operator.EQUAL, other_column=Column("b")
        )

        assert isinstance(cond, Condition)

    @pytest.mark.parametrize(
        "operator,expected",
        [
            pytest.param(Operator.EQUAL, "end_date == start_date", id="equal"),
            pytest.param(Operator.NOT_EQUAL, "end_date != start_date", id="not_equal"),
            pytest.param(Operator.LESS_THAN, "end_date < start_date", id="less_than"),
            pytest.param(
                Operator.LESS_THAN_OR_EQUAL, "end_date <= start_date", id="less_than_or_equal"
            ),
            pytest.param(Operator.GREATER_THAN, "end_date > start_date", id="greater_than"),
            pytest.param(
                Operator.GREATER_THAN_OR_EQUAL,
                "end_date >= start_date",
                id="greater_than_or_equal",
            ),
        ],
    )
    def test_repr_shows_left_operator_right(self, operator: Operator, expected: str):
        cond = ColumnComparisonCondition(
            column=Column("end_date"), operator=operator, other_column=Column("start_date")
        )

        assert repr(cond) == expected

    def test_repr_shows_names_as_written(self):
        cond = ColumnComparisonCondition(
            column=Column("End Date"),
            operator=Operator.GREATER_THAN,
            other_column=Column("start-date"),
        )

        assert repr(cond) == "End Date > start-date"

    @pytest.mark.parametrize("operator", COMPARISON_OPERATORS)
    def test_serialization_has_the_four_documented_keys(self, operator: Operator):
        cond = ColumnComparisonCondition(
            column=Column("end_date"), operator=operator, other_column=Column("start_date")
        )

        expected = {
            "type": "column_comparison",
            "column": {"name": "end_date"},
            "operator": operator.value,
            "other_column": {"name": "start_date"},
        }
        assert cond.dict() == expected
        assert cond.dict(exclude_defaults=True) == expected

    def test_serialization_is_distinct_from_the_literal_comparison(self):
        column_cond = ColumnComparisonCondition(
            column=Column("a"), operator=Operator.EQUAL, other_column=Column("b")
        )
        literal_cond = ComparisonCondition(
            column=Column("a"), operator=Operator.EQUAL, parameter="b"
        )

        assert column_cond.dict()["type"] != literal_cond.dict()["type"]
        assert "other_column" not in literal_cond.dict()
        assert "parameter" not in column_cond.dict()

    def test_the_same_column_on_both_sides_is_allowed(self):
        cond = ColumnComparisonCondition(
            column=Column("a"), operator=Operator.EQUAL, other_column=Column("a")
        )

        assert repr(cond) == "a == a"

    def test_names_are_not_validated(self):
        cond = ColumnComparisonCondition(
            column=Column('we"ird `name`'),
            operator=Operator.LESS_THAN,
            other_column=Column("other [col]"),
        )

        assert cond.column.name == 'we"ird `name`'
        assert cond.other_column.name == "other [col]"

    def test_equality_follows_columns_in_order_and_operator(self):
        def build(left: str, operator: Operator, right: str) -> ColumnComparisonCondition:
            return ColumnComparisonCondition(
                column=Column(left), operator=operator, other_column=Column(right)
            )

        base = build("a", Operator.GREATER_THAN, "b")

        assert base == build("a", Operator.GREATER_THAN, "b")
        assert base != build("b", Operator.GREATER_THAN, "a")
        assert base != build("a", Operator.LESS_THAN, "b")
        assert base != build("a", Operator.GREATER_THAN, "c")

    @pytest.mark.parametrize("operator", SET_OPERATORS)
    def test_set_operators_are_rejected_at_construction(self, operator: Operator):
        with pytest.raises(ValidationError) as exc_info:
            ColumnComparisonCondition(
                column=Column("a"), operator=operator, other_column=Column("b")
            )

        message = str(exc_info.value)
        assert "Column comparisons support ==, !=, <, <=, > and >=" in message
        assert f"not {operator.value}" in message
        assert "Set membership against a column is not supported" in message

    @pytest.mark.parametrize("operator", SET_OPERATORS)
    def test_set_operators_given_as_plain_strings_are_rejected(self, operator: Operator):
        with pytest.raises(ValidationError, match="Set membership against a column"):
            ColumnComparisonCondition.parse_obj(
                {
                    "column": {"name": "a"},
                    "operator": operator.value,
                    "other_column": {"name": "b"},
                }
            )

    def test_unknown_operator_is_rejected(self):
        with pytest.raises(ValidationError):
            ColumnComparisonCondition.parse_obj(
                {
                    "column": {"name": "a"},
                    "operator": "LIKE",
                    "other_column": {"name": "b"},
                }
            )

    @pytest.mark.parametrize("operator", SET_OPERATORS)
    def test_unsupported_operator_error_names_the_operator(self, operator: Operator):
        error = UnsupportedColumnComparisonOperatorError(operator.value)

        assert isinstance(error, ValueError)
        assert str(error) == (
            f"Column comparisons support ==, !=, <, <=, > and >=, not {operator.value}. "
            "Set membership against a column is not supported."
        )

    def test_docstring_states_the_null_rule(self):
        doc = ColumnComparisonCondition.__doc__ or ""

        assert "null" in doc
        assert "every operator" in doc


@pytest.mark.parametrize(
    "compare,operator",
    [
        pytest.param(eq, Operator.EQUAL, id="equal"),
        pytest.param(ne, Operator.NOT_EQUAL, id="not_equal"),
        pytest.param(lt, Operator.LESS_THAN, id="less_than"),
        pytest.param(le, Operator.LESS_THAN_OR_EQUAL, id="less_than_or_equal"),
        pytest.param(gt, Operator.GREATER_THAN, id="greater_than"),
        pytest.param(ge, Operator.GREATER_THAN_OR_EQUAL, id="greater_than_or_equal"),
    ],
)
class TestColumnComparisonOperators:
    """Tests for how the comparison operators on Column choose the condition they build."""

    def test_a_column_on_the_right_builds_a_column_comparison(self, compare, operator):
        result = compare(Column("end_date"), Column("start_date"))

        assert isinstance(result, ColumnComparisonCondition)
        assert result.dict() == {
            "type": "column_comparison",
            "column": {"name": "end_date"},
            "operator": operator.value,
            "other_column": {"name": "start_date"},
        }

    def test_a_column_comparison_keeps_the_left_and_right_sides_in_order(self, compare, operator):
        result = compare(Column("left_side"), Column("right_side"))

        assert isinstance(result, ColumnComparisonCondition)
        assert result.column.name == "left_side"
        assert result.other_column.name == "right_side"

    def test_a_column_on_the_right_matches_the_directly_built_condition(self, compare, operator):
        result = compare(Column("a"), Column("b"))
        expected = ColumnComparisonCondition(
            column=Column("a"), operator=operator, other_column=Column("b")
        )

        assert result == expected

    def test_the_same_column_on_both_sides_is_a_column_comparison(self, compare, operator):
        result = compare(Column("a"), Column("a"))

        assert isinstance(result, ColumnComparisonCondition)
        assert result.column.name == "a"
        assert result.other_column.name == "a"

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param(18, id="int"),
            pytest.param(1.5, id="float"),
            pytest.param("active", id="str"),
            pytest.param(True, id="bool"),
        ],
    )
    def test_a_value_on_the_right_builds_the_literal_comparison(self, compare, operator, value):
        result = compare(Column("status"), value)

        assert type(result) is ComparisonCondition
        assert result.dict() == {
            "type": "comparison",
            "column": {"name": "status"},
            "operator": operator.value,
            "parameter": value,
        }

    def test_a_dict_holding_a_name_on_the_right_stays_a_literal_value(self, compare, operator):
        result = compare(Column("status"), {"name": "other"})

        assert type(result) is ComparisonCondition
        assert result.parameter == {"name": "other"}


class TestColumnComparisonOperatorTyping:
    def test_the_result_type_narrows_to_one_condition_class(self) -> None:
        # The annotations are checked by the type checker (this method is annotated so that it
        # checks the body): if the operators returned a union, or the wrong class for either
        # right-hand side, these assignments would not type-check.
        left, right = Column("a"), Column("b")

        column_pair_eq: ColumnComparisonCondition = left == right
        column_pair_ne: ColumnComparisonCondition = left != right
        column_pair_lt: ColumnComparisonCondition = left < right
        column_pair_le: ColumnComparisonCondition = left <= right
        column_pair_gt: ColumnComparisonCondition = left > right
        column_pair_ge: ColumnComparisonCondition = left >= right
        literal_eq: ComparisonCondition = left == 5
        literal_ne: ComparisonCondition = left != 5
        literal_lt: ComparisonCondition = left < 5
        literal_le: ComparisonCondition = left <= 5
        literal_gt: ComparisonCondition = left > 5
        literal_ge: ComparisonCondition = left >= 5

        for column_pair in (
            column_pair_eq,
            column_pair_ne,
            column_pair_lt,
            column_pair_le,
            column_pair_gt,
            column_pair_ge,
        ):
            assert type(column_pair) is ColumnComparisonCondition
        for literal in (literal_eq, literal_ne, literal_lt, literal_le, literal_gt, literal_ge):
            assert type(literal) is ComparisonCondition

    def test_a_column_comparison_combines_with_other_conditions(self):
        combined = (Column("a") > Column("b")) & (Column("c") == "x")

        assert isinstance(combined, AndCondition)
        assert isinstance(combined.conditions[0], ColumnComparisonCondition)
        assert isinstance(combined.conditions[1], ComparisonCondition)


class TestDirectlyBuiltLiteralWithColumnValue:
    @pytest.mark.parametrize("operator", COMPARISON_OPERATORS)
    def test_it_stays_a_literal_comparison(self, operator: Operator):
        # Only the operators on Column route a column on the right to the column comparison.
        # Building the literal condition directly is unchanged: it stays a literal and keeps its
        # column value.
        result = ComparisonCondition(column=Column("a"), operator=operator, parameter=Column("b"))

        assert type(result) is ComparisonCondition
        assert result.type == "comparison"
        assert isinstance(result.parameter, Column)
        assert result.parameter.name == "b"
        assert result.dict() == {
            "type": "comparison",
            "column": {"name": "a"},
            "operator": operator.value,
            "parameter": {"name": "b"},
        }


@pytest.mark.parametrize("method_name", ["is_in", "is_not_in"])
class TestColumnSetMembershipGuard:
    def test_a_bare_column_is_rejected(self, method_name):
        method = getattr(Column("status"), method_name)

        with pytest.raises(InvalidParameterTypeError) as exc_info:
            method(Column("allowed"))

        message = str(exc_info.value)
        assert message.startswith("Invalid Parameter type: ")
        assert f"{method_name} does not accept a Column" in message
        assert "set membership against a column is not supported" in message
        assert "use ==, !=, <, <=, > or >=" in message

    def test_a_list_holding_a_column_is_rejected(self, method_name):
        method = getattr(Column("status"), method_name)

        with pytest.raises(InvalidParameterTypeError) as exc_info:
            method(["active", Column("allowed")])

        message = str(exc_info.value)
        assert f"{method_name} does not accept a Column" in message
        assert "set membership against a column is not supported" in message
        assert "use ==, !=, <, <=, > or >=" in message

    def test_a_column_as_the_first_element_is_rejected(self, method_name):
        method = getattr(Column("status"), method_name)

        with pytest.raises(InvalidParameterTypeError, match="does not accept a Column"):
            method([Column("allowed")])

    def test_a_generator_holding_a_column_is_rejected(self, method_name):
        method = getattr(Column("status"), method_name)

        with pytest.raises(InvalidParameterTypeError, match="does not accept a Column"):
            method(item for item in ["active", Column("allowed")])

    def test_the_rejection_is_a_type_error_raised_before_validation(self, method_name):
        method = getattr(Column("status"), method_name)

        with pytest.raises(TypeError) as exc_info:
            method(Column("allowed"))

        assert not isinstance(exc_info.value, ValidationError)

    def test_a_generator_of_plain_values_is_read_once(self, method_name):
        method = getattr(Column("status"), method_name)
        expected_operator = Operator.IN if method_name == "is_in" else Operator.NOT_IN
        values = (item for item in ["active", "pending"])

        result = method(values)

        assert type(result) is ComparisonCondition
        assert result.operator == expected_operator.value
        assert result.parameter == ["active", "pending"]

    def test_a_tuple_of_plain_values_still_builds_a_literal_condition(self, method_name):
        method = getattr(Column("status"), method_name)

        result = method(("active", "pending"))

        assert type(result) is ComparisonCondition
        assert result.parameter == ["active", "pending"]


def _column_comparison(
    left: str = "end_date", operator: Operator = Operator.GREATER_THAN, right: str = "start_date"
) -> ColumnComparisonCondition:
    return ColumnComparisonCondition(
        column=Column(left), operator=operator, other_column=Column(right)
    )


class TestColumnComparisonDeserialization:
    """A saved column comparison reloads as a column comparison."""

    @pytest.mark.parametrize("operator", COMPARISON_OPERATORS)
    def test_a_saved_column_comparison_reloads_as_one(self, operator: Operator):
        saved = {
            "type": "column_comparison",
            "column": {"name": "end_date"},
            "operator": operator.value,
            "other_column": {"name": "start_date"},
        }

        result = deserialize_row_condition(saved)

        assert type(result) is ColumnComparisonCondition
        assert result.column.name == "end_date"
        assert result.operator == operator.value
        assert result.other_column.name == "start_date"
        assert result.dict() == saved

    @pytest.mark.parametrize("operator", COMPARISON_OPERATORS)
    def test_round_trip_standalone(self, operator: Operator):
        original = _column_comparison(operator=operator)

        reloaded = deserialize_row_condition(original.dict())

        assert type(reloaded) is ColumnComparisonCondition
        assert reloaded == original
        assert reloaded.dict() == original.dict()

    def test_round_trip_with_defaults_excluded(self):
        original = _column_comparison()

        reloaded = deserialize_row_condition(original.dict(exclude_defaults=True))

        assert type(reloaded) is ColumnComparisonCondition
        assert reloaded.dict() == original.dict()

    def test_round_trip_nested_in_and(self):
        original = AndCondition(
            conditions=[
                _column_comparison("end_date", Operator.GREATER_THAN, "start_date"),
                ComparisonCondition(
                    column=Column("status"), operator=Operator.EQUAL, parameter="x"
                ),
                _column_comparison("price", Operator.LESS_THAN_OR_EQUAL, "cost"),
            ]
        )

        reloaded = deserialize_row_condition(original.dict())

        assert type(reloaded) is AndCondition
        assert [type(child) for child in reloaded.conditions] == [
            ColumnComparisonCondition,
            ComparisonCondition,
            ColumnComparisonCondition,
        ]
        assert reloaded.dict() == original.dict()
        assert reloaded == original

    def test_round_trip_nested_in_or(self):
        original = OrCondition(
            conditions=[
                _column_comparison("a", Operator.EQUAL, "b"),
                NullityCondition(column=Column("a"), is_null=True),
                _column_comparison("c", Operator.NOT_EQUAL, "d"),
            ]
        )

        reloaded = deserialize_row_condition(original.dict())

        assert type(reloaded) is OrCondition
        assert [type(child) for child in reloaded.conditions] == [
            ColumnComparisonCondition,
            NullityCondition,
            ColumnComparisonCondition,
        ]
        assert reloaded.dict() == original.dict()
        assert reloaded == original

    def test_round_trip_of_a_group_built_with_operators(self):
        original = (Column("a") > Column("b")) & (Column("c") == "x")

        reloaded = deserialize_row_condition(original.dict())

        assert type(reloaded) is AndCondition
        assert type(reloaded.conditions[0]) is ColumnComparisonCondition
        assert type(reloaded.conditions[1]) is ComparisonCondition
        assert reloaded.dict() == original.dict()

    @pytest.mark.parametrize(
        "group,type_tag", [(AndCondition, "and"), (OrCondition, "or")], ids=["and", "or"]
    )
    def test_a_group_parsed_from_a_dict_restores_column_comparison_children(
        self, group: type[AndCondition | OrCondition], type_tag: str
    ):
        saved = {
            "type": type_tag,
            "conditions": [
                _column_comparison().dict(),
                _column_comparison("x", Operator.EQUAL, "y").dict(),
            ],
        }

        result = group.parse_obj(saved)

        assert [type(child) for child in result.conditions] == [ColumnComparisonCondition] * 2
        assert result.dict() == saved


class TestSavedLiteralComparisonWithDictValue:
    """A literal comparison whose value looks like a column stays a literal comparison."""

    SAVED_LITERAL = {
        "type": "comparison",
        "column": {"name": "a"},
        "operator": "==",
        "parameter": {"name": "b"},
    }

    def test_it_reloads_as_a_literal_comparison(self):
        result = deserialize_row_condition(dict(self.SAVED_LITERAL))

        assert type(result) is ComparisonCondition
        assert type(result) is not ColumnComparisonCondition
        assert result.parameter == {"name": "b"}
        assert not isinstance(result.parameter, Column)

    def test_it_round_trips_unchanged(self):
        reloaded = deserialize_row_condition(dict(self.SAVED_LITERAL))

        assert type(reloaded) is ComparisonCondition
        assert reloaded.dict() == self.SAVED_LITERAL
        assert deserialize_row_condition(reloaded.dict()).dict() == self.SAVED_LITERAL

    @pytest.mark.parametrize("type_tag", ["and", "or"])
    def test_it_stays_a_literal_inside_a_group(self, type_tag: str) -> None:
        saved = {
            "type": type_tag,
            "conditions": [dict(self.SAVED_LITERAL), _column_comparison().dict()],
        }

        reloaded = deserialize_row_condition(saved)

        assert isinstance(reloaded, (AndCondition, OrCondition))
        assert type(reloaded.conditions[0]) is ComparisonCondition
        assert type(reloaded.conditions[1]) is ColumnComparisonCondition
        assert reloaded.dict() == saved

    def test_a_literal_and_a_column_comparison_of_the_same_columns_stay_distinct(self):
        literal = deserialize_row_condition(
            {**self.SAVED_LITERAL, "operator": ">"},
        )
        column_pair = deserialize_row_condition(
            _column_comparison("a", Operator.GREATER_THAN, "b").dict()
        )

        assert type(literal) is ComparisonCondition
        assert type(column_pair) is ColumnComparisonCondition
        assert literal.dict() != column_pair.dict()


class TestSetOperatorsRejectedWhenLoadingAColumnComparison:
    @pytest.mark.parametrize("operator", SET_OPERATORS)
    def test_loading_a_standalone_column_comparison_is_rejected(self, operator: Operator):
        saved = {
            "type": "column_comparison",
            "column": {"name": "a"},
            "operator": operator.value,
            "other_column": {"name": "b"},
        }

        with pytest.raises(ValidationError) as exc_info:
            deserialize_row_condition(saved)

        message = str(exc_info.value)
        assert "Set membership against a column is not supported" in message
        assert f"not {operator.value}" in message

    @pytest.mark.parametrize("group", ["and", "or"])
    @pytest.mark.parametrize("operator", SET_OPERATORS)
    def test_loading_one_nested_in_a_group_is_rejected(self, group: str, operator: Operator):
        saved = {
            "type": group,
            "conditions": [
                _column_comparison().dict(),
                {
                    "type": "column_comparison",
                    "column": {"name": "a"},
                    "operator": operator.value,
                    "other_column": {"name": "b"},
                },
            ],
        }

        with pytest.raises(
            ValidationError, match="Set membership against a column is not supported"
        ):
            deserialize_row_condition(saved)


@pytest.mark.parametrize(
    "module_name",
    [
        "great_expectations.expectations.row_conditions",
        "great_expectations.expectations.conditions",
    ],
)
class TestColumnComparisonConditionIsPublic:
    def test_it_is_importable_from_the_module(self, module_name: str):
        module = importlib.import_module(module_name)

        assert hasattr(module, "ColumnComparisonCondition")

    def test_it_is_the_same_class_from_every_module(self, module_name: str):
        module = importlib.import_module(module_name)

        assert module.ColumnComparisonCondition is ColumnComparisonCondition

    def test_it_has_a_docstring(self, module_name: str):
        module = importlib.import_module(module_name)

        assert module.ColumnComparisonCondition.__doc__
        assert module.ColumnComparisonCondition.__doc__.strip()

    def test_the_existing_condition_names_are_still_exported(self, module_name: str):
        module = importlib.import_module(module_name)

        for name in (
            "AndCondition",
            "Column",
            "ComparisonCondition",
            "Condition",
            "NullityCondition",
            "Operator",
            "OrCondition",
            "PassThroughCondition",
            "RowConditionType",
            "deserialize_row_condition",
            "validate_row_condition",
        ):
            assert hasattr(module, name), name


class _RowConditionHolder(BaseModel):
    row_condition: RowConditionType = None


class TestRowConditionTypeUnion:
    """Parsing a dict into a ``RowConditionType`` field picks the member the dict is tagged for."""

    def test_a_column_comparison_dict_parses_as_a_column_comparison(self):
        saved = _column_comparison().dict()

        holder = _RowConditionHolder(row_condition=saved)

        assert type(holder.row_condition) is ColumnComparisonCondition
        assert holder.row_condition.dict() == saved

    def test_a_comparison_dict_parses_as_a_literal_comparison(self):
        saved = {
            "type": "comparison",
            "column": {"name": "a"},
            "operator": "==",
            "parameter": 1,
        }

        holder = _RowConditionHolder(row_condition=saved)

        assert type(holder.row_condition) is ComparisonCondition
        assert holder.row_condition.dict() == saved

    def test_a_comparison_dict_with_a_column_shaped_value_stays_a_literal_comparison(self):
        saved = {
            "type": "comparison",
            "column": {"name": "a"},
            "operator": "==",
            "parameter": {"name": "b"},
        }

        holder = _RowConditionHolder(row_condition=saved)

        assert type(holder.row_condition) is ComparisonCondition
        assert holder.row_condition.dict() == saved

    def test_a_column_comparison_instance_is_kept(self):
        condition = _column_comparison()

        holder = _RowConditionHolder(row_condition=condition)

        assert type(holder.row_condition) is ColumnComparisonCondition
        assert holder.row_condition.dict() == condition.dict()

    def test_existing_members_still_parse(self):
        nullity = {"type": "nullity", "column": {"name": "a"}, "is_null": True}
        pass_through = {"type": "pass_through", "pass_through_filter": "a > 1"}

        assert type(_RowConditionHolder(row_condition=nullity).row_condition) is NullityCondition
        assert (
            type(_RowConditionHolder(row_condition=pass_through).row_condition)
            is PassThroughCondition
        )
        assert _RowConditionHolder(row_condition="a > 1").row_condition == "a > 1"
        assert _RowConditionHolder(row_condition=None).row_condition is None

    def test_a_column_comparison_with_a_set_operator_is_not_accepted(self):
        saved = {
            "type": "column_comparison",
            "column": {"name": "a"},
            "operator": Operator.IN.value,
            "other_column": {"name": "b"},
        }

        with pytest.raises(
            ValidationError, match="Set membership against a column is not supported"
        ):
            _RowConditionHolder(row_condition=saved)

    def test_the_column_comparison_member_comes_after_the_pass_through_member(self):
        # Appending the new member keeps the position of every existing member, so the schemas
        # generated from this union only gain an entry at the end.
        members = list(RowConditionType.__args__)

        assert members.index(ColumnComparisonCondition) == members.index(PassThroughCondition) + 1
        assert members[-1] is type(None)
        assert members[:7] == [
            str,
            ComparisonCondition,
            NullityCondition,
            AndCondition,
            OrCondition,
            PassThroughCondition,
            ColumnComparisonCondition,
        ]


class TestFindColumnComparisons:
    """``find_column_comparisons`` lists every column comparison in a row condition."""

    @staticmethod
    def _described(found: list[ColumnComparisonCondition]) -> list[str]:
        for condition in found:
            assert type(condition) is ColumnComparisonCondition
        return [repr(condition) for condition in found]

    def test_a_standalone_column_comparison_is_returned_on_its_own(self):
        found = find_column_comparisons(_column_comparison("end_date", Operator.GREATER_THAN, "s"))

        assert self._described(found) == ["end_date > s"]
        assert found[0].column.name == "end_date"
        assert found[0].operator == Operator.GREATER_THAN.value
        assert found[0].other_column.name == "s"

    @pytest.mark.parametrize(
        "row_condition",
        [
            pytest.param(None, id="absent"),
            pytest.param("a > b", id="legacy string"),
            pytest.param(PassThroughCondition(pass_through_filter="a > b"), id="pass-through"),
            pytest.param(Column("a") > 1, id="literal comparison"),
            pytest.param(Column("a") > "b", id="literal comparison against a string"),
            pytest.param(Column("a").is_null(), id="nullity"),
            pytest.param((Column("a") > 1) & Column("b").is_not_null(), id="literal-only AND"),
            pytest.param(
                OrCondition(conditions=[Column("a") > 1, Column("b").is_null()]),
                id="literal-only OR",
            ),
            pytest.param(
                OrCondition(
                    conditions=[
                        AndCondition(conditions=[Column("a") > 1, Column("b") < 2]),
                        Column("c").is_null(),
                    ]
                ),
                id="literal-only OR of an AND",
            ),
            pytest.param(
                ComparisonCondition(
                    column=Column("a"), operator=Operator.EQUAL, parameter={"name": "b"}
                ),
                id="literal comparison whose value looks like a column",
            ),
        ],
    )
    def test_nothing_is_found_without_a_column_comparison(self, row_condition: RowConditionType):
        assert find_column_comparisons(row_condition) == []

    @pytest.mark.parametrize("group", [AndCondition, OrCondition])
    def test_group_members_are_returned_in_order(self, group: type[AndCondition | OrCondition]):
        row_condition = group(
            conditions=[
                _column_comparison("a", Operator.LESS_THAN, "b"),
                Column("status") == "shipped",
                _column_comparison("c", Operator.NOT_EQUAL, "d"),
                Column("e").is_null(),
                _column_comparison("f", Operator.GREATER_THAN_OR_EQUAL, "g"),
            ]
        )

        found = find_column_comparisons(row_condition)

        assert self._described(found) == ["a < b", "c != d", "f >= g"]

    def test_the_search_is_depth_first_and_left_to_right(self):
        # A breadth-first search would visit the shallow "s < t" first.
        row_condition = OrCondition(
            conditions=[
                AndCondition(
                    conditions=[
                        AndCondition(
                            conditions=[
                                _column_comparison("a", Operator.EQUAL, "b"),
                                AndCondition(
                                    conditions=[_column_comparison("c", Operator.EQUAL, "d")]
                                ),
                            ]
                        ),
                        _column_comparison("e", Operator.EQUAL, "f"),
                    ]
                ),
                _column_comparison("s", Operator.LESS_THAN, "t"),
                AndCondition(
                    conditions=[
                        Column("x") > 1,
                        _column_comparison("u", Operator.GREATER_THAN, "v"),
                    ]
                ),
            ]
        )

        found = find_column_comparisons(row_condition)

        assert self._described(found) == ["a == b", "c == d", "e == f", "s < t", "u > v"]

    def test_a_group_with_an_or_inside_an_and_is_still_searched(self):
        # The search does not validate: it walks whatever tree it is given.
        row_condition = AndCondition(
            conditions=[
                OrCondition(
                    conditions=[
                        _column_comparison("a", Operator.EQUAL, "b"),
                        _column_comparison("c", Operator.EQUAL, "d"),
                    ]
                ),
                _column_comparison("e", Operator.EQUAL, "f"),
            ]
        )

        found = find_column_comparisons(row_condition)

        assert self._described(found) == ["a == b", "c == d", "e == f"]

    def test_the_same_comparison_written_twice_is_returned_twice(self):
        row_condition = AndCondition(
            conditions=[_column_comparison("a", Operator.EQUAL, "b")] * 2
            + [_column_comparison("b", Operator.EQUAL, "a")]
        )

        found = find_column_comparisons(row_condition)

        assert self._described(found) == ["a == b", "a == b", "b == a"]

    def test_a_column_comparison_that_was_saved_and_reloaded_is_found(self):
        saved = OrCondition(
            conditions=[
                AndCondition(
                    conditions=[
                        Column("a") > 1,
                        _column_comparison("end_date", Operator.GREATER_THAN, "start_date"),
                    ]
                ),
                _column_comparison("x", Operator.LESS_THAN_OR_EQUAL, "y"),
            ]
        ).dict()

        found = find_column_comparisons(deserialize_row_condition(saved))

        assert self._described(found) == ["end_date > start_date", "x <= y"]

    def test_the_search_leaves_the_row_condition_unchanged(self):
        row_condition = AndCondition(
            conditions=[_column_comparison("a", Operator.EQUAL, "b"), Column("c") > 1]
        )
        before = row_condition.dict()

        find_column_comparisons(row_condition)

        assert row_condition.dict() == before
