SELECT ff.status, count(ff.tid)
FROM coneg.fato_faces ff
WHERE local = %s
GROUP BY ff.status;