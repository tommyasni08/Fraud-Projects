# Stage 1 Foundation Write-up

## 1. Introduction (Context & Objective)

- Fraud/chargebacks are major costs for merchants.
- Goal: Analyze transaction and login data to **identify anomalies** and **quantify chargeback trends**.
- Two deliverables: (a) anomaly-detection EDA, (b) interactive dashboard.

---

## 2. Exploratory Data Analysis (EDA) & Anomaly Detection

- **Login anomalies**: unusual number of logins per user; flagged outlier.
- **Distinct IP patterns**: some accounts logged in from many IPs, possibly account sharing or credential stuffing.
- **Transaction amounts**: long-tailed distribution; clipping top 0.5% highlights normal spending vs extreme spikes.
- **Payment method fraud rates**: some payment methods had significantly higher chargeback ratios
- **User-level scatterplots**: high-spend users sometimes had elevated fraud rates - a red flag for "big-ticket" fraud attempts.
- **Login failures vs. fraud correlation**: modest correlation between high failure rates, many unique IPs, and fraud-prone accounts.

Takeaway: EDA surfaces **suspicious cluters of behaviour** and highlights **key risk drivers** (method, amount, login/IP patterns)

---

## 3. Dashboard Development (Chargeback Analytics)

Built a **Streamlit + Plotly app** to make these insights operational:

- **Filters**: date range, payment method, transaction amount, and granularity (daily/weekly).
- **KPIs**: chargeback count, rate, total $ lost, average chargeback amount.
- **Trend chart**: chargeback count (bar) vs chargeback rate (line) over time.
- **Breakdown by payment method**: sortable bar chart + CSV export.
- **Time-to-chargeback distribution**: how many days after purchase disputes occur (0-10,11-30,31-60, >60).
- **Top users**: by total chargeback $ and by count, with exportable tables.
- **Usability**: handles empty data gracefully, includes expander "About" sections, and downloadable CSVs for reporting.

Takeaway: The dashboard enables **risk analyts** to slice data, monitor KPIs, and export tables - bridging analytics and business use.

---

## Closing Line

This **Stage 1** project provided a **full fraud-analytics pipeline**: anomaly detection, EDA storytelling, and a self-service dashboard. It uncovered actionable insights (e.g. risky payment methods, user anomalies, time-to-chargeback patterns) and laid the foundation for a predictive **fraud model**.
