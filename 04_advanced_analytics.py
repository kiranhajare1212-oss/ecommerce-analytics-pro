"""
E-Commerce Analytics Project
Script 4: Advanced Analytics
  - Revenue Forecasting (linear trend + seasonality)
  - Churn Prediction (logistic regression from scratch)
  - Price Elasticity Analysis
  - Market Basket Analysis (co-purchase patterns)
  - Customer Lifetime Value Prediction
  - Discount Optimisation
"""

import pandas as pd
import numpy as np
import os
import json
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = "../data"
OUT_DIR  = "../data/analysis_outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# ── LOAD ─────────────────────────────────────────────────────
def load():
    orders      = pd.read_csv(f"{DATA_DIR}/orders.csv",      parse_dates=["order_date"])
    order_items = pd.read_csv(f"{DATA_DIR}/order_items.csv")
    products    = pd.read_csv(f"{DATA_DIR}/products.csv")
    customers   = pd.read_csv(f"{DATA_DIR}/customers.csv",   parse_dates=["registration_date"])
    returns     = pd.read_csv(f"{DATA_DIR}/returns.csv",     parse_dates=["return_date"])
    rfm         = pd.read_csv(f"{DATA_DIR}/analysis_outputs/rfm_scores.csv")
    return orders, order_items, products, customers, returns, rfm


# ════════════════════════════════════════════════════════════
# 1. REVENUE FORECASTING — Linear Trend + Monthly Seasonality
# ════════════════════════════════════════════════════════════
def revenue_forecast(orders, forecast_months=6):
    print("\n" + "═"*60)
    print("  1. REVENUE FORECASTING")
    print("═"*60)

    delivered = orders[orders["status"] != "Cancelled"].copy()
    delivered["ym"]  = delivered["order_date"].dt.to_period("M")
    delivered["month_num"] = (
        (delivered["order_date"].dt.year - 2022) * 12 +
        delivered["order_date"].dt.month
    )

    monthly = (delivered.groupby(["ym","month_num"])
               .agg(revenue=("order_total","sum"),
                    orders=("order_id","nunique"))
               .reset_index()
               .sort_values("month_num"))

    X = monthly["month_num"].values
    y = monthly["revenue"].values
    n = len(X)

    # Monthly seasonality index
    delivered["month"] = delivered["order_date"].dt.month
    seas = (delivered.groupby("month")["order_total"]
            .sum()
            .reset_index())
    seas["index"] = seas["order_total"] / seas["order_total"].mean()
    seas_dict = dict(zip(seas["month"], seas["index"]))

    # OLS linear regression (no sklearn needed)
    X_mean, y_mean = X.mean(), y.mean()
    slope  = np.sum((X - X_mean) * (y - y_mean)) / np.sum((X - X_mean)**2)
    intercept = y_mean - slope * X_mean

    # R²
    y_pred = slope * X + intercept
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - y_mean)**2)
    r2     = 1 - ss_res / ss_tot

    print(f"  Trend slope   : ₹{slope:,.2f} / month")
    print(f"  R² (fit)      : {r2:.4f}")

    # Forecast next N months
    last_month_num = int(monthly["month_num"].max())
    last_period    = monthly["ym"].max()

    forecast_rows = []
    for i in range(1, forecast_months + 1):
        m_num   = last_month_num + i
        period  = last_period + i
        cal_mon = int(str(period)[-2:]) if int(str(period)[-2:]) else 12
        base    = slope * m_num + intercept
        adj     = base * seas_dict.get(cal_mon, 1.0)
        forecast_rows.append({
            "period":      str(period),
            "month_num":   m_num,
            "forecast_revenue": round(adj, 2),
            "trend_revenue":    round(base, 2),
        })

    fc_df = pd.DataFrame(forecast_rows)
    print(f"\n  6-Month Revenue Forecast:")
    for _, row in fc_df.iterrows():
        print(f"    {row['period']}  →  ₹{row['forecast_revenue']:>15,.2f}")

    # Save historical + forecast
    historical = monthly[["ym","revenue","orders"]].copy()
    historical["ym"]  = historical["ym"].astype(str)
    historical["type"] = "actual"
    historical["forecast_revenue"] = historical["revenue"]
    fc_df["type"]    = "forecast"
    fc_df["revenue"] = fc_df["forecast_revenue"]
    fc_df["orders"]  = None

    combined = pd.concat([
        historical[["ym","revenue","orders","type","forecast_revenue"]],
        fc_df[["period","revenue","orders","type","forecast_revenue"]].rename(columns={"period":"ym"})
    ], ignore_index=True)
    combined.to_csv(f"{OUT_DIR}/revenue_forecast.csv", index=False)
    print(f"\n  Saved → {OUT_DIR}/revenue_forecast.csv")
    return fc_df


