# Chargeback Analytics (Streamlit)

## Overview

A lightweight Streamlit dashboard to explore **chargebacks** and related **fraud signals** from transaction data. You'll be able to:

- Track **chargeback trends** (daily/weekly).
- Slice by **payment method** and **amount ranges**.
- See **chargeback rate, $ amounts**, and **time-to-chargeback** distributions.
- Identify **top risky users** and **methods** driving losses.

This app is designed for portfolio use and mirrors workflows seen in fintech/e-commerce risk teams.

---

## Data Schema (CSV)

We'll use the already generate datasets:

- `transactions.csv`
  - `transaction_id (int)`
  - `user_id (int)`
  - `timestamp (datetime)`
  - `amount (float)`
  - `payment_method (str)`
  - `is_fraud (0/1)`
- `chargebacks.csv`
  - `transaction_id (int)`
  - `user_id (int)`
  - `amount (float)`
  - `days_after_purchase`

---

## Core **KPIs**

- **Chargeback Count** (by day/week, filtered).
- **Chargeback Rate** = `# chargeback txns / total txns` (in filter window).
- **Chargeback Amount ($)** - sum and average
- **Time to Chargeback** - distribution by bucket (0-10,11-30,31-60 days).
- **CB Rate by Payment Method** and **CB Amount by Method**.

## What the App Does (Features)

- **File input**: Load data from `data/` folder.
- **Filters (sidebar)**:
  - Date range (min-max from transactions).
  - Payment method multi-select.
  - Amount range slider.
- **KPI tiles**: CB count, CB rate, total CB $, avg CB $.
- **Charts**:
  - Timeseries: CB count & CB rate (toggle day/week).
  - Bar/heatmap: CB rate by payment method (and by week).
  - Histogram: time-to-chargeback buckets.
- **Tables**:
  - Top users by total CB amount and CB count.
- **Exports**:
  - Download filtered table as CSV.

---

## Project structure (suggested)

```
.
│── app.py
│── README.md            # (this file)
```
