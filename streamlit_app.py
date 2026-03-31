"""
E-Commerce Analytics Project
dashboard/streamlit_app.py
Interactive web dashboard — run with: streamlit run dashboard/streamlit_app.py
Requires: pip install streamlit plotly pandas
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PATHS ─────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT  = os.path.join(DATA, "analysis_outputs")

# ── CHECK PLOTLY ──────────────────────────────────────────────
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ── LOAD DATA ─────────────────────────────────────────────────
@st.cache_data
def load_all():
    orders      = pd.read_csv(f"{DATA}/orders.csv",      parse_dates=["order_date"])
    products    = pd.read_csv(f"{DATA}/products.csv")
    customers   = pd.read_csv(f"{DATA}/customers.csv",   parse_dates=["registration_date"])
    returns     = pd.read_csv(f"{DATA}/returns.csv",     parse_dates=["return_date"])
    order_items = pd.read_csv(f"{DATA}/order_items.csv")
    rfm         = pd.read_csv(f"{OUT}/rfm_scores.csv")
    rfm_seg     = pd.read_csv(f"{OUT}/rfm_segments.csv")
    monthly     = pd.read_csv(f"{OUT}/monthly_revenue.csv", parse_dates=["order_date"])
    cat_perf    = pd.read_csv(f"{OUT}/category_performance.csv")
    forecast    = pd.read_csv(f"{OUT}/revenue_forecast.csv")
    churn       = pd.read_csv(f"{OUT}/churn_predictions.csv")
    clv         = pd.read_csv(f"{OUT}/clv_predictions.csv")
    top_prods   = pd.read_csv(f"{OUT}/top_products.csv")
    with open(f"{OUT}/churn_model_metrics.json") as f:
        churn_metrics = json.load(f)
    return (orders, products, customers, returns, order_items,
            rfm, rfm_seg, monthly, cat_perf, forecast, churn, clv, top_prods, churn_metrics)

# ── CHECK DATA EXISTS ─────────────────────────────────────────
if not os.path.exists(f"{DATA}/orders.csv"):
    st.error("⚠️ Data not found. Please run the pipeline first:")
    st.code("python run_all.py")
    st.stop()

(orders, products, customers, returns, order_items,
 rfm, rfm_seg, monthly, cat_perf, forecast, churn, clv, top_prods, churn_metrics) = load_all()

# ── DERIVED METRICS ───────────────────────────────────────────
delivered = orders[orders["status"] != "Cancelled"]
total_rev    = delivered["order_total"].sum()
total_orders = delivered["order_id"].nunique()
total_cust   = delivered["customer_id"].nunique()
aov          = total_rev / total_orders
total_units  = order_items.merge(delivered[["order_id"]], on="order_id")["quantity"].sum()
return_rate  = len(returns) / len(delivered[delivered["status"] == "Delivered"]) * 100
canc_rate    = (orders["status"] == "Cancelled").sum() / len(orders) * 100

# ── CUSTOM CSS ────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetric"] { background: #F0F4F8; border-radius: 10px; padding: 12px 16px; border-left: 3px solid #00B4D8; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #718096 !important; }
[data-testid="stMetricValue"] { font-size: 24px !important; color: #0D1B2A !important; font-weight: 700 !important; }
.block-container { padding-top: 1.5rem; }
h1 { color: #0D1B2A; }
h2 { color: #1B5E8B; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; }
h3 { color: #0D1B2A; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SIDEBAR — FILTERS
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=60)
    st.title("🛒 E-Commerce\nAnalytics")
    st.caption("Portfolio Project — SQL · Python · Excel · Power BI")
    st.divider()

    st.subheader("🔧 Filters")
    years = sorted(orders["order_date"].dt.year.unique())
    sel_years = st.multiselect("Year", years, default=years)

    countries = sorted(orders["country"].dropna().unique())
    sel_countries = st.multiselect("Country", countries, default=countries)

    channels = sorted(orders["channel"].dropna().unique())
    sel_channels = st.multiselect("Channel", channels, default=channels)

    st.divider()
    st.caption(f"**Data period:** Jan 2022 – Dec 2024")
    st.caption(f"**Generated:** Synthetic data, seed=42")

# ── APPLY FILTERS ─────────────────────────────────────────────
mask = (
    orders["order_date"].dt.year.isin(sel_years) &
    orders["country"].isin(sel_countries) &
    orders["channel"].isin(sel_channels)
)
orders_f   = orders[mask]
delivered_f = orders_f[orders_f["status"] != "Cancelled"]

# ══════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════
page = st.sidebar.radio(
    "📄 Page",
    ["📊 Executive Overview", "📈 Revenue Trends", "🗂 Products", "👥 Customers", "↩ Returns", "🧠 ML Models"],
    index=0,
)

# ══════════════════════════════════════════════════════════════
# PAGE 1: EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════
if page == "📊 Executive Overview":
    st.title("📊 Executive Overview")
    st.caption(f"Filtered to: {', '.join(map(str, sel_years))} | {len(sel_countries)} countries | {len(sel_channels)} channels")

    # KPI row
    k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
    frev   = delivered_f["order_total"].sum()
    fords  = delivered_f["order_id"].nunique()
    fcust  = delivered_f["customer_id"].nunique()
    faov   = frev / fords if fords else 0
    fcanc  = (orders_f["status"] == "Cancelled").sum() / len(orders_f) * 100 if len(orders_f) else 0
    fret_d = orders_f[orders_f["status"] == "Delivered"]["order_id"]
    fret_r = returns[returns["order_id"].isin(fret_d)]
    fret_rate = len(fret_r) / len(fret_d) * 100 if len(fret_d) else 0

    k1.metric("💰 Revenue", f"₹{frev/1e7:.1f}Cr")
    k2.metric("📦 Orders", f"{fords:,}")
    k3.metric("👥 Customers", f"{fcust:,}")
    k4.metric("🛍 AOV", f"₹{faov:,.0f}")
    k5.metric("📊 Products", f"{products['is_active'].sum()}")
    k6.metric("↩ Return Rate", f"{fret_rate:.1f}%")
    k7.metric("❌ Cancellations", f"{fcanc:.1f}%")
    k8.metric("💳 Coupons", f"{delivered_f['coupon_used'].mean()*100:.0f}%")

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Monthly Revenue")
        monthly_f = (delivered_f
                     .set_index("order_date")
                     .resample("ME")["order_total"]
                     .sum()
                     .reset_index())
        monthly_f.columns = ["Month", "Revenue (₹M)"]
        monthly_f["Revenue (₹M)"] = monthly_f["Revenue (₹M)"] / 1e6
        if HAS_PLOTLY:
            fig = px.area(monthly_f, x="Month", y="Revenue (₹M)",
                          color_discrete_sequence=["#00B4D8"],
                          template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(monthly_f.set_index("Month"))

    with col2:
        st.subheader("Order Status")
        status_counts = orders_f["status"].value_counts()
        if HAS_PLOTLY:
            fig = px.pie(values=status_counts.values, names=status_counts.index,
                         color_discrete_sequence=["#2DC653","#00B4D8","#F4A261","#E63946"],
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(status_counts)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Revenue by Channel")
        ch = delivered_f.groupby("channel")["order_total"].sum().sort_values(ascending=True) / 1e6
        if HAS_PLOTLY:
            fig = px.bar(x=ch.values, y=ch.index, orientation="h",
                         labels={"x": "Revenue (₹M)", "y": ""},
                         color_discrete_sequence=["#1B5E8B"], template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(ch)

    with col4:
        st.subheader("Revenue by Country")
        ctry = delivered_f.groupby("country")["order_total"].sum().sort_values(ascending=False).head(8) / 1e6
        if HAS_PLOTLY:
            fig = px.bar(x=ctry.index, y=ctry.values,
                         labels={"x": "", "y": "Revenue (₹M)"},
                         color_discrete_sequence=["#6C3483"], template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(ctry)

# ══════════════════════════════════════════════════════════════
# PAGE 2: REVENUE TRENDS
# ══════════════════════════════════════════════════════════════
elif page == "📈 Revenue Trends":
    st.title("📈 Revenue Trends & Forecast")

    # Forecast chart
    st.subheader("Actual vs Forecast (₹M)")
    fc_act  = forecast[forecast["type"] == "actual"].copy()
    fc_fore = forecast[forecast["type"] == "forecast"].copy()
    fc_act["revenue_m"]  = fc_act["revenue"] / 1e6
    fc_fore["revenue_m"] = fc_fore["forecast_revenue"] / 1e6

    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fc_act["ym"], y=fc_act["revenue_m"],
                                  mode="lines+markers", name="Actual",
                                  line=dict(color="#00B4D8", width=2)))
        fig.add_trace(go.Bar(x=fc_fore["ym"], y=fc_fore["revenue_m"],
                              name="Forecast", marker_color="#2DC653", opacity=0.75))
        fig.update_layout(template="plotly_white", margin=dict(t=20, b=20),
                          legend=dict(orientation="h"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(fc_act.set_index("ym")["revenue_m"])
        st.bar_chart(fc_fore.set_index("ym")["revenue_m"])

    # MoM growth
    monthly_f = (delivered_f
                 .set_index("order_date")
                 .resample("ME")["order_total"]
                 .sum()
                 .reset_index())
    monthly_f.columns = ["Month", "Revenue"]
    monthly_f["MoM Growth %"] = monthly_f["Revenue"].pct_change() * 100
    monthly_f["Revenue (₹M)"] = monthly_f["Revenue"] / 1e6

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Month-over-Month Growth %")
        if HAS_PLOTLY:
            fig = px.bar(monthly_f.dropna(), x="Month", y="MoM Growth %",
                         color="MoM Growth %",
                         color_continuous_scale=["#E63946", "#F4A261", "#2DC653"],
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(monthly_f.set_index("Month")["MoM Growth %"])

    with col2:
        st.subheader("Revenue by Payment Method")
        pay = delivered_f.groupby("payment_method")["order_total"].sum().sort_values(ascending=False) / 1e6
        if HAS_PLOTLY:
            fig = px.bar(x=pay.index, y=pay.values,
                         labels={"x": "", "y": "Revenue (₹M)"},
                         color_discrete_sequence=["#1B5E8B"], template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(pay)

# ══════════════════════════════════════════════════════════════
# PAGE 3: PRODUCTS
# ══════════════════════════════════════════════════════════════
elif page == "🗂 Products":
    st.title("🗂 Product Analytics")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenue by Category (₹M)")
        cat_sorted = cat_perf.sort_values("revenue", ascending=True)
        if HAS_PLOTLY:
            fig = px.bar(cat_sorted, x="revenue", y="category", orientation="h",
                         color="gp_margin", color_continuous_scale="Teal",
                         labels={"revenue": "Revenue (₹)", "category": ""},
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cat_sorted.set_index("category")["revenue"])

    with col2:
        st.subheader("Gross Profit Margin % by Category")
        if HAS_PLOTLY:
            fig = px.bar(cat_sorted, x="gp_margin", y="category", orientation="h",
                         color_discrete_sequence=["#2DC653"], template="plotly_white",
                         labels={"gp_margin": "GP Margin %", "category": ""})
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(cat_sorted.set_index("category")["gp_margin"])

    st.subheader("Top 20 Products by Revenue")
    top20 = top_prods.head(20).copy()
    top20["revenue_m"] = (top20["revenue"] / 1e6).round(2)
    st.dataframe(
        top20[["product_name", "category", "brand", "units_sold", "revenue_m"]]
        .rename(columns={"product_name": "Product", "category": "Category",
                         "brand": "Brand", "units_sold": "Units Sold",
                         "revenue_m": "Revenue (₹M)"}),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Inventory Health")
    inv = products[["product_name","category","stock_quantity","is_active"]].copy()
    inv["Status"] = pd.cut(inv["stock_quantity"],
                           bins=[-1, 0, 10, 50, 9999999],
                           labels=["Out of Stock","Critical","Low Stock","Healthy"])
    status_counts = inv["Status"].value_counts()
    col3, col4, col5, col6 = st.columns(4)
    col3.metric("✅ Healthy",       int(status_counts.get("Healthy", 0)))
    col4.metric("⚠️ Low Stock",     int(status_counts.get("Low Stock", 0)))
    col5.metric("🔴 Critical",      int(status_counts.get("Critical", 0)))
    col6.metric("⛔ Out of Stock",  int(status_counts.get("Out of Stock", 0)))

# ══════════════════════════════════════════════════════════════
# PAGE 4: CUSTOMERS
# ══════════════════════════════════════════════════════════════
elif page == "👥 Customers":
    st.title("👥 Customer Analytics")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("RFM Segment Revenue (₹M)")
        rfm_sorted = rfm_seg.sort_values("total_rev", ascending=True).copy()
        rfm_sorted["total_rev_m"] = rfm_sorted["total_rev"] / 1e6
        if HAS_PLOTLY:
            PALETTE = ["#0D1B2A","#1B5E8B","#00B4D8","#2DC653","#F4A261","#E63946","#6C3483"]
            fig = px.bar(rfm_sorted, x="total_rev_m", y="segment", orientation="h",
                         color="segment", color_discrete_sequence=PALETTE,
                         labels={"total_rev_m": "Revenue (₹M)", "segment": ""},
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(rfm_sorted.set_index("segment")["total_rev_m"])

    with col2:
        st.subheader("Customer Distribution by Segment")
        if HAS_PLOTLY:
            fig = px.pie(rfm_seg, values="customers", names="segment",
                         color_discrete_sequence=["#0D1B2A","#1B5E8B","#00B4D8","#2DC653","#F4A261","#E63946","#6C3483"],
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(rfm_seg.set_index("segment")["customers"])

    st.subheader("RFM Segment Detail")
    display_rfm = rfm_seg.copy()
    display_rfm["total_rev"] = (display_rfm["total_rev"] / 1e6).round(2)
    display_rfm["avg_monetary"] = display_rfm["avg_monetary"].round(0).astype(int)
    st.dataframe(
        display_rfm.sort_values("total_rev", ascending=False)
        .rename(columns={"segment":"Segment","customers":"Customers",
                         "avg_recency":"Avg Recency (days)","avg_freq":"Avg Orders",
                         "avg_monetary":"Avg Spend (₹)","total_rev":"Total Revenue (₹M)"}),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Cohort Retention Heatmap")
    cohort = pd.read_csv(f"{OUT}/cohort_retention.csv", index_col=0)
    int_cols = [c for c in cohort.columns if str(c).isdigit()][:13]
    cohort_display = cohort[[c for c in int_cols]].head(24)
    if HAS_PLOTLY:
        fig = px.imshow(
            cohort_display.values,
            x=[f"M{c}" for c in int_cols],
            y=cohort_display.index.astype(str),
            color_continuous_scale=["#E63946","#F4A261","#2DC653","#145A32"],
            zmin=0, zmax=1,
            aspect="auto",
            labels=dict(color="Retention"),
        )
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.dataframe(cohort_display.style.background_gradient(cmap="RdYlGn", vmin=0, vmax=1))

# ══════════════════════════════════════════════════════════════
# PAGE 5: RETURNS
# ══════════════════════════════════════════════════════════════
elif page == "↩ Returns":
    st.title("↩ Returns & Refunds Analysis")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Returns",    f"{len(returns):,}")
    r2.metric("Total Refunded",   f"₹{returns['refund_amount'].sum()/1e6:.2f}M")
    r3.metric("Avg Refund",       f"₹{returns['refund_amount'].mean():,.0f}")
    r4.metric("Return Rate",      f"{return_rate:.1f}%")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Returns by Reason")
        reasons = returns["reason"].value_counts().reset_index()
        reasons.columns = ["Reason", "Count"]
        if HAS_PLOTLY:
            fig = px.bar(reasons.sort_values("Count"), x="Count", y="Reason",
                         orientation="h", color_discrete_sequence=["#E63946"],
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(reasons.set_index("Reason"))

    with col2:
        st.subheader("Return Status")
        r_status = returns["return_status"].value_counts()
        if HAS_PLOTLY:
            fig = px.pie(values=r_status.values, names=r_status.index,
                         color_discrete_sequence=["#2DC653","#F4A261","#E63946"],
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(r_status)

    st.subheader("Returns Over Time")
    returns_m = (returns.set_index("return_date")
                 .resample("ME")["return_id"]
                 .count()
                 .reset_index())
    returns_m.columns = ["Month", "Returns"]
    if HAS_PLOTLY:
        fig = px.line(returns_m, x="Month", y="Returns",
                      color_discrete_sequence=["#E63946"], template="plotly_white")
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(returns_m.set_index("Month"))

# ══════════════════════════════════════════════════════════════
# PAGE 6: ML MODELS
# ══════════════════════════════════════════════════════════════
elif page == "🧠 ML Models":
    st.title("🧠 ML Model Results")

    st.subheader("Churn Prediction — Model Performance")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Accuracy",    f"{churn_metrics['accuracy']*100:.2f}%")
    m2.metric("Precision",   f"{churn_metrics['precision']:.3f}")
    m3.metric("Recall",      f"{churn_metrics['recall']:.3f}")
    m4.metric("F1-Score",    f"{churn_metrics['f1_score']:.3f}")
    m5.metric("Churn Rate",  f"{churn_metrics['churn_rate']*100:.1f}%")

    st.markdown("""
    > **Algorithm:** Logistic Regression implemented from scratch (numpy only)  
    > **Features:** Recency, Frequency, Monetary, Avg Order Value  
    > **Threshold:** Churned = no purchase in >180 days  
    > **Train/Test:** 80% / 20% split, seed=42
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Churn Risk Distribution")
        risk_order = ["Low", "Medium", "High", "Critical"]
        churn_copy = churn.copy()
        churn_copy["churn_risk"] = pd.Categorical(
            churn_copy["churn_risk"], categories=risk_order, ordered=True)
        risk_counts = (churn_copy.groupby("churn_risk", observed=True)["customer_id"]
                       .count().reset_index())
        risk_counts.columns = ["Risk", "Count"]
        if HAS_PLOTLY:
            fig = px.bar(risk_counts, x="Risk", y="Count",
                         color="Risk",
                         color_discrete_map={"Low":"#2DC653","Medium":"#F4A261",
                                              "High":"#E67E22","Critical":"#E63946"},
                         template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(risk_counts.set_index("Risk"))

    with col2:
        st.subheader("Confusion Matrix")
        cm = churn_metrics["confusion_matrix"]
        cm_df = pd.DataFrame(
            [[cm["TP"], cm["FN"]], [cm["FP"], cm["TN"]]],
            index=["Actual Churned", "Actual Active"],
            columns=["Predicted Churned", "Predicted Active"]
        )
        if HAS_PLOTLY:
            fig = px.imshow(cm_df, text_auto=True,
                            color_continuous_scale=["#F0F4F8","#1B5E8B"],
                            template="plotly_white")
            fig.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(cm_df)

    st.subheader("Customer Lifetime Value — 12-Month Predictions")
    clv_tiers = (clv.groupby("clv_tier", observed=True)
                 .agg(customers=("customer_id","count"),
                      avg_clv=("clv_12m","mean"),
                      total_clv=("clv_12m","sum"))
                 .reset_index()
                 .sort_values("total_clv", ascending=False))
    clv_tiers["avg_clv"]   = clv_tiers["avg_clv"].round(0).astype(int)
    clv_tiers["total_clv_m"] = (clv_tiers["total_clv"] / 1e6).round(2)
    st.dataframe(
        clv_tiers[["clv_tier","customers","avg_clv","total_clv_m"]]
        .rename(columns={"clv_tier":"Tier","customers":"Customers",
                         "avg_clv":"Avg CLV (₹)","total_clv_m":"Total CLV (₹M)"}),
        use_container_width=True, hide_index=True,
    )
    st.metric("Total Predicted 12-Month Revenue",
              f"₹{clv['clv_12m'].sum()/1e7:.2f} Cr")

    st.subheader("Revenue Forecast — 6 Months (Jan–Jun 2025)")
    fc_fore = forecast[forecast["type"] == "forecast"].copy()
    fc_fore["Revenue (₹M)"] = (fc_fore["forecast_revenue"] / 1e6).round(2)
    st.dataframe(
        fc_fore[["ym","Revenue (₹M)"]].rename(columns={"ym":"Period"}),
        use_container_width=True, hide_index=True,
    )
    st.caption("*Model: OLS linear trend + monthly seasonality index. R² = 0.83*")

# ── FOOTER ────────────────────────────────────────────────────
st.divider()
st.caption("🛒 E-Commerce Analytics Portfolio Project · SQL · Python · Excel · Power BI · Synthetic data only")
