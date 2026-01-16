import datetime
import decimal
import platform
import sys

import numpy as np
import pytest
from numpy.lib.npyio import DataSource

from great_expectations import validator
from great_expectations.expectations.row_conditions import (
    AndCondition,
    Column,
    ComparisonCondition,
    NullityCondition,
    OrCondition,
)


@pytest.mark.big
def test_recursively_convert_to_json_serializable(tmp_path):
    x = {
        "w": ["aaaa", "bbbb", 1.3, 5, 6, 7],
        "x": np.array([1, 2, 3]),
        "y": {"alpha": None, "beta": np.nan, "delta": np.inf, "gamma": -np.inf},
        "z": {1, 2, 3, 4, 5},
        "zz": (1, 2, 3),
        "zzz": [
            datetime.datetime(2017, 1, 1),  # noqa: DTZ001 # FIXME CoP
            datetime.date(2017, 5, 1),
        ],
        "np.bool": np.bool_([True, False, True]),
        "np.int_": np.int_([5, 3, 2]),
        "np.int8": np.int8([5, 3, 2]),
        "np.int16": np.int16([10, 6, 4]),
        "np.int32": np.int32([20, 12, 8]),
        "np.uint": np.uint([20, 5, 6]),
        "np.uint8": np.uint8([40, 10, 12]),
        "np.uint64": np.uint64([80, 20, 24]),
        "np.float_": np.float64([3.2, 5.6, 7.8]),
        "np.float32": np.float32([5.999999999, 5.6]),
        "np.float64": np.float64([5.9999999999999999999, 10.2]),
        # 'np.complex64': np.complex64([10.9999999 + 4.9999999j, 11.2+7.3j]),
        # 'np.complex128': np.complex128([20.999999999978335216827+10.99999999j, 22.4+14.6j]),
        # 'np.complex256': np.complex256([40.99999999 + 20.99999999j, 44.8+29.2j]),
        "np.str": np.str_(["hello"]),
        "yyy": decimal.Decimal("123.456"),
    }
    if hasattr(np, "float128") and platform.system() != "Windows":
        x["np.float128"] = np.float128([5.999999999998786324399999999, 20.4])

    x = validator.util.recursively_convert_to_json_serializable(x)
    assert isinstance(x["x"], list)

    assert isinstance(x["np.bool"][0], bool)
    assert isinstance(x["np.int_"][0], int)
    assert isinstance(x["np.int8"][0], int)
    assert isinstance(x["np.int16"][0], int)
    assert isinstance(x["np.int32"][0], int)

    assert isinstance(x["np.uint"][0], int)
    assert isinstance(x["np.uint8"][0], int)
    assert isinstance(x["np.uint64"][0], int)

    assert isinstance(x["np.float32"][0], float)
    assert isinstance(x["np.float64"][0], float)
    if hasattr(np, "float128") and platform.system() != "Windows":
        assert isinstance(x["np.float128"][0], float)
    # self.assertEqual(type(x['np.complex64'][0]), complex)
    # self.assertEqual(type(x['np.complex128'][0]), complex)
    # self.assertEqual(type(x['np.complex256'][0]), complex)
    assert isinstance(x["np.float_"][0], float)

    # Make sure nothing is going wrong with precision rounding
    if hasattr(np, "float128") and platform.system() != "Windows":
        assert np.allclose(
            x["np.float128"][0],
            5.999999999998786324399999999,
            atol=10 ** (-sys.float_info.dig),
        )

    # TypeError when non-serializable numpy object is in dataset.
    with pytest.raises(TypeError):
        y = {"p": DataSource(tmp_path)}
        validator.util.recursively_convert_to_json_serializable(y)


@pytest.mark.unit
def test_recursively_convert_to_json_serializable_with_nullity_condition():
    """Test that NullityCondition objects can be serialized."""
    condition = Column("COLUMN1").is_not_null()
    assert isinstance(condition, NullityCondition)

    result = validator.util.recursively_convert_to_json_serializable({"row_condition": condition})

    assert result == {
        "row_condition": {
            "type": "nullity",
            "column": {"name": "COLUMN1"},
            "is_null": False,
        }
    }


