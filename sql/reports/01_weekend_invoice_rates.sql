-- Q1: Which rate do we use for an invoice dated on a weekend or holiday? (USD, last 10 days)
SELECT full_date, day_of_week, rate_date, foreign_per_aud AS usd_per_aud,
       aud_per_foreign AS aud_per_usd, is_carried_forward
FROM v_rate_as_of
WHERE currency_code = 'USD'
  AND rate_date IS NOT NULL
ORDER BY full_date DESC
LIMIT 10;