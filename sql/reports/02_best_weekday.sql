-- Q2: On average, which weekday gives the most USD per AUD? (published days only)
SELECT d.day_of_week,
       COUNT(*)                         AS published_days,
       ROUND(AVG(f.foreign_per_aud), 5) AS avg_usd_per_aud
FROM fct_daily_rate f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.currency_code = 'USD'
GROUP BY d.day_of_week, ISODOW(d.full_date)
ORDER BY ISODOW(d.full_date);