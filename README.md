# 🛒 End-to-End E-Commerce Analytics Project

> A complete data analytics portfolio project using **SQL · Python · Excel · Power BI**  
> Covering data generation, exploration, KPI reporting, customer segmentation, and dashboard design.

---

## 📌 Project Overview

This project simulates a real-world e-commerce analytics pipeline for a multi-region online retailer. It covers the full lifecycle from raw data to business insights:

| Layer | Tool | What It Does |
|---|---|---|
| Data Generation | Python | Synthetic realistic dataset (12K orders, 2K customers) |
| Data Storage | SQLite / CSV | Relational schema with indexes and views |
| Analytics Queries | SQL | 20+ business queries (revenue, RFM, cohorts, ops) |
| Exploratory Analysis | Python (pandas) | EDA, RFM scoring, cohort retention |
| Reporting | Excel (openpyxl) | 7-sheet workbook with charts and heatmaps |
| Dashboard | Power BI | 5-page interactive dashboard with DAX measures |

---

## 📂 Project Structure

```
ecommerce_analytics/
│
├── run_all.py                     # ← Master orchestration (run this first!)
├── requirements.txt
│
├── data/                          # Generated datasets
│   ├── customers.csv              # 2,000 customers
│   ├── products.csv               # ~113 products across 6 categories
│   ├── orders.csv                 # 12,000 orders (2022-2024)
│   ├── order_items.csv            # 25,000+ line items
│   ├── returns.csv                # ~693 return records
│   ├── ecommerce.db               # SQLite database (auto-generated)
│   └── analysis_outputs/          # EDA & ML output files
│       ├── monthly_revenue.csv
│       ├── category_performance.csv
│       ├── rfm_scores.csv
│       ├── rfm_segments.csv
│       ├── cohort_retention.csv
│       ├── top_products.csv
│       ├── returns_detail.csv
│       ├── revenue_forecast.csv       # 6-month forecast
│       ├── churn_predictions.csv      # Per-customer churn probability
│       ├── churn_model_metrics.json   # Accuracy, F1, precision, recall
│       ├── clv_predictions.csv        # 12-month CLV per customer
│       ├── price_elasticity.csv
│       ├── elasticity_summary.csv
│       ├── market_basket.csv
│       ├── discount_optimisation.csv
│       └── discount_recommendations.csv
│
├── sql/
│   ├── 01_schema.sql              # Table definitions & indexes
│   ├── 02_analytics_queries.sql   # 20+ analytical queries (5 sections)
│   ├── 03_views.sql               # Reporting views for Power BI
│   └── 04_advanced_sql.sql        # 10 advanced SQL patterns
│
├── python/
│   ├── 01_generate_data.py        # Synthetic data generator
│   ├── 02_eda_analysis.py         # EDA, RFM, cohort analysis + SQLite DB
│   ├── 03_excel_report.py         # 7-sheet Excel report builder
│   ├── 04_advanced_analytics.py   # Forecasting, churn ML, CLV, market basket
│   └── 05_html_dashboard.py       # Self-contained HTML analytics dashboard
│
├── excel/
│   └── ecommerce_analytics_report.xlsx   # 7-sheet Excel workbook
│
├── docs/
│   ├── analytics_dashboard.html   # Standalone HTML dashboard (open in browser)
│   ├── METHODOLOGY.md             # Design decisions & technical rationale
│   └── INTERVIEW_QA.md            # Common interview Q&A for this project
│
├── powerbi/
│   ├── POWERBI_SETUP.md           # Step-by-step Power BI guide + DAX library
│   └── theme.json                 # Custom Power BI colour theme
│
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
# Only needs: pandas, numpy, openpyxl
```

### Option A — Run Everything (Recommended)
```bash
python run_all.py
```

### Option B — Run Step by Step
```bash
cd python
python 01_generate_data.py        # Generate dataset
python 02_eda_analysis.py         # EDA + SQLite DB
python 03_excel_report.py         # Excel workbook
python 04_advanced_analytics.py   # ML + forecasting
python 05_html_dashboard.py       # HTML dashboard
```

### View the Dashboard
Open `docs/analytics_dashboard.html` in any browser — no server needed.

---

## 🗃️ Dataset Schema

### `customers`
| Column | Type | Description |
|---|---|---|
| customer_id | VARCHAR | Primary key (CUST00001 format) |
| first_name, last_name | VARCHAR | Customer name |
| email, phone | VARCHAR | Contact info |
| city, state, country | VARCHAR | Location (India, USA, UK, UAE, Singapore) |
| registration_date | DATE | When they signed up |
| acquisition_channel | VARCHAR | Organic / Paid / Social / Email / Referral / Direct |
| age_group | VARCHAR | 18-24, 25-34, 35-44, 45-54, 55+ |
| gender | VARCHAR | Male / Female / Other |

