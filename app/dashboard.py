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

# ---------------------------------------------------------------- Day planner
st.divider()
st.header("Day planner")
st.caption("Forecast for one day, colored by price level, and the cheapest window for a flexible load.")

p1, p2, p3 = st.columns(3)
plan_day  = p1.date_input("Day", df["timestamp"].max().date(),
                          min_value=df["timestamp"].min().date(), max_value=df["timestamp"].max().date(),
                          key="plan_day")
load_mw   = p2.number_input("Flexible load (MW)", min_value=0.1, value=5.0, step=0.5)
run_hours = p3.slider("Hours it needs to run", 1, 12, 4)

day = df[(df["clv_nodo"] == node) & (df["timestamp"].dt.date == plan_day)].sort_values("timestamp").reset_index(drop=True)

if len(day) == 24:
    # Price level of each hour, relative to that day's own forecast
    low, high = day["pred_xgb"].quantile([1/3, 2/3])
    day["Level"] = day["pred_xgb"].apply(lambda v: "Cheap" if v <= low else ("Expensive" if v > high else "Medium"))
    day["Hour"] = day["timestamp"].dt.strftime("%H:%M")

    fig_day = px.bar(day, x="Hour", y="pred_xgb", color="Level",
                     color_discrete_map={"Cheap": "#2EC4B6", "Medium": "#FFD166", "Expensive": "#EF476F"},
                     category_orders={"Hour": day["Hour"].tolist(), "Level": ["Cheap", "Medium", "Expensive"]},
                     labels={"pred_xgb": "Forecast price (MXN/MWh)"})
    fig_day.add_scatter(x=day["Hour"], y=day["pml"], mode="lines+markers", name="Actual price",
                        line=dict(color="#F5F5F5"))
    st.plotly_chart(fig_day, use_container_width=True)

    # Cheapest consecutive window according to the forecast
    starts = range(0, 24 - run_hours + 1)
    best  = min(starts, key=lambda s: day["pred_xgb"].iloc[s:s + run_hours].sum())
    worst = max(starts, key=lambda s: day["pred_xgb"].iloc[s:s + run_hours].sum())
    energy = load_mw * run_hours                                   # MWh for the run

    cost_best  = day["pml"].iloc[best:best + run_hours].mean()  * energy    # what it really cost
    cost_worst = day["pml"].iloc[worst:worst + run_hours].mean() * energy

    c1, c2, c3 = st.columns(3)
    c1.metric("Recommended start", day["Hour"].iloc[best])
    c2.metric("Cost in recommended window", f"{cost_best:,.0f} MXN")
    c3.metric("Saved vs. most expensive window", f"{cost_worst - cost_best:,.0f} MXN",
              f"{(1 - cost_best / cost_worst) * 100:.0f}% lower" if cost_worst > 0 else None)
    st.caption(f"Window chosen from the forecast, cost measured with actual prices (backtest). "
               f"Most expensive forecast window starts at {day['Hour'].iloc[worst]}.")
else:
    st.info("No complete day of data for this date.")    