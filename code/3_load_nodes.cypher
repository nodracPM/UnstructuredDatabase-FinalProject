// =====================================================
// 3. CARGA DE NODOS
// =====================================================

LOAD CSV WITH HEADERS FROM 'file:///personas.csv' AS row
CALL {
  WITH row
  MERGE (p:Persona {id_persona: row.id_persona})
  SET p.nombre = row.nombre,
      p.apellido_paterno = row.apellido_paterno,
      p.apellido_materno = row.apellido_materno,
      p.fecha_nacimiento = date(row.fecha_nacimiento),
      p.curp = row.curp,
      p.rfc = row.rfc,
      p.es_fraude = toInteger(row.es_fraude)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///solicitudes.csv' AS row
CALL {
  WITH row
  MERGE (s:Solicitud {id_solicitud: row.id_solicitud})
  SET s.fecha_solicitud = date(row.fecha_solicitud),
      s.canal = row.canal,
      s.estatus = row.estatus,
      s.score_inicial = toInteger(row.score_inicial)
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///telefonos.csv' AS row
CALL {
  WITH row
  MERGE (t:Telefono {id_telefono: row.id_telefono})
  SET t.numero = row.numero
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///correos.csv' AS row
CALL {
  WITH row
  MERGE (c:Correo {id_correo: row.id_correo})
  SET c.email = row.email
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///domicilios.csv' AS row
CALL {
  WITH row
  MERGE (d:Domicilio {id_domicilio: row.id_domicilio})
  SET d.calle = row.calle,
      d.numero = row.numero,
      d.colonia = row.colonia,
      d.ciudad = row.ciudad,
      d.estado = row.estado,
      d.codigo_postal = row.codigo_postal
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///dispositivos.csv' AS row
CALL {
  WITH row
  MERGE (d:Dispositivo {id_dispositivo: row.id_dispositivo})
  SET d.tipo = row.tipo,
      d.sistema_operativo = row.sistema_operativo,
      d.huella_digital = row.huella_digital
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///ips.csv' AS row
CALL {
  WITH row
  MERGE (ip:IP {id_ip: row.id_ip})
  SET ip.direccion_ip = row.direccion_ip,
      ip.proveedor = row.proveedor,
      ip.ubicacion_aproximada = row.ubicacion_aproximada
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///documentos.csv' AS row
CALL {
  WITH row
  MERGE (d:Documento {id_documento: row.id_documento})
  SET d.tipo_documento = row.tipo_documento,
      d.folio = row.folio,
      d.estatus_validacion = row.estatus_validacion
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///cuentas.csv' AS row
CALL {
  WITH row
  MERGE (c:Cuenta {id_cuenta: row.id_cuenta})
  SET c.fecha_apertura = date(row.fecha_apertura),
      c.tipo_cuenta = row.tipo_cuenta,
      c.estatus = row.estatus
} IN TRANSACTIONS OF 10000 ROWS;


LOAD CSV WITH HEADERS FROM 'file:///transacciones.csv' AS row
CALL {
  WITH row
  MERGE (t:Transaccion {id_transaccion: row.id_transaccion})
  SET t.fecha_hora = datetime(row.fecha_hora),
      t.monto = toFloat(row.monto),
      t.tipo = row.tipo,
      t.estatus = row.estatus
} IN TRANSACTIONS OF 20000 ROWS;