### `products`
| Column | Type | Description |
|---|---|---|
| product_id | VARCHAR | Primary key |
| product_name | VARCHAR | Name with variant (Standard/Pro/Lite) |
| category | VARCHAR | Electronics, Clothing, Home & Kitchen, Books, Sports & Fitness, Beauty & Health |
| brand | VARCHAR | 8 fictional brands |
| selling_price | DECIMAL | Customer-facing price |
| cost_price | DECIMAL | COGS (35–60% of selling price) |
| stock_quantity | INT | Current inventory |
| rating | DECIMAL | 3.0–5.0 |
| is_active | SMALLINT | 1 = active |

### `orders`
| Column | Type | Description |
|---|---|---|
| order_id | VARCHAR | Primary key |
| customer_id | VARCHAR | FK → customers |
| order_date | DATE | Purchase date |
| delivery_date | DATE | Actual delivery (null if not delivered) |
| status | VARCHAR | Delivered / Shipped / Processing / Cancelled |
| payment_method | VARCHAR | Credit Card / Debit Card / UPI / Net Banking / Wallet / COD |
| channel | VARCHAR | Acquisition channel for this order |
| order_total | DECIMAL | Total value of order |
| shipping_fee | DECIMAL | 0 / 49 / 99 / 149 |
| coupon_used | SMALLINT | 1 if coupon applied |

### `order_items`
| Column | Type | Description |
|---|---|---|
| item_id | VARCHAR | Primary key |
| order_id | VARCHAR | FK → orders |
| product_id | VARCHAR | FK → products |
| quantity | INT | Units purchased |
| unit_price | DECIMAL | Price at time of purchase |
| discount_pct | DECIMAL | 0–20% |
| line_total | DECIMAL | unit_price × qty × (1 - discount) |

### `returns`
| Column | Type | Description |
|---|---|---|
| return_id | VARCHAR | Primary key |
| order_id | VARCHAR | FK → orders |
| customer_id | VARCHAR | FK → customers |
| return_date | DATE | Date of return |
| reason | VARCHAR | 7 possible reasons |
| refund_amount | DECIMAL | 50–100% of order total |
| return_status | VARCHAR | Refunded / Processing / Rejected |

---

## 📊 SQL Analytics Queries (02_analytics_queries.sql)

### Section A — Revenue & Sales
| Query | Description |
|---|---|
| A1 | Monthly revenue, orders, customers, AOV trend |
| A2 | Category revenue with COGS and gross profit margin |
| A3 | Top 20 best-selling products |
| A4 | Sales channel performance with revenue share |
| A5 | Payment method mix |

### Section B — Customer Analytics
| Query | Description |
|---|---|
| B1 | Customer Lifetime Value with segmentation |
| B2 | RFM segmentation using NTILE window functions |
| B3 | New vs returning customers monthly |
| B4 | Cohort retention analysis (monthly) |

### Section C — Geography & Demographics
| Query | Description |
|---|---|
| C1 | Revenue by country |
| C2 | Top 20 revenue cities |
| C3 | Revenue by age group × gender |

### Section D — Operational KPIs
| Query | Description |
|---|---|
| D1 | Order status distribution |
| D2 | Average delivery time by country |
| D3 | Return rate by category |
| D4 | Return reason breakdown |
| D5 | Inventory health (low stock alerts) |

### Section E — Advanced Window Functions
| Query | Description |
|---|---|
| E1 | YTD revenue + MoM growth % using LAG |
| E2 | Category revenue rank per month using RANK() |
| E3 | Customer purchase gap analysis |
| E4 | Discount band impact on revenue |

### `04_advanced_sql.sql` — 10 Advanced SQL Patterns
| Pattern | Description |
|---|---|
| 1 | Recursive date spine — calendar table via recursive CTE |
| 2 | PIVOT — monthly revenue cross-tab by year (CASE WHEN) |
| 3 | Rolling 3-month average revenue |
| 4 | Customer decile analysis using NTILE(10) |
| 5 | First/last order gap — customer journey with LAG/LEAD |
| 6 | Product affinity self-join — co-purchase frequency |
| 7 | ABC inventory classification (cumulative revenue share) |
| 8 | Cohort retention matrix — compact version |
| 9 | Week-over-week anomaly detection using Z-scores |
| 10 | Next-best-action — high-value at-risk customer targeting |

---

## 📈 Excel Report (7 Sheets)

| Sheet | Contents |
|---|---|
| 📊 Executive Summary | KPI banner cards, banner styling |
| 📈 Monthly Revenue | Trend table + line chart |
| 🗂 Category Performance | Revenue + margin table + bar chart |
| 🏆 Top Products | Top 25 by revenue with data bars |
| 👥 RFM Segments | Segment table with color-coded rows + pie chart |
| ↩ Returns Analysis | Reason breakdown + KPI summary |
| 🔁 Cohort Retention | Full cohort heatmap with conditional color gradient |

