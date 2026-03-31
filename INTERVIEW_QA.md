# Interview Q&A — E-Commerce Analytics Project

Common interview questions about this project, with detailed answers.

---

## SQL Questions

**Q: Walk me through your SQL schema design.**

The schema follows a classic star schema with `orders` as the fact table and `customers`, `products` as dimensions. `order_items` is a bridge table handling the M:M relationship between orders and products. `returns` links back to `orders` and `customers`. I added indexes on all FK columns and frequently-filtered columns (`order_date`, `status`, `country`) to support analytical query performance.

---

**Q: How did you implement RFM segmentation in SQL?**

I used `NTILE(5)` window functions partitioned over the customer population to score each dimension independently. Recency is scored inversely (lower days = higher score) by reversing the ORDER BY. The segments are then assigned using nested CASE WHEN logic on the R/F scores. The full query is in `02_analytics_queries.sql`, Section B2.

---

**Q: What window functions did you use, and why?**

- `NTILE(5)` — for RFM percentile binning
- `LAG / LEAD` — for MoM growth and purchase gap analysis
- `SUM() OVER (PARTITION BY ... ORDER BY ...)` — for running YTD totals
- `RANK()` — for category revenue ranking within each month
- `FIRST_VALUE()` — for cohort retention rate normalisation
- `AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` — for 3-month rolling average

---

**Q: How would you scale this to billions of rows?**

1. Move from SQLite to a columnar store (BigQuery, Redshift, Snowflake)
2. Partition the `orders` table by `order_date` (monthly partitions)
3. Use materialised views / pre-aggregated summary tables for dashboard queries
4. Push heavy window functions to dbt transformation layer, not live query time
5. Index on `customer_id`, `order_date`, `status` for OLTP; clustering keys for OLAP

---

## Python Questions

**Q: Why did you implement logistic regression from scratch?**

To demonstrate understanding of the underlying mathematics — gradient descent, the sigmoid function, cost function minimisation — rather than treating ML as a black box. In production I'd use scikit-learn for robustness, cross-validation, and richer feature engineering.

---

**Q: How does your forecasting model work?**

OLS linear regression over a month-number index captures the underlying trend (R² = 0.83, meaning 83% of revenue variance is explained by time). A seasonality index (actual monthly revenue / average monthly revenue) is then multiplied to adjust for within-year patterns. This is equivalent to a multiplicative decomposition with a linear trend component.

---

**Q: What does CLV prediction mean in practice?**

CLV (Customer Lifetime Value) is the predicted revenue a customer will generate over a future horizon. My 12-month heuristic uses: `predicted_orders = purchase_rate × 12 × retention_probability` and `CLV = predicted_orders × avg_order_value`. This is a simplified version of the BG/NBD model. It's actionable for prioritising retention spend — focus on Platinum-tier customers at churn risk.

---

**Q: How would you improve the churn model?**

1. Add more features: product category preference, channel, coupon usage, return history, device type
2. Try gradient boosting (XGBoost, LightGBM) which handles non-linearities and interactions
3. Calibrate probability outputs (Platt scaling)
4. Use time-aware cross-validation (walk-forward) to prevent leakage
5. Add SHAP values for interpretability — explain why each customer is predicted to churn

---

## Excel Questions

**Q: Why generate Excel with Python instead of building it manually?**

Two reasons: (1) reproducibility — re-running the script with updated data regenerates the workbook in seconds; (2) scale — with 10,000+ rows of data, Python handles formatting and chart creation far faster than manual work. The workbook becomes a deliverable artefact of the pipeline, not a manually maintained file.

---

**Q: What Excel features did you use programmatically?**

Via `openpyxl`: cell formatting (fonts, fills, borders), merged cells, column widths, number formats, chart objects (bar, line, pie), conditional formatting (data bars, colour scale), and cohort heatmap with manual colour grading.

---

## Power BI / DAX Questions

**Q: Explain the difference between CALCULATE and FILTER in DAX.**

`CALCULATE` modifies the filter context of a measure evaluation — it's the most powerful DAX function. `FILTER` returns a table (row by row), and is much slower because it evaluates the expression for every row. Best practice: prefer `CALCULATE` with direct filter predicates over wrapping `FILTER` in `CALCULATE` unless you need complex row-level logic.

---

**Q: How did you set up time intelligence?**

I created a Date table using `CALENDAR()` covering the full date range, added Year/Month/Quarter/WeekDay columns, marked it as a Date Table in the model, and connected it to `orders[order_date]`. This enables DAX time intelligence functions: `DATESYTD`, `SAMEPERIODLASTYEAR`, `PREVIOUSMONTH`, `DATESMTD`, etc.

---

**Q: What's the difference between star and snowflake schema for Power BI?**

Star schema (which I used) has denormalised dimensions — every attribute of a customer is in the customers table. Snowflake normalises further (e.g., separate city/country tables). Star schema is preferred in Power BI because it reduces the JOIN complexity the engine has to handle and produces simpler DAX, at the cost of slightly larger dimension tables.

---

## General Analytics Questions

**Q: What were your most interesting findings?**

1. **80/20 applies strongly** — top 20% of products drive ~80% of revenue, consistent with Pareto
2. **Champions churn is expensive** — the 393 Champion customers represent ₹22Cr, so even 5% churn = ₹1.1Cr lost
3. **Discounts don't drive volume** — price elasticity analysis showed near-zero elasticity across all categories, suggesting discounts reduce margin without meaningfully increasing units
4. **Duplicate orders** are the #1 return reason — suggests a UX/checkout problem worth fixing

---

**Q: How would you present this to a non-technical stakeholder?**

I'd lead with the HTML dashboard or Power BI — visuals first, numbers second. I'd focus on 3-4 actionable insights: (1) which customer segment needs a win-back campaign, (2) which product category has eroding margin, (3) forecast showing revenue trajectory, (4) the return reason pointing to a product/ops fix. I'd avoid discussing model metrics like F1-score or R² unless asked.
