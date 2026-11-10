"""Tests for condition validators on row_condition in Expectations."""

import json
from datetime import datetime, timezone
from operator import eq, ge, gt, le, lt, ne
from typing import Callable, Dict, List

import pytest

from great_expectations.compatibility.pydantic import ValidationError
from great_expectations.core.expectation_suite import ExpectationSuite, ExpectationSuiteSchema
from great_expectations.expectations.core import (
    ExpectColumnValuesToBeInSet,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToEqual,
)
from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
from great_expectations.expectations.row_conditions import (
    AndCondition,
    Column,
    ColumnComparisonCondition,
    ComparisonCondition,
    Condition,
    NullityCondition,
    Operator,
    OrCondition,
    RowConditionType,
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


def _column_comparison(index: int = 0) -> ColumnComparisonCondition:
    condition = Column(f"end_{index}") > Column(f"start_{index}")
    assert isinstance(condition, ColumnComparisonCondition)
    return condition


def _literal_comparison(index: int = 0) -> ComparisonCondition:
    condition = Column(f"end_{index}") > 1
    assert isinstance(condition, ComparisonCondition)
    return condition


def _expectation_with(row_condition: RowConditionType) -> ExpectColumnValuesToBeInSet:
    return ExpectColumnValuesToBeInSet(
        column="test_column", value_set=["a", "b"], row_condition=row_condition
    )


def _rejection_error_types(row_condition: RowConditionType) -> List[str]:
    """The pydantic error types an Expectation raises for the row condition.

    The type names the exception class the validator raised, so equal types mean the same error.
    """
    with pytest.raises(ValidationError) as exc_info:
        _expectation_with(row_condition)
    return [error["type"] for error in exc_info.value.errors()]


def _shape_of(row_condition: object) -> object:
    """The group structure of a row condition with every leaf condition reduced to ``"leaf"``."""
    if isinstance(row_condition, (AndCondition, OrCondition)):
        return (row_condition.type, [_shape_of(child) for child in row_condition.conditions])
    return "leaf"


def _leaf_types(group: Condition) -> list[type]:
    assert isinstance(group, (AndCondition, OrCondition))
    return [type(condition) for condition in group.conditions]


class TestExpectationAcceptsColumnComparison:
    """An Expectation accepts a column comparison wherever it accepts a literal comparison."""

    @pytest.mark.parametrize(
        "operator_func",
        [
            pytest.param(eq, id="eq"),
            pytest.param(ne, id="ne"),
            pytest.param(lt, id="lt"),
            pytest.param(le, id="le"),
            pytest.param(gt, id="gt"),
            pytest.param(ge, id="ge"),
        ],
    )
    def test_a_standalone_column_comparison_is_accepted(self, operator_func):
        row_condition = operator_func(Column("end_date"), Column("start_date"))

        expectation = _expectation_with(row_condition)

        assert type(expectation.row_condition) is ColumnComparisonCondition
        assert expectation.row_condition.dict() == row_condition.dict()

    def test_a_standalone_column_comparison_is_accepted_by_a_table_expectation(self):
        row_condition = _column_comparison()

        expectation = ExpectTableRowCountToEqual(value=10, row_condition=row_condition)

        assert type(expectation.row_condition) is ColumnComparisonCondition
        assert expectation.row_condition.dict() == row_condition.dict()

    def test_a_standalone_column_comparison_is_accepted_by_a_non_null_expectation(self):
        row_condition = _column_comparison()

        expectation = ExpectColumnValuesToNotBeNull(column="x", row_condition=row_condition)

        assert type(expectation.row_condition) is ColumnComparisonCondition
        assert expectation.row_condition.dict() == row_condition.dict()

    def test_a_column_comparison_joined_with_a_literal_by_and_is_accepted(self):
        row_condition = _column_comparison() & (Column("status") == "shipped")

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, AndCondition)
        assert _leaf_types(expectation.row_condition) == [
            ColumnComparisonCondition,
            ComparisonCondition,
        ]

    def test_a_column_comparison_on_the_right_of_and_is_accepted(self):
        row_condition = (Column("status") == "shipped") & _column_comparison()

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, AndCondition)
        assert _leaf_types(expectation.row_condition) == [
            ComparisonCondition,
            ColumnComparisonCondition,
        ]

    def test_two_column_comparisons_joined_by_and_are_accepted(self):
        row_condition = _column_comparison(0) & _column_comparison(1)

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, AndCondition)
        assert _leaf_types(expectation.row_condition) == [ColumnComparisonCondition] * 2

    def test_nested_ands_holding_column_comparisons_are_flattened_in_order(self):
        row_condition = (_column_comparison(0) & _literal_comparison(1)) & (
            _column_comparison(2) & Column("x").is_not_null()
        )

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, AndCondition)
        assert _leaf_types(expectation.row_condition) == [
            ColumnComparisonCondition,
            ComparisonCondition,
            ColumnComparisonCondition,
            NullityCondition,
        ]
        assert [repr(c) for c in expectation.row_condition.conditions] == [
            "end_0 > start_0",
            "end_1 > 1",
            "end_2 > start_2",
            "x IS NOT NULL",
        ]

    def test_a_column_comparison_joined_with_a_literal_by_or_is_accepted(self):
        row_condition = _column_comparison() | (Column("status") == "shipped")

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, OrCondition)
        assert _leaf_types(expectation.row_condition) == [
            ColumnComparisonCondition,
            ComparisonCondition,
        ]

    def test_a_column_comparison_on_the_right_of_or_is_accepted(self):
        row_condition = (Column("status") == "shipped") | _column_comparison()

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, OrCondition)
        assert _leaf_types(expectation.row_condition) == [
            ComparisonCondition,
            ColumnComparisonCondition,
        ]

    def test_a_column_comparison_with_both_null_checks_in_an_or_is_accepted(self):
        row_condition = OrCondition(
            conditions=[
                _column_comparison(),
                Column("start_0").is_null(),
                Column("end_0").is_null(),
            ]
        )

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, OrCondition)
        assert _leaf_types(expectation.row_condition) == [
            ColumnComparisonCondition,
            NullityCondition,
            NullityCondition,
        ]

    def test_column_comparisons_inside_the_and_groups_of_an_or_are_accepted(self):
        row_condition = (_column_comparison(0) & _literal_comparison(1)) | (
            _literal_comparison(2) & _column_comparison(3)
        )

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, OrCondition)
        assert [_leaf_types(group) for group in expectation.row_condition.conditions] == [
            [ColumnComparisonCondition, ComparisonCondition],
            [ComparisonCondition, ColumnComparisonCondition],
        ]

    def test_a_column_comparison_is_accepted_wherever_the_literal_one_is(self):
        # Each shape is built once with literal leaves and once with column-comparison leaves.
        shapes = [
            lambda leaf: leaf(0),
            lambda leaf: leaf(0) & leaf(1),
            lambda leaf: leaf(0) | leaf(1),
            lambda leaf: AndCondition(conditions=[leaf(i) for i in range(5)]),
            lambda leaf: OrCondition(conditions=[leaf(i) for i in range(5)]),
            lambda leaf: (leaf(0) & leaf(1)) & (leaf(2) & leaf(3)),
            lambda leaf: (leaf(0) & leaf(1)) | (leaf(2) & leaf(3)),
            lambda leaf: OrCondition(
                conditions=[AndCondition(conditions=[leaf(0), leaf(1)]), leaf(2), leaf(3)]
            ),
        ]

        for shape in shapes:
            with_literals = _expectation_with(shape(_literal_comparison))
            with_column_comparisons = _expectation_with(shape(_column_comparison))

            assert _shape_of(with_column_comparisons.row_condition) == _shape_of(
                with_literals.row_condition
            )


