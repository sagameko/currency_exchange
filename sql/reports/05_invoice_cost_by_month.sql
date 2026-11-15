-- Q5: What did a 10,000 USD invoice cost in AUD on the first day of each month?
SELECT full_date, day_of_week, rate_date,
       ROUND(10000 * aud_per_foreign, 2) AS aud_cost_of_10000_usd
FROM v_rate_as_of
WHERE currency_code = 'USD'
  AND EXTRACT(day FROM full_date) = 1
  AND rate_date IS NOT NULL
ORDER BY full_date;