# TPO — Ingeniería de Datos II
## Tema 12 · Municipio Digital · Gestión de Trámites Ciudadanos

Trabajo Práctico Obligatorio · UADE · Cuatrimestre 1, 2026

---

## Motores utilizados

| Motor | Servicio | Rol en el sistema |
|---|---|---|
| **MongoDB** | Atlas | Fuente de verdad — trámites, ciudadanos, organismos, documentos |
| **Neo4j** | Aura | Grafo de flujos — derivaciones, dependencias y centralidad |
| **Cassandra** | Astra DB | Log de eventos y métricas — series temporales de alto volumen |

---

## Estructura del repositorio

```
tpo-municipio-digital-main/
├── app_poliglota/
│   ├── app_poliglota.py          ← Aplicación web + 5 operaciones políglotas
│   └── requirements.txt          ← Dependencias Python
├── cassandra/
│   ├── schema.cql                ← Definición de tablas Cassandra
│   ├── carga_inicial_cassandra.py← Script de carga de datos
│   ├── consultas_cassandra.py    ← Funciones de consulta por tabla
│   ├── connect_database.py       ← Test de conectividad
│   └── README.md                 ← Documentación del módulo
├── mongo/
│   └── scripts/
│       ├── carga_inicial_mongo.js
│       └── consultas_mongo.js
├── neo4j/
│   └── scripts/
│       ├── carga_inicial_neo4j.cypher
│       └── consultas_neo4j.cypher
├── shared/
│   └── decisiones_modelado/
│       ├── modelo_inicial.md     ← Decisiones Entrega 1 (MongoDB + Neo4j)
│       └── modelo_cassandra.md   ← Decisiones Entrega 2 (Cassandra + políglota)
├── docs/
│   ├── enunciado/                ← Consigna del TPO
│   ├── informe/                  ← Informe técnico
│   └── evidencias/               ← Capturas y resultados de ejecución
├── .env.example                  ← Variables de entorno requeridas
└── README.md                     ← Este archivo
```

---

## Variables de entorno

Copiar `.env.example` como `.env` y completar los valores:

```bash
cp .env.example .env
```

```env
# Cassandra (Astra DB)
ASTRA_TOKEN=AstraCS:...
ASTRA_ENDPOINT=https://<id>-<region>.apps.astra.datastax.com
ASTRA_KEYSPACE=municipio_digital

# MongoDB (Atlas)
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
MONGO_DB=municipio_digital

# Neo4j (Aura)
NEO4J_URI=neo4j+s://<id>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<password>
NEO4J_DATABASE=neo4j
```

---

## Carga inicial de datos

Ejecutar en el siguiente orden:

### 1. MongoDB

```bash
# Desde MongoDB Compass o mongosh
mongosh --file mongo/scripts/carga_inicial_mongo.js
```

### 2. Neo4j

```bash
# Desde Neo4j Browser o cypher-shell
# Copiar y ejecutar el contenido de:
neo4j/scripts/carga_inicial_neo4j.cypher
```

### 3. Cassandra

```bash
# Crear las tablas primero (desde CQL Console en Astra DB)
# Copiar y ejecutar el contenido de:
cassandra/schema.cql

# Luego cargar datos
cd cassandra
pip install astrapy python-dotenv
python carga_inicial_cassandra.py
```

---

## Ejecutar la aplicación políglota

```bash
cd app_poliglota
pip install -r requirements.txt
python app_poliglota.py
```

Luego abrir **http://localhost:5000** en el navegador.

La aplicación implementa las 5 operaciones de negocio políglotas:

| Operación | Descripción | Motores |
|---|---|---|
| **OP-1** | Panel del Ciudadano — trámites, historial y flujo | MongoDB + Cassandra + Neo4j |
| **OP-2** | Procesar Evento — escritura coordinada | Cassandra + MongoDB + Neo4j |
| **OP-3** | Panel de Desempeño — SLA y métricas | MongoDB + Cassandra |
| **OP-4** | Cuellos de Botella — ranking e impacto | Cassandra + Neo4j |
| **OP-5** | Reporte Ejecutivo — demanda y complejidad | Cassandra + MongoDB + Neo4j |

---

## Verificación de integridad

La sección **Verificación** de la aplicación comprueba:
- Conteos de documentos/nodos en los 3 motores
- Coherencia de IDs de trámites entre MongoDB y Neo4j
- Coherencia de IDs de ciudadanos entre MongoDB y Neo4j

También se puede ejecutar `consultas_cassandra.py` directamente como demo de las queries Cassandra:

```bash
cd cassandra
python consultas_cassandra.py
```

---

## Datos de prueba disponibles

| Entidad | Cantidad |
|---|---|
| Ciudadanos | 10 (DNI 30000001 al 30000010) |
| Trámites | 25 (TRA-2026-000001 al TRA-2026-000025) |
| Organismos | 8 |
| Tipos de trámite | 10 |
| Eventos en Cassandra | ~70 (eventos_tramite + eventos_por_tramite) |
| Métricas diarias | ~488 (8 organismos × ~61 días) |
