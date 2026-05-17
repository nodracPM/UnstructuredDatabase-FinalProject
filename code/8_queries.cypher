// =====================================================
// 7. RESET DE INDICADORES
// =====================================================

MATCH (p:Persona)
SET p.risk_tel = 0,
    p.risk_device = 0,
    p.risk_ip = 0,
    p.risk_dom = 0,
    p.similarity_flag = 0,
    p.risk_score = 0,
    p.risk_level = "BAJO";


// =====================================================
// 8. RIESGO POR TELÉFONO COMPARTIDO
// =====================================================

MATCH (p:Persona)-[:TIENE_TELEFONO]->(t:Telefono)<-[:TIENE_TELEFONO]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_tel = total;


// =====================================================
// 9. RIESGO POR DISPOSITIVO COMPARTIDO
// =====================================================

MATCH (p:Persona)-[:REALIZA]->(:Solicitud)-[:USA_DISPOSITIVO]->(d:Dispositivo)
MATCH (d)<-[:USA_DISPOSITIVO]-(:Solicitud)<-[:REALIZA]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_device = total;


// =====================================================
// 10. RIESGO POR IP COMPARTIDA
// =====================================================

MATCH (p:Persona)-[:REALIZA]->(:Solicitud)-[:SE_ORIGINA_EN]->(ip:IP)
MATCH (ip)<-[:SE_ORIGINA_EN]-(:Solicitud)<-[:REALIZA]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_ip = total;


// =====================================================
// 11. RIESGO POR DOMICILIO COMPARTIDO
// =====================================================

MATCH (p:Persona)-[:DECLARA_DOMICILIO]->(d:Domicilio)<-[:DECLARA_DOMICILIO]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_dom = total;


// =====================================================
// 12. BANDERA DE SIMILITUD RELACIONAL
// =====================================================

MATCH (p1:Persona)-[:TIENE_TELEFONO|TIENE_CORREO|DECLARA_DOMICILIO]->(x)<-[:TIENE_TELEFONO|TIENE_CORREO|DECLARA_DOMICILIO]-(p2:Persona)
WHERE id(p1) < id(p2)
WITH p1, p2, count(DISTINCT x) AS atributos_compartidos
WHERE atributos_compartidos >= 2
SET p1.similarity_flag = 1,
    p2.similarity_flag = 1;


// =====================================================
// 13. SCORE FINAL
// =====================================================

MATCH (p:Persona)
SET p.risk_score =
    coalesce(p.risk_tel, 0) * 2 +
    coalesce(p.risk_device, 0) * 3 +
    coalesce(p.risk_ip, 0) * 2 +
    coalesce(p.risk_dom, 0) * 1 +
    coalesce(p.similarity_flag, 0) * 4;


// =====================================================
// 14. CLASIFICACIÓN DE RIESGO
// =====================================================

MATCH (p:Persona)
SET p.risk_level =
CASE
    WHEN p.risk_score >= 35 THEN "ALTO"
    WHEN p.risk_score >= 20 THEN "MEDIO"
    ELSE "BAJO"
END;


// =====================================================
// 15. VALIDACIÓN DE SCORE
// =====================================================

MATCH (p:Persona)
RETURN p.es_fraude AS fraude_real,
       p.risk_level AS nivel_riesgo,
       count(*) AS total
ORDER BY fraude_real DESC, nivel_riesgo;


MATCH (p:Persona)
RETURN p.id_persona AS id_persona,
       p.nombre AS nombre,
       p.apellido_paterno AS apellido_paterno,
       p.es_fraude AS fraude_real,
       p.risk_tel AS telefono_compartido,
       p.risk_device AS dispositivo_compartido,
       p.risk_ip AS ip_compartida,
       p.risk_dom AS domicilio_compartido,
       p.similarity_flag AS similitud,
       p.risk_score AS score,
       p.risk_level AS nivel_riesgo
ORDER BY score DESC
LIMIT 50;


// =====================================================
// 16. GRAPH DATA SCIENCE
// =====================================================
// Ejecuta este bloque solo si CALL gds.version(); funciona.

CALL gds.graph.project(
  'fraudeGraph',
  ['Persona', 'Telefono', 'Correo', 'Domicilio', 'Dispositivo', 'IP', 'Solicitud'],
  {
    TIENE_TELEFONO: {orientation: 'UNDIRECTED'},
    TIENE_CORREO: {orientation: 'UNDIRECTED'},
    DECLARA_DOMICILIO: {orientation: 'UNDIRECTED'},
    REALIZA: {orientation: 'UNDIRECTED'},
    USA_DISPOSITIVO: {orientation: 'UNDIRECTED'},
    SE_ORIGINA_EN: {orientation: 'UNDIRECTED'}
  }
);