# ════════════════════════════════════════════════════════════
# 2. CHURN PREDICTION — Logistic Regression (numpy only)
# ════════════════════════════════════════════════════════════
def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

def logistic_fit(X, y, lr=0.01, epochs=1000):
    m, n = X.shape
    theta = np.zeros(n)
    for _ in range(epochs):
        h    = sigmoid(X @ theta)
        grad = X.T @ (h - y) / m
        theta -= lr * grad
    return theta

def churn_prediction(orders, rfm):
    print("\n" + "═"*60)
    print("  2. CHURN PREDICTION (Logistic Regression)")
    print("═"*60)

    snapshot = pd.Timestamp("2025-01-01")
    delivered = orders[orders["status"] != "Cancelled"]
    cust_stats = (delivered.groupby("customer_id")
                  .agg(recency=("order_date", lambda x: (snapshot - x.max()).days),
                       frequency=("order_id","nunique"),
                       monetary=("order_total","sum"),
                       last_order=("order_date","max"))
                  .reset_index())

    # Label: churned if last order > 180 days ago
    cust_stats["churned"] = (cust_stats["recency"] > 180).astype(int)
    churn_rate = cust_stats["churned"].mean()
    print(f"  Churn rate (>180 days inactive): {churn_rate*100:.1f}%")

    # Features: recency, frequency, monetary, avg_order
    cust_stats["avg_order"] = cust_stats["monetary"] / cust_stats["frequency"]

    features = ["recency","frequency","monetary","avg_order"]
    X_raw = cust_stats[features].fillna(0).values
    y     = cust_stats["churned"].values

    # Normalise
    X_mean = X_raw.mean(axis=0)
    X_std  = X_raw.std(axis=0) + 1e-8
    X_norm = (X_raw - X_mean) / X_std
    X_b    = np.hstack([np.ones((len(X_norm),1)), X_norm])

    # Train/test split (80/20)
    np.random.seed(42)
    idx   = np.random.permutation(len(X_b))
    split = int(0.8 * len(idx))
    tr, te = idx[:split], idx[split:]

    theta = logistic_fit(X_b[tr], y[tr], lr=0.05, epochs=2000)
    y_prob = sigmoid(X_b[te] @ theta)
    y_pred = (y_prob >= 0.5).astype(int)

    # Metrics
    tp = int(((y_pred == 1) & (y[te] == 1)).sum())
    tn = int(((y_pred == 0) & (y[te] == 0)).sum())
    fp = int(((y_pred == 1) & (y[te] == 0)).sum())
    fn = int(((y_pred == 0) & (y[te] == 1)).sum())
    accuracy  = (tp + tn) / len(te)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"  Model Accuracy  : {accuracy*100:.2f}%")
    print(f"  Precision       : {precision:.3f}")
    print(f"  Recall          : {recall:.3f}")
    print(f"  F1-Score        : {f1:.3f}")

    # All-customer predictions
    y_all_prob = sigmoid(X_b @ theta)
    cust_stats["churn_probability"] = y_all_prob.round(4)
    cust_stats["churn_risk"] = pd.cut(
        cust_stats["churn_probability"],
        bins=[0, 0.3, 0.6, 0.8, 1.0],
        labels=["Low","Medium","High","Critical"]
    )

    risk_summary = cust_stats.groupby("churn_risk", observed=True).agg(
        customers=("customer_id","count"),
        avg_monetary=("monetary","mean"),
        total_revenue=("monetary","sum")
    ).round(2)
    print(f"\n  Churn Risk Distribution:")
    print(risk_summary.to_string())

    cust_stats.to_csv(f"{OUT_DIR}/churn_predictions.csv", index=False)

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "churn_rate": round(float(churn_rate), 4),
        "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn}
    }
    with open(f"{OUT_DIR}/churn_model_metrics.json","w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n  Saved → {OUT_DIR}/churn_predictions.csv")
    return cust_stats, metrics


