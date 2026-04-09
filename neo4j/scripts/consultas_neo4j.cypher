// ============================================================
// CONSULTAS NEO4J — TPO Municipio Digital
// ============================================================

// --- C1: Recorrido completo de un tramite especifico ----------
// Muestra el ciudadano que lo inicio, el tipo, los organismos
// por los que debe pasar segun su tipo, y donde esta ahora.
MATCH (c:Ciudadano)-[:INICIO]->(t:Tramite {numero: 'TRA-2026-000001'})-[:ES_DE_TIPO]->(tipo:TipoTramite),
      (tipo)-[:INICIA_EN|PASA_POR]->(org:Organismo),
      (t)-[:ESTA_EN]->(orgActual:Organismo)
RETURN c.nombre + ' ' + c.apellido AS ciudadano,
       t.numero AS tramite,
       t.estado  AS estado,
       tipo.nombre AS tipo,
       collect(DISTINCT org.nombre) AS flujo_organismos,
       orgActual.nombre AS organismo_actual;

// --- C2: Flujo completo de un tipo de tramite ----------------
// Util para visualizar el camino en el grafo.
MATCH path = (tipo:TipoTramite {nombre: 'Habilitacion comercial'})-[:INICIA_EN|PASA_POR*]->(org:Organismo)
RETURN path;

// --- C3: Organismos mas demandados (cuello de botella) --------
// Cuenta cuantos tipos de tramite pasan por cada organismo.
MATCH (tipo:TipoTramite)-[:INICIA_EN|PASA_POR]->(org:Organismo)
RETURN org.nombre AS organismo, COUNT(DISTINCT tipo) AS tipos_de_tramite
ORDER BY tipos_de_tramite DESC;

// --- C4: Tramites actualmente en cada organismo ---------------
MATCH (t:Tramite)-[:ESTA_EN]->(org:Organismo)
WHERE t.estado <> 'resuelto'
RETURN org.nombre AS organismo, COUNT(t) AS tramites_activos
ORDER BY tramites_activos DESC;

// --- C5: Cadena de derivaciones entre organismos -------------
MATCH (o1:Organismo)-[r:DERIVA_A]->(o2:Organismo)
RETURN o1.nombre AS origen, r.condicion AS condicion, o2.nombre AS destino
ORDER BY origen;

// --- C6: Tramites con dependencias sin resolver ---------------
// Muestra tramites bloqueados porque dependen de otro pendiente.
MATCH (t:Tramite)-[:DEPENDE_DE]->(dep:Tramite)
WHERE dep.estado <> 'resuelto'
RETURN t.numero AS tramite_bloqueado,
       t.estado  AS estado_bloqueado,
       dep.numero AS depende_de,
       dep.estado  AS estado_dependencia;

// --- C7: Todos los tramites de un ciudadano ------------------
MATCH (c:Ciudadano {dni: '30000001'})-[:INICIO]->(t:Tramite)-[:ES_DE_TIPO]->(tipo:TipoTramite)
RETURN t.numero AS tramite, tipo.nombre AS tipo, t.estado AS estado, t.fecha_inicio AS inicio
ORDER BY t.fecha_inicio;

// --- C8: Ciudadanos con mas tramites iniciados ---------------
MATCH (c:Ciudadano)-[:INICIO]->(t:Tramite)
RETURN c.nombre + ' ' + c.apellido AS ciudadano, COUNT(t) AS cantidad_tramites
ORDER BY cantidad_tramites DESC
LIMIT 5;

// --- C9: Grafo completo de dependencias entre tramites --------
MATCH path = (t:Tramite)-[:DEPENDE_DE*]->(dep:Tramite)
RETURN path;

// --- C10: Organismos sin carga activa ------------------------
MATCH (org:Organismo)
WHERE NOT EXISTS {
  MATCH (t:Tramite)-[:ESTA_EN]->(org)
  WHERE t.estado IN ['pendiente', 'en_revision']
}
RETURN org.nombre AS organismo_sin_carga_activa;