// ============================================================
// CONSULTAS NEO4J — TPO Municipio Digital
// Consultas alineadas con la consigna
// ============================================================

// --- C1: Flujo completo de derivaciones posibles entre organismos ---
// Dado un tipo de tramite, muestra los organismos involucrados
// en su flujo (inicio + pasos posteriores).
MATCH (tipo:TipoTramite {nombre: 'Habilitacion comercial'})-[r:INICIA_EN|PASA_POR]->(org:Organismo)
RETURN tipo.nombre AS tipo_tramite,
       type(r) AS relacion,
       org.nombre AS organismo,
       r.orden AS orden
ORDER BY orden;

// --- C2: Organismo mas critico de la red ---------------------
// Aproximacion: organismo que participa en la mayor cantidad
// de tipos de tramite distintos.
MATCH (tipo:TipoTramite)-[:INICIA_EN|PASA_POR]->(org:Organismo)
RETURN org.nombre AS organismo,
       COUNT(DISTINCT tipo) AS tipos_afectados
ORDER BY tipos_afectados DESC
LIMIT 1;

// --- C3: Punto actual del flujo de un tramite en curso -------
// Dado un tramite, muestra organismo actual, posicion en el flujo
// y cantidad de etapas faltantes.
MATCH (t:Tramite {numero: 'TRA-2026-000001'})-[:ES_DE_TIPO]->(tipo:TipoTramite),
      (t)-[:ESTA_EN]->(orgActual:Organismo),
      (tipo)-[r:INICIA_EN|PASA_POR]->(org:Organismo)
WITH t, tipo, orgActual,
     collect({
       organismo: org.nombre,
       orden: coalesce(r.orden, 1)
     }) AS etapas
UNWIND etapas AS etapa
WITH t, tipo, orgActual, etapas, etapa
WHERE etapa.organismo = orgActual.nombre
WITH t, tipo, orgActual, etapa.orden AS posicion_actual, size(etapas) AS etapas_totales
RETURN t.numero AS tramite,
       tipo.nombre AS tipo_tramite,
       orgActual.nombre AS organismo_actual,
       posicion_actual,
       etapas_totales,
       (etapas_totales - posicion_actual) AS etapas_faltantes;

// --- C4: Deteccion de ciclos en el flujo de derivaciones -----
// Busca ciclos entre organismos para el tipo de tramite indicado.
MATCH (tipo:TipoTramite {nombre: 'Habilitacion comercial'})-[:INICIA_EN|PASA_POR]->(orgInicio:Organismo)
MATCH p = (orgInicio)-[:DERIVA_A*1..10]->(orgInicio)
RETURN tipo.nombre AS tipo_tramite,
       p;

// --- C5: Tramites de un ciudadano y dependencias entre ellos --
// Devuelve todos los tramites del ciudadano y, si existen,
// sus dependencias con otros tramites.
MATCH (c:Ciudadano {dni: '30000001'})-[:INICIO]->(t:Tramite)
OPTIONAL MATCH (t)-[r:DEPENDE_DE]->(dep:Tramite)
RETURN c.nombre + ' ' + c.apellido AS ciudadano,
       t.numero AS tramite,
       t.estado AS estado,
       dep.numero AS depende_de,
       dep.estado AS estado_dependencia,
       r.motivo AS motivo
ORDER BY tramite;
