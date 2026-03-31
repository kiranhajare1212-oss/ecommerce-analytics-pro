# Project Methodology & Design Decisions

## 1. Data Architecture

### Why SQLite?
SQLite was chosen as the analytical store because:
- Zero-configuration, no server process needed
- Full SQL including window functions (since v3.25)
- Single `.db` file is easy to version-control and share
- Python's `sqlite3` module is part of the standard library
- Power BI can connect via ODBC driver

For production, the schema and queries are written to be fully compatible with **PostgreSQL** and **MySQL 8+** with minor dialect adjustments (e.g., `strftime` → `DATE_TRUNC`).

### Star Schema Design
```
            ┌────────────┐
            │  customers │
            └─────┬──────┘
                  │ 1:M
┌──────────┐ 1:M ┌▼──────────┐ M:1 ┌──────────┐
│ returns  ├─────┤  orders   ├─────┤ products │
└──────────┘     └─────┬─────┘     └──────────┘
                       │ 1:M
                  ┌────▼──────┐
                  │order_items│
                  └───────────┘
```

This classic **star schema** enables:
- Simple JOIN paths for any analytical query
- Efficient aggregation at any grain (order, customer, product, time)
- Direct Power BI relationship mapping

---

## 2. Data Generation Strategy

### Realism Mechanisms
| Dimension | Technique |
|---|---|
| Names | Culturally diverse first/last name pool (Indian, Western, East Asian) |
| Geography | Real city/state/country combinations |
| Pricing | Category-specific price ranges with realistic variance |
| Order dates | Random within customer tenure (can't order before registration) |
| Status distribution | Weighted: 72% Delivered, 10% Shipped, 8% Processing, 10% Cancelled |
| Seasonality | Implicit in random date distribution |
| Returns | 8% of delivered orders, reason-weighted, 5–30 days post-delivery |

### Reproducibility
All scripts use `random.seed(42)` and `np.random.seed(42)` for fully reproducible outputs.

---

## 3. RFM Segmentation Methodology

### Scoring
- **Recency**: Days since last order → NTILE(5), higher score = more recent
- **Frequency**: Number of distinct orders → NTILE(5), higher = more orders  
- **Monetary**: Sum of order totals → NTILE(5), higher = more spend

### Segment Rules
```
R≥4 & F≥4  → Champions          (best customers, buy often and recently)
R≥3 & F≥3  → Loyal Customers    (frequent but not quite top tier)
R≥4 & F≤2  → New/Recent         (bought recently but infrequent)
R≤2 & F≥3  → At Risk            (used to buy often, going cold)
R≤2 & F≤2  → Lost               (haven't bought in long time, rarely did)
M≥4         → High Spenders      (big-ticket buyers)
else        → Potential Loyalists
```

---

## 4. Churn Model Design

### Definition
A customer is labelled **churned** if their last purchase was > 180 days before the analysis snapshot (2025-01-01). This threshold can be tuned per business context.

### Algorithm
**Logistic Regression** implemented from scratch using NumPy:
- Gradient descent optimisation (lr=0.05, 2000 epochs)
- Feature normalisation (zero mean, unit variance)
- 80/20 train/test split

### Features
| Feature | Description |
|---|---|
| Recency | Days since last order |
| Frequency | Number of orders |
| Monetary | Lifetime spend |
| Avg Order | Monetary / Frequency |

### Why not sklearn?
To demonstrate ML fundamentals without external ML dependencies, making this project runnable with only `pandas` and `numpy`.

---

## 5. Revenue Forecasting Approach

### Model
**OLS Linear Regression** + **Monthly Seasonality Index**

Steps:
1. Fit linear trend: `revenue = slope × month_number + intercept`
2. Compute seasonality index per calendar month: `actual / mean`
3. Forecast: `trend_value × seasonal_index`

### Limitations
- Assumes linear growth (adequate for 3-year horizon)
- Seasonality computed from historical average (not multiplicative decomposition)
- Does not capture sudden structural breaks (e.g., COVID-style disruptions)

For production: consider **Facebook Prophet** or **SARIMA** for richer seasonality and uncertainty intervals.

---

## 6. Excel Report Design Decisions

### Why openpyxl (not xlsxwriter)?
- openpyxl supports both reading and writing
- Better chart API for our use case
- Native support for conditional formatting rules
- Active maintenance and wide compatibility

### Sheet Structure Logic
Each sheet is self-contained with its own banner, headers, and charts so the workbook can be shared as a standalone deliverable without requiring the data CSVs.

### Colour Coding Strategy
- **Dark Navy** (`#0D1B2A`): Headers, navigation
- **Teal** (`#00B4D8`): Primary metric highlight
- **Green** (`#2DC653`): Positive / profit metrics
- **Amber** (`#F4A261`): Warning / discount-related
- **Red** (`#E63946`): Risk / cancellation / returns

---

## 7. Power BI Architecture

### Data Flow
```
CSV files / SQLite DB
        ↓ (Get Data)
Power Query (M) — cleaning, type casting
        ↓
Data Model — star schema relationships
        ↓
DAX Measures — KPI calculations
        ↓
Report Pages — 5 dashboard views
```

### DAX Design Principles
1. **Base measures first** — e.g., `Total Revenue` before `Revenue YoY`
2. **Use CALCULATE sparingly** — wrap only what needs context modification
3. **DIVIDE over `/`** — always handles division-by-zero safely
4. **Time intelligence** — requires a connected Date Table marked as such
5. **SELECTEDVALUE / HASONEVALUE** — for conditional card labels

---

## 8. SQL Query Patterns Used

| Pattern | Queries |
|---|---|
| Window functions | Running totals, rank, LAG/LEAD, NTILE |
| CTEs | Multi-step aggregations, RFM, cohorts |
| Self-joins | Product affinity / co-purchase analysis |
| CASE WHEN pivot | Monthly revenue cross-tab by year |
| Recursive CTE | Date spine generation |
| Subqueries | Normalisation denominators, first_value lookups |
| LEFT JOIN | Preserving products/customers with no orders |

---

## 9. Potential Extensions

| Feature | Tool | Complexity |
|---|---|---|
| Real-time dashboard | Streamlit + SQLite | Medium |
| ML churn (full) | scikit-learn + SHAP | Medium |
| dbt transformation layer | dbt-core + SQLite | Medium |
| Forecasting with confidence intervals | Prophet / statsmodels | Medium |
| Email segmentation automation | Python + SMTP | Low |
| A/B test analysis | scipy.stats | Low |
| Cloud deployment | AWS RDS + QuickSight | High |
| Kafka streaming pipeline | Kafka + Spark | High |
