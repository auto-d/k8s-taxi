"""
Implements metric computation
 - Load baseline and current data
 - Compute 5+ metrics (nulls, distributions, PSI, KS test, etc.)
 - Report metrics and thresholds
 - Determine if any alerts should fire
"""
import sys
import pandas as pd 
from scipy.stats import ks_2samp
from metric_template import MetricComputer
import json

def load_data(): 
    """
    Load our baseline and newly arrived data 
    """
    baseline = pd.read_parquet("data/demand_enriched_baseline.parquet")
    new_data = pd.read_parquet("data/demand_enriched_week4.parquet")

    return baseline, new_data

def get_timestamp(): 
    """
    Generate a textual timestamp for our filename
    """
    # NOTE: gpt-5.5-sourced snippet for timestamp
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def write_metrics(metrics_dict): 
    """
    Write our metrics to disk
    """
    path = f"metrics-{get_timestamp()}.json"
    with open(path, "w") as file: 
        json.dump(metrics_dict, file)

def main(): 
    """
    CLI entrypoint for use w/ github actions (see validate-data.yml)
    """
    baseline, new = load_data()

    mc = MetricComputer(baseline)
    
    metrics = mc.compute_all_metrics(new_df = new)
    print(metrics)
    write_metrics(metrics)

if __name__ == "__main__":
    main()