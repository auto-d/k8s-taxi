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
from week4.scripts.metric_template import MetricComputer
from week3.backend.data import forecast_demand

import json

def load_data(): 
    """
    Load our baseline and newly arrived data 
    """

    print("Loading datasets...")
    baseline = pd.read_parquet("week4/data/demand_enriched_baseline.parquet")
    new = pd.read_parquet("week4/data/demand_enriched_week4.parquet")

    SAMPLE_HOURS = 12

    latest = new["time_bucket"].max()
    begin = latest - pd.Timedelta(hours=SAMPLE_HOURS)
    print(f"Extracting last {SAMPLE_HOURS} hours ({begin} -> {latest})")

    return baseline, new[new.time_bucket > begin].copy()

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
    print("Loading datasets...")
    baseline, new = load_data()

    print("Running demand forecast...")
    #TODO: forecast demand using buckets with, i presume, the trip_count as the ground_truth
    for row in new: 
        
        print(row )
        
        # Steps default to 4 and that's what our dataset reports in 
        demand = forecast_demand(zone_id=row.service_zone_id, hour=row.hour, dow=row.dayofweek)        
        print(demand) 
        sys.exit(1)

    mc = MetricComputer(baseline)    
    metrics = mc.compute_all_metrics(new_df = new)
    print(metrics)
    write_metrics(metrics)

if __name__ == "__main__":
    main()