CALL gds.louvain.write('fraudeGraph', {
  writeProperty: 'community_id'
})
YIELD communityCount, modularity
RETURN communityCount, modularity;


CALL gds.degree.write('fraudeGraph', {
  writeProperty: 'degree_centrality'
})
YIELD centralityDistribution
RETURN centralityDistribution;


// =====================================================
// 17. AGREGADOS PARA DASHBOARD
// =====================================================

CREATE CONSTRAINT kpi_resumen_id IF NOT EXISTS
FOR (k:KPIResumen) REQUIRE k.id IS UNIQUE;

CREATE CONSTRAINT comunidad_resumen_id IF NOT EXISTS
FOR (c:ComunidadResumen) REQUIRE c.community_id IS UNIQUE;

CREATE CONSTRAINT riesgo_resumen_nivel IF NOT EXISTS
FOR (r:RiesgoResumen) REQUIRE r.nivel IS UNIQUE;

CREATE CONSTRAINT transaccion_tipo_resumen_id IF NOT EXISTS
FOR (tr:TransaccionTipoResumen) REQUIRE tr.tipo IS UNIQUE;


// KPI global de personas
MATCH (p:Persona)
WITH count(p) AS total_clientes,
     sum(CASE WHEN p.risk_level = "ALTO" THEN 1 ELSE 0 END) AS alto,
     sum(CASE WHEN p.risk_level = "MEDIO" THEN 1 ELSE 0 END) AS medio,
     sum(CASE WHEN p.risk_level = "BAJO" THEN 1 ELSE 0 END) AS bajo,
     avg(p.risk_score) AS score_promedio
MERGE (k:KPIResumen {id: "global"})
SET k.total_clientes = total_clientes,
    k.alto_riesgo = alto,
    k.medio_riesgo = medio,
    k.bajo_riesgo = bajo,
    k.score_promedio = round(score_promedio, 2),
    k.actualizado = datetime();


// Resumen por riesgo
MATCH (p:Persona)
WITH p.risk_level AS nivel, count(*) AS total
MERGE (r:RiesgoResumen {nivel: nivel})
SET r.total = total,
    r.actualizado = datetime();


// Resumen por comunidad
MATCH (p:Persona)
WHERE p.community_id IS NOT NULL
WITH p.community_id AS comunidad,
     count(p) AS total_personas,
     sum(CASE WHEN p.risk_level = "ALTO" THEN 1 ELSE 0 END) AS alto_riesgo,
     avg(p.risk_score) AS score_promedio
MERGE (c:ComunidadResumen {community_id: comunidad})
SET c.total_personas = total_personas,
    c.alto_riesgo = alto_riesgo,
    c.score_promedio = round(score_promedio, 2),
    c.actualizado = datetime();


// KPI global transaccional
MATCH (t:Transaccion)
WITH count(t) AS total_transacciones,
     avg(t.monto) AS monto_promedio,
     sum(t.monto) AS volumen_total
MERGE (k:KPIResumen {id: "global"})
SET k.total_transacciones = total_transacciones,
    k.monto_promedio = round(monto_promedio, 2),
    k.volumen_total = round(volumen_total, 2),
    k.actualizado = datetime();


// Resumen por tipo de transacción
MATCH (t:Transaccion)
WITH t.tipo AS tipo,
     count(*) AS total,
     avg(t.monto) AS monto_promedio,
     sum(t.monto) AS volumen_total
MERGE (tr:TransaccionTipoResumen {tipo: tipo})
SET tr.total = total,
    tr.monto_promedio = round(monto_promedio, 2),
    tr.volumen_total = round(volumen_total, 2),
    tr.actualizado = datetime();


// =====================================================
// 18. VALIDACIONES FINALES
// =====================================================

MATCH (k:KPIResumen {id: "global"})
RETURN k;


MATCH (r:RiesgoResumen)
RETURN r.nivel, r.total
ORDER BY r.total DESC;


MATCH (c:ComunidadResumen)
RETURN c.community_id,
       c.total_personas,
       c.alto_riesgo,
       c.score_promedio
ORDER BY c.alto_riesgo DESC, c.score_promedio DESC
LIMIT 25;


MATCH (tr:TransaccionTipoResumen)
RETURN tr.tipo,
       tr.total,
       tr.monto_promedio,
       tr.volumen_total
ORDER BY tr.total DESC;


SHOW INDEXES;