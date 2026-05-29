# Cassandra / Astra DB — Módulo TPO Municipio Digital

Este módulo implementa el tercer motor NoSQL de la segunda entrega: **Apache Cassandra** a través de **DataStax Astra DB**.

## Rol en la arquitectura políglota

Cassandra se incorpora para gestionar el **log de eventos y métricas operativas** del sistema municipal. Su particionamiento por organismo y fecha permite realizar análisis de desempeño sin afectar la performance de la base transaccional (MongoDB).

| Motor | Qué almacena |
|---|---|
| MongoDB | Datos maestros: trámites, ciudadanos, organismos, documentos |
| Neo4j | Grafo de relaciones: flujo de derivaciones, dependencias |
| **Cassandra** | **Series temporales: eventos, métricas diarias, notificaciones** |

## Archivos

| Archivo | Descripción |
|---|---|
| `schema.cql` | Definición de las 5 tablas con Partition Keys y Clustering Keys justificadas |
| `carga_inicial_cassandra.py` | Script oficial de carga de datos (usa `.env`) |
| `consultas_cassandra.py` | Funciones de consulta por tabla, con demo ejecutable |
| `connect_database.py` | Test de conectividad a Astra DB |

## Tablas y patrones de acceso

| Tabla | Partition Key | Clustering Key | Operación |
|---|---|---|---|
| `eventos_tramite` | `(organismo_id, fecha)` | `timestamp DESC` | OP-3 panel diario |
| `eventos_por_tramite` | `tramite_id` | `timestamp ASC` | OP-1 historial |
| `metricas_organismo` | `(organismo_id, anio_mes)` | `fecha ASC` | OP-3 y OP-4 |
| `demanda_tipo_tramite` | `(tipo_tramite, anio_mes)` | `fecha ASC, zona ASC` | OP-5 reporte |
| `notificaciones_ciudadano` | `ciudadano_id` | `timestamp DESC` | OP-1 buzón |

## Ejecución

```bash
# 1. Crear tablas (desde CQL Console en Astra DB)
#    Copiar y ejecutar el contenido de schema.cql

# 2. Cargar datos iniciales
python carga_inicial_cassandra.py

# 3. Demo de consultas
python consultas_cassandra.py
```

## Variables de entorno requeridas

```env
ASTRA_TOKEN=AstraCS:...
ASTRA_ENDPOINT=https://<id>-<region>.apps.astra.datastax.com
ASTRA_KEYSPACE=municipio_digital
```

## Seguridad

El token de acceso debe configurarse exclusivamente en el archivo `.env` (no incluido en el repositorio). El archivo `.gitignore` excluye `.env` y cualquier archivo `.json` con credenciales.