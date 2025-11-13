-- kyc_risk.sql
-- Example SQL view to aggregate recent transactional behaviour per client.

WITH tx_base AS (
  SELECT
    t.client_id,
    t.ts::date AS dt,
    t.amount_usd,
    t.channel,
    t.direction,
    t.counterparty_country,
    CASE WHEN cr.is_high_risk = 1 THEN 1 ELSE 0 END AS is_hrc,
    CASE WHEN t.channel = 'swift' AND t.direction = 'out' THEN 1 ELSE 0 END AS is_swift_out,
    CASE WHEN t.channel = 'cash' AND t.amount_usd BETWEEN 8000 AND 9999 THEN 1 ELSE 0 END AS is_structuring,
    CASE WHEN t.amount_usd >= 100000 THEN 1 ELSE 0 END AS is_large,
    CASE WHEN t.counterparty_country <> c.residency_country THEN 1 ELSE 0 END AS is_intl
  FROM transactions t
  JOIN clients c ON c.client_id = t.client_id
  LEFT JOIN country_risk cr ON cr.country = t.counterparty_country
),
agg AS (
  SELECT
    client_id,
    COUNT(*) FILTER (WHERE dt >= current_date - 90) AS tx_90d,
    AVG(is_intl::float) FILTER (WHERE dt >= current_date - 90) AS intl_rate_90d,
    SUM(is_hrc) FILTER (WHERE dt >= current_date - 90) AS hrc_hits_90d,
    SUM(is_swift_out) FILTER (WHERE dt >= current_date - 90) AS swift_out_90d,
    SUM(is_structuring) FILTER (WHERE dt >= current_date - 30) AS cash_structuring_hits_30d,
    AVG(is_large::float) FILTER (WHERE dt >= current_date - 180) AS large_value_rate_180d,
    COUNT(DISTINCT counterparty_country) FILTER (WHERE dt >= current_date - 180) AS geo_diversity_180d
  FROM tx_base
  GROUP BY client_id
)
SELECT * FROM agg;
