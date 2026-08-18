from __future__ import annotations

import copy
import inspect
import logging
import pathlib
import re
from dataclasses import dataclass
from pprint import pformat as pf
from typing import TYPE_CHECKING, Any, Optional, Type

import pytest
from pytest import MonkeyPatch, param

import great_expectations.exceptions as ge_exceptions
import great_expectations.execution_engine.pandas_execution_engine
from great_expectations.compatibility import pydantic
from great_expectations.core.partitioners import FileNamePartitionerMonthly
from great_expectations.datasource.fluent import BatchRequest, PandasFilesystemDatasource
from great_expectations.datasource.fluent.data_asset.path.pandas.generated_assets import (
    CSVAsset,
    JSONAsset,
)
from great_expectations.datasource.fluent.data_connector import (
    FilesystemDataConnector,
)
from great_expectations.datasource.fluent.dynamic_pandas import PANDAS_VERSION
from great_expectations.datasource.fluent.interfaces import TestConnectionError
from great_expectations.datasource.fluent.sources import _get_field_details
from great_expectations.exceptions.exceptions import NoAvailableBatchesError
from great_expectations.warnings import GxDeprecationWarning

if TYPE_CHECKING:
    from great_expectations.alias_types import PathStr
    from great_expectations.data_context import AbstractDataContext
    from great_expectations.datasource.fluent.data_asset.path.path_data_asset import (
        PathDataAsset,
    )
    from great_expectations.datasource.fluent.interfaces import (
        BatchMetadata,
        BatchSlice,
    )

logger = logging.getLogger(__file__)

# apply markers to entire test module
pytestmark = [
    pytest.mark.skipif(
        PANDAS_VERSION < 1.2, reason=f"Fluent pandas not supported on {PANDAS_VERSION}"
    )
]


class SpyInterrupt(RuntimeError):
    """
    Exception that may be raised to interrupt the control flow of the program
    when a spy has already captured everything needed.
    """


@pytest.fixture
def capture_reader_fn_params(monkeypatch: MonkeyPatch):
    """
    Capture the `reader_options` arguments being passed to the `PandasExecutionEngine`.

    Note this fixture is heavily reliant on the implementation details of `PandasExecutionEngine`,
    should this change this fixture will need to change.
    """
    captured_args: list[list] = []
    captured_kwargs: list[dict[str, Any]] = []

    def reader_fn_spy(*args, **kwargs):
        logging.info(f"reader_fn_spy() called with...\n{args}\n{kwargs}")
        captured_args.append(args)
        captured_kwargs.append(kwargs)
        raise SpyInterrupt("Reader options have been captured")

    monkeypatch.setattr(
        great_expectations.execution_engine.pandas_execution_engine.PandasExecutionEngine,
        "_get_reader_fn",
        lambda *_: reader_fn_spy,
        raising=True,
    )

    yield captured_args, captured_kwargs


