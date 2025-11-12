import pytest
from Validation.VersionValidation.version_validation import simple_semver_validator

@pytest.mark.unit_test
@pytest.mark.parametrize("version,expected", [
    ("", False),
    (".", False),
    ("..", False),
    ("...", False),
    ("1.", False),
    (".1", False),
    ("1.1", False),
    ("1.1.1", True),
    ("9.9.9", True),
    ("1.1.10", False), # simple validator should invalidate non-single-digit version components
    ("1.10.1", False), # simple validator should invalidate non-single-digit version components
    ("100.1.1", False), # simple validator should invalidate non-single-digit version components
])
def test_simple_semver_validator(version, expected):
    assert simple_semver_validator(version) is expected