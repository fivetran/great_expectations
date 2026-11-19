"""How column-to-column row conditions treat NaN, pinned on pandas, Spark and PostgreSQL.

GX does not give NaN a meaning of its own in a column comparison. Each backend applies its own
rules, the same ones it applies when a NaN column is compared with a literal, so a user can reason
about NaN in a row condition the way they would for any other query on that backend:

* Spark and PostgreSQL store NaN as a value, distinct from null. They treat it as equal to itself
  and greater than every number, so a pair with a NaN in it can satisfy a comparison.
* pandas treats NaN as missing, so a pair with a NaN in either column satisfies no comparison,
  whatever the operator.

The cross-backend module cannot pin this. The shared fixtures load NaN as null on Spark and on SQL
backends, which erases exactly the distinction these cases are about. Each backend here is built
without that step instead: Spark from a DataFrame with an explicit double schema, PostgreSQL from a
table filled through bound ``float("nan")`` parameters, and pandas from a plain DataFrame. Spark and
PostgreSQL first check that the stored value really is NaN and not null, because a table holding
nulls would pin the wrong behavior with every case still passing.

The expected outcome of every operator is written out in full for each kind of pair, so a change to
any one outcome on any backend fails the one case that names it. Each case also checks the ordinary
rows, whose outcome follows from the operator alone. That keeps a filter that selects everything, or
nothing, from satisfying a case.

Column names here avoid the substrings ``AND``, ``OR`` and ``NOT`` (in any case): the atomic
row-condition renderer splits on them even inside a name, which is unrelated to what this module
verifies.
"""

from __future__ import annotations

import math
import operator
from typing import TYPE_CHECKING, Any, Callable, Iterator, Sequence
from uuid import uuid4

import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.compatibility.sqlalchemy import (
    Column as SqlColumn,
)
from great_expectations.compatibility.sqlalchemy import (
    MetaData,
    Table,
    TextClause,
    create_engine,
    insert,
    sqltypes,
)
from great_expectations.expectations.row_conditions import Column
from tests.integration.test_utils.data_source_config.postgres import PostgresBatchTestSetup

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    from great_expectations.datasource.fluent.interfaces import Batch

ID_COLUMN = "id"
LEFT_COLUMN = "left_value"
RIGHT_COLUMN = "right_value"

NAN = float("nan")

# The three ways a NaN can appear in a pair of columns, then three ordinary rows. Among the
# ordinary rows one has left < right, one left == right and one left > right, so every operator
# selects a different non-empty proper subset of them. The values are exactly representable in
# binary, so equality is not at the mercy of rounding on any backend.
ROWS: list[tuple[int, float, float]] = [
    (1, NAN, 2.0),
    (2, NAN, NAN),
    (3, 2.0, NAN),
    (4, 1.0, 2.0),
    (5, 2.0, 2.0),
    (6, 3.0, 2.0),
]
NAN_ROW_IDS = {"nan_vs_number": 1, "nan_vs_nan": 2, "number_vs_nan": 3}
ORDINARY_ROW_IDS = (4, 5, 6)
# No row has this id, so the ids that fail to be in the set are exactly the rows that survive the
# row condition.
ABSENT_ID = -1

Comparison = Callable[[Any, Any], Any]
"""A binary comparison. The same function builds the condition (applied to two ``Column`` objects,
which overload the operators) and the oracle for the ordinary rows (applied to two plain numbers),
so a case names an operator once and cannot test one while its oracle checks another."""

OPERATORS: dict[str, Comparison] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "le": operator.le,
    "gt": operator.gt,
    "ge": operator.ge,
}

# For each kind of pair, the operators under which the row is kept; under every other operator it
# is dropped. These are pinned values, not derived ones: they are what Spark and PostgreSQL do
# today, and the module exists so that a change to any of them is a failure rather than a silent
# shift in results. They happen to be what "NaN equals itself and sorts above every number" gives.
KEPT_BY_VALUE_SEMANTICS: dict[str, frozenset[str]] = {
    "nan_vs_number": frozenset({"gt", "ge", "ne"}),
    "nan_vs_nan": frozenset({"eq", "le", "ge"}),
    "number_vs_nan": frozenset({"lt", "le", "ne"}),
}

