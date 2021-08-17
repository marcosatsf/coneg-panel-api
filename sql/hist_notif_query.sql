SELECT ff.pessoa, dc.nome, ff.ts, ff.local
FROM coneg.fato_faces ff
JOIN coneg.dim_cadastrados dc
ON ff.pessoa=dc.pesid
WHERE ff.pessoa = %s
ORDER BY ff.ts DESC
OFFSET %s
LIMIT 10;