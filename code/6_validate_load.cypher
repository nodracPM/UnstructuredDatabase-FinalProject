// =====================================================
// 6. VALIDACIÓN DE CARGA
// =====================================================

MATCH (n)
RETURN labels(n) AS label, count(n) AS total
ORDER BY total DESC;


MATCH ()-[r]->()
RETURN type(r) AS relacion, count(r) AS total
ORDER BY total DESC;


MATCH (p:Persona)
RETURN p.es_fraude AS es_fraude, count(*) AS total
ORDER BY es_fraude DESC;