@pytest.mark.unit
def test_recursively_convert_to_json_serializable_with_is_null_condition():
    """Test that NullityCondition with is_null=True can be serialized."""
    condition = Column("col").is_null()
    assert isinstance(condition, NullityCondition)

    result = validator.util.recursively_convert_to_json_serializable({"row_condition": condition})

    assert result == {
        "row_condition": {
            "type": "nullity",
            "column": {"name": "col"},
            "is_null": True,
        }
    }


@pytest.mark.unit
def test_recursively_convert_to_json_serializable_with_comparison_condition():
    """Test that ComparisonCondition objects can be serialized."""
    condition = Column("tenure") > 2
    assert isinstance(condition, ComparisonCondition)

    result = validator.util.recursively_convert_to_json_serializable({"row_condition": condition})

    assert result == {
        "row_condition": {
            "type": "comparison",
            "column": {"name": "tenure"},
            "operator": ">",
            "parameter": 2,
        }
    }


@pytest.mark.unit
def test_recursively_convert_to_json_serializable_with_and_condition():
    """Test that AndCondition objects can be serialized."""
    condition = (Column("tenure") > 2) & (Column("salary") <= 50000)
    assert isinstance(condition, AndCondition)

    result = validator.util.recursively_convert_to_json_serializable({"row_condition": condition})

    assert result == {
        "row_condition": {
            "type": "and",
            "conditions": [
                {
                    "type": "comparison",
                    "column": {"name": "tenure"},
                    "operator": ">",
                    "parameter": 2,
                },
                {
                    "type": "comparison",
                    "column": {"name": "salary"},
                    "operator": "<=",
                    "parameter": 50000,
                },
            ],
        }
    }


@pytest.mark.unit
def test_recursively_convert_to_json_serializable_with_or_condition():
    """Test that OrCondition objects can be serialized."""
    condition = (Column("name") == "alice") | (Column("name") == "bob")
    assert isinstance(condition, OrCondition)

    result = validator.util.recursively_convert_to_json_serializable({"row_condition": condition})

    assert result == {
        "row_condition": {
            "type": "or",
            "conditions": [
                {
                    "type": "comparison",
                    "column": {"name": "name"},
                    "operator": "==",
                    "parameter": "alice",
                },
                {
                    "type": "comparison",
                    "column": {"name": "name"},
                    "operator": "==",
                    "parameter": "bob",
                },
            ],
        }
    }


@pytest.mark.unit
def test_recursively_convert_to_json_serializable_with_complex_condition():
    """Test serialization of complex condition: (A & B) | C."""
    statement_1 = Column("tenure") > 2
    statement_2 = Column("salary") <= 50000
    statement_3 = Column("department") == "Sales"

    block_1 = statement_1 & statement_2
    row_condition = block_1 | statement_3

    result = validator.util.recursively_convert_to_json_serializable(
        {"row_condition": row_condition}
    )

    assert result["row_condition"]["type"] == "or"
    assert len(result["row_condition"]["conditions"]) == 2


@pytest.mark.unit
def test_ensure_row_condition_is_correct_with_condition_object():
    """Test that ensure_row_condition_is_correct does not raise for Condition objects."""
    condition = Column("COLUMN1").is_not_null()

    # Should not raise
    validator.util.ensure_row_condition_is_correct(condition)


@pytest.mark.unit
def test_ensure_row_condition_is_correct_with_string():
    """Test that ensure_row_condition_is_correct still validates strings."""
    from great_expectations.exceptions import InvalidExpectationConfigurationError

    # Valid string should not raise
    validator.util.ensure_row_condition_is_correct('col("x") > 5')

    # String with single quotes should raise
    with pytest.raises(InvalidExpectationConfigurationError):
        validator.util.ensure_row_condition_is_correct("col('x') > 5")

    # String with newline should raise
    with pytest.raises(InvalidExpectationConfigurationError):
        validator.util.ensure_row_condition_is_correct('col("x")\n> 5')