---

## 📉 Power BI Dashboard (5 Pages)

| Page | Key Visuals |
|---|---|
| Executive Overview | KPI cards, revenue line, channel bar, order status donut |
| Product Analytics | Top products bar, category treemap, rating scatter |
| Customer Analytics | RFM segments, map, new vs returning, age/gender matrix |
| Returns & Operations | Return reason bar, return rate trend, delivery gauge |
| Cohort Analysis | Retention heatmap matrix, cohort retention lines |

See `powerbi/POWERBI_SETUP.md` for full connection and DAX setup.

---

## 📈 Python Analytics Scripts (5 scripts)

| Script | Description |
|---|---|
| `01_generate_data.py` | Synthetic data generator — customers, products, orders, returns |
| `02_eda_analysis.py` | EDA, RFM segmentation, cohort retention, SQLite DB build |
| `03_excel_report.py` | 7-sheet Excel workbook with charts and conditional formatting |
| `04_advanced_analytics.py` | Revenue forecasting, churn ML, CLV, market basket, discount optimisation |
| `05_html_dashboard.py` | Self-contained HTML dashboard — open in any browser |

---

## 🌐 HTML Dashboard

`docs/analytics_dashboard.html` is a fully self-contained analytics dashboard built with Chart.js that renders in any browser. It includes:

- 8 executive KPI cards with colour-coded accents
- Monthly revenue trend line chart (2022–2024)
- 6-month revenue forecast bar chart
- Category revenue + GP margin charts
- Channel revenue donut, payment method pie
- RFM segment revenue bar chart
- Churn risk distribution donut
- Revenue by country bar chart
- Return reasons breakdown
- Top 10 products table with pill badges
- RFM segment detail table
- Churn model performance metrics panel

No server required — just open the file in Chrome, Firefox or Edge.

---

## 🔍 Key Business Insights

| Finding | Detail |
|---|---|
| 📊 Revenue concentration | Electronics alone = 58% of total revenue at 49.6% gross margin |
| 👑 RFM Champions | 393 customers (20%) drive ₹22Cr — 28% of all revenue |
| ↩ Return problem | 8% return rate; top reason is "Duplicate Order" → checkout UX issue |
| 🏷 Discount insight | Near-zero price elasticity across all categories — discounts cut margin without lifting volume |
| 🔮 Forecast | Revenue trend slope = ₹17.7L/month; R² = 0.83 showing strong linear growth |
| ⚠ Churn risk | 15.8% of customers inactive >180 days; ML model catches 93% of churners (recall) |
| 💰 CLV | Platinum tier customers (1,906) represent ₹293Cr predicted 12-month value |
| 💳 Payments | UPI and Credit Card dominate; COD has highest average order |

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.9+ | Data generation, EDA, ML, reporting |
| pandas | 1.5+ | Data wrangling & aggregation |
| numpy | 1.23+ | Numerical computing, ML from scratch |
| openpyxl | 3.0+ | Excel workbook creation |
| SQLite | Built-in | Star-schema relational store |
| SQL | ANSI + SQLite | 30+ analytical queries |
| Chart.js | 4.4 (CDN) | HTML dashboard visualisations |
| Excel | 2019 / 365 | Report delivery |
| Power BI Desktop | Latest | Interactive self-service BI |

---

## 📁 Additional Documentation

| File | Contents |
|---|---|
| `docs/METHODOLOGY.md` | Design decisions: schema choice, RFM rules, ML rationale, forecasting approach |
| `docs/INTERVIEW_QA.md` | 15 interview Q&As covering SQL, Python, Excel, Power BI, and analytics thinking |
| `powerbi/POWERBI_SETUP.md` | Step-by-step Power BI connection guide + 20 DAX measures |

---

## 🤝 Extension Ideas

Pull requests welcome! Suggested next steps:

| Extension | Tools |
|---|---|
| Streamlit web app | streamlit, plotly |
| Full ML pipeline | scikit-learn, SHAP, mlflow |
| dbt transformation layer | dbt-core, SQLite adapter |
| Richer forecasting | Prophet, statsmodels SARIMA |
| Cloud deployment | AWS S3 + Athena + QuickSight |
| Real-time streaming | Kafka + Spark Structured Streaming |
| A/B test framework | scipy.stats, bayesian A/B |

---

## 📄 License

MIT — free to use, adapt, and extend for portfolio or learning purposes.

---

*End-to-end e-commerce analytics portfolio project — SQL · Python · Excel · Power BI*  
*Data is fully synthetic and randomly generated. No real customer information is used.*
