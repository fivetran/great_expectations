from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict

import pytest

from great_expectations.data_context.util import file_relative_path
from great_expectations.exceptions import InvalidQueryError, MissingKeysError
from great_expectations.expectations import UnexpectedRowsExpectation
from great_expectations.expectations.metrics.util import MAX_RESULT_RECORDS
from great_expectations.render.renderer.content_block.content_block import ContentBlockRenderer

if TYPE_CHECKING:
    from great_expectations.data_context import AbstractDataContext
    from great_expectations.datasource.fluent.interfaces import Batch
    from great_expectations.datasource.fluent.sqlite_datasource import SqliteDatasource


@pytest.fixture
def taxi_db_path() -> str:
    return file_relative_path(__file__, "../../test_sets/quickstart/yellow_tripdata.db")


@pytest.fixture
def sqlite_datasource(
    in_memory_runtime_context: AbstractDataContext, taxi_db_path: str
) -> SqliteDatasource:
    context = in_memory_runtime_context
    datasource_name = "my_sqlite_datasource"
    return context.data_sources.add_sqlite(
        datasource_name, connection_string=f"sqlite:///{taxi_db_path}"
    )


@pytest.fixture
def sqlite_batch(sqlite_datasource: SqliteDatasource) -> Batch:
    datasource = sqlite_datasource
    asset = datasource.add_table_asset("yellow_tripdata_sample_2022_01")

    batch_request = asset.build_batch_request()
    return asset.get_batch(batch_request)


@pytest.mark.unit
@pytest.mark.parametrize(
    "query",
    [
        pytest.param("SELECT * FROM table", id="no batch"),
        pytest.param("SELECT * FROM {{ batch }}", id="invalid format"),
        pytest.param("SELECT * FROM {active_batch}", id="legacy syntax"),
    ],
)
def test_unexpected_rows_expectation_invalid_query_info_message(query: str, caplog, capfd):
    # info log is emitted
    with caplog.at_level(logging.INFO):
        UnexpectedRowsExpectation(unexpected_rows_query=query)

    # stdout is printed to console
    out, _ = capfd.readouterr()
    assert "{batch}" in out


@pytest.mark.unit
def test_unexpected_rows_expectation_template_dict_basic():
    """Test basic template_dict functionality"""

    query = "SELECT * FROM {batch} WHERE {column} IS NULL"
    template_dict = {"column": "user_id"}
    expectation = UnexpectedRowsExpectation(
        unexpected_rows_query=query, template_dict=template_dict
    )

    assert expectation.template_dict == template_dict
    assert expectation.unexpected_rows_query == query


@pytest.mark.unit
def test_unexpected_rows_expectation_get_rendered_query():
    """Test that _get_rendered_query properly replaces template variables"""

    query = "SELECT * FROM {batch} WHERE {column_a} IS NOT NULL AND {column_b} IS NULL"
    template_dict = {"column_a": "start_date", "column_b": "end_date"}
    expectation = UnexpectedRowsExpectation(
        unexpected_rows_query=query, template_dict=template_dict
    )
    rendered_query = expectation._get_rendered_query()

    assert (
        rendered_query == "SELECT * FROM {batch} WHERE start_date IS NOT NULL AND end_date IS NULL"
    )
    assert "{column_a}" not in rendered_query
    assert "{column_b}" not in rendered_query


@pytest.mark.unit
def test_unexpected_rows_expectation_missing_template_variable():
    """Test that missing template variables raise appropriate errors"""

    query = "SELECT * FROM {batch} WHERE {column} IS NULL"
    template_dict = {}  # Missing 'column' key
    expectation = UnexpectedRowsExpectation(
        unexpected_rows_query=query, template_dict=template_dict
    )

    with pytest.raises(InvalidQueryError) as exc_info:
        expectation._get_rendered_query()
    assert "Query contains template variable that is not in template_dict" in str(exc_info.value)


@pytest.mark.unit
def test_unexpected_rows_expectation_backward_compatibility():
    """Test that queries without templates still work (backward compatibility)"""

    query = "SELECT * FROM {batch} WHERE status = 'invalid'"
    expectation = UnexpectedRowsExpectation(unexpected_rows_query=query)

    # Should not raise any errors
    expectation.validate_configuration()
    rendered_query = expectation._get_rendered_query()
    assert rendered_query == query


@pytest.mark.unit
class TestUnexpectedRowsExpectationWithRequiredTemplateKeys:
    """Test subclassing with required template keys"""

    def test_required_template_keys_validation(self):
        """Test validation when required_template_keys is defined"""

        class CustomUnexpectedRowsExpectation(UnexpectedRowsExpectation):
            required_template_keys = ("column_a", "column_b")

        # Should fail without template_dict
        with pytest.raises(MissingKeysError) as exc_info:
            CustomUnexpectedRowsExpectation(
                unexpected_rows_query="SELECT * FROM {batch} WHERE {column_a} = {column_b}"
            )

        # Should fail with incomplete template_dict
        with pytest.raises(InvalidQueryError) as exc_info:
            CustomUnexpectedRowsExpectation(
                unexpected_rows_query="SELECT * FROM {batch} WHERE {column_a} = {column_b}",
                template_dict={"column_a": "col1"},  # Missing column_b
            )
        assert "column_b" in str(exc_info.value)

        # Should succeed with complete template_dict
        expectation = CustomUnexpectedRowsExpectation(
            unexpected_rows_query="SELECT * FROM {batch} WHERE {column_a} = {column_b}",
            template_dict={"column_a": "col1", "column_b": "col2"},
        )
        assert expectation.template_dict == {"column_a": "col1", "column_b": "col2"}