class TestColumnComparisonsAreCountedTowardsTheLimit:
    """Each column comparison counts as one condition toward the 100-condition limit."""

    def test_exactly_100_column_comparisons_in_an_and_are_accepted(self):
        row_condition = AndCondition(conditions=[_column_comparison(i) for i in range(100)])

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, AndCondition)
        assert len(expectation.row_condition.conditions) == 100
        assert set(_leaf_types(expectation.row_condition)) == {ColumnComparisonCondition}

    def test_101_column_comparisons_in_an_and_are_rejected(self):
        row_condition = AndCondition(conditions=[_column_comparison(i) for i in range(101)])

        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            _expectation_with(row_condition)

    def test_exactly_100_column_comparisons_in_an_or_are_accepted(self):
        row_condition = OrCondition(conditions=[_column_comparison(i) for i in range(100)])

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, OrCondition)
        assert len(expectation.row_condition.conditions) == 100

    def test_101_column_comparisons_in_an_or_are_rejected(self):
        row_condition = OrCondition(conditions=[_column_comparison(i) for i in range(101)])

        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            _expectation_with(row_condition)

    def test_exactly_100_column_comparisons_built_with_and_are_accepted(self):
        row_condition: RowConditionType = _column_comparison(0)
        for i in range(1, 100):
            row_condition = row_condition & _column_comparison(i)

        expectation = _expectation_with(row_condition)

        assert isinstance(expectation.row_condition, AndCondition)
        assert len(expectation.row_condition.conditions) == 100

    def test_101_column_comparisons_built_with_and_are_rejected(self):
        row_condition: RowConditionType = _column_comparison(0)
        for i in range(1, 101):
            row_condition = row_condition & _column_comparison(i)

        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            _expectation_with(row_condition)

    def test_column_comparisons_and_literals_count_together(self):
        accepted = AndCondition(
            conditions=[_column_comparison(i) for i in range(50)]
            + [_literal_comparison(i) for i in range(50)]
        )
        rejected = AndCondition(
            conditions=[_column_comparison(i) for i in range(50)]
            + [_literal_comparison(i) for i in range(51)]
        )

        assert isinstance(_expectation_with(accepted).row_condition, AndCondition)
        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            _expectation_with(rejected)

    def test_nested_and_groups_of_column_comparisons_count_towards_the_limit(self):
        first_group = AndCondition(conditions=[_column_comparison(i) for i in range(50)])
        second_group = AndCondition(conditions=[_column_comparison(i) for i in range(50, 101)])

        with pytest.raises(
            ValueError, match="100 conditions is the maximum, but 101 conditions are defined"
        ):
            _expectation_with(first_group | second_group)

    def test_the_too_many_conditions_error_is_the_one_a_literal_gets(self):
        column_comparisons = AndCondition(conditions=[_column_comparison(i) for i in range(101)])
        literals = AndCondition(conditions=[_literal_comparison(i) for i in range(101)])

        assert _rejection_error_types(column_comparisons) == _rejection_error_types(literals)
        assert _rejection_error_types(column_comparisons) == ["value_error.toomanyconditions"]


