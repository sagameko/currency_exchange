-- Q3: How has the monthly average AUD/USD rate changed over the years?
SELECT d.year, d.month_name,
       ROUND(AVG(f.foreign_per_aud), 5) AS avg_usd_per_aud,
       MIN(f.foreign_per_aud)           AS lowest,
       MAX(f.foreign_per_aud)           AS highest
FROM fct_daily_rate f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.currency_code = 'USD'
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;