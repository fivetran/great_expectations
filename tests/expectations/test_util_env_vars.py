import os
from importlib import reload
from unittest import mock

import pytest

import great_expectations.expectations.metrics.util as util_module


class TestMaxResultRecordsEnvVar:
    """TMAX_RESULT_RECORDS environment variable configuration"""

    def test_max_result_records_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            reload(util_module)
            assert util_module.MAX_RESULT_RECORDS == 200

    def test_max_result_records_from_env(self):
        with mock.patch.dict(os.environ, {"GX_MAX_RESULT_RECORDS": "500"}):
            reload(util_module)
            assert util_module.MAX_RESULT_RECORDS == 500

    def test_max_result_records_invalid_env_value(self):
        with mock.patch.dict(os.environ, {"GX_MAX_RESULT_RECORDS": "not_a_number"}):
            with pytest.raises(ValueError):
                reload(util_module)

    def test_max_result_records_negative_value(self):
        with mock.patch.dict(os.environ, {"GX_MAX_RESULT_RECORDS": "-100"}):
            reload(util_module)
            assert util_module.MAX_RESULT_RECORDS == -100

    def teardown_method(self):
        """Ensure module is reset after each test"""
        os.environ.pop("GX_MAX_RESULT_RECORDS", None)
        reload(util_module)
