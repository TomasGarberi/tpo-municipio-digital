-- ============================================================
-- SCHEMA CASSANDRA / ASTRA DB

-- TPO Municipio Digital
-- ============================================================

-- Definición de tablas Cassandra.
-- Pendiente de confirmación según implementación final.
=======
-- Motor: Apache Cassandra
-- Keyspace: municipio_digital
-- ============================================================
-- cada tabla responde a una query específica.
-- ============================================================


-- ============================================================
-- TABLA: eventos_tramite
-- CU: obtener todos los eventos procesados por un
--organismo en una fecha dada.
--
-- Partition key: (organismo_id, fecha)
--    todos los eventos de un organismo en un dia quedan en
--     la misma partición; lectura eficiente por organismo+dia.
-- Clustering key: timestamp DESC
--    el evento mas reciente aparece primero, esto facilita ver
--     la actividad más nueva sin reordenar en el cliente.
-- ============================================================
CREATE TABLE IF NOT EXISTS eventos_tramite (
    organismo_id  TEXT,
    fecha         DATE,
    timestamp     TIMESTAMP,
    tramite_id    TEXT,
    tipo          TEXT,
    agente_id     TEXT,
    duracion_min  INT,
    detalle       TEXT,
    PRIMARY KEY ((organismo_id, fecha), timestamp, tramite_id)
) WITH CLUSTERING ORDER BY (timestamp DESC, tramite_id ASC);


-- ============================================================
-- TABLA: eventos_por_tramite
-- CU: reconstruir el historial completo de un tramite
-- en orden cronológico (vista del ciudadano / panel OP-1).
--
-- Partition key: tramite_id
--    todos los eventos del tramite en la misma particion;
--     lectura constante O(1) independientemente del volumen total.
-- Clustering key: timestamp ASC
--    es orden cronologico ascendente para reconstruir el flujo.
--
-- Aclaracion: duplica intencional del mismo evento respecto a
-- eventos_tramite. mayor uso de almacenamiento a
-- cambio de dos queries de alta performance con distinto punto
-- de acceso (por organismo vs. por tramite).
-- ============================================================
CREATE TABLE IF NOT EXISTS eventos_por_tramite (
    tramite_id   TEXT,
    timestamp    TIMESTAMP,
    organismo_id TEXT,
    tipo         TEXT,
    agente_id    TEXT,
    duracion_min INT,
    detalle      TEXT,
    PRIMARY KEY (tramite_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp ASC);


-- ============================================================
-- TABLA: metricas_organismo
-- CU: metricas diarias y mensuales de cada organismo
-- para el panel de desempeño(OP-3) y analisis de cuellos
-- de botella (OP-4).
--
-- Partition key: (organismo_id, anio_mes)
--    todos los dias de un organismo en un mes agrupados.
--     permite analizar la evolución mensual de forma directa.
-- Clustering key: fecha ASC
--    recorrido cronologico del mes sin reordenar.
-- ============================================================
CREATE TABLE IF NOT EXISTS metricas_organismo (
    organismo_id          TEXT,
    anio_mes              TEXT,
    fecha                 DATE,
    tramites_procesados   INT,
    tiempo_promedio_min   FLOAT,
    sla_cumplidos         INT,
    sla_incumplidos       INT,
    PRIMARY KEY ((organismo_id, anio_mes), fecha)
) WITH CLUSTERING ORDER BY (fecha ASC);


-- ============================================================
-- TABLA: demanda_tipo_tramite
-- CU: analisis de demanda mensual por tipo de trámite
-- y zona geográfica(OP-5 reporte ejecutivo).
--
-- Partition key: (tipo_tramite, anio_mes)
--    toda la demanda de un tipo en un mes en una particioo,
--     permite comparar zonas y detectar crecimiento mensual.
-- Clustering key: (fecha ASC, zona ASC)
--   permite filtrar por día o zona dentro del mes.
--
-- Por que de residencia en Cassandra vs MongoDB:
--   esta tabla recibe escrituras continuas(cada solicitud
--   incrementa el contador de su zona y fecha). MongoDB no
--   está optimizado para alta concurrencia de
--   escrituras sobre el mismo documento. Cassandra escala
--   horizontalmente y se maneja de forma nativa.
-- ============================================================
CREATE TABLE IF NOT EXISTS demanda_tipo_tramite (
    tipo_tramite TEXT,
    anio_mes     TEXT,
    fecha        DATE,
    zona         TEXT,
    total        INT,
    PRIMARY KEY ((tipo_tramite, anio_mes), fecha, zona)
) WITH CLUSTERING ORDER BY (fecha ASC, zona ASC);


-- ============================================================
-- TABLA: notificaciones_ciudadano
-- CU: historial de notificaciones enviadas a un
-- ciudadano (OP-1 panel ciudadano, canal de comunicaciones).
--
-- Partition key: ciudadano_id
--    todas las notificaciones del ciudadano en una partición,
--     sin scan global para mostrar el buzon de un usuario.
-- Clustering key: timestamp DESC
--    notificaciones ordenadas desde la mas reciente.
-- ============================================================
CREATE TABLE IF NOT EXISTS notificaciones_ciudadano (
    ciudadano_id TEXT,
    timestamp    TIMESTAMP,
    tramite_id   TEXT,
    tipo         TEXT,
    canal        TEXT,
    mensaje      TEXT,
    leida        BOOLEAN,
    PRIMARY KEY (ciudadano_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);
>>>>>>> 63d8c301b7902a1ea1b8f77991a74b55ee603fcf
