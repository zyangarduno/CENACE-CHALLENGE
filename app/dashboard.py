import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Monclova LMP Forecast", layout="wide")
st.title("Monclova day-ahead price forecast")
st.caption("Prototype analyst view. Backtest on April–June 2025 (MDA prices, MXN/MWh), not a live forecast.")

@st.cache_data
def load():
    return pd.read_parquet("data/forecasts/test_predictions.parquet")

df = load()
models = {"XGBoost forecast": "pred_xgb", "Prophet forecast": "pred_prophet", "Naive forecast": "pred_naive"}
colors = {"Actual price": "#F5F5F5", "XGBoost forecast": "#FF9F1C",
          "Prophet forecast": "#2EC4B6", "Naive forecast": "#8D99AE"}

last_day = df["timestamp"].max().date()
node   = st.sidebar.selectbox("Node", sorted(df["clv_nodo"].unique()))
chosen = st.sidebar.multiselect("Models", list(models), default=["XGBoost forecast"])
period = st.sidebar.date_input("Period", (last_day - pd.Timedelta(days=13), last_day),
                               min_value=df["timestamp"].min().date(), max_value=last_day)

if len(period) == 2:
    d = df[(df["clv_nodo"] == node)
           & (df["timestamp"].dt.date >= period[0]) & (df["timestamp"].dt.date <= period[1])].copy()
    d = d.rename(columns={"pml": "Actual price", **{v: k for k, v in models.items()}})

    cols = st.columns(len(chosen) + 1)
    cols[0].metric("Average actual price", f"{d['Actual price'].mean():,.0f}")
    for c, name in zip(cols[1:], chosen):
        c.metric(f"{name}: average miss", f"{(d['Actual price'] - d[name]).abs().mean():,.0f}")

    fig = px.line(d, x="timestamp", y=["Actual price"] + chosen, color_discrete_map=colors,
                  labels={"value": "MXN/MWh", "variable": "", "timestamp": ""})
    flagged = d[d["anom_model"]].copy()
    fig.add_scatter(x=flagged["timestamp"], y=flagged["Actual price"], mode="markers",
                    marker=dict(size=9, color="red"), name="Anomaly")
    st.plotly_chart(fig, use_container_width=True)

    day = d[d["timestamp"].dt.date == period[1]]
    if len(day) and "XGBoost forecast" in d.columns:
        peak = day.loc[day["XGBoost forecast"].idxmax()]
        cheap = day.nsmallest(3, "XGBoost forecast")["timestamp"].dt.strftime("%H:%M").tolist()
        st.subheader(f"Day summary: {period[1]}")
        a, b = st.columns(2)
        a.metric("Forecast peak", f"{peak['XGBoost forecast']:,.0f} at {peak['timestamp']:%H:%M}")
        b.metric("Cheapest forecast hours", ", ".join(sorted(cheap)))

    st.subheader("Flagged anomalies")
    flagged["Miss (MXN/MWh)"] = (flagged["Actual price"] - flagged["XGBoost forecast"]).round(0)
    flagged["Direction"] = flagged["Miss (MXN/MWh)"].apply(lambda x: "above forecast" if x > 0 else "below forecast")
    table = flagged[["timestamp", "Actual price", "XGBoost forecast", "Miss (MXN/MWh)", "Direction", "z_model"]]
    st.dataframe(table.rename(columns={"z_model": "Deviation score"}).round(1),
                 use_container_width=True, hide_index=True)