SELECT count(tid) AS today_tot
FROM coneg.fato_faces ff
WHERE local = %s AND status > 0 AND date_trunc('day', ts) = CURRENT_DATE
GROUP BY date_trunc('day', ts)