# pandas treats NaN as missing, so no operator keeps a row with a NaN in either column.
KEPT_BY_MISSING_SEMANTICS: dict[str, frozenset[str]] = {
    "nan_vs_number": frozenset(),
    "nan_vs_nan": frozenset(),
    "number_vs_nan": frozenset(),
}


def _cases(kept_by: dict[str, frozenset[str]]) -> list[ParameterSet]:
    """One named case per kind of NaN pair and operator, e.g. ``nan_vs_number-gt-kept``."""
    return [
        pytest.param(
            pair,
            operator_name,
            operator_name in kept_operators,
            id=f"{pair}-{operator_name}-{'kept' if operator_name in kept_operators else 'dropped'}",
        )
        for pair, kept_operators in kept_by.items()
        for operator_name in OPERATORS
    ]


MISSING_CASES = _cases(KEPT_BY_MISSING_SEMANTICS)
VALUE_CASES = _cases(KEPT_BY_VALUE_SEMANTICS)
CASE_PARAMETERS = ("pair", "operator_name", "kept")


def _ids_holding_nan(rows: Sequence[tuple[int, float, float]], column_index: int) -> list[int]:
    return [row[0] for row in rows if math.isnan(row[column_index])]


@pytest.fixture
def pandas_nan_batch() -> Batch:
    frame = pd.DataFrame(ROWS, columns=[ID_COLUMN, LEFT_COLUMN, RIGHT_COLUMN])
    datasource = gx.get_context(mode="ephemeral").data_sources.add_pandas(name="pandas")
    return (
        datasource.add_dataframe_asset(name="nan_frame")
        .add_batch_definition_whole_dataframe("nan_frame_definition")
        .get_batch(batch_parameters={"dataframe": frame})
    )


@pytest.fixture
def spark_nan_batch(spark_session: Any) -> Batch:
    from great_expectations.compatibility.pyspark import types as pyspark_types

    schema = pyspark_types.StructType(
        [
            pyspark_types.StructField(ID_COLUMN, pyspark_types.IntegerType(), False),
            pyspark_types.StructField(LEFT_COLUMN, pyspark_types.DoubleType(), True),
            pyspark_types.StructField(RIGHT_COLUMN, pyspark_types.DoubleType(), True),
        ]
    )
    dataframe = spark_session.createDataFrame(ROWS, schema)

    stored = [(row[ID_COLUMN], row[LEFT_COLUMN], row[RIGHT_COLUMN]) for row in dataframe.collect()]
    assert all(value is not None for _, left, right in stored for value in (left, right)), (
        "the DataFrame holds nulls where NaN was given, so no case here would be about NaN"
    )
    for column_index, column in ((1, LEFT_COLUMN), (2, RIGHT_COLUMN)):
        assert sorted(_ids_holding_nan(stored, column_index)) == sorted(
            _ids_holding_nan(ROWS, column_index)
        ), f"Spark does not store NaN in {column}"

    datasource = gx.get_context(mode="ephemeral").data_sources.add_spark(name="spark")
    return (
        datasource.add_dataframe_asset(name="nan_frame")
        .add_batch_definition_whole_dataframe("nan_frame_definition")
        .get_batch(batch_parameters={"dataframe": dataframe})
    )


