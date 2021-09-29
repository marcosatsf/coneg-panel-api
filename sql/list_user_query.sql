SELECT pesid, nome, email, telefone
FROM coneg.dim_cadastrados
OFFSET %s
LIMIT 10;