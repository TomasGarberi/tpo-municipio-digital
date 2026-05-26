// ============================================================
// CONSULTAS NEO4J — TPO Municipio Digital
// ============================================================


// ------------------------------------------------------------
// A) Flujo completo de un tipo de trámite
// ------------------------------------------------------------
// Muestra los organismos por los que pasa un tipo de trámite.
MATCH (tipo:TipoTramite {nombre: 'Habilitacion comercial'})-[r:INICIA_EN|PASA_POR]->(org:Organismo)
RETURN tipo.nombre AS tipo_tramite,
       type(r) AS relacion,
       org.nombre AS organismo,
       r.orden AS orden
ORDER BY orden;


// ------------------------------------------------------------
// B) Organismo más crítico de la red
// ------------------------------------------------------------
// Identifica el organismo que afecta a más tipos de trámite.
MATCH (org:Organismo)<-[:INICIA_EN|PASA_POR]-(tipo:TipoTramite)
WITH org,
     collect(DISTINCT tipo.nombre) AS tipos_tramite_afectados,
     count(DISTINCT tipo) AS cantidad_tipos_afectados
RETURN org.nombre AS organismo_critico,
       cantidad_tipos_afectados,
       tipos_tramite_afectados
ORDER BY cantidad_tipos_afectados DESC, organismo_critico ASC
LIMIT 1;


// ------------------------------------------------------------
// C) Estado actual de un trámite y etapas restantes
// ------------------------------------------------------------
// Ubica el trámite dentro del flujo y calcula lo que falta.
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
WITH t, tipo, orgActual,
     etapa.orden AS posicion_actual,
     size(etapas) AS etapas_totales
RETURN t.numero AS tramite,
       tipo.nombre AS tipo_tramite,
       orgActual.nombre AS organismo_actual,
       posicion_actual,
       etapas_totales,
       (etapas_totales - posicion_actual) AS etapas_faltantes;


// ------------------------------------------------------------
// D) Detección de ciclos en el flujo
// ------------------------------------------------------------
// Busca loops en derivaciones entre organismos.
MATCH (tipo:TipoTramite {nombre: 'Habilitacion comercial'})-[:INICIA_EN|PASA_POR]->(org:Organismo)
MATCH p = (org)-[:DERIVA_A*1..10]->(org)
RETURN tipo.nombre AS tipo_tramite, p;


// ------------------------------------------------------------
// E) Trámites de un ciudadano y dependencias
// ------------------------------------------------------------
// Devuelve trámites y relaciones de dependencia.
MATCH (c:Ciudadano {dni: '30000001'})-[:INICIO]->(t:Tramite)
OPTIONAL MATCH (t)-[r:DEPENDE_DE]->(dep:Tramite)
RETURN c.nombre + ' ' + c.apellido AS ciudadano,
       t.numero AS tramite,
       t.estado AS estado,
       dep.numero AS depende_de,
       dep.estado AS estado_dependencia,
       r.motivo AS motivo
ORDER BY tramite;