# ════════════════════════════════════════════════════════════
# 3. PRICE ELASTICITY ANALYSIS
# ════════════════════════════════════════════════════════════
def price_elasticity(orders, order_items, products):
    print("\n" + "═"*60)
    print("  3. PRICE ELASTICITY ANALYSIS")
    print("═"*60)

    delivered = orders[orders["status"] != "Cancelled"][["order_id"]]
    df = (delivered
          .merge(order_items, on="order_id")
          .merge(products[["product_id","category","selling_price"]], on="product_id"))

    # Bin discount levels and measure volume response
    df["discount_band"] = pd.cut(
        df["discount_pct"],
        bins=[-0.01, 0.001, 0.05, 0.10, 0.15, 0.20],
        labels=["0%","1-5%","6-10%","11-15%","16-20%"]
    )

    elasticity = (df.groupby(["category","discount_band"], observed=True)
                  .agg(avg_qty=("quantity","mean"),
                       total_units=("quantity","sum"),
                       avg_revenue=("line_total","mean"),
                       orders=("order_id","nunique"))
                  .reset_index())

    # Simple elasticity: % change qty / % change price for 0% vs 16-20%
    results = []
    for cat in df["category"].unique():
        sub = elasticity[elasticity["category"] == cat]
        base = sub[sub["discount_band"]=="0%"]["avg_qty"].values
        high = sub[sub["discount_band"]=="16-20%"]["avg_qty"].values
        if len(base) > 0 and len(high) > 0:
            pct_qty_change  = (high[0] - base[0]) / base[0] if base[0] > 0 else 0
            pct_price_change = -0.18  # midpoint of 16-20%
            elasticity_val   = pct_qty_change / pct_price_change if pct_price_change != 0 else 0
            results.append({
                "category": cat,
                "base_avg_qty": round(float(base[0]),2),
                "discounted_avg_qty": round(float(high[0]),2),
                "price_elasticity": round(float(elasticity_val),3),
                "elastic": "Yes" if abs(elasticity_val) > 1 else "No"
            })

    el_df = pd.DataFrame(results).sort_values("price_elasticity")
    print("\n  Price Elasticity by Category (0% vs 16-20% discount):")
    print(el_df.to_string(index=False))

    elasticity.to_csv(f"{OUT_DIR}/price_elasticity.csv", index=False)
    el_df.to_csv(f"{OUT_DIR}/elasticity_summary.csv", index=False)
    print(f"\n  Saved → {OUT_DIR}/price_elasticity.csv")
    return el_df


# ════════════════════════════════════════════════════════════
# 4. MARKET BASKET ANALYSIS (Co-purchase frequency)
# ════════════════════════════════════════════════════════════
def market_basket(orders, order_items, products, min_support=0.005):
    print("\n" + "═"*60)
    print("  4. MARKET BASKET ANALYSIS")
    print("═"*60)

    delivered = orders[orders["status"] != "Cancelled"][["order_id"]]
    df = delivered.merge(order_items[["order_id","product_id"]], on="order_id")
    df = df.merge(products[["product_id","category"]], on="product_id")

    # Work at category level (more meaningful with our product count)
    basket = (df.groupby(["order_id","category"])["product_id"]
              .count()
              .unstack(fill_value=0)
              .clip(upper=1))  # binary

    n_orders = len(basket)
    categories = basket.columns.tolist()

    # Support for each category
    support = (basket.sum() / n_orders).round(4)

    # Co-occurrence (pairs)
    pairs = []
    for i, c1 in enumerate(categories):
        for c2 in categories[i+1:]:
            co_support = (basket[c1] & basket[c2]).sum() / n_orders
            if co_support >= min_support:
                conf_c1_c2 = co_support / support[c1] if support[c1] > 0 else 0
                conf_c2_c1 = co_support / support[c2] if support[c2] > 0 else 0
                lift = co_support / (support[c1] * support[c2]) if (support[c1] * support[c2]) > 0 else 0
                pairs.append({
                    "category_A":    c1,
                    "category_B":    c2,
                    "support":       round(float(co_support),4),
                    "confidence_A→B": round(float(conf_c1_c2),4),
                    "confidence_B→A": round(float(conf_c2_c1),4),
                    "lift":          round(float(lift),4),
                    "rule_strength": "Strong" if lift > 1.2 else "Moderate" if lift > 1.0 else "Weak"
                })

    pairs_df = pd.DataFrame(pairs).sort_values("lift", ascending=False)
    print(f"\n  Category Co-purchase Pairs (lift ≥ 1.0):")
    strong = pairs_df[pairs_df["lift"] >= 1.0]
    print(strong[["category_A","category_B","support","lift","rule_strength"]].to_string(index=False))

    pairs_df.to_csv(f"{OUT_DIR}/market_basket.csv", index=False)
    print(f"\n  Saved → {OUT_DIR}/market_basket.csv")
    return pairs_df


