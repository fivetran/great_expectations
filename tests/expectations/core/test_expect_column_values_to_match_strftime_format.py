import pytest

from great_expectations.expectations.core import ExpectColumnValuesToMatchStrftimeFormat


class TestStrftimeFormatValidation:
    """Tests for the strftime_format Pydantic validator."""

    @pytest.mark.unit
    def test_timezone_aware_format_with_z_accepted(self):
        """Regression test for #9203 / PR #11812.

        Formats containing %z should be accepted, not raise ValidationError.
        Previously, the validator used datetime.now() (naive), so %z rendered
        as an empty string and strptime failed on the round-trip.
        """
        exp = ExpectColumnValuesToMatchStrftimeFormat(
            column="col", strftime_format="%Y-%m-%dT%H:%M:%S%z"
        )
        assert exp.strftime_format == "%Y-%m-%dT%H:%M:%S%z"

    @pytest.mark.unit
    def test_basic_format_accepted(self):
        """Standard non-timezone formats continue to work."""
        exp = ExpectColumnValuesToMatchStrftimeFormat(column="col", strftime_format="%Y-%m-%d")
        assert exp.strftime_format == "%Y-%m-%d"

    @pytest.mark.unit
    def test_invalid_format_rejected(self):
        """Truly invalid / non-round-trippable formats still raise."""
        with pytest.raises(Exception, match="Unable to use provided strftime_format"):
            ExpectColumnValuesToMatchStrftimeFormat(column="col", strftime_format="%D")
