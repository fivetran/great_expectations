import pytest

from great_expectations.analytics.anonymizer import anonymize


@pytest.mark.unit
def test_anonymizer_anonymize():
    assert anonymize("string") == "473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8"
