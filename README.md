# CENACE-CHALLENGE
CENACE (Centro Nacional de Control de Energía) is the air traffic control of Mexico’s electricity grid. It owns no power plants and sells no electricity. Its job is to:

*   Decide, every hour, which power plants run and how much each one produces, so supply matches demand exactly (electricity can’t be stored at scale, so this balance has to hold every second).
*   Keep the transmission network from overloading.
*   Run the wholesale electricity market (MEM, Mercado Eléctrico Mayorista) and publish its prices.

The 2025 energy reform kept this role. Under the new Ley del Sector Eléctrico, CENACE, as the independent system operator, will continue operating the national grid, administering the Wholesale Electricity Market and determining the works needed to expand it. The new law also established CFE’s prevalence in generation (at least 54 percent) and confirmed the existence of the MEM under state direction. The market and its price data still exist. The rules around them have shifted.

How the price gets set (the key idea)
Imagine CENACE running an auction every hour:

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

USE YAML TO CHANGE CONFIGURATION

LIVE DASHBOARD
https://cenace-challenge-tzqpi8grwfoqd8amtdpxve.streamlit.app/

TO REPRODUCE
pip install -r requirements.txt
streamlit run app/dashboard.py