@pytest.mark.unit
class TestDynamicPandasAssets:
    @pytest.mark.parametrize(
        "method_name",
        [
            param("read_clipboard", marks=pytest.mark.xfail(reason="not path based")),
            param("read_csv"),
            param("read_excel"),
            param("read_feather"),
            param("read_fwf"),
            param("read_gbq", marks=pytest.mark.xfail(reason="not path based")),
            param("read_hdf"),
            param("read_html"),
            param("read_json"),
            param("read_orc"),
            param("read_parquet"),
            param("read_pickle"),
            param("read_sas"),
            param("read_spss"),
            param(
                "read_sql",
                marks=pytest.mark.xfail(reason="name conflict & not path based"),
            ),
            param(
                "read_sql_query",
                marks=pytest.mark.xfail(
                    reason="type name logic expects 'sqltable' & not path based"
                ),
            ),
            param(
                "read_sql_table",
                marks=pytest.mark.xfail(
                    reason="type name logic expects 'sqltable' & not path based"
                ),
            ),
            param("read_stata"),
            param(
                "read_table",
                marks=pytest.mark.xfail(reason="name conflict & not path based"),
            ),
            param(
                "read_xml",
                marks=pytest.mark.skipif(
                    PANDAS_VERSION < 1.3,
                    reason=f"read_xml does not exist on {PANDAS_VERSION} ",
                ),
            ),
        ],
    )
    def test_data_asset_defined_for_io_read_method(self, method_name: str):
        _, type_name = method_name.split("read_")
        assert type_name

        asset_class_names: set[str] = {
            t.__name__.lower().split("asset")[0] for t in PandasFilesystemDatasource.asset_types
        }
        print(asset_class_names)

        assert type_name in asset_class_names

    @pytest.mark.parametrize("asset_class", PandasFilesystemDatasource.asset_types)
    def test_add_asset_method_exists_and_is_functional(self, asset_class: Type[PathDataAsset]):
        type_name: str = _get_field_details(asset_class, "type").default_value
        method_name: str = f"add_{type_name}_asset"

        print(f"{method_name}() -> {asset_class.__name__}")

        assert method_name in PandasFilesystemDatasource.__dict__

        ds = PandasFilesystemDatasource(
            name="ds_for_testing_add_asset_methods",
            base_directory=pathlib.Path.cwd(),
        )
        method = getattr(ds, method_name)

        with pytest.raises(pydantic.ValidationError) as exc_info:
            method(
                f"{asset_class.__name__}_add_asset_test",
                batching_regex="great_expectations",
                _invalid_key="foobar",
            )
        # importantly check that the method creates (or attempts to create) the intended asset
        assert exc_info.value.model == asset_class

    @pytest.mark.parametrize("asset_class", PandasFilesystemDatasource.asset_types)
    def test_add_asset_method_signature(self, asset_class: Type[PathDataAsset]):
        type_name: str = _get_field_details(asset_class, "type").default_value
        method_name: str = f"add_{type_name}_asset"

        ds = PandasFilesystemDatasource(
            name="ds_for_testing_add_asset_methods",
            base_directory=pathlib.Path.cwd(),
        )
        method = getattr(ds, method_name)

        add_asset_method_sig: inspect.Signature = inspect.signature(method)
        print(f"\t{method_name}()\n{add_asset_method_sig}\n")

        asset_class_init_sig: inspect.Signature = inspect.signature(asset_class)
        print(f"\t{asset_class.__name__}\n{asset_class_init_sig}\n")

        for i, param_name in enumerate(asset_class_init_sig.parameters):
            print(f"{i} {param_name} ", end="")

            if param_name == "type":
                assert param_name not in add_asset_method_sig.parameters, (
                    "type should not be part of the `add_<TYPE>_asset` method"
                )
                print("⏩")
                continue

            assert param_name in add_asset_method_sig.parameters
            print("✅")

    @pytest.mark.parametrize(
        ["asset_model", "extra_kwargs"],
        [
            (CSVAsset, {"sep": "|", "names": ["col1", "col2", "col3"]}),
            (JSONAsset, {"orient": "records", "convert_dates": True}),
        ],
    )
    def test_data_asset_defaults(
        self,
        asset_model: Type[PathDataAsset],
        extra_kwargs: dict,
    ):
        """
        Test that an asset dictionary can be dumped with only the original passed keys
        present.
        """
        kwargs: dict[str, Any] = {
            "name": "test",
        }
        kwargs.update(extra_kwargs)
        print(f"extra_kwargs\n{pf(extra_kwargs)}")
        asset_instance = asset_model(**kwargs)
        assert asset_instance.dict(exclude={"type"}) == kwargs

    @pytest.mark.parametrize(
        "extra_kwargs",
        [
            {"sep": "|", "decimal": ","},
            {"usecols": [0, 1, 2], "names": ["foo", "bar"]},
            {"dtype": {"col_1": "Int64"}},
        ],
    )
    def test_data_asset_reader_options_passthrough(
        self,
        empty_data_context: AbstractDataContext,
        csv_path: pathlib.Path,
        capture_reader_fn_params: tuple[list[list], list[dict]],
        extra_kwargs: dict,
    ):
        batch_request = (
            empty_data_context.data_sources.add_pandas_filesystem(  # .build_batch_request
                "my_pandas",
                base_directory=csv_path,
            )
            .add_csv_asset(
                "my_csv",
                **extra_kwargs,
            )
            .build_batch_request(
                {"year": "2018"},
                partitioner=FileNamePartitionerMonthly(
                    regex=re.compile(
                        r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
                    )
                ),
            )
        )
        with pytest.raises(SpyInterrupt):
            empty_data_context.get_validator(batch_request=batch_request)

        captured_args, captured_kwargs = capture_reader_fn_params
        print(f"positional args:\n{pf(captured_args[-1])}\n")
        print(f"keyword args:\n{pf(captured_kwargs[-1])}")

        assert captured_kwargs[-1] == extra_kwargs


