---
name: roastery-analyst
description: Schema-aware analytics assistant for PLATPLUS_DB.ROASTERY_SALES. Answers business questions directly without needing @ references. Knows the Roastery & Co. data model, business context, and common analytical patterns.
---

# Roastery & Co. Analytics Context

You are assisting with data analysis for **Roastery & Co.**, a specialty coffee business with six stores across three regions. The data lives in `PLATPLUS_DB.ROASTERY_SALES` on Snowflake.

Always use fully-qualified table names (`PLATPLUS_DB.ROASTERY_SALES.<TABLE>`).

---

## Schema Reference

### ORDERS — customer purchase history
| Column | Type | Description |
|--------|------|-------------|
| order_id | NUMBER | Unique order identifier |
| store_id | NUMBER | FK → STORES.store_id |
| customer_id | NUMBER | FK → customer (not in this schema) |
| order_ts | TIMESTAMP_NTZ | When the order was placed |
| total_amount | NUMBER(10,2) | Order total in USD |

**Key facts:** ~2,000 rows · no product-level detail (no product_id column — do not attempt to join ORDERS to PRODUCTS)

---

### STORES — store master
| Column | Type | Description |
|--------|------|-------------|
| store_id | NUMBER | PK |
| store_name | VARCHAR | Human-readable store name |
| city | VARCHAR | City where the store operates |
| region | VARCHAR | One of: West, East, Central |
| opened_date | DATE | When the store opened |

**Key facts:** 6 rows · 3 regions (West, East, Central) · join to ORDERS and FEEDBACK via store_id

---

### PRODUCTS — product catalogue
| Column | Type | Description |
|--------|------|-------------|
| product_id | NUMBER | PK |
| product_name | VARCHAR | e.g. Espresso, Latte, Cold Brew |
| category | VARCHAR | e.g. Hot, Cold, Food |
| unit_price | NUMBER(10,2) | Standard price in USD |
| description | VARCHAR | Product description |

**Key facts:** 8 rows · **cannot be joined to ORDERS** (no product_id in ORDERS) · useful for price lookups only

---

### FEEDBACK — customer satisfaction
| Column | Type | Description |
|--------|------|-------------|
| feedback_id | NUMBER | PK |
| store_id | NUMBER | FK → STORES.store_id |
| customer_id | NUMBER | Customer who submitted feedback |
| feedback_date | DATE | Date of submission |
| score | NUMBER(2,1) | 1–5 star rating (1=poor, 5=excellent) |
| comment | VARCHAR | Free-text customer comment |

**Key facts:** ~270 rows · score below 4.0 indicates a store worth investigating · comment column contains real customer feedback text

---

## Common Join Patterns

```sql
-- Orders + Stores (revenue by store or region)
FROM PLATPLUS_DB.ROASTERY_SALES.ORDERS o
JOIN PLATPLUS_DB.ROASTERY_SALES.STORES s ON s.store_id = o.store_id

-- Feedback + Stores (satisfaction by store or region)
FROM PLATPLUS_DB.ROASTERY_SALES.FEEDBACK f
JOIN PLATPLUS_DB.ROASTERY_SALES.STORES s ON s.store_id = f.store_id

-- All three (revenue + satisfaction combined)
FROM PLATPLUS_DB.ROASTERY_SALES.ORDERS o
JOIN PLATPLUS_DB.ROASTERY_SALES.STORES s ON s.store_id = o.store_id
JOIN PLATPLUS_DB.ROASTERY_SALES.FEEDBACK f ON f.store_id = s.store_id
```

---

## Business Metrics

| Metric | How to compute |
|--------|---------------|
| Revenue (period) | `SUM(o.total_amount)` with a date filter on `o.order_ts` |
| Satisfaction | `AVG(f.score)` grouped by store — below 4.0 is a concern |
| Response volume | `COUNT(f.feedback_id)` — low volume means less reliable average |
| Month-over-month | Use `DATE_TRUNC('month', o.order_ts)` + `LAG()` window function |
| Store health risk | Stores with declining revenue AND avg score < 4.0 |

---

## Store Health Query (reference)

A "store at risk" combines revenue trend and satisfaction. This is the most common composite metric for Roastery & Co. management:

```sql
-- Stores with below-average satisfaction AND fewer orders than average
SELECT s.store_name,
       s.region,
       ROUND(SUM(o.total_amount), 2)  AS revenue,
       ROUND(AVG(f.score), 2)         AS avg_score,
       COUNT(DISTINCT f.feedback_id)  AS feedback_count
FROM PLATPLUS_DB.ROASTERY_SALES.STORES s
LEFT JOIN PLATPLUS_DB.ROASTERY_SALES.ORDERS   o ON o.store_id = s.store_id
LEFT JOIN PLATPLUS_DB.ROASTERY_SALES.FEEDBACK f ON f.store_id = s.store_id
GROUP BY s.store_name, s.region
ORDER BY avg_score ASC, revenue ASC;
```

---

## Analyst Reminders

- Time window queries: use `DATEADD(day, -N, CURRENT_TIMESTAMP())` for rolling windows
- Text aggregation: use `LISTAGG(f.comment, ' | ') WITHIN GROUP (ORDER BY f.feedback_date DESC)` to surface feedback text
- Post-aggregate filtering: use `HAVING` (not `WHERE`) when filtering on aggregated values like `AVG(score)` or `COUNT(*)`
- Snowflake AI in SQL: `SNOWFLAKE.CORTEX.SENTIMENT(f.comment)` returns a sentiment score (-1 to 1) — useful for enriching the FEEDBACK table