class TestColumnComparisonsFollowTheGroupConstraints:
    """A column comparison breaks a group constraint exactly where a literal comparison does."""

    def test_an_or_inside_an_and_is_rejected(self):
        row_condition = _column_comparison(0) & (_column_comparison(1) | _column_comparison(2))

        with pytest.raises(ValueError, match="AND groups cannot contain OR conditions"):
            _expectation_with(row_condition)

    def test_an_or_inside_an_and_is_rejected_with_the_error_a_literal_gets(self):
        column_comparisons = _column_comparison(0) & (_column_comparison(1) | _column_comparison(2))
        literals = _literal_comparison(0) & (_literal_comparison(1) | _literal_comparison(2))

        assert _rejection_error_types(column_comparisons) == _rejection_error_types(literals)
        assert _rejection_error_types(column_comparisons) == ["value_error.andcontainsor"]

    def test_an_or_of_one_column_comparison_and_a_literal_inside_an_and_is_rejected(self):
        row_condition = _literal_comparison(0) & (_column_comparison(1) | _literal_comparison(2))

        assert _rejection_error_types(row_condition) == ["value_error.andcontainsor"]

    def test_a_nested_or_is_rejected(self):
        row_condition = _column_comparison(0) | (_column_comparison(1) | _column_comparison(2))

        with pytest.raises(ValueError, match="OR groups cannot contain nested OR conditions"):
            _expectation_with(row_condition)

    def test_a_nested_or_is_rejected_with_the_error_a_literal_gets(self):
        column_comparisons = _column_comparison(0) | (_column_comparison(1) | _column_comparison(2))
        literals = _literal_comparison(0) | (_literal_comparison(1) | _literal_comparison(2))

        assert _rejection_error_types(column_comparisons) == _rejection_error_types(literals)
        assert _rejection_error_types(column_comparisons) == ["value_error.nestedor"]

    def test_an_or_inside_an_and_inside_an_or_is_rejected_with_the_error_a_literal_gets(self):
        def build(leaf):
            return OrCondition(
                conditions=[
                    leaf(0),
                    AndCondition(conditions=[leaf(1), OrCondition(conditions=[leaf(2), leaf(3)])]),
                ]
            )

        assert _rejection_error_types(build(_column_comparison)) == _rejection_error_types(
            build(_literal_comparison)
        )
        assert _rejection_error_types(build(_column_comparison)) == ["value_error.nestedor"]

    def test_a_group_that_breaks_a_constraint_is_rejected_by_a_table_expectation_too(self):
        row_condition = _column_comparison(0) & (_column_comparison(1) | _column_comparison(2))

        with pytest.raises(ValueError, match="AND groups cannot contain OR conditions"):
            ExpectTableRowCountToEqual(value=10, row_condition=row_condition)


