"""
Data Quality Validation Framework Template

This file is a starting point for your validation code.
Modify or replace as needed based on the issues you identify.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys 

class DataQualityValidator:
    """Validates data against quality expectations."""

    def __init__(self, baseline: pd.DataFrame = None):
        """
        Initialize validator.

        Args:
            baseline_df: Clean reference data for comparison
        """
        self.baseline = baseline

    def validate(self, df: pd.DataFrame) -> list:
        """Check data quality. Return a list of issues."""
        
        self.issues = []
                
        if type(self.baseline) != pd.DataFrame:
            raise ValueError("Baseline dataframe is required to enable validation!")

        self.check_duplicates(df)
        self.check_schema(df)
        self.check_value_ranges(df)
        self.check_null_rates(df) 

        return self.issues

    def check_duplicates(self, df: pd.DataFrame):
        """Check for duplicate rows."""
                
        duplicated_rows = df.duplicated().sum()
        if duplicated_rows > 0: 
            self._add_issue("Duplicate", "Minor", f"Detected duplicate rows", duplicated_rows)

        if not df.index.is_unique: 
            duplicated_ixs = len(df) - len(df.index.unique())        
            self._add_issue("Duplicate", "Minor", f"Detected duplicate indices", duplicated_ixs)

    def check_schema(self, df: pd.DataFrame):
        """Check that required columns exist with correct types."""
        
        base_cols = set(self.baseline.columns)
        new_cols = set(df.columns)

        int_cols = base_cols.intersection(new_cols)
        if not int_cols == base_cols:
            self._add_issue("Schema", "Major", f"New data has missing features", len(base_cols) - len(int_cols))
        
        diff_cols = base_cols.difference(new_cols)
        if len(diff_cols) > 0:
            self._add_issue("Schema", "Moderate", f"Detected schema drift", len(diff_cols))

    def check_value_ranges(self, df: pd.DataFrame):
        """Check if values fall within expected ranges."""
        
        b_stats = self.baseline.describe()
        key_numeric_cols = [ 
            "trip_count", 
            "hour", 
            "minute", 
            "month", 
            "year",
        ]

        n_stats = df.describe()

        for col in key_numeric_cols: 
            
            if not hasattr(n_stats, col): 
                self._add_issue("Schema", "Major", f"Missing key column: {col}", 1)
                continue

            min = b_stats[col]['min']
            if n_stats[col]['min'] < min:                 
                self._add_issue("Range", "Minor", f"Minimum for {col} below baseline data", 0)

            max = b_stats[col]['max']
            if n_stats[col]['max'] > max:                 
                self._add_issue("Range", "Minor", f"Maximum for {col} above baseline data", 0)

    def check_null_rates(self, df: pd.DataFrame):
        """Check if any column has excessive nulls."""
        
        key_columns = [
            "PULocationID",
            "time_bucket",
            "trip_count",
            "hour",
            "minute",
            "dayofweek",
            "is_weekend",
            "month",
            "dayofyear",
            "weekofyear",
            "year",
            "slot_of_day",
            "is_holiday",
            "cbd_pricing_active",
            "borough_id",
            "service_zone_id",
            "is_airport_zone",
            "zone_slot_baseline",
            ]
        # NOTE: syntax to get the iterable here from sum() courtesy of chatGPT: 
        #  - prompt: "eh, how do I iterate over the returned series (from sum())? no iterrows and treating as an iterable hides the index."
        #  - model: gpt-5.4-codex,  28 May
        for col, count in df.isna().sum().items(): 
            if col in key_columns and count != 0:
                self._add_issue("Missing", "Moderate", f"Missing values for column {col}", count)
    
    def _add_issue(
        self,
        issue_type: str,
        severity: str,
        description: str,
        count: int = None,
        **details
    ):
        """Helper to add issue to list."""
        issue = {
            "type": issue_type,
            "severity": severity,  # 'critical', 'high', 'medium', 'low'
            "description": description,
            "count": count,
            **details,
        }
        self.issues.append(issue)

def load_data(): 
    """
    Load and split our artificial dataset here into baseline and 'new' 
    (corrupted) rows to demonstrate how validation would work on a 
    schedule (or on a commit hook) for arriving data. 
    """
    path = "data/demand_enriched_corrupted.parquet"
    CUTOFF = pd.Timestamp("2026-01-16")

    df = pd.read_parquet(path)
    old = df[df['time_bucket'] < CUTOFF] 
    new = df[df['time_bucket'] >= CUTOFF]

    return old, new

def filter_issues(issues, filter):
    """Filter issue set down based on criteria"""
    
    filtered = []
    for issue in issues: 
        if issue['type'] in filter: 
            filtered.append(issue)
    return filtered 

def print_issues(issues): 
    """Pretty-print issues (if any)"""
    
    if len(issues) > 0: 
        print(f"{'TYPE':<10}{'SEVERITY':<10}{'COUNT':<10}{'DESCRIPTION':<10}")
        
        for issue in issues: 
            print(f"{issue['type']:<10}{issue['severity']:<10}{issue['count']:<10}{issue['description']:<10}")

def main(): 
    """
    CLI entrypoint for use w/ github actions (see validate-data.yml)
    """
    old, new = load_data()

    dqv = DataQualityValidator(old)
    issues = dqv.validate(new)

    if 0 != len(issues): 
        print_issues(issues)        
        return 1

    return 0 

if __name__ == "__main__":

    # NOTE: sys.exit incantation from chatGPT consult: 
    # - prompt: "what is the right way to return an exit code in a python script?"
    # - model: chatGPT-5.5, 28 May 2026
    sys.exit(main()) 