
// =====================================================
// 5. ÍNDICES PARA CONSULTAS Y DASHBOARD
// =====================================================

CREATE INDEX persona_risk_level IF NOT EXISTS
FOR (p:Persona) ON (p.risk_level);

CREATE INDEX persona_risk_score IF NOT EXISTS
FOR (p:Persona) ON (p.risk_score);

CREATE INDEX persona_community_id IF NOT EXISTS
FOR (p:Persona) ON (p.community_id);

CREATE INDEX persona_es_fraude IF NOT EXISTS
FOR (p:Persona) ON (p.es_fraude);

CREATE INDEX solicitud_fecha IF NOT EXISTS
FOR (s:Solicitud) ON (s.fecha_solicitud);

CREATE INDEX transaccion_fecha IF NOT EXISTS
FOR (t:Transaccion) ON (t.fecha_hora);

CREATE INDEX transaccion_monto IF NOT EXISTS
FOR (t:Transaccion) ON (t.monto);

CREATE INDEX transaccion_tipo IF NOT EXISTS
FOR (t:Transaccion) ON (t.tipo);
