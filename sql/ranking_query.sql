SELECT ff.pessoa, dc.nome, count(*) as qtd
FROM coneg.fato_faces ff
JOIN coneg.dim_cadastrados dc 
ON ff.pessoa = dc.pesid
GROUP BY ff.pessoa, dc.nome
ORDER BY qtd DESC
LIMIT 5;