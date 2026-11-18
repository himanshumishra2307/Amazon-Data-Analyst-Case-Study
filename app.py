import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Amazon Marketplace Analytics", page_icon="📦", layout="wide")

DATA = "data"


# ---------------------------------------------------------------
# 1. DATA LOADING + CLEANING (same logic as the Phase 1 notebook)
# ---------------------------------------------------------------
def parse_dates(col):
    return pd.to_datetime(col, format="mixed", errors="coerce")


@st.cache_data
def load_data():
    cust = pd.read_csv(f"{DATA}/amazon_customers.csv")
    orders = pd.read_csv(f"{DATA}/amazon_orders.csv")
    rev = pd.read_csv(f"{DATA}/amazon_revenue.csv")

    # Customers
    cust = cust.drop_duplicates("customer_id", keep="first")
    cust["email"] = cust["email"].str.replace(r"\s+at\s+", "@", regex=True)
    cust["membership_tier"] = cust["membership_tier"].fillna("Unknown")
    cust["city"] = cust["city"].astype(str).str.strip().str.title()
    cust["signup_date"] = parse_dates(cust["signup_date"])
    cust["is_prime"] = cust["membership_tier"].map(
        {"Prime": "Prime", "Prime Student": "Prime", "Non-Prime": "Non-Prime"}
    ).fillna("Unknown")

    # Orders
    orders = orders.drop_duplicates("order_id", keep="first")
    orders["unit_price_usd"] = pd.to_numeric(
        orders["unit_price_usd"].astype(str).str.replace(r"[$,]", "", regex=True),
        errors="coerce",
    )
    orders["order_status"] = orders["order_status"].fillna("Unknown")
    orders["order_date"] = parse_dates(orders["order_date"])
    orders["negative_qty_flag"] = orders["quantity"] < 0
    orders["quantity"] = orders["quantity"].abs()  # corrected, flag kept

    # Revenue: duplicate payments differ only by revenue_id -> keep one per order
    rev = rev.drop_duplicates("order_id", keep="first")
    rev["payment_date"] = parse_dates(rev["payment_date"])
    rev = rev.merge(orders[["order_id", "quantity", "unit_price_usd"]], on="order_id", how="left")
    rev["amount_recomputed"] = rev["amount_paid_usd"].isna()
    mask = rev["amount_paid_usd"].isna()
    rev.loc[mask, "amount_paid_usd"] = rev.loc[mask, "quantity"] * rev.loc[mask, "unit_price_usd"]
    rev = rev.drop(columns=["quantity", "unit_price_usd"])

    # Master table: LEFT JOIN keeps the unpaid orders visible
    df = (
        orders.merge(cust, on="customer_id", how="left")
        .merge(rev, on="order_id", how="left")
    )
    df["is_paid"] = df["revenue_id"].notna()
    df["amount_paid_usd"] = df["amount_paid_usd"].fillna(0)
    df["refund_amount_usd"] = df["refund_amount_usd"].fillna(0)
    df["net_revenue"] = df["amount_paid_usd"] - df["refund_amount_usd"]
    df["days_to_payment"] = (df["payment_date"] - df["order_date"]).dt.days
    df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    return df


df = load_data()

# ---------------------------------------------------------------
# 2. SIDEBAR FILTERS
# ---------------------------------------------------------------
st.sidebar.header("Filters")
tiers = st.sidebar.multiselect(
    "Membership tier", sorted(df["membership_tier"].unique()), default=sorted(df["membership_tier"].unique())
)
cats = st.sidebar.multiselect(
    "Product category", sorted(df["product_category"].unique()), default=sorted(df["product_category"].unique())
)
pays = st.sidebar.multiselect(
    "Payment method", sorted(df["payment_method"].unique()), default=sorted(df["payment_method"].unique())
)
cities = st.sidebar.multiselect(
    "City", sorted(df["city"].unique()), default=sorted(df["city"].unique())
)
d_min, d_max = df["order_date"].min().date(), df["order_date"].max().date()
date_range = st.sidebar.date_input("Order date range", (d_min, d_max), min_value=d_min, max_value=d_max)

