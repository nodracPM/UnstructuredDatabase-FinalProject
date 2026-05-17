// =====================================================
// 1. RESET DE INDICADORES
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
// 2. RIESGO POR TELÉFONO
// =====================================================
MATCH (p:Persona)-[:TIENE_TELEFONO]->(t:Telefono)<-[:TIENE_TELEFONO]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_tel = total;


// =====================================================
// 3. RIESGO POR DISPOSITIVO
// =====================================================
MATCH (p:Persona)-[:REALIZA]->(:Solicitud)-[:USA_DISPOSITIVO]->(d:Dispositivo)
MATCH (d)<-[:USA_DISPOSITIVO]-(:Solicitud)<-[:REALIZA]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_device = total;


// =====================================================
// 4. RIESGO POR IP
// =====================================================
MATCH (p:Persona)-[:REALIZA]->(:Solicitud)-[:SE_ORIGINA_EN]->(ip:IP)
MATCH (ip)<-[:SE_ORIGINA_EN]-(:Solicitud)<-[:REALIZA]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_ip = total;


// =====================================================
// 5. RIESGO POR DOMICILIO
// =====================================================
MATCH (p:Persona)-[:DECLARA_DOMICILIO]->(d:Domicilio)<-[:DECLARA_DOMICILIO]-(otros:Persona)
WHERE p <> otros
WITH p, count(DISTINCT otros) AS total
SET p.risk_dom = total;


// =====================================================
// 6. SIMILITUD RELACIONAL
// =====================================================
MATCH (p1:Persona)-[:TIENE_TELEFONO|TIENE_CORREO|DECLARA_DOMICILIO]->(x)<-[:TIENE_TELEFONO|TIENE_CORREO|DECLARA_DOMICILIO]-(p2:Persona)
WHERE id(p1) < id(p2)
WITH p1, p2, count(DISTINCT x) AS atributos_compartidos
WHERE atributos_compartidos >= 2
SET p1.similarity_flag = 1,
    p2.similarity_flag = 1;


// =====================================================
// 7. SCORE FINAL
// =====================================================
MATCH (p:Persona)
SET p.risk_score =
    coalesce(p.risk_tel, 0) * 2 +
    coalesce(p.risk_device, 0) * 3 +
    coalesce(p.risk_ip, 0) * 2 +
    coalesce(p.risk_dom, 0) * 1 +
    coalesce(p.similarity_flag, 0) * 4;


// =====================================================
// 8. CLASIFICACIÓN DE RIESGO
// =====================================================
MATCH (p:Persona)
SET p.risk_level =
CASE
    WHEN p.risk_score >= 35 THEN "ALTO"
    WHEN p.risk_score >= 20 THEN "MEDIO"
    ELSE "BAJO"
END;


// =====================================================
// 9. VALIDAR QUE YA EXISTE risk_level
// =====================================================
MATCH (p:Persona)
RETURN p.risk_level AS nivel, count(*) AS total
ORDER BY total DESC;