# ════════════════════════════════════════════════════════════
# 5. CLV PREDICTION (BG/NBD-inspired heuristic)
# ════════════════════════════════════════════════════════════
def clv_prediction(orders, customers):
    print("\n" + "═"*60)
    print("  5. CUSTOMER LIFETIME VALUE PREDICTION (12-month horizon)")
    print("═"*60)

    snapshot = pd.Timestamp("2025-01-01")
    delivered = orders[orders["status"] != "Cancelled"]

    stats = (delivered.groupby("customer_id")
             .agg(first_order=("order_date","min"),
                  last_order=("order_date","max"),
                  frequency=("order_id","nunique"),
                  monetary=("order_total","sum"))
             .reset_index())

    stats["recency_days"]  = (snapshot - stats["last_order"]).dt.days
    stats["tenure_days"]   = (stats["last_order"] - stats["first_order"]).dt.days.clip(lower=1)
    stats["avg_order"]     = stats["monetary"] / stats["frequency"]
    stats["purchase_rate"] = stats["frequency"] / (stats["tenure_days"] / 30.0)  # orders/month

    # Simple CLV heuristic: predicted_orders_12m × avg_order_value × retention_prob
    stats["retention_prob"] = np.clip(
        1 - stats["recency_days"] / 730, 0.05, 0.99
    )
    stats["predicted_orders_12m"] = (
        stats["purchase_rate"] * 12 * stats["retention_prob"]
    ).clip(lower=0.1)
    stats["clv_12m"] = (
        stats["predicted_orders_12m"] * stats["avg_order"]
    ).round(2)

    clv_tier = pd.cut(
        stats["clv_12m"],
        bins=[-1, 5000, 20000, 50000, float("inf")],
        labels=["Bronze","Silver","Gold","Platinum"]
    )
    stats["clv_tier"] = clv_tier

    tier_summary = stats.groupby("clv_tier", observed=True).agg(
        customers=("customer_id","count"),
        avg_clv=("clv_12m","mean"),
        total_predicted_revenue=("clv_12m","sum")
    ).round(2)

    print(f"\n  Predicted 12-Month Revenue by CLV Tier:")
    print(tier_summary.to_string())
    print(f"\n  Total Predicted 12-Month Revenue: ₹{stats['clv_12m'].sum():,.2f}")

    # Merge with customer info
    result = stats.merge(customers[["customer_id","city","country","acquisition_channel"]], on="customer_id")
    result.to_csv(f"{OUT_DIR}/clv_predictions.csv", index=False)
    print(f"\n  Saved → {OUT_DIR}/clv_predictions.csv")
    return stats


# ════════════════════════════════════════════════════════════
# 6. DISCOUNT OPTIMISATION
# ════════════════════════════════════════════════════════════
def discount_optimisation(orders, order_items, products):
    print("\n" + "═"*60)
    print("  6. DISCOUNT OPTIMISATION ANALYSIS")
    print("═"*60)

    delivered = orders[orders["status"] != "Cancelled"][["order_id"]]
    df = (delivered
          .merge(order_items, on="order_id")
          .merge(products[["product_id","category","cost_price","selling_price"]], on="product_id"))

    df["margin_pct"]    = (df["line_total"] - df["quantity"]*df["cost_price"]) / df["line_total"].clip(lower=0.01)
    df["discount_band"] = pd.cut(
        df["discount_pct"],
        bins=[-0.01,0.001,0.05,0.10,0.15,0.20],
        labels=["0%","1-5%","6-10%","11-15%","16-20%"]
    )

    opt = (df.groupby(["category","discount_band"], observed=True)
           .agg(orders=("order_id","nunique"),
                units=("quantity","sum"),
                revenue=("line_total","sum"),
                avg_margin=("margin_pct","mean"))
           .reset_index())
    opt["revenue_per_order"] = opt["revenue"] / opt["orders"].clip(lower=1)

    # Find optimal discount band per category (max revenue_per_order with margin > 30%)
    recommendations = []
    for cat in opt["category"].unique():
        sub = opt[(opt["category"]==cat) & (opt["avg_margin"] > 0.30)]
        if len(sub) > 0:
            best = sub.loc[sub["revenue_per_order"].idxmax()]
            recommendations.append({
                "category":           cat,
                "recommended_discount": str(best["discount_band"]),
                "expected_revenue_per_order": round(best["revenue_per_order"],2),
                "expected_margin":    round(best["avg_margin"]*100,1),
            })

    rec_df = pd.DataFrame(recommendations)
    print("\n  Discount Recommendations per Category:")
    print(rec_df.to_string(index=False))

    opt.to_csv(f"{OUT_DIR}/discount_optimisation.csv", index=False)
    rec_df.to_csv(f"{OUT_DIR}/discount_recommendations.csv", index=False)
    print(f"\n  Saved → {OUT_DIR}/discount_optimisation.csv")
    return rec_df


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("\n🔄 Loading data...")
    orders, order_items, products, customers, returns, rfm = load()

    revenue_forecast(orders)
    churn_prediction(orders, rfm)
    price_elasticity(orders, order_items, products)
    market_basket(orders, order_items, products)
    clv_prediction(orders, customers)
    discount_optimisation(orders, order_items, products)

    print("\n" + "═"*60)
    print("  ✅ ADVANCED ANALYTICS COMPLETE")
    print(f"     Outputs → {os.path.abspath(OUT_DIR)}")
    print("═"*60)

if __name__ == "__main__":
    main()