class TestColumnComparisonSurvivesSavingAnExpectation:
    """A column comparison in an Expectation's configuration and suite JSON reloads unchanged."""

    ROW_CONDITIONS: Dict[str, Callable[[], RowConditionType]] = {
        "standalone": lambda: _column_comparison(0),
        "in an AND": lambda: _column_comparison(0) & _literal_comparison(1),
        "in an OR": lambda: OrCondition(
            conditions=[
                _column_comparison(0),
                Column("start_0").is_null(),
                Column("end_0").is_null(),
            ]
        ),
        "in the groups of an OR": lambda: (
            (_column_comparison(0) & _literal_comparison(1)) | _column_comparison(2)
        ),
    }

    @pytest.fixture(params=list(ROW_CONDITIONS))
    def expectation(self, request) -> ExpectColumnValuesToNotBeNull:
        return ExpectColumnValuesToNotBeNull(
            column="x", row_condition=self.ROW_CONDITIONS[request.param]()
        )

    def test_the_saved_configuration_tags_the_column_comparison(self, expectation):
        saved = json.loads(json.dumps(expectation.configuration.to_json_dict()))

        saved_row_condition = saved["kwargs"]["row_condition"]
        leaves = (
            saved_row_condition["conditions"]
            if saved_row_condition["type"] in ("and", "or")
            else [saved_row_condition]
        )
        column_comparisons = [leaf for leaf in leaves if leaf["type"] == "column_comparison"]
        assert column_comparisons
        for saved_leaf in column_comparisons:
            assert set(saved_leaf) == {"type", "column", "operator", "other_column"}

    def test_the_configuration_reloads_with_the_same_column_comparison(self, expectation):
        saved = json.loads(json.dumps(expectation.configuration.to_json_dict()))

        reloaded = ExpectationConfiguration(**saved).to_domain_obj()

        assert type(reloaded.row_condition) is type(expectation.row_condition)
        assert reloaded.row_condition.dict() == expectation.row_condition.dict()

    def test_the_suite_json_reloads_with_the_same_column_comparison(self, expectation):
        suite = ExpectationSuite(name="suite", expectations=[expectation])

        saved = json.loads(ExpectationSuiteSchema().dumps(suite, indent=2, sort_keys=True))
        reloaded_suite = ExpectationSuite(**saved)

        (reloaded,) = reloaded_suite.expectations
        assert type(reloaded.row_condition) is type(expectation.row_condition)
        assert reloaded.row_condition.dict() == expectation.row_condition.dict()

    def test_the_suite_to_json_dict_reloads_with_the_same_column_comparison(self, expectation):
        suite = ExpectationSuite(name="suite", expectations=[expectation])

        saved = json.loads(json.dumps(suite.to_json_dict()))
        reloaded_suite = ExpectationSuite(**saved)

        (reloaded,) = reloaded_suite.expectations
        assert type(reloaded.row_condition) is type(expectation.row_condition)
        assert reloaded.row_condition.dict() == expectation.row_condition.dict()
