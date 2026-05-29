# Decisiones de Modelado — Cassandra + Capa Políglota
## Segunda Entrega · TPO Municipio Digital

---

## 1. Por qué Cassandra para este dominio

El dominio municipal genera dos tipos de datos con características opuestas:

- **Datos estáticos y relacionales** (trámites, ciudadanos, flujos): baja frecuencia de escritura, consultas complejas con joins → MongoDB y Neo4j.
- **Series temporales de alto volumen** (eventos, métricas diarias, notificaciones): escritura continua desde múltiples organismos, consultas por rango de tiempo → Cassandra.

Con 8 organismos procesando trámites continuamente, los eventos se acumulan a un ritmo que haría crecer el array embebido de MongoDB sin control. Cassandra resuelve este problema particionando los eventos por organismo y fecha, de modo que cada partición contiene únicamente los eventos de un organismo en un día: volumen acotado y lectura eficiente.

---

## 2. Principio de diseño: query-driven modeling

A diferencia de MongoDB (modelo documental orientado a la entidad) o de un modelo relacional (normalización), Cassandra se diseña a partir de las consultas esperadas. Cada tabla responde a exactamente un patrón de acceso.

**Consecuencia directa:** un mismo evento se escribe en DOS tablas (desnormalización intencional). Esto es una decisión correcta en Cassandra: se sacrifica espacio de almacenamiento para garantizar lecturas O(1) desde cualquier punto de acceso.

---

## 3. Tablas y justificación de claves

### 3.1 `eventos_tramite`
**Patrón de acceso:** "¿Qué eventos procesó el organismo X en la fecha Y?"

```
Partition Key: (organismo_id, fecha)
Clustering Key: timestamp DESC, tramite_id ASC
```

**Justificación:** agrupar por organismo+fecha garantiza que todos los eventos de un día de trabajo queden en la misma partición. El orden descendente por timestamp prioriza los eventos más recientes, que son los más consultados en el panel operativo.

---

### 3.2 `eventos_por_tramite`
**Patrón de acceso:** "¿Cuál es el historial completo del trámite X?"

```
Partition Key: tramite_id
Clustering Key: timestamp ASC
```

**Justificación:** toda la historia de un trámite en una sola partición. Independientemente de cuántos trámites existan en el sistema, la lectura es O(1) en función del `tramite_id`. El orden ascendente reconstruye el flujo cronológico sin reordenamiento en el cliente.

**Desnormalización respecto a `eventos_tramite`:** ambas tablas almacenan el mismo evento. La duplicación es intencional y justificada porque los dos patrones de acceso (por organismo y por trámite) son igualmente frecuentes y prioritarios.

---

### 3.3 `metricas_organismo`
**Patrón de acceso:** "¿Cuáles son las métricas del organismo X en el mes Y?"

```
Partition Key: (organismo_id, anio_mes)
Clustering Key: fecha ASC
```

**Justificación:** un mes de métricas de un organismo tiene exactamente entre 28 y 31 filas: partición de tamaño fijo y predecible. Agrupar por mes permite analizar la evolución mensual sin escaneos. El orden ascendente por fecha facilita el recorrido cronológico del panel de desempeño.

---

### 3.4 `demanda_tipo_tramite`
**Patrón de acceso:** "¿Cuántas solicitudes del tipo X hubo en el mes Y, desglosado por zona?"

```
Partition Key: (tipo_tramite, anio_mes)
Clustering Key: fecha ASC, zona ASC
```

**Justificación:** permite comparar la demanda de un tipo de trámite entre zonas geográficas dentro de un mes. Cassandra es ideal para esta tabla porque recibe escrituras de alta concurrencia (cada nueva solicitud incrementa el contador de su zona y fecha), sin la degradación que sufriría MongoDB ante inserciones masivas sobre el mismo documento.

---

### 3.5 `notificaciones_ciudadano`
**Patrón de acceso:** "¿Cuáles son las últimas notificaciones del ciudadano X?"

```
Partition Key: ciudadano_id
Clustering Key: timestamp DESC
```

**Justificación:** todas las notificaciones de un ciudadano en una sola partición permite mostrar el buzón sin scan global. El orden descendente muestra primero las notificaciones más recientes, que son las de mayor relevancia para el usuario.

---

## 4. Responsabilidades en la capa políglota

| Operación | MongoDB | Neo4j | Cassandra |
|---|---|---|---|
| OP-1: Panel ciudadano | Datos maestros del trámite | Etapas restantes del flujo | Historial de eventos |
| OP-2: Procesar evento | Actualizar estado + push array | Actualizar posición en grafo | INSERT doble eventos |
| OP-3: Panel desempeño | Trámites activos + alertas SLA | No participa | Métricas diarias del mes |
| OP-4: Cuellos de botella | No participa | Centralidad del organismo | Ranking SLA incumplidos |
| OP-5: Reporte ejecutivo | Distribución de estados | Complejidad de flujos | Demanda por tipo y zona |

---

## 5. Coherencia eventual y manejo de fallos

La capa políglota no implementa transacciones distribuidas (no hay 2PC). Se asume un modelo de coherencia eventual:

- **OP-2** escribe primero en Cassandra (log de eventos). Si esta escritura falla, la operación se aborta y no se modifica ningún otro motor.
- Si Cassandra escribe correctamente pero MongoDB o Neo4j fallan, el estado diverge temporalmente. La estrategia de compensación consiste en registrar el fallo en el log de la aplicación para reintento asíncrono.
- En producción, esta compensación se implementaría con una cola de mensajes (ej. Kafka o RabbitMQ). En el contexto del TP, el log de la OP-2 documenta explícitamente cada escritura exitosa o fallida.

---

## 6. Nota sobre el cálculo de SLA

El SLA en `metricas_organismo` registra trámites como `sla_cumplidos` o `sla_incumplidos` usando días corridos como simplificación académica. En un sistema productivo, el cálculo correcto utilizaría días hábiles excluyendo fines de semana y feriados municipales. Esta simplificación fue adoptada conscientemente para no agregar complejidad de calendario al dominio de datos, y se documenta aquí para transparencia.
