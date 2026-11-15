-- Q4: Biggest % moves between two consecutive published days, per currency (top 10)
WITH with_previous AS (
    SELECT f.currency_code, d.full_date, f.foreign_per_aud,
           LAG(f.foreign_per_aud) OVER (PARTITION BY f.currency_code ORDER BY d.full_date) AS previous_rate,
           LAG(d.full_date)       OVER (PARTITION BY f.currency_code ORDER BY d.full_date) AS previous_date
    FROM fct_daily_rate f
    JOIN dim_date d ON f.date_key = d.date_key
)
SELECT currency_code, previous_date, full_date,
       previous_rate, foreign_per_aud AS rate,
       ROUND(100.0 * (foreign_per_aud - previous_rate) / previous_rate, 3) AS pct_change
FROM with_previous
WHERE previous_rate IS NOT NULL
ORDER BY ABS(pct_change) DESC
LIMIT 10;