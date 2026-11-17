# How to read and use the Monclova price forecast

*A one-page guide for analysts and operations teams.*

## What you receive each morning

For each of the nine Monclova nodes, a forecast of **tomorrow's 24 hourly day-ahead (MDA) prices**, in MXN per MWh, plus:

- a **color level** for every hour: Cheap, Medium or Expensive,
- the **recommended start time** for a flexible process, and what it would cost,
- **alerts** for hours where the actual price broke far away from the forecast.

The nine nodes move almost identically (a median gap of about 3 MXN/MWh), so for planning you can read any one of them as "the Monclova price."

## How to read the colors

The colors compare the hours **within that one day**, not against history:

| Color | Meaning | What to do |
|---|---|---|
| Cheap (green) | Among the 8 cheapest hours of the day | Schedule flexible, energy-heavy work here |
| Medium (yellow) | The middle 8 hours | Acceptable; prefer green if you can move |
| Expensive (red) | Among the 8 most expensive hours | Avoid running flexible loads; check alerts |

A "cheap" hour on an expensive day can still cost more than an "expensive" hour on a quiet day. Use the colors to choose **when** to run, and the price itself to estimate **how much** it will cost.

## How much to trust it

| Situation | Reliability | Typical miss |
|---|---|---|
| Night and morning hours | High | about 60–90 MXN/MWh |
| Afternoon | Good | about 100–140 MXN/MWh |
| **Evening, 19:00–21:00** | **Lower; tends to forecast too low** | about 270–410 MXN/MWh |
| Heat waves and grid emergencies | Low: these come from events the model can't see | can be several thousand |

Rules of thumb:

- **The order of the hours is more reliable than the exact price.** The forecast ranks the hours of a day well (rank agreement 0.79), which is what scheduling needs.
- **Treat the evening forecast as a minimum.** If a red hour is forecast at 900, the real price may be well above it.
- **Watch the news in spring.** In April–June 2024 prices reached 15 times their normal level during national grid emergencies. The forecast won't anticipate events like these.

## What an alert means

An alert marks an hour where the actual price came in much further from the forecast than usual for that time of day (more than 4 typical errors).

- **Most alerts are real market events,** not data errors: 92% of them hit all nine nodes at once, a sign of system-wide stress.
- **Almost all are upward:** prices higher than expected.
- **What to do:** check whether a process ran during that hour, note the cost impact, and treat several alerts in a row as a signal that the grid is under strain and the next days may also be expensive.

## Example: scheduling a flexible process

A 5 MW process that must run 4 hours in a row, once a day, at node 06MON-115 (backtest, April–June 2025):

| How the start time is chosen | Average price paid (MXN/MWh) |
|---|---|
| Always in the evening (18:00–22:00) | 1,007 |
| A fixed overnight timetable | 601 |
| **Following the forecast's recommended window** | **539** |
| Perfect knowledge of prices (best possible) | 511 |

Following the forecast cost 46% less than running in the evening and captured 94% of the best possible saving. Compared with a well-chosen fixed timetable, it saved about 10%.

Separately, in the same period the average price was about 30% lower on Sundays than on Tuesday to Friday, a useful fact for weekly processes.

## What this forecast is not

- **Not a trading signal.** A typical miss of about 20% of the price is fine for planning and too large for trading.
- **Not a guarantee for the evening peak** or for extreme events.
- **Not a real-time price.** It forecasts the day-ahead market (MDA); real-time (MTR) prices can differ.

## If something looks wrong

- **No forecast today:** the system publishes yesterday's prices as a fallback; plan with them and expect a larger error.
- **A forecast far from recent days, with no news to explain it:** report it before acting on it.
- **Frequent alerts for several days:** the model may need retraining. Notify the data team.

*Forecast model: XGBoost, retrained monthly. Data: CENACE public price service. Backtest results are for April–June 2025 and may differ in other seasons.*
