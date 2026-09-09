import pandas as pd
import streamlit as st
import plotly.express as px


@st.cache_data
def load_data():
    df = pd.read_csv("inventory_data.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_data()

st.set_page_config(
    page_title="Inventory and Store Performance Dashboard",
    page_icon="📦",
    layout="wide",
)

st.title("Inventory and Store Performance Dashboard")
st.caption("A simple sample dashboard for sales, inventory, and store performance.")

# Sidebar filters
st.sidebar.header("Filters")
store_options = sorted(df["store"].unique())
category_options = sorted(df["category"].unique())
min_date = df["date"].min().date()
max_date = df["date"].max().date()

selected_stores = st.sidebar.multiselect("Store", store_options, default=store_options)
selected_categories = st.sidebar.multiselect("Category", category_options, default=category_options)
start_date, end_date = st.sidebar.date_input(
    "Date",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

filtered_df = df[
    df["store"].isin(selected_stores)
    & df["category"].isin(selected_categories)
    & df["date"].dt.date.between(start_date, end_date)
]

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

# KPI cards
revenue_total = filtered_df["revenue"].sum()
units_sold_total = filtered_df["units_sold"].sum()
avg_stock = filtered_df["stock_on_hand"].mean()
orders_total = filtered_df["orders"].sum()
return_rate = (filtered_df["returns"].sum() / units_sold_total) * 100 if units_sold_total else 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Revenue", f"${revenue_total:,.0f}")
col2.metric("Units Sold", f"{units_sold_total:,}")
col3.metric("Avg. Stock", f"{avg_stock:,.0f}")
col4.metric("Total Orders", f"{orders_total:,}")
col5.metric("Return Rate", f"{return_rate:.1f}%")

# Charts
st.subheader("Sales and Inventory Overview")

monthly_sales = filtered_df.groupby("date")["revenue"].sum().reset_index()
store_sales = (
    filtered_df.groupby("store", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
)
category_sales = (
    filtered_df.groupby("category", as_index=False)["units_sold"].sum().sort_values("units_sold", ascending=False)
)

chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    st.write("Monthly Revenue")
    st.line_chart(monthly_sales.set_index("date")["revenue"])

with chart_col2:
    st.write("Revenue by Store")
    st.bar_chart(store_sales.set_index("store")["revenue"])

with chart_col3:
    st.write("Units Sold by Category")
    st.bar_chart(category_sales.set_index("category")["units_sold"])

# Inventory section
st.subheader("Inventory Alerts")

inventory_summary = (
    filtered_df.groupby(["store", "product"], as_index=False)
    .agg(
        stock_on_hand=("stock_on_hand", "max"),
        units_sold=("units_sold", "sum"),
        revenue=("revenue", "sum"),
    )
    .sort_values("stock_on_hand")
)

low_stock = inventory_summary[inventory_summary["stock_on_hand"] < 250].copy()
reorder_needed = inventory_summary[inventory_summary["stock_on_hand"] < 200].copy()

low_stock_col, reorder_col = st.columns(2)

with low_stock_col:
    st.write("Low-Stock Products")
    if low_stock.empty:
        st.info("No products are currently low in stock.")
    else:
        st.dataframe(low_stock, use_container_width=True)

with reorder_col:
    st.write("Products Needing Reorder")
    if reorder_needed.empty:
        st.info("No products currently need reordering.")
    else:
        st.dataframe(reorder_needed, use_container_width=True)

# Store performance section
st.subheader("Store Performance")

store_performance = (
    filtered_df.groupby("store", as_index=False)
    .agg(
        revenue=("revenue", "sum"),
        units_sold=("units_sold", "sum"),
        profit=("revenue", "sum")
    )
)

# Use a simple profit estimate: revenue minus 60% cost
store_performance["profit"] = store_performance["revenue"] * 0.4

store_performance = store_performance.sort_values("revenue", ascending=False)
best_store = store_performance.iloc[0]

st.success(f"Best-performing store: {best_store['store']} with ${best_store['revenue']:,.0f} in revenue.")

store_chart = px.bar(
    store_performance,
    x="store",
    y="revenue",
    color="store",
    title="Revenue by Store",
    labels={"store": "Store", "revenue": "Revenue ($)"},
)

st.plotly_chart(store_chart, use_container_width=True)

store_metrics_col1, store_metrics_col2, store_metrics_col3 = st.columns(3)

with store_metrics_col1:
    st.write("Revenue by Store")
    st.dataframe(store_performance[["store", "revenue"]], use_container_width=True)

with store_metrics_col2:
    st.write("Units Sold by Store")
    units_by_store = filtered_df.groupby("store", as_index=False)["units_sold"].sum()
    st.dataframe(units_by_store, use_container_width=True)

with store_metrics_col3:
    st.write("Profit by Store")
    profit_by_store = store_performance[["store", "profit"]].copy()
    st.dataframe(profit_by_store, use_container_width=True)

# Data table
st.subheader("Sample Inventory Data")
st.dataframe(filtered_df, use_container_width=True)
