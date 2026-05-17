// =====================================================
// 0. OPCIONAL: CREAR DATABASE
// =====================================================
// En algunas versiones de Neo4j Desktop se trabaja directo sobre la DB activa.
// Si tu versión permite CREATE DATABASE, puedes usar:
//
// CREATE DATABASE fraude_bancario_2M;
// :use fraude_bancario_2M
//
// Si no, crea la instancia/base desde Neo4j Desktop y ejecuta todo ahí.


// =====================================================
// 1. LIMPIAR BASE
// =====================================================

MATCH (n)
DETACH DELETE n;