@pytest.mark.unit
def test_construct_pandas_filesystem_datasource(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    assert pandas_filesystem_datasource.name == "pandas_filesystem_datasource"


@pytest.mark.unit
def test_add_csv_asset_to_datasource(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    assert asset.name == "csv_asset"


@pytest.mark.unit
def test_add_csv_asset_with_batching_regex_to_datasource(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    assert asset.name == "csv_asset"


@pytest.mark.unit
def test_invalid_connect_options(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    with pytest.raises(pydantic.ValidationError) as exc_info:
        pandas_filesystem_datasource.add_csv_asset(  # type: ignore[call-arg] # FIXME CoP
            name="csv_asset",
            glob_foobar="invalid",
        )

    error_dicts = exc_info.value.errors()
    print(pf(error_dicts))
    assert error_dicts == [
        {
            "loc": ("glob_foobar",),
            "msg": "extra fields not permitted",
            "type": "value_error.extra",
        }
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ["glob_directive", "expected_error"],
    [
        ({"invalid", "type"}, pydantic.ValidationError),
        ("not_a_dir/*.csv", TestConnectionError),
    ],
)
def test_invalid_connect_options_value(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    glob_directive,
    expected_error: Type[Exception],
):
    with pytest.raises(expected_error) as exc_info:
        pandas_filesystem_datasource.add_csv_asset(
            name="csv_asset",
            glob_directive=glob_directive,
        )

    print(f"Exception raised:\n\t{exc_info.value!r}")

    if isinstance(exc_info.value, pydantic.ValidationError):
        error_dicts = exc_info.value.errors()
        print(pf(error_dicts))
        assert error_dicts == [
            {
                "loc": ("glob_directive",),
                "msg": "str type expected",
                "type": "type_error.str",
            }
        ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "connect_options",
    [
        param({"glob_directive": "**/*"}, id="glob **/*"),
        param({"glob_directive": "**/*.csv"}, id="glob **/*.csv"),
        param({}, id="default connect options"),
    ],
)
def test_asset_connect_options_in_repr(
    pandas_filesystem_datasource: PandasFilesystemDatasource, connect_options: dict
):
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        **connect_options,
    )
    asset_repr = repr(asset)
    print(asset_repr)

    if connect_options:
        assert "glob_directive" in asset_repr
        assert connect_options["glob_directive"] in asset_repr
    else:
        # if no connect options are provided the defaults should be used and should not
        # be part of any serialization. repr == asset.yaml()
        assert "glob_directive" not in asset_repr


@pytest.mark.unit
def test_csv_asset_with_batching_regex_named_parameters(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    batching_regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=batching_regex)
    options = asset.get_batch_parameters_keys(partitioner=batch_def.partitioner)
    assert options == ("path", "year", "month")


@pytest.mark.unit
def test_csv_asset_with_non_string_batching_regex_named_parameters(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """An integer batching_regex parameter selects a batch instead of being rejected;
    a digit-string sibling in the same request keeps working with a deprecation
    warning."""
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=regex)

    with pytest.warns(GxDeprecationWarning):
        # year is an int and is accepted outright; month is a digit-string, which is
        # accepted but deprecated.
        batch = batch_def.get_batch(batch_parameters={"year": 2018, "month": "04"})

    assert batch.metadata == {
        "path": "yellow_tripdata_sample_2018-04.csv",
        "year": "2018",
        "month": "04",
    }


@pytest.mark.unit
def test_integer_rejected_for_regex_group_the_partitioner_does_not_declare_numeric(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """A regex group name alone does not make a parameter numeric -- only a group the
    partitioner's own numeric declaration also names does. A group captured by the
    regex but outside the partitioner's declared parameters is rejected as a
    non-string/non-numeric value with a message naming it, not silently treated as
    numeric."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    # "revision" is captured by the regex but is not one of the monthly partitioner's
    # declared (and therefore numeric) parameters.
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})-(?P<revision>\d+)\.csv"
    partitioner = FileNamePartitionerMonthly(regex=re.compile(regex))

    with pytest.raises(
        ge_exceptions.InvalidBatchRequestError,
        match="'revision' is not a string or an integer",
    ):
        asset.build_batch_request(
            {"year": 2018, "month": "04", "revision": 1}, partitioner=partitioner
        )


@pytest.mark.unit
def test_boolean_rejected_for_declared_numeric_parameter(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """A boolean is not an acceptable numeric parameter even though Python treats it
    as an int (`isinstance(True, int)` is `True`) -- a bool value for a declared
    numeric parameter is rejected, not silently admitted as 1."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    partitioner = FileNamePartitionerMonthly(regex=re.compile(regex))

    with pytest.raises(
        ge_exceptions.InvalidBatchRequestError,
        match="'month' is not a string or an integer",
    ):
        asset.build_batch_request({"year": 2018, "month": True}, partitioner=partitioner)


@pytest.mark.unit
def test_numeric_coercion_limited_to_params_both_declared_and_captured(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """A partitioner's declared numeric parameters are only coerced when the regex
    also captures them by that name. "month" is declared numeric by the monthly
    partitioner but the regex here has no named "month" group, so only "year" -- both
    declared and captured -- is coerced; "month" is passed through untouched, matching
    today's string contract, rather than being coerced on the strength of the
    declaration alone."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-\d{1,2}\.csv"
    partitioner = FileNamePartitionerMonthly(regex=re.compile(regex))

    with pytest.warns(GxDeprecationWarning):
        request = asset.build_batch_request(
            {"year": "2018", "month": "04"}, partitioner=partitioner
        )

    assert request.options["year"] == 2018
    assert request.options["month"] == "04"


def _batches_selected_without_normalization(
    asset: PathDataAsset,
    partitioner: FileNamePartitionerMonthly,
    year: str,
    month: str,
) -> set[tuple[str, str]]:
    """The (year, month) pairs selected by today's string contract.

    Builds the `BatchRequest` directly, bypassing `build_batch_request`'s
    normalization and type-check wiring, so this reflects only the underlying regex
    matching -- independent of the behavior under test -- and can serve as a ground
    truth for the equivalent integer/digit-string requests.
    """
    request = BatchRequest(
        datasource_name=asset.datasource.name,
        data_asset_name=asset.name,
        options={"year": year, "month": month},
        partitioner=partitioner,
    )
    return {
        (identifiers["year"], identifiers["month"])
        for identifiers in asset.get_batch_identifiers_list(request)
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "regex",
    [
        pytest.param(
            r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv", id="fixed-width"
        ),
        pytest.param(
            r"yellow_tripdata_sample_(?P<year>\d{1,4})-(?P<month>\d{1,2})\.csv",
            id="variable-width",
        ),
    ],
)
def test_integer_batch_parameters_select_same_batches_as_zero_padded_strings(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    regex: str,
):
    """Integer batch parameters select exactly the batches their zero-padded string
    form selects today, including a single-digit month -- the trap a textual (rather
    than numeric) normalization would fail."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    partitioner = FileNamePartitionerMonthly(regex=re.compile(regex))

    expected = _batches_selected_without_normalization(asset, partitioner, year="2018", month="04")
    assert expected == {("2018", "04")}

    int_request = asset.build_batch_request({"year": 2018, "month": 4}, partitioner=partitioner)
    int_selected = {
        (identifiers["year"], identifiers["month"])
        for identifiers in asset.get_batch_identifiers_list(int_request)
    }

    assert int_selected == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "regex",
    [
        pytest.param(
            r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv", id="fixed-width"
        ),
        pytest.param(
            r"yellow_tripdata_sample_(?P<year>\d{1,4})-(?P<month>\d{1,2})\.csv",
            id="variable-width",
        ),
    ],
)
def test_digit_string_batch_parameters_select_same_batches_as_integers_and_warn(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    regex: str,
):
    """A digit-string batch parameter selects the same batches as its integer
    equivalent and emits a deprecation warning instead of raising."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    partitioner = FileNamePartitionerMonthly(regex=re.compile(regex))

    expected = _batches_selected_without_normalization(asset, partitioner, year="2018", month="04")

    with pytest.warns(GxDeprecationWarning):
        digit_string_request = asset.build_batch_request(
            {"year": "2018", "month": "04"}, partitioner=partitioner
        )
    digit_string_selected = {
        (identifiers["year"], identifiers["month"])
        for identifiers in asset.get_batch_identifiers_list(digit_string_request)
    }

    assert digit_string_selected == expected


@pytest.mark.unit
def test_integer_batch_parameter_keeps_zero_padded_string_identifiers_and_batch_id(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """Selecting a batch with integer batch parameters keeps the zero-padded string
    captures in metadata and identifiers, and the batch ID equals the literal produced
    by the equivalent (string-contract) request today."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=regex)

    with pytest.warns(GxDeprecationWarning):
        string_batch = batch_def.get_batch(batch_parameters={"year": "2018", "month": "04"})
    int_batch = batch_def.get_batch(batch_parameters={"year": 2018, "month": 4})

    assert int_batch.metadata == string_batch.metadata
    assert int_batch.metadata == {
        "path": "yellow_tripdata_sample_2018-04.csv",
        "year": "2018",
        "month": "04",
    }
    assert int_batch.id == string_batch.id
    assert string_batch.id == "pandas_filesystem_datasource-csv_asset-year_2018-month_04"


@pytest.mark.unit
def test_batch_definition_build_batch_request_forwards_normalization(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """`BatchDefinition.build_batch_request` is a verbatim forwarder to the asset
    override -- it has no logic of its own, so a test that merely calls it and checks
    for "no exception" would pass even if the forwarding stopped reaching the
    normalization boundary. Asserting the *normalized* (int-valued) options is what
    makes this test fail if that boundary is skipped: an unnormalized forward would
    leave "month" as the digit-string "04" in `request.options`, not the int `4`.
    """
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=regex)

    with pytest.warns(GxDeprecationWarning):
        request = batch_def.build_batch_request({"year": "2018", "month": "04"})

    assert request.options == {"year": 2018, "month": 4}


@pytest.mark.unit
def test_batch_definition_get_batch_identifiers_list_forwards_normalization(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    """`BatchDefinition.get_batch_identifiers_list` is also a verbatim forwarder --
    through its own `build_batch_request`, in turn through the asset override. Integer
    batch parameters alone would not prove forwarding reaches the boundary: the file
    matching sites already tolerate int-vs-zero-padded-string candidates
    unconditionally, so a raw, unnormalized `BatchRequest` built with int options would
    select the same identifiers regardless of whether normalization ran. A digit-string
    request is the assertion that goes red if forwarding stops reaching the boundary --
    it only selects the equivalent batch, and only warns, if normalization actually
    ran; an unnormalized bypass would either raise (pre-relaxation) or, absent that
    check too, simply never emit the warning `pytest.warns` requires here.
    """
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=regex)

    with pytest.warns(GxDeprecationWarning):
        identifiers_list = batch_def.get_batch_identifiers_list({"year": "2018", "month": "04"})

    assert identifiers_list == [
        {"path": "yellow_tripdata_sample_2018-04.csv", "year": "2018", "month": "04"}
    ]


@pytest.mark.unit
@pytest.mark.parametrize("sort_ascending", [True, False])
def test_string_batch_parameters_preserve_batch_ordering(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    sort_ascending: bool,
):
    """String batch parameters continue to produce identifier lists in the same
    ascending/descending order they do today."""
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    partitioner = FileNamePartitionerMonthly(regex=re.compile(regex), sort_ascending=sort_ascending)

    with pytest.warns(GxDeprecationWarning):
        request = asset.build_batch_request({"year": "2018"}, partitioner=partitioner)
    identifiers_list = asset.get_batch_identifiers_list(request)
    months = [identifiers["month"] for identifiers in identifiers_list]

    assert months == sorted(months, reverse=not sort_ascending)
    assert len(months) == 12


@pytest.mark.unit
def test_get_batch_list_from_fully_specified_batch_request(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=regex)
    batch_parameters = {"year": "2018", "month": "04"}
    batch = batch_def.get_batch(batch_parameters=batch_parameters)
    assert batch.batch_request.datasource_name == pandas_filesystem_datasource.name
    assert batch.batch_request.data_asset_name == asset.name

    path = "yellow_tripdata_sample_2018-04.csv"
    assert batch.batch_request.options == {"path": path, "year": "2018", "month": "04"}
    assert batch.metadata == {"path": path, "year": "2018", "month": "04"}

    assert batch.id == "pandas_filesystem_datasource-csv_asset-year_2018-month_04"


@pytest.mark.unit
@pytest.mark.parametrize(
    "year,month,path,batch_count",
    [
        ("2018", "04", "yellow_tripdata_sample_2018-04.csv", 1),
        ("2018", None, None, 12),
        (None, "04", None, 3),
        (None, "03", "yellow_tripdata_sample_2018-04.csv", 0),
    ],
)
def test_get_batch_identifiers_list_count(
    year: Optional[str],
    month: Optional[str],
    path: Optional[str],
    batch_count: int,
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    request = asset.build_batch_request(
        {"year": year, "month": month, "path": path},
        partitioner=FileNamePartitionerMonthly(
            regex=re.compile(r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv")
        ),
    )
    batch_identifier_list = asset.get_batch_identifiers_list(request)
    assert len(batch_identifier_list) == batch_count


@pytest.mark.unit
def test_get_batch_identifiers_list_from_partially_specified_batch_request(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    # Verify test directory has files that don't match what we will query for
    file_name: PathStr
    all_files: list[str] = [
        file_name.stem
        for file_name in list(pathlib.Path(pandas_filesystem_datasource.base_directory).iterdir())
    ]
    # assert there are files that are not csv files
    assert any(not file_name.endswith("csv") for file_name in all_files)
    # assert there are 12 files from 2018
    files_for_2018 = [file_name for file_name in all_files if file_name.find("2018") >= 0]
    assert len(files_for_2018) == 12

    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    request = asset.build_batch_request(
        {"year": "2018"},
        partitioner=FileNamePartitionerMonthly(
            regex=re.compile(r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv")
        ),
    )
    batches = asset.get_batch_identifiers_list(request)
    assert (len(batches)) == 12
    batch_filenames = [pathlib.Path(batch["path"]).stem for batch in batches]
    assert set(files_for_2018) == set(batch_filenames)

    @dataclass(frozen=True)
    class YearMonth:
        year: str
        month: str

    expected_year_month = {YearMonth(year="2018", month=format(m, "02d")) for m in range(1, 13)}
    batch_year_month = {YearMonth(year=batch["year"], month=batch["month"]) for batch in batches}
    assert expected_year_month == batch_year_month


@pytest.mark.unit
@pytest.mark.parametrize(
    "batch_slice, expected_batch_count",
    [
        ("[-3:]", 3),
        ("[5:9]", 4),
        ("[:10:2]", 5),
        (slice(-3, None), 3),
        (slice(5, 9), 4),
        (slice(0, 10, 2), 5),
        ("-5", 1),
        ("-1", 1),
        (11, 1),
        (0, 1),
        ([3], 1),
        (None, 12),
        ("", 12),
    ],
)
def test_pandas_slice_batch_count(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    batch_slice: BatchSlice,
    expected_batch_count: int,
) -> None:
    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
    )
    batch_request = asset.build_batch_request(
        options={"year": "2019"},
        batch_slice=batch_slice,
        partitioner=FileNamePartitionerMonthly(
            regex=re.compile(r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv")
        ),
    )
    batch_identifiers_list = asset.get_batch_identifiers_list(batch_request=batch_request)
    assert len(batch_identifiers_list) == expected_batch_count


def bad_batching_regex_config(
    csv_path: pathlib.Path,
) -> tuple[re.Pattern, TestConnectionError]:
    batching_regex = re.compile(r"green_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv")
    test_connection_error = TestConnectionError(
        "No file at base_directory path "
        f'"{csv_path.resolve()}" matched regular expressions pattern '
        f'"{batching_regex.pattern}" and/or glob_directive "**/*" for '
        'DataAsset "csv_asset".'
    )
    return batching_regex, test_connection_error


@pytest.fixture(params=[bad_batching_regex_config])
def datasource_test_connection_error_messages(
    csv_path: pathlib.Path,
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    request,
) -> tuple[PandasFilesystemDatasource, TestConnectionError]:
    _, test_connection_error = request.param(csv_path=csv_path)
    csv_asset = CSVAsset(  # type: ignore[call-arg] # FIXME CoP
        name="csv_asset",
    )
    csv_asset._datasource = pandas_filesystem_datasource
    pandas_filesystem_datasource.assets = [
        csv_asset,
    ]
    csv_asset._data_connector = FilesystemDataConnector(
        datasource_name=pandas_filesystem_datasource.name,
        data_asset_name=csv_asset.name,
        base_directory=pandas_filesystem_datasource.base_directory,
        data_context_root_directory=pandas_filesystem_datasource.data_context_root_directory,
    )
    csv_asset._test_connection_error_message = test_connection_error
    return pandas_filesystem_datasource, test_connection_error


@pytest.mark.timeout(
    5,  # deepcopy operation can be slow. Try to eliminate it in the future.
)
@pytest.mark.unit
def test_csv_asset_batch_metadata(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
):
    my_config_variables = {"pipeline_filename": __file__}
    pandas_filesystem_datasource._data_context.config_variables.update(  # type: ignore[union-attr] # `_data_context`
        my_config_variables
    )

    asset_specified_metadata = {
        "pipeline_name": "my_pipeline",
        "no_curly_pipeline_filename": "$pipeline_filename",
        "curly_pipeline_filename": "${pipeline_filename}",
    }

    asset = pandas_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batch_metadata=asset_specified_metadata,
    )
    assert asset.batch_metadata == asset_specified_metadata

    batch_request = asset.build_batch_request(
        partitioner=FileNamePartitionerMonthly(
            regex=re.compile(r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv")
        )
    )

    batch = pandas_filesystem_datasource.get_batch(batch_request)

    substituted_batch_metadata: BatchMetadata = copy.deepcopy(asset_specified_metadata)
    substituted_batch_metadata.update(
        {
            "no_curly_pipeline_filename": __file__,
            "curly_pipeline_filename": __file__,
        }
    )

    actual_metadata = copy.deepcopy(batch.metadata)

    actual_metadata.pop("path")
    actual_metadata.pop("year")
    actual_metadata.pop("month")

    assert len(actual_metadata)
    assert actual_metadata == substituted_batch_metadata


@pytest.mark.parametrize(
    ("sort_ascending", "expected_metadata"),
    [
        (True, {"year": "2020", "month": "12", "path": "yellow_tripdata_sample_2020-12.csv"}),
        (False, {"year": "2018", "month": "01", "path": "yellow_tripdata_sample_2018-01.csv"}),
    ],
)
@pytest.mark.unit
def test_get_batch_respects_order_ascending(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
    sort_ascending: bool,
    expected_metadata: dict,
) -> None:
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(
        name="batch def", regex=regex, sort_ascending=sort_ascending
    )
    batch = batch_def.get_batch()
    assert batch.metadata == expected_metadata


@pytest.mark.unit
def test_raises_if_no_matching_batches(
    pandas_filesystem_datasource: PandasFilesystemDatasource,
) -> None:
    asset = pandas_filesystem_datasource.add_csv_asset(name="csv_asset")
    regex = r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    batch_def = asset.add_batch_definition_monthly(name="batch def", regex=regex)
    with pytest.raises(NoAvailableBatchesError):
        batch_def.get_batch(batch_parameters={"year": "1995", "month": "01"})
