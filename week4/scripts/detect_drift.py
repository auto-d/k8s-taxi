"""
Drift detection skeleton.

Write code to detect 4+ distinct drift patterns between baseline and new data.
Use statistical tests (KS, PSI, chi-square) to quantify drift.
"""

import sys 
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from sklearn.metrics import accuracy_score, mean_absolute_error
from metric_template import MetricComputer, predict_demand, load_data

def detect_feature_drift(baseline_df: pd.DataFrame, new_df: pd.DataFrame, feature: str):
    """
    Detect drift in a single feature.
    """
    result = ks_2samp(baseline_df[feature], new_df[feature])
    
    drift = True if result['statistic'] > 0.1 else False
    return drift, {
        "pvalue": result.pvalue, 
        "statistic" : result.statistic, 
        "drift_detected" : drift
    }


def error_by_ordinal(df, col='PULocationID', n=1000):
    """
    Calculate the error for a specific ordinal value, based on provided number of samples 
    per ordinal value 
    """    
    # Group and sample to achieve stratified sampling by the provided column 
    groups = df.groupby(col)
    df_sample = groups.sample(n=n)

    # Predict on our smaller dataset 
    preds = predict_demand(df)

    # Dump all but essential columns
    df_sample_small = df_sample[[col, 'trip_count']].copy()

    # Tack on our predictions and error
    df_sample_small['preds'] = preds 
    df_sample_small['error'] = abs(df_sample_small['trip_count'] - preds) 
    
    # Return the averages for each ordinal valu e
    return df_sample_small.groupby(col).mean()


def detect_concept_drift_by_segment(baseline_df: pd.DataFrame, new_df: pd.DataFrame, feature) -> dict:
    """
    Detect concept drift (accuracy degradation by segment).
    """

    drift = False 

    # Decompose model performance by location ordinals
    baseline_error = error_by_ordinal(baseline_df, col=feature)    
    new_error = error_by_ordinal(new_df, col=feature)
    
    baseline_it = baseline_error.reset_index(0).iterrows()
    new_it = new_error.reset_index(0).iterrows()

    error = {}
    for baseline_row, new_row in zip(baseline_it, new_it):             

        loc = baseline_row[1][feature]
        if loc != new_row[1][feature]: 
            raise ValueError("Mismatched ordinals, can't generate ordinal-based errors")

        # Record the errors for each ordinal value
        segment_drift = True if new_row[1].error > baseline_row[1].error else False
        error[int(loc)] = { 
            "baseline": baseline_row[1].error, 
            "new": new_row[1].error,
            "drift_detected": segment_drift
            }
        
        drift = drift or segment_drift

    return drift, error


def main():
    """Main drift detection analysis."""
    print("=" * 70)
    print("DRIFT DETECTION")
    print("=" * 70)

    baseline, new = load_data() 
    
    weekend_drift, weekend_results = detect_feature_drift(baseline, new, "is_weekend")
    trip_drift, trip_results = detect_feature_drift(baseline, new, "trip_count")
    
    hour_drift, hour_segment_results = detect_concept_drift_by_segment(baseline, new, "hour")
    loc_drift, loc_segment_results = detect_concept_drift_by_segment(baseline, new, "PULocationID")

    drift = weekend_drift or trip_drift or hour_drift or loc_drift 
    result = { 
        "weekend_drift": weekend_results, 
        "trip_drift": trip_results, 
        "hour_drift": hour_segment_results, 
        "loc_drift": loc_segment_results
    }

    print(result)

    return 1 if drift else 0

if __name__ == "__main__":
    sys.exit(main())