f = df[
    df["membership_tier"].isin(tiers)
    & df["product_category"].isin(cats)
    & df["payment_method"].isin(pays)
    & df["city"].isin(cities)
]
if isinstance(date_range, tuple) and len(date_range) == 2:
    f = f[(f["order_date"].dt.date >= date_range[0]) & (f["order_date"].dt.date <= date_range[1])]

if f.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---------------------------------------------------------------
# 3. HEADER + KPIs
# ---------------------------------------------------------------
st.title("Amazon Marketplace Analytics")
st.caption("Category breadth, membership ROI and return-rate analytics · US marketplace · cleaned with pandas, queried in PostgreSQL")

total_orders = len(f)
gross = f["amount_paid_usd"].sum()
refunds = f["refund_amount_usd"].sum()
net = f["net_revenue"].sum()
gap_pct = (~f["is_paid"]).mean() * 100
refund_rate = refunds / gross * 100 if gross else 0
aov = gross / f["is_paid"].sum() if f["is_paid"].sum() else 0

k = st.columns(6)
k[0].metric("Total Orders", f"{total_orders:,}")
k[1].metric("Gross Revenue", f"${gross:,.0f}")
k[2].metric("Net Revenue", f"${net:,.0f}")
k[3].metric("Payment Gap %", f"{gap_pct:.1f}%")
k[4].metric("Refund Rate", f"{refund_rate:.1f}%")
k[5].metric("Avg Order Value", f"${aov:,.0f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Categories", "Membership ROI", "Payment Risk", "Trends", "Top Customers"]
)

# ---------------------------------------------------------------
# TAB 1: CATEGORIES
# ---------------------------------------------------------------
with tab1:
    cat = (
        f.groupby("product_category")
        .agg(orders=("order_id", "count"), gross=("amount_paid_usd", "sum"),
             refunds=("refund_amount_usd", "sum"), net=("net_revenue", "sum"))
        .reset_index()
    )
    cat["refund_rate_%"] = (cat["refunds"] / cat["gross"] * 100).round(1)
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(cat.sort_values("net"), x="net", y="product_category", orientation="h",
               title="Net revenue by category", labels={"net": "Net revenue (USD)", "product_category": ""}),
        width="stretch",
    )
    c2.plotly_chart(
        px.bar(cat.sort_values("refund_rate_%"), x="refund_rate_%", y="product_category", orientation="h",
               title="Refund rate by category (%)", labels={"refund_rate_%": "Refund rate %", "product_category": ""}),
        width="stretch",
    )
    st.subheader("Order status funnel")
    status = f["order_status"].value_counts().reset_index()
    status.columns = ["order_status", "orders"]
    st.plotly_chart(px.bar(status, x="order_status", y="orders", text="orders"), width="stretch")

# ---------------------------------------------------------------
# TAB 2: MEMBERSHIP ROI
# ---------------------------------------------------------------
with tab2:
    cust_ltv = (
        f.groupby(["customer_id", "membership_tier", "is_prime"])
        .agg(orders=("order_id", "count"), net=("net_revenue", "sum"))
        .reset_index()
    )
    tier = (
        cust_ltv.groupby("membership_tier")
        .agg(customers=("customer_id", "count"), avg_orders=("orders", "mean"), avg_ltv=("net", "mean"))
        .reset_index()
    )
    c1, c2 = st.columns(2)
    c1.plotly_chart(
        px.bar(tier, x="membership_tier", y="avg_ltv", text=tier["avg_ltv"].round(0),
               title="Avg net lifetime value per customer", labels={"avg_ltv": "Avg net LTV (USD)", "membership_tier": ""}),
        width="stretch",
    )
    c2.plotly_chart(
        px.bar(tier, x="membership_tier", y="avg_orders", text=tier["avg_orders"].round(2),
               title="Avg orders per customer", labels={"avg_orders": "Avg orders", "membership_tier": ""}),
        width="stretch",
    )
    st.caption("If Prime customers order more but net LTV is not proportionally higher, membership is not paying for itself.")
    st.dataframe(tier.round(2), width="stretch", hide_index=True)

