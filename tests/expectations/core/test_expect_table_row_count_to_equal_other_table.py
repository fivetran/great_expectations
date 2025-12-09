import sqlite3
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pytest

import great_expectations.expectations as gxe
from great_expectations.util import build_in_memory_runtime_context

if TYPE_CHECKING:
    from great_expectations.core.expectation_validation_result import (
        ExpectationValidationResult,
    )


@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database with two tables for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create first table with 10 rows
        cursor.execute("""
            CREATE TABLE main_table (
                name TEXT,
                age INTEGER
            )
        """)

        main_data = [
            ("José", 25),
            ("Bob", 30),
            ("Charlie", 15),
            ("David", 35),
            ("Eve", 22),
            ("Frank", 16),
            ("Grace", 28),
            ("Hannah", 17),
            ("Ian", 40),
            ("Jane", 12),
        ]
        cursor.executemany("INSERT INTO main_table VALUES (?, ?)", main_data)

        # Create second table with 10 rows (same count)
        cursor.execute("""
            CREATE TABLE other_table (
                name TEXT,
                age INTEGER
            )
        """)
        cursor.executemany("INSERT INTO other_table VALUES (?, ?)", main_data)

        # Create third table with 6 rows (different count)
        cursor.execute("""
            CREATE TABLE smaller_table (
                name TEXT,
                age INTEGER
            )
        """)
        smaller_data = [row for row in main_data if row[1] >= 18]  # Only adults
        cursor.executemany("INSERT INTO smaller_table VALUES (?, ?)", smaller_data)

        conn.commit()
        conn.close()

        yield str(db_path)


@pytest.mark.sqlite
@pytest.mark.parametrize(
    "other_table,row_condition,success,expected_self_count,expected_other_count",
    [
        # Without row_condition - comparing main_table (10 rows) to other_table (10 rows)
        ("other_table", None, True, 10, 10),
        # Without row_condition - comparing main_table (10 rows) to smaller_table (6 rows)
        ("smaller_table", None, False, 10, 6),
        # With row_condition on main_table filtering age >= 18 (6 rows) to other_table (10 rows)
        ("other_table", 'col("age") >= 18', False, 6, 10),
        # With row_condition on main_table filtering age >= 18 (6 rows) to smaller_table (6 rows)
        ("smaller_table", 'col("age") >= 18', True, 6, 6),
        # With row_condition on main_table filtering age < 18 (4 rows) to smaller_table (6 rows)
        ("smaller_table", 'col("age") < 18', False, 4, 6),
        # With row_condition filtering name == "José" (1 row) to smaller_table (6 rows)
        ("smaller_table", 'col("name") == "José"', False, 1, 6),
    ],
)
def test_expect_table_row_count_to_equal_other_table(
    temp_sqlite_db: str,
    other_table: str,
    row_condition: Optional[str],
    success: bool,
    expected_self_count: int,
    expected_other_count: int,
):
    """Test multi-table row count comparison with and without row_condition.

    The row_condition should be applied only to the main table (self) before counting,
    while the other table should be counted without any filtering.
    """
    context = build_in_memory_runtime_context()

    # Create SQLite datasource
    datasource = context.data_sources.add_sqlite(
        name="test_sqlite",
        connection_string=f"sqlite:///{temp_sqlite_db}",
    )

    # Add table asset for main_table
    asset = datasource.add_table_asset(name="main_table", table_name="main_table")
    batch_definition = asset.add_batch_definition(name="test_batch")
    batch = batch_definition.get_batch()

    expectation = gxe.ExpectTableRowCountToEqualOtherTable(
        other_table_name=other_table,
        row_condition=row_condition,
        condition_parser="great_expectations",
    )

    result: ExpectationValidationResult = batch.validate(expectation)

    assert result.success is success
    assert result.result["observed_value"]["self"] == expected_self_count
    assert result.result["observed_value"]["other"] == expected_other_count
