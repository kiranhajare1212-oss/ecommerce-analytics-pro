"""
E-Commerce Analytics Project
Script 5: KPI Dashboard Report Generator
Generates a complete HTML dashboard from all analytics outputs
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

DATA_DIR = "../data"
OUT_DIR  = "../data/analysis_outputs"
OUT_FILE = "../docs/analytics_dashboard.html"
os.makedirs("../docs", exist_ok=True)

# ── LOAD ALL OUTPUTS ──────────────────────────────────────────
orders      = pd.read_csv(f"{DATA_DIR}/orders.csv",      parse_dates=["order_date"])
products    = pd.read_csv(f"{DATA_DIR}/products.csv")
customers   = pd.read_csv(f"{DATA_DIR}/customers.csv")
returns     = pd.read_csv(f"{DATA_DIR}/returns.csv")
order_items = pd.read_csv(f"{DATA_DIR}/order_items.csv")
rfm_seg     = pd.read_csv(f"{OUT_DIR}/rfm_segments.csv")
monthly     = pd.read_csv(f"{OUT_DIR}/monthly_revenue.csv", parse_dates=["order_date"])
cat_perf    = pd.read_csv(f"{OUT_DIR}/category_performance.csv")
top_prods   = pd.read_csv(f"{OUT_DIR}/top_products.csv")
forecast    = pd.read_csv(f"{OUT_DIR}/revenue_forecast.csv")
churn       = pd.read_csv(f"{OUT_DIR}/churn_predictions.csv")
clv         = pd.read_csv(f"{OUT_DIR}/clv_predictions.csv")

with open(f"{OUT_DIR}/churn_model_metrics.json") as f:
    churn_metrics = json.load(f)

# ── COMPUTE KPIs ──────────────────────────────────────────────
delivered = orders[orders["status"] != "Cancelled"]
total_rev     = delivered["order_total"].sum()
total_orders  = delivered["order_id"].nunique()
total_cust    = delivered["customer_id"].nunique()
aov           = total_rev / total_orders
total_units   = order_items.merge(delivered[["order_id"]], on="order_id")["quantity"].sum()
canc_rate     = (orders["status"] == "Cancelled").sum() / len(orders) * 100
return_rate   = len(returns) / len(delivered[delivered["status"]=="Delivered"]) * 100
total_refund  = returns["refund_amount"].sum()

# Monthly data for charts
monthly_data = (delivered
    .set_index("order_date")
    .resample("ME")["order_total"]
    .sum()
    .reset_index())
monthly_data.columns = ["month","revenue"]
monthly_data["month_str"] = monthly_data["month"].dt.strftime("%b %Y")

# Category data
cat_perf_sorted = cat_perf.sort_values("revenue", ascending=False)

# Channel revenue
channel_rev = (delivered.groupby("channel")["order_total"]
               .sum().sort_values(ascending=False).reset_index())

# Payment mix
payment_mix = (delivered.groupby("payment_method")["order_id"]
               .nunique().sort_values(ascending=False).reset_index())

# Country revenue
country_rev = (delivered.groupby("country")["order_total"]
               .sum().sort_values(ascending=False).head(8).reset_index())

# Return reasons
return_reasons = returns["reason"].value_counts().reset_index()
return_reasons.columns = ["reason","count"]

# Forecast
fc_actual   = forecast[forecast["type"]=="actual"].tail(12)
fc_forecast = forecast[forecast["type"]=="forecast"]

# RFM
rfm_plot = rfm_seg.sort_values("total_rev", ascending=False)

# CLV tiers
clv_tiers = (clv.groupby("clv_tier", observed=True)
             .agg(customers=("customer_id","count"),
                  total_clv=("clv_12m","sum"))
             .reset_index())

# ── JSON SERIALIZE ────────────────────────────────────────────
def jl(lst):
    return json.dumps(lst)

months_labels  = jl(monthly_data["month_str"].tolist())
revenue_values = jl([round(v/1e6, 2) for v in monthly_data["revenue"].tolist()])

cat_labels    = jl(cat_perf_sorted["category"].tolist())
cat_revenues  = jl([round(v/1e6, 2) for v in cat_perf_sorted["revenue"].tolist()])
cat_margins   = jl([round(v, 2) for v in cat_perf_sorted["gp_margin"].tolist()])

ch_labels  = jl(channel_rev["channel"].tolist())
ch_values  = jl([round(v/1e6, 2) for v in channel_rev["order_total"].tolist()])

pay_labels = jl(payment_mix["payment_method"].tolist())
pay_values = jl(payment_mix["order_id"].tolist())

country_labels = jl(country_rev["country"].tolist())
country_values = jl([round(v/1e6, 2) for v in country_rev["order_total"].tolist()])

ret_labels = jl(return_reasons["reason"].tolist())
ret_values = jl(return_reasons["count"].tolist())

rfm_labels   = jl(rfm_plot["segment"].tolist())
rfm_values   = jl([round(v/1e6, 2) for v in rfm_plot["total_rev"].tolist()])
rfm_cust     = jl(rfm_plot["customers"].tolist())

fc_act_labels  = jl(fc_actual["ym"].tolist())
fc_act_values  = jl([round(v/1e6, 2) for v in fc_actual["revenue"].tolist()])
fc_fore_labels = jl(fc_forecast["ym"].tolist())
fc_fore_values = jl([round(v/1e6, 2) for v in fc_forecast["forecast_revenue"].tolist()])

clv_labels = jl(clv_tiers["clv_tier"].tolist())
clv_cust   = jl(clv_tiers["customers"].tolist())
clv_rev    = jl([round(v/1e6, 2) for v in clv_tiers["total_clv"].tolist()])

top5 = top_prods.head(5)
top5_names  = jl([n[:30] for n in top5["product_name"].tolist()])
top5_rev    = jl([round(v/1e6, 2) for v in top5["revenue"].tolist()])

# Churn risk
churn_risk = (churn.groupby("churn_risk", observed=True)["customer_id"]
              .count().reset_index())
churn_risk.columns = ["risk","count"]
# Fix ordering
risk_order = ["Low","Medium","High","Critical"]
churn_risk["risk"] = pd.Categorical(churn_risk["risk"], categories=risk_order, ordered=True)
churn_risk = churn_risk.sort_values("risk")
churn_labels = jl(churn_risk["risk"].tolist())
churn_values_j = jl(churn_risk["count"].tolist())

generated_at = datetime.now().strftime("%d %B %Y, %H:%M")

# ── HTML ─────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>E-Commerce Analytics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  :root {{
    --navy:   #0D1B2A;
    --blue:   #1B5E8B;
    --teal:   #00B4D8;
    --green:  #2DC653;
    --amber:  #F4A261;
    --red:    #E63946;
    --purple: #6C3483;
    --slate:  #F0F4F8;
    --card:   #FFFFFF;
    --border: #E2E8F0;
    --text:   #1A202C;
    --muted:  #718096;
    --font:   'DM Sans', sans-serif;
    --mono:   'DM Mono', monospace;
  }}

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: var(--font);
    background: var(--slate);
    color: var(--text);
    min-height: 100vh;
  }}

  /* HEADER */
  .header {{
    background: linear-gradient(135deg, var(--navy) 0%, #1a3a5c 100%);
    padding: 32px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 24px rgba(13,27,42,0.3);
  }}
  .header-left h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.5px;
  }}
  .header-left p {{
    color: rgba(255,255,255,0.55);
    font-size: 13px;
    margin-top: 4px;
    font-family: var(--mono);
  }}
  .header-badge {{
    background: rgba(0,180,216,0.15);
    border: 1px solid rgba(0,180,216,0.4);
    border-radius: 20px;
    padding: 6px 18px;
    color: var(--teal);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}

  /* LAYOUT */
  .container {{ max-width: 1440px; margin: 0 auto; padding: 32px 48px 64px; }}

  .section-title {{
    font-size: 18px;
    font-weight: 700;
    color: var(--navy);
    margin: 40px 0 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .section-title::before {{
    content: '';
    display: inline-block;
    width: 4px;
    height: 20px;
    background: var(--teal);
    border-radius: 2px;
  }}

  /* KPI CARDS */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 14px;
    margin-bottom: 8px;
  }}
  @media (max-width: 1200px) {{ .kpi-grid {{ grid-template-columns: repeat(4, 1fr); }} }}
  @media (max-width: 700px)  {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}

  .kpi {{
    background: var(--card);
    border-radius: 12px;
    padding: 20px 16px;
    border: 1px solid var(--border);
    transition: transform 0.18s, box-shadow 0.18s;
    position: relative;
    overflow: hidden;
  }}
  .kpi:hover {{ transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,0,0,0.10); }}
  .kpi-accent {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 3px;
    border-radius: 12px 12px 0 0;
  }}
  .kpi-icon {{
    font-size: 22px;
    margin-bottom: 8px;
  }}
  .kpi-value {{
    font-size: 22px;
    font-weight: 700;
    color: var(--navy);
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }}
  .kpi-label {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 5px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  /* CHART CARDS */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
  .grid-31 {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }}
  @media (max-width: 900px) {{
    .grid-2, .grid-3, .grid-31 {{ grid-template-columns: 1fr; }}
  }}

  .card {{
    background: var(--card);
    border-radius: 14px;
    padding: 24px;
    border: 1px solid var(--border);
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  }}
  .card-title {{
    font-size: 14px;
    font-weight: 700;
    color: var(--navy);
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card-title .badge {{
    font-size: 10px;
    background: var(--slate);
    color: var(--blue);
    border-radius: 6px;
    padding: 2px 8px;
    font-weight: 600;
  }}

  canvas {{ max-width: 100%; }}

  /* TABLE */
  .data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  .data-table th {{
    background: var(--navy);
    color: #fff;
    padding: 10px 14px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    text-align: left;
  }}
  .data-table th:first-child {{ border-radius: 8px 0 0 0; }}
  .data-table th:last-child  {{ border-radius: 0 8px 0 0; }}
  .data-table td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
  }}
  .data-table tr:nth-child(even) td {{ background: var(--slate); }}
  .data-table tr:hover td {{ background: #EBF8FF; }}
  .pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }}
  .pill-green  {{ background: #D4EDDA; color: #155724; }}
  .pill-amber  {{ background: #FFF3CD; color: #856404; }}
  .pill-red    {{ background: #F8D7DA; color: #721C24; }}
  .pill-blue   {{ background: #CCE5FF; color: #004085; }}
  .pill-purple {{ background: #E2D9F3; color: #4A235A; }}

  /* METRIC ROW */
  .metric-row {{
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }}
  .metric-box {{
    flex: 1;
    min-width: 140px;
    background: var(--slate);
    border-radius: 10px;
    padding: 14px 18px;
    border-left: 3px solid var(--teal);
  }}
  .metric-box .val {{ font-size: 20px; font-weight: 700; color: var(--navy); }}
  .metric-box .lbl {{ font-size: 11px; color: var(--muted); margin-top: 2px; font-weight: 500; }}

  /* FOOTER */
  .footer {{
    text-align: center;
    padding: 32px;
    color: var(--muted);
    font-size: 12px;
    border-top: 1px solid var(--border);
    margin-top: 48px;
    font-family: var(--mono);
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>🛒 E-Commerce Analytics Dashboard</h1>
    <p>Generated: {generated_at} &nbsp;|&nbsp; Period: Jan 2022 – Dec 2024 &nbsp;|&nbsp; SQL · Python · Excel · Power BI</p>
  </div>
  <span class="header-badge">PORTFOLIO PROJECT</span>
</div>

<div class="container">

  <!-- KPI STRIP -->
  <div class="section-title">Executive KPIs</div>
  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-accent" style="background:var(--teal)"></div><div class="kpi-icon">💰</div><div class="kpi-value">₹{total_rev/1e7:.1f}Cr</div><div class="kpi-label">Gross Revenue</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:var(--blue)"></div><div class="kpi-icon">📦</div><div class="kpi-value">{total_orders:,}</div><div class="kpi-label">Total Orders</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:var(--green)"></div><div class="kpi-icon">👥</div><div class="kpi-value">{total_cust:,}</div><div class="kpi-label">Customers</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:var(--purple)"></div><div class="kpi-icon">🛍</div><div class="kpi-value">₹{aov/1000:.1f}K</div><div class="kpi-label">Avg Order Value</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:var(--amber)"></div><div class="kpi-icon">📊</div><div class="kpi-value">{total_units:,}</div><div class="kpi-label">Units Sold</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:var(--red)"></div><div class="kpi-icon">↩</div><div class="kpi-value">{return_rate:.1f}%</div><div class="kpi-label">Return Rate</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:#E63946"></div><div class="kpi-icon">❌</div><div class="kpi-value">{canc_rate:.1f}%</div><div class="kpi-label">Cancellation</div></div>
    <div class="kpi"><div class="kpi-accent" style="background:#117A65"></div><div class="kpi-icon">⭐</div><div class="kpi-value">{products['is_active'].sum()}</div><div class="kpi-label">Active SKUs</div></div>
  </div>

  <!-- REVENUE TRENDS -->
  <div class="section-title">Revenue Trends & Forecast</div>
  <div class="grid-31">
    <div class="card">
      <div class="card-title">Monthly Revenue Trend (₹ Millions) <span class="badge">2022-2024</span></div>
      <canvas id="revenueChart" height="110"></canvas>
    </div>
    <div class="card">
      <div class="card-title">6-Month Revenue Forecast <span class="badge">Jan–Jun 2025</span></div>
      <canvas id="forecastChart" height="110"></canvas>
    </div>
  </div>

  <!-- CATEGORY & CHANNEL -->
  <div class="section-title">Category & Channel Performance</div>
  <div class="grid-3">
    <div class="card">
      <div class="card-title">Revenue by Category (₹M)</div>
      <canvas id="catChart" height="200"></canvas>
    </div>
    <div class="card">
      <div class="card-title">GP Margin % by Category</div>
      <canvas id="marginChart" height="200"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Revenue by Channel (₹M)</div>
      <canvas id="channelChart" height="200"></canvas>
    </div>
  </div>

  <!-- CUSTOMER ANALYTICS -->
  <div class="section-title">Customer Analytics — RFM & CLV</div>
  <div class="grid-2">
    <div class="card">
      <div class="card-title">RFM Segment Revenue (₹M)</div>
      <canvas id="rfmChart" height="200"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Churn Risk Distribution</div>
      <canvas id="churnChart" height="200"></canvas>
    </div>
  </div>

  <!-- CHURN MODEL METRICS -->
  <div class="section-title">Churn Prediction Model Performance</div>
  <div class="metric-row">
    <div class="metric-box"><div class="val">{churn_metrics['accuracy']*100:.1f}%</div><div class="lbl">Accuracy</div></div>
    <div class="metric-box"><div class="val">{churn_metrics['precision']:.3f}</div><div class="lbl">Precision</div></div>
    <div class="metric-box"><div class="val">{churn_metrics['recall']:.3f}</div><div class="lbl">Recall</div></div>
    <div class="metric-box"><div class="val">{churn_metrics['f1_score']:.3f}</div><div class="lbl">F1-Score</div></div>
    <div class="metric-box"><div class="val">{churn_metrics['churn_rate']*100:.1f}%</div><div class="lbl">Base Churn Rate</div></div>
    <div class="metric-box"><div class="val">Logistic<br>Regression</div><div class="lbl">Algorithm</div></div>
  </div>

  <!-- GEOGRAPHY & PAYMENTS -->
  <div class="section-title">Geography & Payment Mix</div>
  <div class="grid-2">
    <div class="card">
      <div class="card-title">Revenue by Country (₹M)</div>
      <canvas id="countryChart" height="180"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Payment Method Mix (Orders)</div>
      <canvas id="paymentChart" height="180"></canvas>
    </div>
  </div>

  <!-- RETURNS -->
  <div class="section-title">Returns Analysis</div>
  <div class="grid-31">
    <div class="card">
      <div class="card-title">Return Reasons Breakdown</div>
      <canvas id="returnChart" height="120"></canvas>
    </div>
    <div class="card">
      <div class="card-title">Returns KPIs</div>
      <div class="metric-row" style="flex-direction:column; gap:12px; margin:0;">
        <div class="metric-box" style="border-color:var(--red)"><div class="val">{len(returns):,}</div><div class="lbl">Total Returns</div></div>
        <div class="metric-box" style="border-color:var(--red)"><div class="val">₹{total_refund/1e6:.2f}M</div><div class="lbl">Total Refunded</div></div>
        <div class="metric-box" style="border-color:var(--amber)"><div class="val">₹{returns['refund_amount'].mean():,.0f}</div><div class="lbl">Avg Refund Amount</div></div>
        <div class="metric-box" style="border-color:var(--green)"><div class="val">{return_rate:.1f}%</div><div class="lbl">Return Rate</div></div>
      </div>
    </div>
  </div>

  <!-- TOP PRODUCTS TABLE -->
  <div class="section-title">Top 10 Products by Revenue</div>
  <div class="card">
    <table class="data-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Product</th>
          <th>Category</th>
          <th>Brand</th>
          <th>Units Sold</th>
          <th>Revenue</th>
          <th>Avg Discount</th>
        </tr>
      </thead>
      <tbody>
        {''.join([
            f"""<tr>
              <td><strong>{i+1}</strong></td>
              <td>{row['product_name']}</td>
              <td><span class='pill pill-blue'>{row['category']}</span></td>
              <td>{row['brand']}</td>
              <td>{int(row['units_sold']):,}</td>
              <td><strong>₹{row['revenue']/1e6:.2f}M</strong></td>
              <td><span class='pill pill-blue'>—</span></td>
            </tr>"""
            for i, row in top_prods.head(10).iterrows()
        ])}
      </tbody>
    </table>
  </div>

  <!-- RFM TABLE -->
  <div class="section-title">RFM Segment Details</div>
  <div class="card">
    <table class="data-table">
      <thead>
        <tr><th>Segment</th><th>Customers</th><th>Avg Recency (days)</th><th>Avg Frequency</th><th>Avg Monetary (₹)</th><th>Total Revenue</th><th>% of Revenue</th></tr>
      </thead>
      <tbody>
        {''.join([
            f"""<tr>
              <td><span class='pill {"pill-green" if row["segment"] in ["Champions","Loyal"] else "pill-amber" if row["segment"] in ["New/Recent","Potential Loyal","High Spender"] else "pill-red"}'>{row["segment"]}</span></td>
              <td>{int(row["customers"]):,}</td>
              <td>{row["avg_recency"]:.0f}</td>
              <td>{row["avg_freq"]:.1f}</td>
              <td>₹{row["avg_monetary"]:,.0f}</td>
              <td>₹{row["total_rev"]/1e6:.2f}M</td>
              <td>{row["total_rev"]/rfm_seg["total_rev"].sum()*100:.1f}%</td>
            </tr>"""
            for _, row in rfm_seg.sort_values("total_rev",ascending=False).iterrows()
        ])}
      </tbody>
    </table>
  </div>

</div>

<div class="footer">
  E-Commerce Analytics Portfolio Project &nbsp;·&nbsp; SQL · Python · Excel · Power BI &nbsp;·&nbsp; Generated {generated_at}
</div>

<script>
const COLORS = ['#0D1B2A','#1B5E8B','#00B4D8','#2DC653','#F4A261','#E63946','#6C3483','#117A65'];
const opts = {{ responsive:true, plugins:{{ legend:{{ display:false }}, tooltip:{{ callbacks:{{ label: ctx => ' ₹'+ctx.parsed.y?.toFixed?.(2)+' M' }} }} }} }};

// Revenue trend
new Chart(document.getElementById('revenueChart'), {{
  type:'line',
  data:{{ labels:{months_labels}, datasets:[{{ label:'Revenue', data:{revenue_values},
    borderColor:'#00B4D8', backgroundColor:'rgba(0,180,216,0.08)',
    tension:0.4, fill:true, pointRadius:3, pointBackgroundColor:'#00B4D8' }}] }},
  options:{{ ...opts, plugins:{{ ...opts.plugins, tooltip:{{ callbacks:{{ label: ctx => ' ₹'+ctx.parsed.y+' M' }} }} }} }}
}});

// Forecast
new Chart(document.getElementById('forecastChart'), {{
  type:'bar',
  data:{{ labels:{fc_fore_labels}, datasets:[{{ label:'Forecast', data:{fc_fore_values},
    backgroundColor:'rgba(44,198,83,0.75)', borderRadius:6 }}] }},
  options:{{ ...opts, plugins:{{ ...opts.plugins, tooltip:{{ callbacks:{{ label: ctx => ' ₹'+ctx.parsed.y+' M' }} }} }} }}
}});

// Category revenue
new Chart(document.getElementById('catChart'), {{
  type:'bar',
  data:{{ labels:{cat_labels}, datasets:[{{ data:{cat_revenues},
    backgroundColor:COLORS, borderRadius:5 }}] }},
  options:{{ ...opts, indexAxis:'y' }}
}});

// Margin
new Chart(document.getElementById('marginChart'), {{
  type:'bar',
  data:{{ labels:{cat_labels}, datasets:[{{ data:{cat_margins},
    backgroundColor:'rgba(0,180,216,0.7)', borderRadius:5 }}] }},
  options:{{ responsive:true, plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label: ctx => ' '+ctx.parsed.x+'%'}}}} }}, indexAxis:'y' }}
}});

// Channel
new Chart(document.getElementById('channelChart'), {{
  type:'doughnut',
  data:{{ labels:{ch_labels}, datasets:[{{ data:{ch_values}, backgroundColor:COLORS, hoverOffset:8 }}] }},
  options:{{ responsive:true, plugins:{{ legend:{{position:'bottom', labels:{{font:{{size:11}}}}}} }} }}
}});

// RFM
new Chart(document.getElementById('rfmChart'), {{
  type:'bar',
  data:{{ labels:{rfm_labels}, datasets:[{{ data:{rfm_values}, backgroundColor:COLORS, borderRadius:6 }}] }},
  options:{{ ...opts }}
}});

// Churn risk
new Chart(document.getElementById('churnChart'), {{
  type:'doughnut',
  data:{{ labels:{churn_labels}, datasets:[{{ data:{churn_values_j},
    backgroundColor:['#2DC653','#F4A261','#E67E22','#E63946'], hoverOffset:8 }}] }},
  options:{{ responsive:true, plugins:{{ legend:{{position:'bottom'}} }} }}
}});

// Country
new Chart(document.getElementById('countryChart'), {{
  type:'bar',
  data:{{ labels:{country_labels}, datasets:[{{ data:{country_values},
    backgroundColor:'rgba(27,94,139,0.8)', borderRadius:5 }}] }},
  options:{{ ...opts }}
}});

// Payment
new Chart(document.getElementById('paymentChart'), {{
  type:'pie',
  data:{{ labels:{pay_labels}, datasets:[{{ data:{pay_values}, backgroundColor:COLORS, hoverOffset:6 }}] }},
  options:{{ responsive:true, plugins:{{ legend:{{position:'right', labels:{{font:{{size:11}}}}}} }} }}
}});

// Returns
new Chart(document.getElementById('returnChart'), {{
  type:'bar',
  data:{{ labels:{ret_labels}, datasets:[{{ data:{ret_values},
    backgroundColor:'rgba(230,57,70,0.75)', borderRadius:5 }}] }},
  options:{{ ...opts, indexAxis:'y',
    plugins:{{ ...opts.plugins, tooltip:{{ callbacks:{{ label: ctx => ' '+ctx.parsed.x+' returns' }} }} }} }}
}});
</script>
</body>
</html>"""

with open(OUT_FILE, "w") as f:
    f.write(html)

print(f"✅ HTML Dashboard saved: {os.path.abspath(OUT_FILE)}")
print(f"   Open in browser: file://{os.path.abspath(OUT_FILE)}")