# ---------------------------------------------------------------
# TAB 3: PAYMENT RISK
# ---------------------------------------------------------------
with tab3:
    pay = (
        f.groupby("payment_method")
        .agg(orders=("order_id", "count"), unpaid=("is_paid", lambda s: (~s).sum()),
             gross=("amount_paid_usd", "sum"), refunds=("refund_amount_usd", "sum"))
        .reset_index()
    )
    pay["payment_gap_%"] = (pay["unpaid"] / pay["orders"] * 100).round(2)
    pay["refund_rate_%"] = (pay["refunds"] / pay["gross"] * 100).round(2)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(pay, x="payment_method", y="payment_gap_%", title="Payment gap % by method"), width="stretch")
    c2.plotly_chart(px.bar(pay, x="payment_method", y="refund_rate_%", title="Refund rate % by method"), width="stretch")

    st.subheader("Net revenue: category × payment method")
    heat = f.pivot_table(index="product_category", columns="payment_method", values="net_revenue", aggfunc="sum")
    st.plotly_chart(px.imshow(heat, text_auto=".0f", aspect="auto", color_continuous_scale="Blues"), width="stretch")

    st.subheader("Unpaid orders (no payment record) by category and city")
    unpaid = f[~f["is_paid"]]
    u1, u2 = st.columns(2)
    u1.plotly_chart(px.bar(unpaid["product_category"].value_counts().reset_index(), x="product_category", y="count"), width="stretch")
    u2.plotly_chart(px.bar(unpaid["city"].value_counts().reset_index(), x="city", y="count"), width="stretch")

# ---------------------------------------------------------------
# TAB 4: TRENDS
# ---------------------------------------------------------------
with tab4:
    m = f.groupby("order_month").agg(gross=("amount_paid_usd", "sum"), net=("net_revenue", "sum")).reset_index()
    st.plotly_chart(
        px.line(m, x="order_month", y=["gross", "net"], title="Monthly revenue trend",
                labels={"value": "USD", "order_month": "", "variable": ""}),
        width="stretch",
    )
    by_city = f.groupby("city")["net_revenue"].sum().sort_values().reset_index()
    st.plotly_chart(px.bar(by_city, x="net_revenue", y="city", orientation="h", title="Net revenue by city"), width="stretch")

# ---------------------------------------------------------------
# TAB 5: TOP CUSTOMERS + ANOMALY
# ---------------------------------------------------------------
with tab5:
    top = (
        f.groupby(["customer_id", "customer_name", "membership_tier", "city"])
        .agg(orders=("order_id", "count"), net_ltv=("net_revenue", "sum"))
        .reset_index().sort_values("net_ltv", ascending=False).head(10)
    )
    st.subheader("Top 10 customers by net lifetime value")
    st.dataframe(top.round(2), width="stretch", hide_index=True)

    st.subheader("Refund anomaly: non-Returned orders with a refund")
    anom = f[(f["refund_amount_usd"] > 0) & (f["order_status"] != "Returned")]
    st.write(f"{len(anom):,} orders · ${anom['refund_amount_usd'].sum():,.0f} refunded")
    st.plotly_chart(px.bar(anom["product_category"].value_counts().reset_index(), x="product_category", y="count"), width="stretch")

with st.expander("Data cleaning decisions"):
    st.markdown(
        """
- Removed 166 duplicate customers and 166 duplicate orders (by ID); removed duplicate payment rows per order.
- Parsed three mixed date formats into one ISO date.
- Standardised city casing (30 spellings to 10 cities); repaired `" at "` emails.
- Stripped `$` from unit prices and cast to float; negative quantities flagged and corrected to absolute value.
- Blank membership tier / order status set to `Unknown`; missing paid amounts recomputed as quantity × unit price.
- Orders joined to payments with a LEFT JOIN so the payment gap stays visible.
"""
    )
