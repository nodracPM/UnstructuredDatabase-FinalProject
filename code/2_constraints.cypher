// =====================================================
// 2. CONSTRAINTS DE UNICIDAD
// =====================================================

CREATE CONSTRAINT persona_id IF NOT EXISTS
FOR (p:Persona) REQUIRE p.id_persona IS UNIQUE;

CREATE CONSTRAINT solicitud_id IF NOT EXISTS
FOR (s:Solicitud) REQUIRE s.id_solicitud IS UNIQUE;

CREATE CONSTRAINT telefono_id IF NOT EXISTS
FOR (t:Telefono) REQUIRE t.id_telefono IS UNIQUE;

CREATE CONSTRAINT correo_id IF NOT EXISTS
FOR (c:Correo) REQUIRE c.id_correo IS UNIQUE;

CREATE CONSTRAINT domicilio_id IF NOT EXISTS
FOR (d:Domicilio) REQUIRE d.id_domicilio IS UNIQUE;

CREATE CONSTRAINT dispositivo_id IF NOT EXISTS
FOR (d:Dispositivo) REQUIRE d.id_dispositivo IS UNIQUE;

CREATE CONSTRAINT ip_id IF NOT EXISTS
FOR (ip:IP) REQUIRE ip.id_ip IS UNIQUE;

CREATE CONSTRAINT documento_id IF NOT EXISTS
FOR (d:Documento) REQUIRE d.id_documento IS UNIQUE;

CREATE CONSTRAINT cuenta_id IF NOT EXISTS
FOR (c:Cuenta) REQUIRE c.id_cuenta IS UNIQUE;

CREATE CONSTRAINT transaccion_id IF NOT EXISTS
FOR (t:Transaccion) REQUIRE t.id_transaccion IS UNIQUE;