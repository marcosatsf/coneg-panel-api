WITH local_count AS (
    SELECT distinct(ff.local), st
    FROM coneg.fato_faces ff
    CROSS JOIN GENERATE_SERIES(0, 2) st
    ORDER BY ff.local, st
),
filtered_fato_faces AS (
    SELECT ff.local, ff.status
    FROM coneg.fato_faces ff
    WHERE DATE_TRUNC('day',ff.ts)=CURRENT_DATE
)
SELECT
    lc.local,
    --lc.st,
    COALESCE(count(fff.status),0)
FROM local_count lc
LEFT JOIN filtered_fato_faces fff
ON fff.local = lc.local AND fff.status = lc.st
GROUP BY lc.local, lc.st
ORDER BY lc.local, lc.st;