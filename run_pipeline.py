"""Run the whole pipeline: extract -> checks -> features -> train -> forecast -> evaluate.

Usage (from the project folder):
    python run_pipeline.py                 # download missing data, then model
    python run_pipeline.py --skip-extract  # reuse the saved dataset
"""
import argparse
import logging

import pandas as pd

from src.config import ROOT, load_config
from src.evaluate import evaluate_by_node
from src.extract import build_dataset, download_raw, validate
from src.features import add_features, feature_names
from src.models import flag_anomalies, train_xgboost

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("pipeline")


def main(skip_extract=False):
    cfg = load_config()
    m = cfg["modeling"]
    proceso = cfg["api"]["proceso"]
    target, lags, peak = m["target"], m["lags"], m["peak_hours"]
    dataset_path = ROOT / "data" / "processed" / f"pml_{proceso.lower()}.parquet"

    # 1. Extract
    if skip_extract:
        log.info("Step 1/5 Extract: skipped, reading %s", dataset_path.name)
        df = pd.read_parquet(dataset_path)
    else:
        log.info("Step 1/5 Extract: downloading missing chunks")
        failed = download_raw(cfg, ROOT / "data" / "raw")
        if failed:
            raise RuntimeError(f"{len(failed)} chunks failed; rerun to retry them")
        df = build_dataset(ROOT / "data" / "raw", proceso)
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(dataset_path, index=False)

    # 2. Data checks
    log.info("Step 2/5 Data checks")
    validate(df, n_nodes=len(cfg["nodes"]))

    # 3. Features and time split
    log.info("Step 3/5 Features and split")
    x_cols = feature_names(lags)
    feat = add_features(df, target, lags, cfg["nodes"])
    split, val_start = pd.Timestamp(m["split_date"]), pd.Timestamp(m["val_start"])
    fit_set = feat[feat["timestamp"] < val_start]
    val_set = feat[(feat["timestamp"] >= val_start) & (feat["timestamp"] < split)]
    test = feat[feat["timestamp"] >= split].copy()
    log.info("Rows: fit %d | validation %d | test %d", len(fit_set), len(val_set), len(test))

    # 4. Train and forecast
    log.info("Step 4/5 Train XGBoost and forecast the test period")
    model = train_xgboost(fit_set, val_set, x_cols, target)
    log.info("Trees used: %d", model.best_iteration)
    test["pred_naive"] = test["lag_24"]              # baseline and production fallback
    test["pred_xgb"] = model.predict(test[x_cols])
    test["z_model"], test["anom_model"] = flag_anomalies(val_set, test, model, x_cols, target, "pred_xgb")

    # 5. Evaluate and save
    log.info("Step 5/5 Evaluate and save outputs")
    naive = evaluate_by_node(test, "pred_naive", target, peak)
    xgb = evaluate_by_node(test, "pred_xgb", target, peak)
    summary = pd.DataFrame({"Naive (yesterday)": naive.loc["ALL"], "XGBoost": xgb.loc["ALL"]}).T
    summary["MAE_skill_%"] = ((1 - summary["MAE"] / summary.loc["Naive (yesterday)", "MAE"]) * 100).round(1)

    reports = ROOT / "reports"
    forecasts = ROOT / "data" / "forecasts"
    models_dir = ROOT / "models"
    for folder in (reports, forecasts, models_dir):
        folder.mkdir(parents=True, exist_ok=True)

    summary.to_csv(reports / "metrics_summary.csv")
    xgb.to_csv(reports / "metrics_xgboost_by_node.csv")
    out_cols = ["clv_nodo", "timestamp", "hour", target, "pred_naive", "pred_xgb", "z_model", "anom_model"]
    test[out_cols].to_parquet(forecasts / "pipeline_predictions.parquet", index=False)
    model.save_model(models_dir / "xgboost_mae.json")

    log.info("Anomalies flagged: %.2f%% of test hours", test["anom_model"].mean() * 100)
    log.info("Results:\n%s", summary.to_string())
    log.info("Done. Outputs in reports/, data/forecasts/ and models/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monclova LMP forecasting pipeline")
    parser.add_argument("--skip-extract", action="store_true", help="reuse the saved dataset")
    main(parser.parse_args().skip_extract)
