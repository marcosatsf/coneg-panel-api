WITH daily_report AS (
    (
        SELECT date_trunc('day', ts) AS day, count(tid) AS partial_tot
        FROM coneg.fato_faces ff
        WHERE local = %s AND status > 0
        GROUP BY date_trunc('day', ts)
    )
    UNION ALL
    (
        WITH today_tot AS (
            SELECT count(tid) AS partial_tot, CURRENT_DATE AS today 
            FROM coneg.fato_faces ff
            WHERE local = %s AND status > 0 AND date_trunc('day', ts) = CURRENT_DATE
            GROUP BY date_trunc('day', ts)
        )
        SELECT DISTINCT CURRENT_DATE, coalesce(tt.partial_tot, 0) AS partial_tot
        FROM coneg.fato_faces ff
        LEFT JOIN today_tot tt ON tt.today=CURRENT_DATE
    )
),
sum_tot_values AS (
    SELECT sum(partial_tot) AS sum_tot, day FROM daily_report GROUP BY day
)
(
    SELECT sum_tot, day::date FROM sum_tot_values ORDER BY sum_tot DESC, day DESC LIMIT 1
)
UNION ALL
(
    SELECT sum_tot, day::date FROM sum_tot_values ORDER BY sum_tot, day DESC LIMIT 1
);