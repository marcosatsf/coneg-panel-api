WITH daily_status_table AS (
SELECT *
FROM GENERATE_SERIES(DATE_TRUNC('day', CURRENT_DATE - interval '6 day'), DATE_TRUNC('day', CURRENT_DATE), '1 day'::interval) ts
CROSS JOIN GENERATE_SERIES(0, 2) status
),
daily_report AS (
SELECT
    date_trunc('day', ts) AS day,
    ff.status,
    COUNT(tid) AS partial_tot
FROM coneg.fato_faces ff
WHERE
    local = 'Entrada principal' AND
    ts BETWEEN date_trunc('day', CURRENT_DATE - interval '7 day') AND
    date_trunc('day', CURRENT_DATE)
GROUP BY date_trunc('day', ts), ff.status
)
SELECT
    dst.status,
    dst.ts,
    COALESCE(SUM(partial_tot),0)::INTEGER AS total
FROM daily_status_table dst
LEFT JOIN daily_report dr
ON dst.status = dr.status AND dst.ts = dr.day
GROUP BY dst.status, dst.ts
ORDER BY dst.status, dst.ts