@pytest.fixture(scope="module")
def postgresql_nan_batch() -> Iterator[Batch]:
    table_name = f"column_comparison_nan_{uuid4().hex[:10]}"
    connection_string = PostgresBatchTestSetup._BASE_CONNECTION_STRING
    engine = create_engine(url=connection_string)
    metadata = MetaData()
    table = Table(
        table_name,
        metadata,
        SqlColumn(ID_COLUMN, sqltypes.Integer, primary_key=True),
        # FLOAT(53) is PostgreSQL's double precision, which is what holds a NaN.
        SqlColumn(LEFT_COLUMN, sqltypes.Float(53)),
        SqlColumn(RIGHT_COLUMN, sqltypes.Float(53)),
    )
    datasource = None
    try:
        with engine.begin() as connection:
            metadata.create_all(connection)
            connection.execute(
                insert(table),
                [
                    {ID_COLUMN: row_id, LEFT_COLUMN: left, RIGHT_COLUMN: right}
                    for row_id, left, right in ROWS
                ],
            )

        # Compare as text, so that this check does not itself rest on a comparison rule under test.
        with engine.connect() as connection:
            for column_index, column in ((1, LEFT_COLUMN), (2, RIGHT_COLUMN)):
                stored_nan = [
                    row[0]
                    for row in connection.execute(
                        TextClause(
                            f"SELECT {ID_COLUMN} FROM {table_name} "
                            f"WHERE {column}::text = 'NaN' ORDER BY {ID_COLUMN}"
                        )
                    )
                ]
                assert stored_nan == sorted(_ids_holding_nan(ROWS, column_index)), (
                    f"PostgreSQL does not store NaN in {column}"
                )
                stored_null = connection.execute(
                    TextClause(f"SELECT count(*) FROM {table_name} WHERE {column} IS NULL")
                ).scalar()
                assert stored_null == 0, f"{column} holds nulls where NaN was given"

        datasource = gx.get_context(mode="ephemeral").data_sources.add_postgres(
            name="postgresql", connection_string=connection_string
        )
        yield (
            datasource.add_table_asset(name="nan_table", table_name=table_name)
            .add_batch_definition_whole_table("nan_table_definition")
            .get_batch()
        )
    finally:
        if datasource is not None:
            datasource.get_engine().dispose()
        with engine.begin() as connection:
            table.drop(connection, checkfirst=True)
        engine.dispose()


def surviving_ids(batch: Batch, row_condition: Any) -> list[int]:
    """The ids of the rows that remain once ``row_condition`` filters the batch.

    ``ExpectColumnValuesToBeInSet`` is given a set that holds no id, so every row that survives
    the filter is unexpected and is listed in full. Asserting ``success`` on an aggregate alone
    cannot tell "filtered correctly" from "filtered nothing".
    """
    result = batch.validate(
        gxe.ExpectColumnValuesToBeInSet(
            column=ID_COLUMN,
            value_set=[ABSENT_ID],
            row_condition=row_condition,
        ),
        result_format="COMPLETE",
    )
    assert result.result, result.exception_info
    return sorted(int(row_id) for row_id in result.result["unexpected_list"])


def assert_nan_row_outcome(batch: Batch, pair: str, operator_name: str, kept: bool) -> None:
    compare = OPERATORS[operator_name]

    surviving = surviving_ids(batch, compare(Column(LEFT_COLUMN), Column(RIGHT_COLUMN)))

    # The ordinary rows come first: if the filter is wrong for plain numbers, the NaN outcome below
    # says nothing, and this is the failure that should be read.
    ordinary_values = {row_id: (left, right) for row_id, left, right in ROWS}
    expected_ordinary = [row_id for row_id in ORDINARY_ROW_IDS if compare(*ordinary_values[row_id])]
    assert expected_ordinary, "the operator must select some ordinary row"
    assert set(expected_ordinary) < set(ORDINARY_ROW_IDS), (
        "the operator must not select every ordinary row"
    )
    assert [row_id for row_id in surviving if row_id in ORDINARY_ROW_IDS] == expected_ordinary, (
        f"ordinary rows filtered wrongly under {operator_name}: surviving={surviving}"
    )

    nan_row_id = NAN_ROW_IDS[pair]
    assert (nan_row_id in surviving) is kept, (
        f"row {nan_row_id} ({pair}) should be {'kept' if kept else 'dropped'} under "
        f"{operator_name}, but surviving={surviving}"
    )


@pytest.mark.unit
@pytest.mark.parametrize(CASE_PARAMETERS, MISSING_CASES)
def test_pandas_nan_row_outcome(
    pandas_nan_batch: Batch, pair: str, operator_name: str, kept: bool
) -> None:
    assert_nan_row_outcome(pandas_nan_batch, pair, operator_name, kept)


@pytest.mark.spark
@pytest.mark.parametrize(CASE_PARAMETERS, VALUE_CASES)
def test_spark_nan_row_outcome(
    spark_nan_batch: Batch, pair: str, operator_name: str, kept: bool
) -> None:
    assert_nan_row_outcome(spark_nan_batch, pair, operator_name, kept)


@pytest.mark.postgresql
@pytest.mark.parametrize(CASE_PARAMETERS, VALUE_CASES)
def test_postgresql_nan_row_outcome(
    postgresql_nan_batch: Batch, pair: str, operator_name: str, kept: bool
) -> None:
    assert_nan_row_outcome(postgresql_nan_batch, pair, operator_name, kept)
