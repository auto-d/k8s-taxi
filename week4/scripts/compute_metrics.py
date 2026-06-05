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
import lightgbm as lgb
import json

def load_data(): 
    """
    Load our baseline and newly arrived data 
    """
 
    print("Loading datasets...")
    baseline = pd.read_parquet("week4/data/demand_enriched_baseline.parquet")
    new = pd.read_parquet("week4/data/demand_enriched_week4.parquet")

    SAMPLE_HOURS = 24

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

def direct_load_model(): 
    """
    Utility to grab the model right off disk and avoid the global init shenanigans 
    in data.py
    """    

    MODEL_PATH = "week2/model/lgbm_demand_model.txt"

    print("Loading model...")  
    model = lgb.Booster(model_file=str(MODEL_PATH))

    return model 

def predict_demand(df): 
    """
    Utility to bypass the wrappers around the model in data.py so we can get a raw prediction on 
    demand. 
    """

    # NOTE: borrowed columns from data.py
    FEATURES = [
        "PULocationID",
        "hour",
        "minute",
        "dayofweek",
        "is_weekend",
        "month",
        "dayofyear",
        "weekofyear",
        "year",
        "slot_of_day",
        "hour_sin",
        "hour_cos",
        "dow_sin",
        "dow_cos",
        "month_sin",
        "month_cos",
        "is_holiday",
        "cbd_pricing_active",
        "is_airport_zone",
        "borough_id",
        "service_zone_id",
        "zone_slot_baseline",
        "lag_15min",
        "lag_1h",
        "lag_2h",
        "lag_1day",
        "lag_1week",
        "roll_mean_1h",
        "roll_mean_2h",
        "roll_mean_1day",
    ]

    # Create feature dataframe in correct order
    X_pred = df[FEATURES]

    model = direct_load_model()

    # Make prediction and threshold to avoid negative trip predictions 
    preds = model.predict(X_pred)
    preds[preds < 0] = 0 
    
    return preds

def main(): 
    """
    CLI entrypoint for use w/ github actions (see validate-data.yml)
    """        
    print("Loading new data...")
    baseline, new = load_data()
    print(f"Found {len(new)} rows.")

    print("Getting predictions on new data...")        
    preds = predict_demand(new)

    mc = MetricComputer(baseline)    
    metrics = mc.compute_all_metrics(new_df=new, predictions=preds, actuals=new.trip_count)
    print(metrics)
    write_metrics(metrics)

if __name__ == "__main__":
    main()
