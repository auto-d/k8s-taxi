"""
Data Quality Validation Tests Template

Write tests that:
1. Pass for clean (baseline) data
2. Fail for corrupted data
3. Test each issue you identified
"""

import pytest
import pandas as pd
import numpy as np
from backend.data import configure_dataset, forecast_demand
from validation.check_data_quality import load_data, print_issues, filter_issues, DataQualityValidator

@pytest.fixture
def baseline_data():
    """Load clean baseline data."""
    baseline, _ = load_data()
    return baseline

@pytest.fixture
def corrupted_data():
    """Load corrupted data."""
    _, corrupted = load_data()
    return corrupted

@pytest.fixture
def validator(baseline_data):
    """Create validator initialized with baseline."""
    return DataQualityValidator(baseline_data) 


# ============================================================================
# TEST STRUCTURE EXAMPLES
# ============================================================================


class TestBaselineData:
    """Tests that baseline data should pass validation."""

    def test_baseline_passes_validation(self, baseline_data, validator):
        """Baseline data should have no quality issues."""
        issues = validator.validate(baseline_data)
        assert len(issues)==0, f"Baseline failed, issues follow:\n{print_issues(issues)}"

class TestDataQualityIssues:
    """Tests that verify each issue is detected."""

    def test_detect_issue_1(self, corrupted_data, validator):
        """Should detect schema issues."""
        issues = validator.validate(corrupted_data)
        filtered = filter_issues(issues, ['Schema'])
        assert len(filtered)==0, f"Schema issues detected:\n{print_issues(issues)}"

    def test_detect_issue_2(self, corrupted_data, validator):
        """Should detect range issues."""
        issues = validator.validate(corrupted_data)
        filtered = filter_issues(issues, ['Range'])
        assert len(filtered)==0, f"Range issues detected:\n{print_issues(issues)}"

    def test_detect_issue_3(self, corrupted_data, validator):
        """Should detect duplicates."""
        issues = validator.validate(corrupted_data)
        filtered = filter_issues(issues, ['Duplicate'])
        assert len(filtered)==0, f"Duplicates detected:\n{print_issues(issues)}"

    def test_detect_issue_4(self, corrupted_data, validator):
        """Should detect missing values."""
        issues = validator.validate(corrupted_data)
        filtered = filter_issues(issues, ['Missing'])
        assert len(filtered)==0, f"Missing data detected:\n{print_issues(issues)}"


class TestGracefulDegradation:
    """Tests that API gracefully handles bad data."""

    def test_api_does_not_crash_with_bad_data(self, corrupted_data):
        """API should continue running even with corrupted data."""
        # All import and setup logic happens at the module scope, so is 
        # executed on import above, we only need to run a forecast to see how it 
        # behaves
        demand = forecast_demand(12, 3, 5)
        print(demand)

    def test_fallback_is_logged(self, corrupted_data):
        """When graceful degradation happens, it should be logged."""
        # The design of this data module is such that our data quality check
        # happens on module initialization, which is prior to this function's 
        # invocation ... we'll see data issues flagged when this test is 
        # initialized, not on this function actually being called.
        demand = forecast_demand(134, 5,7)

# ============================================================================
# HOW TO RUN
# ============================================================================
#
# From repo root:
#   python -m pytest week3/validation/test_data_quality.py -v
#
# To run specific test:
#   python -m pytest week3/validation/test_data_quality.py::TestDataQualityIssues::test_detect_issue_1 -v
#
# To see print statements:
#   python -m pytest week3/validation/test_data_quality.py -v -s
