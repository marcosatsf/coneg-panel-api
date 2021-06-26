with daily_report AS (
SELECT date_trunc('day', ts) AS day, ff.status, count(tid) AS partial_tot
FROM coneg.fato_faces ff
WHERE local = %s AND status > 0
GROUP BY date_trunc('day', ts), ff.status
),
sum_tot_values AS (
SELECT sum(partial_tot) AS sum_tot, day FROM daily_report GROUP BY day
)
(
SELECT sum_tot, day::date FROM sum_tot_values ORDER BY sum_tot desc limit 1
)
UNION ALL
(
SELECT sum_tot, day::date FROM sum_tot_values ORDER BY sum_tot limit 1
);