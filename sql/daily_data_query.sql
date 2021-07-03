WITH daily_status_table AS (
SELECT *
FROM GENERATE_SERIES(CURRENT_DATE, DATE_TRUNC('minute', NOW()), '30 minute'::interval) ts
CROSS JOIN GENERATE_SERIES(0, 2) status
),
daily_report AS (
SELECT
    date_trunc('minute', ts) AS minutes,
    ff.status,
    COUNT(tid) AS partial_tot
FROM coneg.fato_faces ff
WHERE
    local = %s AND
    ts BETWEEN CURRENT_DATE AND
    DATE_TRUNC('minute', NOW())
GROUP BY date_trunc('minute', ts), ff.status
)
SELECT
    dst.status,
    dst.ts::timestamp,
    COALESCE(SUM(partial_tot),0)::INTEGER AS total
FROM daily_status_table dst
LEFT JOIN daily_report dr
ON dst.status = dr.status AND dst.ts = dr.minutes
GROUP BY dst.status, dst.ts
ORDER BY dst.status, dst.ts;