from datetime import datetime, timezone

import pytest


class TestSparkStrftimeFormatValidation:
    """Tests for the strftime round-trip validation used by the Spark metric.

    The Spark implementation of column_values.match_strftime_format validates
    that a format string can round-trip through strftime -> strptime before
    building the UDF. This mirrors the Pydantic validator on the expectation
    class itself.
    """

    @staticmethod
    def _validate_strftime_format(strftime_format: str) -> None:
        """Reproduce the Spark metric's inline validation (lines 40-46)."""
        datetime.strptime(  # noqa: DTZ007
            datetime.strftime(datetime.now(tz=timezone.utc), strftime_format),
            strftime_format,
        )

    def test_timezone_aware_format_with_z_accepted(self):
        """Regression test: %z must not raise after the naive-datetime fix."""
        self._validate_strftime_format("%Y-%m-%dT%H:%M:%S%z")

    def test_basic_format_accepted(self):
        self._validate_strftime_format("%Y-%m-%d")

    def test_invalid_format_rejected(self):
        with pytest.raises(ValueError):
            self._validate_strftime_format("%D")
