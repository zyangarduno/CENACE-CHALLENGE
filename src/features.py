"""Feature engineering. The same function is used for training and for forecasting."""
import holidays

CALENDAR = ["hour", "weekday", "month", "is_weekend", "is_holiday"]
MX_HOLIDAYS = holidays.Mexico(years=range(2024, 2028))


def feature_names(lags):
    return CALENDAR + [f"lag_{lag}" for lag in lags] + ["roll_mean_24", "roll_max_24", "node_id"]


def add_features(df, target, lags, nodes):
    """Calendar + lag features. All price features use data >= 24h old (day-ahead rule)."""
    df = df.sort_values(["clv_nodo", "timestamp"]).copy()
    ts = df["timestamp"]

    df["hour"] = ts.dt.hour
    df["weekday"] = ts.dt.dayofweek
    df["month"] = ts.dt.month
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["is_holiday"] = ts.dt.date.isin(MX_HOLIDAYS).astype(int)

    g = df.groupby("clv_nodo")[target]
    for lag in lags:
        df[f"lag_{lag}"] = g.shift(lag)
    df["roll_mean_24"] = g.transform(lambda s: s.shift(24).rolling(24).mean())
    df["roll_max_24"] = g.transform(lambda s: s.shift(24).rolling(24).max())

    node_map = {node: i for i, node in enumerate(sorted(nodes))}
    df["node_id"] = df["clv_nodo"].map(node_map)
    return df.dropna(subset=feature_names(lags)).reset_index(drop=True)
