"""Selected model (XGBoost, absolute-error objective) and forecast-based anomaly flags."""
from xgboost import XGBRegressor


def train_xgboost(fit_set, val_set, x_cols, target):
    model = XGBRegressor(
        objective="reg:absoluteerror",   # robust to extreme spikes; matches MAE
        eval_metric="mae",
        n_estimators=2000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=50,
        random_state=42,
    )
    model.fit(fit_set[x_cols], fit_set[target],
              eval_set=[(val_set[x_cols], val_set[target])], verbose=False)
    return model


def flag_anomalies(val_set, data, model, x_cols, target, pred_col, k=4):
    """Flag hours whose miss is more than k typical errors for that hour of day.
    The typical error per hour comes from the validation set."""
    val_resid = val_set[target] - model.predict(val_set[x_cols])
    by_hour = val_resid.groupby(val_set["hour"])
    median = by_hour.median()
    scale = by_hour.apply(lambda s: 1.4826 * (s - s.median()).abs().median())

    resid = data[target] - data[pred_col]
    z = (resid - data["hour"].map(median)) / data["hour"].map(scale)
    return z, z.abs() > k
