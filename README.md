# Amazon Marketplace Analytics Dashboard

Interactive Streamlit dashboard built from a 3-table Amazon case study (customers, orders, revenue).

**Live app:** <paste your Streamlit link here>

## What it answers
- Which categories drive profitable net revenue after refunds
- Whether Prime / Prime Student customers generate higher net lifetime value
- Which payment methods carry the highest payment-gap and refund risk
- How the 493 unpaid orders are distributed by category and city
- Monthly revenue trend, top customers, refund anomalies

## Stack
Python (pandas, Plotly) · PostgreSQL (business queries) · Streamlit

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