@pytest.mark.unit
def test_additional_template_validations():
    """Test custom validation logic through get_additional_template_validations"""

    class CustomValidationExpectation(UnexpectedRowsExpectation):
        required_template_keys = ("column_a", "column_b", "column_c")

        @classmethod
        def get_additional_template_validations(
            cls, template_dict: Dict[str, str]
        ) -> Dict[str, bool]:
            columns = [template_dict.get(key) for key in cls.required_template_keys]
            return {
                "All columns must be different": len(set(columns)) == len(columns),
                "Column names must not be empty": all(col and col.strip() for col in columns),
            }

    # Should fail when columns are not different
    with pytest.raises(MissingKeysError) as exc_info:
        CustomValidationExpectation(
            unexpected_rows_query="SELECT * FROM {batch}",
            template_dict={"column_a": "col1", "column_b": "col1", "column_c": "col3"},
        )
    assert "All columns must be different" in str(exc_info.value)

    # Should fail when column name is empty
    with pytest.raises(MissingKeysError) as exc_info:
        CustomValidationExpectation(
            unexpected_rows_query="SELECT * FROM {batch}",
            template_dict={"column_a": "col1", "column_b": "", "column_c": "col3"},
        )
    assert "Column names must not be empty" in str(exc_info.value)

    # Should succeed with valid template_dict
    expectation = CustomValidationExpectation(
        unexpected_rows_query="SELECT * FROM {batch}",
        template_dict={"column_a": "col1", "column_b": "col2", "column_c": "col3"},
    )
    assert expectation.template_dict["column_a"] == "col1"


@pytest.mark.sqlite
@pytest.mark.parametrize(
    "query, expected_success, expected_observed_value, expected_count_unexpected_rows_returned",
    [
        pytest.param(
            "SELECT * FROM {batch} WHERE passenger_count > 7",
            True,
            0,
            0,
            id="success",
        ),
        pytest.param(
            # There is a single instance where passenger_count == 7
            "SELECT * FROM {batch} WHERE passenger_count > 6",
            False,
            1,
            1,
            id="failure",
        ),
        pytest.param(
            "SELECT * FROM {batch} WHERE passenger_count > 0",
            False,
            97853,
            MAX_RESULT_RECORDS,
            id="greater than MAX_RESULT_RECORDS unexpected rows",
        ),
    ],
)
def test_unexpected_rows_expectation_validate(
    sqlite_batch: Batch,
    query: str,
    expected_success: bool,
    expected_observed_value: int,
    expected_count_unexpected_rows_returned: int,
):
    batch = sqlite_batch

    expectation = UnexpectedRowsExpectation(unexpected_rows_query=query)
    result = batch.validate(expectation)

    assert result.success is expected_success

    res = result.result
    assert res["observed_value"] == expected_observed_value

    unexpected_count_rows_returned = len(res["details"]["unexpected_rows"])
    assert unexpected_count_rows_returned == expected_count_unexpected_rows_returned


@pytest.mark.unit
def test_unexpected_rows_expectation_correctly_interprets_query(
    sqlite_batch: Batch,
):
    query = "SELECT * FROM {batch}\r\n\t  ;\v\r ;"

    expectation = UnexpectedRowsExpectation(unexpected_rows_query=query)

    assert expectation.unexpected_rows_query == "SELECT * FROM {batch}"


@pytest.mark.unit
@pytest.mark.parametrize(
    "description, unexpected_rows_query",
    [
        pytest.param(
            "passenger_count should be less than or equal to 7",
            "SELECT * FROM {batch} WHERE passenger_count > 7",
            id="with description",
        ),
        pytest.param(
            None,
            "SELECT * FROM {batch} WHERE passenger_count > 7",
            id="no description",
        ),
    ],
)
def test_unexpected_rows_expectation_render(
    description: str | None,
    unexpected_rows_query: str,
):
    expectation = UnexpectedRowsExpectation(
        description=description,
        unexpected_rows_query=unexpected_rows_query,
    )
    expectation.render()
    assert (
        expectation.rendered_content[0].value.params.get("unexpected_rows_query").get("value")
        == unexpected_rows_query
    )

    assert expectation.rendered_content[0].value.template == description
    assert (
        expectation.rendered_content[0].value.code_block.get("code_template_str")
        == "$unexpected_rows_query"
    )
    assert expectation.rendered_content[0].value.code_block.get("language") == "sql"


@pytest.mark.unit
def test_data_docs_rendering():
    query = "SELECT * FROM {batch} WHERE passenger_count > 7"
    expectation = UnexpectedRowsExpectation(unexpected_rows_query=query)
    results = ContentBlockRenderer.render(expectation.configuration)
    assert isinstance(results, list) and len(results) == 1
    result = results[0]
    assert result.string_template == {
        "template": "Unexpected rows query: $unexpected_rows_query",
        "params": {"unexpected_rows_query": query},
        "styling": {},
    }
