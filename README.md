# CENACE-CHALLENGE

Monclova LMP Forecasting
Day-ahead electricity price forecasting and anomaly detection for the nine CENACE pricing nodes of the Monclova load zone (Coahuila, Mexico), January 2024 – June 2025.

Live dashboard: https://cenace-challenge-tzqpi8grwfoqd8amtdpxve.streamlit.app/
Slides deck: https://canva.link/lt9hrg9bfanc93v

CONTEXT
CENACE (Centro Nacional de Control de Energía) is the air traffic control of Mexico’s electricity grid. It owns no power plants and sells no electricity. Its job is to:

*   Decide, every hour, which power plants run and how much each one produces, so supply matches demand exactly (electricity can’t be stored at scale, so this balance has to hold every second).
*   Keep the transmission network from overloading.
*   Run the wholesale electricity market (MEM, Mercado Eléctrico Mayorista) and publish its prices.

How the price gets set

*   Every power plant offers its energy at a price. Solar and wind are cheap (no fuel), combined-cycle gas is mid-priced, and old fuel-oil or peaker plants are expensive.
*   CENACE fills demand starting with the cheapest plants and moving up the list until demand is covered.
*   The last (most expensive) plant needed sets the price for everyone. (Precio Marginal Local: the cost of supplying one more MWh)

NOTE: Due to how prices are set it would make sense to see some patterns on the data such as daily, seasonal and spikes.

UNDERSTANDING THE DATA

*   A NodoP (pricing node) is a specific point on the grid, usually a substation, where CENACE calculates a price.

Each NodoP has a different price since other factors and components come in, such as:

*   Energy (pml_ene): the system-wide auction price, the same everywhere.
*   Losses (pml_per): wires waste energy as heat over distance. A node far from the cheap plants pays a bit more.
*   Congestion (pml_cng): if the transmission line into your area is full, CENACE can’t send you more cheap power and has to run a more expensive plant nearby. 

NOTE: Node’s price jump even though the system overall is fine.

*   A Zona de Carga is a group of nodes in one area. For this case we'll focus on Monclova.

WHO BENEFITS FROM THIS DATA

*   Large consumers (factories, retail chains, data centers) that buy electricity in the wholesale market, or through suppliers that pass the price on. Electricity can be one of their biggest operating costs.
*  Generators, deciding when to run, and developers deciding where to build (high-congestion nodes signal where new plants or batteries would earn the most). 
*   Traders and suppliers pricing contracts and hedges.
*   Planners, spotting where the grid is under strain.

NOTE: A high prediction accuracy on real time would bring a lot of value to these users. 

VALUE & PERSPECTIVE

*   Cost management and reduction: Access to information can allow user to move flexible processes to cheapest hours. On a procurement side gives visibility to price supply contracts. 
*   Peaks and spikes matter: Average hours are easy to predict but users can find real value when such scenarios are predicted. 
*   Risk control value: Prediction intervals can add more value than just a simple price prediction during a certain date and time, this wil actually turn a forecast into a risk tool. 
*   Timing importance: Timing here is key so data adds value and can be helpfull for users, the more in the future they can look at the better for their planing processes.
*   Anomaly detection: Early warnings about possible congestions, unusual prices or bad data potentially polluting the reports are important to detect so the tool adds more value to users.

NOT IN THE SCOPE OF THIS CHALLENGE BUT IMPORTANT TO BE AWARE OF: A forecasting tool based only on this database will not foresee dissasters such as a plant failures. Collecting additional data on site through interviews related to this type of issues is highly recommended. 

CHALLENGE OBJECTIVES

Build a reproducible, production-ready analytics pipeline for the Local Marginal Price (LMP) of the nine Monclova load-zone nodes (Jan 1, 2024 – Jun 30, 2025). 

RESULTS AT GLANCE

Results at a glance

Test period: April 1 – June 30, 2025 (data the models never saw), all 9 nodes. Errors in MXN/MWh. Peak hours = 18:00–21:59.

Model	MAE	RMSE	Peak MAE	MAE vs. baseline
XGBoost, absolute-error objective (selected)	129.1	233.1	294.1	23.5% better
Naive baseline: same hour yesterday	168.8	284.9	375.2	baseline
XGBoost, default squared-error objective	175.3	249.3	305.3	3.9% worse

Naive: same hour last week	205.6	336.5	450.2	21.8% worse
Prophet, with lagged prices as regressors	231.5	298.1	429.2	37.1% worse
Anomaly detection: 1.05% of test hours flagged; 92% of flagged hours hit all nine nodes at once.
Business value: scheduling a flexible 4-hour process in the window the forecast marks as cheapest cost 46% less than running it in the evening, and captured 94% of the saving perfect knowledge of prices would have given. Against a well-chosen fixed overnight timetable, the forecast saved about 10%.

WHAT WAS BUILT

Extraction:	Downloads MDA prices from the CENACE SW-PML web service in 7-day chunks (79 requests), with retries and backoff; resumable
Data checks: Confirms 9 nodes, no duplicate node-hours, equal hours per node, and that price components add up to the price
Exploratory analysis: Daily, weekly, and seasonal patterns; spikes; congestion; differences between nodes
Forecasting	Naive baselines, XGBoost (one model for all nodes), and Prophet (one model per node), compared on the same day ahead task
Anomaly detection: Flags hours where the actual price is far from the forecast for that hour of day; a second, model-free method for comparison

HOW TO RUN

# 1. Create and activate an environment
python -m venv arkham-env
arkham-env\Scripts\activate          
# source arkham-env/bin/activate     

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline
python run_pipeline.py                  
python run_pipeline.py --skip-extract   

# 4. Open the dashboard locally
streamlit run app/dashboard.py 

LIVE DASHBOARD
https://cenace-challenge-tzqpi8grwfoqd8amtdpxve.streamlit.app/

TO REPRODUCE
pip install -r requirements.txt
streamlit run app/dashboard.py

REPOSITORY STRUCTURE
├── config.yaml            settings: API, nodes, dates, modeling parameters
├── run_pipeline.py        one command for the full pipeline
├── src/                   reusable code imported by the pipeline
│   ├── config.py          loads config.yaml
│   ├── extract.py         API calls, chunking, retries, parsing, data checks
│   ├── features.py        calendar and lag features (shared by training and forecasting)
│   ├── evaluate.py        MAE, RMSE, peak MAE, per-node scoring
│   └── models.py          XGBoost training and anomaly flags
├── notebooks/             the analysis, step by step
├── app/                   Streamlit dashboard
├── data/
│   ├── reference/         CENACE node catalog
│   ├── processed/         clean hourly dataset (Parquet)
│   └── forecasts/         model predictions used by the dashboard
├── models/                saved model
├── reports/               metrics tables
└── docs/                  analyst guide


LIMITS

The model under-predicts sharp evening peaks, where its average miss is 267–413 MXN/MWh.
Extreme spikes, like those of the April–June 2024 heat wave, come from events not present in price history (weather, demand, plant outages).
The test period contains no extreme spikes, so errors in a heat-wave season would be larger.
The forecast is a single number, not a range.
Business-value figures come from a backtest on one node and assume a load that can move freely within the day.
The dashboard shows backtest results for April – June 2025; it is not connected to live daily data.

NEXT STEPS
Add weather and national demand forecasts as inputs, to address the evening peaks.
Publish a forecast range (for example, quantile regression) alongside the point forecast.
Evaluate with walk-forward backtesting (retrain and test day by day).
Schedule the pipeline daily, with monthly retraining and alert delivery.
Add real-time (MTR) prices and compare them with day-ahead forecasts.
