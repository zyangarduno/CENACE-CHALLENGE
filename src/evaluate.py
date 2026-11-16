"""Scoring rules shared by every model."""
import numpy as np
import pandas as pd


def evaluate(y_true, y_pred, hours, peak_hours):
    err = y_true - y_pred
    peak = hours.isin(peak_hours)
    return {
        "MAE": err.abs().mean(),
        "RMSE": np.sqrt((err ** 2).mean()),
        "MAE_peak": err[peak].abs().mean(),
    }


def evaluate_by_node(data, pred_col, target, peak_hours):
    rows = []
    for node, g in data.groupby("clv_nodo"):
        rows.append({"clv_nodo": node, **evaluate(g[target], g[pred_col], g["hour"], peak_hours)})
    rows.append({"clv_nodo": "ALL", **evaluate(data[target], data[pred_col], data["hour"], peak_hours)})
    return pd.DataFrame(rows).set_index("clv_nodo").round(1)
