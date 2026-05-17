// =====================================================
// 4. CARGA DE RELACIONES
// =====================================================

LOAD CSV WITH HEADERS FROM 'file:///persona_solicitud.csv' AS row
CALL {
  WITH row
  MATCH (p:Persona {id_persona: row.id_persona})
  MATCH (s:Solicitud {id_solicitud: row.id_solicitud})
  MERGE (p)-[:REALIZA]->(s)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///persona_telefono.csv' AS row
CALL {
  WITH row
  MATCH (p:Persona {id_persona: row.id_persona})
  MATCH (t:Telefono {id_telefono: row.id_telefono})
  MERGE (p)-[:TIENE_TELEFONO]->(t)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///persona_correo.csv' AS row
CALL {
  WITH row
  MATCH (p:Persona {id_persona: row.id_persona})
  MATCH (c:Correo {id_correo: row.id_correo})
  MERGE (p)-[:TIENE_CORREO]->(c)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///persona_domicilio.csv' AS row
CALL {
  WITH row
  MATCH (p:Persona {id_persona: row.id_persona})
  MATCH (d:Domicilio {id_domicilio: row.id_domicilio})
  MERGE (p)-[:DECLARA_DOMICILIO]->(d)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///persona_documento.csv' AS row
CALL {
  WITH row
  MATCH (p:Persona {id_persona: row.id_persona})
  MATCH (d:Documento {id_documento: row.id_documento})
  MERGE (p)-[:PRESENTA]->(d)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///persona_cuenta.csv' AS row
CALL {
  WITH row
  MATCH (p:Persona {id_persona: row.id_persona})
  MATCH (c:Cuenta {id_cuenta: row.id_cuenta})
  MERGE (p)-[:POSEE]->(c)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///solicitud_dispositivo.csv' AS row
CALL {
  WITH row
  MATCH (s:Solicitud {id_solicitud: row.id_solicitud})
  MATCH (d:Dispositivo {id_dispositivo: row.id_dispositivo})
  MERGE (s)-[:USA_DISPOSITIVO]->(d)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///solicitud_ip.csv' AS row
CALL {
  WITH row
  MATCH (s:Solicitud {id_solicitud: row.id_solicitud})
  MATCH (ip:IP {id_ip: row.id_ip})
  MERGE (s)-[:SE_ORIGINA_EN]->(ip)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///cuenta_transaccion.csv' AS row
CALL {
  WITH row
  MATCH (c:Cuenta {id_cuenta: row.id_cuenta})
  MATCH (t:Transaccion {id_transaccion: row.id_transaccion})
  MERGE (c)-[:REALIZA]->(t)
} IN TRANSACTIONS OF 20000 ROWS;

