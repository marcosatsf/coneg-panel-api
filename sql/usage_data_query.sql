WITH count_table AS (
    SELECT count(ff.tid) as count_par, ff.status
    FROM coneg.fato_faces ff
    WHERE local = %s
    GROUP BY ff.status
)
SELECT
    coalesce(ct.count_par, 0) as count_total,
    ds.id
FROM coneg.dim_status ds
LEFT JOIN count_table ct ON ds.id=ct.status;