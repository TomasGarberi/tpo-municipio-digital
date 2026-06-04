"""
╔══════════════════════════════════════════════════════════════╗
║   MUNICIPIO DIGITAL — Capa de Persistencia Políglota         ║
║   TPO Ingeniería de Datos II · UADE · Entrega 2              ║
║                                                              ║
║   Motores: MongoDB (Atlas) · Neo4j (Aura) · Cassandra (Astra)║
║                                                              ║
║   Ejecutar:                                                  ║
║     pip install flask pymongo neo4j astrapy python-dotenv    ║
║     python app_poliglota/app_poliglota.py                                  ║
║                                                              ║
║   Luego abrir: http://localhost:5000                         ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = Flask(__name__)

# ══════════════════════════════════════════════════════════════
# DOMINIO — listas de referencia alineadas con seed y Neo4j
# ══════════════════════════════════════════════════════════════
ORGANISMOS = [
    "Mesa de Entradas",
    "Direccion de Habilitaciones",
    "Secretaria de Desarrollo Social",
    "Secretaria de Obras Publicas",
    "Direccion de Transito",
    "Tesoreria Municipal",
    "Inspeccion General",
    "Direccion Ambiental",
]

TIPOS_TRAMITE = [
    "Habilitacion comercial",
    "Solicitud de beca",
    "Reclamo de obra publica",
    "Licencia de conducir",
    "Renovacion de licencia",
    "Subsidio habitacional",
    "Permiso de obra menor",
    "Permiso de evento",
    "Denuncia ambiental",
    "Exencion impositiva",
]

TIPOS_EVENTO = ["recepcion", "derivacion", "resolucion", "rechazo", "observacion"]

# ══════════════════════════════════════════════════════════════
# CONEXIONES — lazy, con caché de instancia
# ══════════════════════════════════════════════════════════════
_mongo = None
_neo4j = None
_cassandra = None


def get_mongo():
    global _mongo
    if _mongo is None:
        from pymongo import MongoClient
        client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        _mongo = client[os.getenv("MONGO_DB", "municipio_digital")]
    return _mongo


def get_neo4j():
    global _neo4j
    if _neo4j is None:
        from neo4j import GraphDatabase
        _neo4j = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
        )
        _neo4j.verify_connectivity()
    return _neo4j


def get_cassandra():
    global _cassandra
    if _cassandra is None:
        from astrapy import DataAPIClient
        client = DataAPIClient(os.getenv("ASTRA_TOKEN"))
        _cassandra = client.get_database_by_api_endpoint(
            os.getenv("ASTRA_ENDPOINT"),
            keyspace=os.getenv("ASTRA_KEYSPACE", "municipio_digital"),
        )
    return _cassandra


def motor_status():
    """Verifica conectividad de los 3 motores."""
    status = {"mongodb": False, "neo4j": False, "cassandra": False}
    try:
        get_mongo()
        status["mongodb"] = True
    except Exception:
        pass
    try:
        get_neo4j()
        status["neo4j"] = True
    except Exception:
        pass
    try:
        get_cassandra()
        status["cassandra"] = True
    except Exception:
        pass
    return status


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def _serialize(obj):
    """Serializa tipos no-JSON (datetime, date, etc.)."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _clean(obj):
    """Convierte recursivamente un objeto a JSON-safe."""
    return json.loads(json.dumps(obj, default=_serialize))


def ok(data):
    return jsonify({"ok": True, "data": _clean(data)})


def err(msg):
    return jsonify({"ok": False, "error": str(msg)}), 500

def _select_initial_port():
    port = 5000
    allSetted = False
    while not allSetted:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                allSetted = True
        port += 1
    return port

# ══════════════════════════════════════════════════════════════
# OP-1 — PANEL CIUDADANO
# Motores: MongoDB → Cassandra → Neo4j
#
# Flujo:
#   1. MongoDB: lista de trámites del ciudadano (datos estáticos)
#   2. Cassandra: historial de eventos de cada trámite
#      (tabla eventos_por_tramite, PK = tramite_id)
#   3. Neo4j: etapas restantes según el grafo del tipo de trámite
#
# Justificación políglota:
#   MongoDB tiene el documento maestro del trámite.
#   Cassandra tiene el log de eventos en orden cronológico
#     sin necesidad de recorrer el array embebido (O(1) por tramite_id).
#   Neo4j calcula la posición en el flujo sin joins tabulares.
# ══════════════════════════════════════════════════════════════
def op1_panel_ciudadano(ciudadano_dni: str) -> dict:
    mongo    = get_mongo()
    cassandra = get_cassandra()
    neo4j    = get_neo4j()

    # ── 1. MongoDB ─────────────────────────────────────────────
    tramites = list(mongo.tramites.find(
        {"ciudadano_dni": ciudadano_dni},
        {
            "_id": 0,
            "numero_tramite": 1,
            "tipo_tramite": 1,
            "estado_actual": 1,
            "organismo_actual": 1,
            "fecha_inicio": 1,
            "fecha_estimada_resolucion": 1,
        },
    ))

    if not tramites:
        return {
            "ciudadano_dni": ciudadano_dni,
            "tramites": [],
            "mensaje": "No se encontraron trámites para el ciudadano.",
        }

    resultado = []
    for t in tramites:
        tramite_id = t["numero_tramite"]

        # ── 2. Cassandra ────────────────────────────────────────
        try:
            tabla  = cassandra.get_table("eventos_por_tramite")
            eventos = list(tabla.find({"tramite_id": tramite_id}))
            # Orden cronológico ascendente (clustering key: timestamp ASC)
            eventos.sort(key=lambda e: str(e.get("timestamp", "")))
            t["historial_eventos"] = [
                {
                    k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for k, v in ev.items()
                }
                for ev in eventos
            ]
            t["total_eventos"] = len(eventos)
        except Exception as e:
            t["historial_eventos"] = []
            t["error_cassandra"] = str(e)

        # ── 3. Neo4j ────────────────────────────────────────────
        try:
            with neo4j.session() as session:
                result = session.run(
                    """
                    MATCH (t:Tramite {numero: $num})-[:ES_DE_TIPO]->(tipo:TipoTramite),
                          (t)-[:ESTA_EN]->(orgActual:Organismo),
                          (tipo)-[r:INICIA_EN|PASA_POR]->(org:Organismo)
                    WITH t, tipo, orgActual,
                         collect({organismo: org.nombre, orden: coalesce(r.orden, 1)}) AS etapas
                    UNWIND etapas AS etapa
                    WITH t, tipo, orgActual, etapas, etapa
                    WHERE etapa.organismo = orgActual.nombre
                    RETURN tipo.nombre        AS tipo_tramite,
                           orgActual.nombre   AS organismo_actual,
                           etapa.orden        AS posicion_actual,
                           size(etapas)       AS etapas_totales,
                           (size(etapas) - etapa.orden) AS etapas_restantes
                    """,
                    num=tramite_id,
                )
                row = result.single()
                t["flujo_neo4j"] = dict(row) if row else {"mensaje": "Trámite no encontrado en el grafo"}
        except Exception as e:
            t["flujo_neo4j"] = {"error": str(e)}

        resultado.append(t)

    return {"ciudadano_dni": ciudadano_dni, "total_tramites": len(resultado), "tramites": resultado}


# ══════════════════════════════════════════════════════════════
# OP-2 — PROCESAR EVENTO
# Motores: Cassandra → MongoDB → Neo4j
#
# Flujo:
#   1. Cassandra: INSERT doble en eventos_tramite + eventos_por_tramite
#      (desnormalización intencional para soportar ambas queries)
#   2. MongoDB: push del evento al array embebido + update de estado
#   3. Neo4j: actualizar posición del trámite en el grafo
#
# Coherencia eventual:
#   Si Cassandra falla, se aborta (no hay escritura parcial).
#   Si MongoDB falla después de Cassandra, se registra en el log
#   para compensación asíncrona. No se implementa 2PC.
# ══════════════════════════════════════════════════════════════
def op2_procesar_evento(
    tramite_id: str,
    organismo_id: str,
    tipo_evento: str,
    agente_id: str,
    duracion_min: int,
) -> dict:
    cassandra = get_cassandra()
    mongo     = get_mongo()
    neo4j     = get_neo4j()

    now           = datetime.utcnow()
    fecha_hoy     = date.today().isoformat()
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    log           = []

    # ── 1. Cassandra (primer motor: log de eventos) ─────────────
    try:
        evento_cass = {
            "organismo_id": organismo_id,
            "fecha":        fecha_hoy,
            "timestamp":    timestamp_str,
            "tramite_id":   tramite_id,
            "tipo":         tipo_evento,
            "agente_id":    agente_id,
            "duracion_min": int(duracion_min),
            "detalle":      f"Evento '{tipo_evento}' procesado por agente {agente_id}",
        }
        cassandra.get_table("eventos_tramite").insert_one(evento_cass)
        cassandra.get_table("eventos_por_tramite").insert_one({
            k: v for k, v in evento_cass.items() if k != "fecha"
        })
        log.append("✅ Cassandra: evento registrado en eventos_tramite y eventos_por_tramite")
    except Exception as e:
        log.append(f"❌ Cassandra: {e}")
        return {"tramite_id": tramite_id, "ok": False, "log": log,
                "nota": "Escritura abortada — fallo en Cassandra antes de actualizar otros motores"}

    # ── 2. MongoDB (actualización del documento maestro) ─────────
    try:
        nuevo_estado = (
            "resuelto"  if tipo_evento == "resolucion" else
            "rechazado" if tipo_evento == "rechazo"    else
            "en_proceso"
        )
        mongo.tramites.update_one(
            {"numero_tramite": tramite_id},
            {
                "$push": {
                    "eventos": {
                        "tipo":         tipo_evento,
                        "organismo":    organismo_id,
                        "agente_id":    agente_id,
                        "duracion_min": int(duracion_min),
                        "timestamp":    now,
                    }
                },
                "$set": {
                    "estado_actual":       nuevo_estado,
                    "organismo_actual":    organismo_id,
                    "ultima_actualizacion": now,
                },
            },
        )
        log.append(f"✅ MongoDB: trámite actualizado → estado '{nuevo_estado}', organismo '{organismo_id}'")
    except Exception as e:
        log.append(f"❌ MongoDB (escritura pendiente de compensación): {e}")

    # ── 3. Neo4j (actualización del grafo) ───────────────────────
    try:
        estado_grafo = "resuelto" if tipo_evento in ("resolucion", "rechazo") else "en_proceso"
        with neo4j.session() as session:
            session.run(
                """
                MATCH (t:Tramite {numero: $tid})
                MATCH (org:Organismo {nombre: $org})
                MERGE (t)-[r:ESTA_EN]->(org)
                SET t.estado = $estado, t.ultima_actualizacion = $ts
                """,
                tid=tramite_id,
                org=organismo_id,
                estado=estado_grafo,
                ts=timestamp_str,
            )
        log.append(f"✅ Neo4j: posición del trámite actualizada → organismo '{organismo_id}'")
    except Exception as e:
        log.append(f"❌ Neo4j (escritura pendiente de compensación): {e}")

    return {
        "tramite_id":  tramite_id,
        "tipo_evento": tipo_evento,
        "timestamp":   timestamp_str,
        "ok":          True,
        "log":         log,
    }


# ══════════════════════════════════════════════════════════════
# OP-3 — PANEL DE DESEMPEÑO DE ORGANISMO
# Motores: MongoDB + Cassandra (Neo4j no participa)
#
# Flujo:
#   1. MongoDB: trámites activos en el organismo con cálculo de SLA
#   2. Cassandra: métricas diarias del mes (metricas_organismo,
#      PK = (organismo_id, anio_mes))
#
# Por qué Neo4j no participa:
#   El panel de desempeño analiza datos operativos y series
#   temporales, no relaciones estructurales del flujo.
# ══════════════════════════════════════════════════════════════
def op3_panel_desempeno(organismo_id: str, anio_mes: str) -> dict:
    mongo     = get_mongo()
    cassandra = get_cassandra()

    # ── 1. MongoDB ─────────────────────────────────────────────
    try:
        tramites_activos = list(mongo.tramites.aggregate([
            {"$match": {"organismo_actual": organismo_id, "estado_actual": "en_proceso"}},
            {"$addFields": {"ultimo_evento": {"$arrayElemAt": ["$eventos", -1]}}},
            {"$lookup": {
                "from": "organismos",
                "localField": "organismo_actual",
                "foreignField": "nombre",
                "as": "org",
            }},
            {"$unwind": "$org"},
            {"$project": {
                "_id": 0,
                "numero_tramite": 1,
                "tipo_tramite":   1,
                "estado_actual":  1,
                "sla_dias":       "$org.sla_dias_habiles_por_etapa",
                "dias_en_etapa": {
                    "$round": [{
                        "$divide": [
                            {"$subtract": [datetime.utcnow(), "$ultimo_evento.timestamp"]},
                            1000 * 60 * 60 * 24,
                        ]
                    }, 1]
                },
            }},
            {"$addFields": {
                "alerta_sla": {"$gt": ["$dias_en_etapa", "$sla_dias"]}
            }},
            {"$sort": {"alerta_sla": -1, "dias_en_etapa": -1}},
        ]))
        alertas_sla = sum(1 for t in tramites_activos if t.get("alerta_sla"))
    except Exception as e:
        tramites_activos = [{"error": str(e)}]
        alertas_sla      = 0

    # ── 2. Cassandra ────────────────────────────────────────────
    try:
        tabla    = cassandra.get_table("metricas_organismo")
        metricas = list(tabla.find({"organismo_id": organismo_id, "anio_mes": anio_mes}))
        metricas.sort(key=lambda m: str(m.get("fecha", "")))

        metricas_clean = [
            {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
             for k, v in m.items()}
            for m in metricas
        ]

        total_proc   = sum(m.get("tramites_procesados", 0) or 0 for m in metricas)
        total_sla_ok = sum(m.get("sla_cumplidos",      0) or 0 for m in metricas)
        total_sla_no = sum(m.get("sla_incumplidos",    0) or 0 for m in metricas)
        tasa_sla     = f"{(total_sla_ok / (total_proc or 1) * 100):.1f}%"
    except Exception as e:
        metricas_clean = [{"error": str(e)}]
        total_proc = total_sla_ok = total_sla_no = 0
        tasa_sla   = "N/A"

    return {
        "organismo":  organismo_id,
        "periodo":    anio_mes,
        "resumen": {
            "tramites_activos":        len(tramites_activos),
            "alertas_sla_activas":     alertas_sla,
            "tramites_procesados_mes": total_proc,
            "sla_cumplidos":           total_sla_ok,
            "sla_incumplidos":         total_sla_no,
            "tasa_cumplimiento_sla":   tasa_sla,
        },
        "tramites_activos_mongo": tramites_activos,
        "metricas_diarias_cassandra": metricas_clean,
    }


# ══════════════════════════════════════════════════════════════
# OP-4 — DETECCIÓN DE CUELLOS DE BOTELLA
# Motores: Cassandra → Neo4j
#
# Flujo:
#   1. Cassandra: rankear organismos por SLA incumplidos en el mes
#      (query partición por partición: O(organismos) = O(8))
#   2. Neo4j: evaluar la centralidad de los top-3 críticos
#      (cuántos tipos de trámite dependen de ese organismo)
#
# Resultado: cruce entre "quién más falla" y "quién más impacta".
# ══════════════════════════════════════════════════════════════
def op4_cuellos_de_botella(anio_mes: str) -> dict:
    cassandra = get_cassandra()
    neo4j     = get_neo4j()

    # ── 1. Cassandra ────────────────────────────────────────────
    tabla   = cassandra.get_table("metricas_organismo")
    ranking = []
    for org in ORGANISMOS:
        try:
            rows        = list(tabla.find({"organismo_id": org, "anio_mes": anio_mes}))
            sla_no      = sum(r.get("sla_incumplidos",    0) or 0 for r in rows)
            procesados  = sum(r.get("tramites_procesados", 0) or 0 for r in rows)
            tiempo_prom = (
                sum(r.get("tiempo_promedio_min", 0) or 0 for r in rows) / len(rows)
                if rows else 0
            )
            ranking.append({
                "organismo":             org,
                "sla_incumplidos":       sla_no,
                "tramites_procesados":   procesados,
                "tiempo_promedio_min":   round(tiempo_prom, 1),
                "tasa_incumplimiento":   f"{(sla_no / (procesados or 1) * 100):.1f}%",
            })
        except Exception:
            pass

    ranking.sort(key=lambda x: x["sla_incumplidos"], reverse=True)
    top_orgs = [r["organismo"] for r in ranking[:3]]

    # ── 2. Neo4j ────────────────────────────────────────────────
    centralidad = []
    try:
        with neo4j.session() as session:
            result = session.run(
                """
                MATCH (org:Organismo)<-[:INICIA_EN|PASA_POR]-(tt:TipoTramite)
                WHERE org.nombre IN $orgs
                RETURN org.nombre                   AS organismo,
                       count(DISTINCT tt)            AS tipos_tramite_afectados,
                       collect(DISTINCT tt.nombre)   AS tramites_afectados
                ORDER BY tipos_tramite_afectados DESC
                """,
                orgs=top_orgs,
            )
            centralidad = [dict(r) for r in result]
    except Exception as e:
        centralidad = [{"error": str(e)}]

    # Enriquecer ranking con centralidad Neo4j
    centralidad_map = {c["organismo"]: c for c in centralidad}
    for r in ranking:
        c = centralidad_map.get(r["organismo"], {})
        r["tipos_tramite_afectados"] = c.get("tipos_tramite_afectados", "N/A")

    diagnostico = (
        f"Los organismos con mayor incumplimiento de SLA son: "
        f"{', '.join(top_orgs)}. "
        f"Su alta centralidad en el grafo indica que un cuello de botella en estos organismos "
        f"impacta en cascada al resto del flujo municipal."
    ) if top_orgs else "Sin datos suficientes para el período seleccionado."

    return {
        "periodo":                  anio_mes,
        "ranking_sla_incumplidos":  ranking,
        "centralidad_neo4j":        centralidad,
        "diagnostico":              diagnostico,
    }


# ══════════════════════════════════════════════════════════════
# OP-5 — REPORTE EJECUTIVO MENSUAL
# Motores: Cassandra + MongoDB + Neo4j
#
# Flujo:
#   1. Cassandra: demanda por tipo de trámite y zona geográfica
#      (tabla demanda_tipo_tramite, PK = (tipo_tramite, anio_mes))
#   2. MongoDB: distribución de estados de trámites (pipeline)
#   3. Neo4j: ranking de complejidad de flujos por tipo de trámite
# ══════════════════════════════════════════════════════════════
def op5_reporte_ejecutivo(anio_mes: str) -> dict:
    cassandra = get_cassandra()
    mongo     = get_mongo()
    neo4j     = get_neo4j()

    # ── 1. Cassandra ────────────────────────────────────────────
    tabla_dem = cassandra.get_table("demanda_tipo_tramite")
    demanda   = []
    for tipo in TIPOS_TRAMITE:
        try:
            rows  = list(tabla_dem.find({"tipo_tramite": tipo, "anio_mes": anio_mes}))
            total = sum(r.get("total", 0) or 0 for r in rows)
            zonas = {}
            for r in rows:
                zona = r.get("zona", "Desconocida")
                zonas[zona] = zonas.get(zona, 0) + (r.get("total", 0) or 0)
            demanda.append({
                "tipo":              tipo,
                "total_solicitudes": total,
                "por_zona":          zonas,
            })
        except Exception:
            pass
    demanda.sort(key=lambda x: x["total_solicitudes"], reverse=True)

    # ── 2. MongoDB ──────────────────────────────────────────────
    try:
        estados_pipeline = list(mongo.tramites.aggregate([
            {"$group": {"_id": "$estado_actual", "cantidad": {"$sum": 1}}},
            {"$sort": {"cantidad": -1}},
            {"$project": {"_id": 0, "estado": "$_id", "cantidad": 1}},
        ]))
        total_tramites = sum(e["cantidad"] for e in estados_pipeline)

        tipos_pipeline = list(mongo.tramites.aggregate([
            {"$group": {"_id": "$tipo_tramite", "cantidad": {"$sum": 1}}},
            {"$sort": {"cantidad": -1}},
            {"$limit": 5},
            {"$project": {"_id": 0, "tipo": "$_id", "cantidad": 1}},
        ]))
    except Exception as e:
        estados_pipeline = [{"error": str(e)}]
        tipos_pipeline   = []
        total_tramites   = 0

    # ── 3. Neo4j ────────────────────────────────────────────────
    try:
        with neo4j.session() as session:
            result = session.run(
                """
                MATCH (tt:TipoTramite)-[r:INICIA_EN|PASA_POR]->(org:Organismo)
                WITH tt, count(r) AS complejidad
                RETURN tt.nombre                 AS tipo_tramite,
                       complejidad,
                       tt.tiempo_estimado_dias   AS tiempo_estimado_dias
                ORDER BY complejidad DESC
                """
            )
            complejidad_flujos = [dict(r) for r in result]
    except Exception as e:
        complejidad_flujos = [{"error": str(e)}]

    return {
        "periodo":                  anio_mes,
        "demanda_por_tipo":         demanda,
        "total_tramites_sistema":   total_tramites,
        "distribucion_estados":     estados_pipeline,
        "top5_tipos_mongo":         tipos_pipeline,
        "complejidad_flujos_neo4j": complejidad_flujos,
    }


# ══════════════════════════════════════════════════════════════
# VERIFICACIÓN DE INTEGRIDAD
# Comprueba coherencia entre los 3 motores.
# ══════════════════════════════════════════════════════════════
def verificacion_integridad() -> dict:
    resultados = {}

    # ── MongoDB ─────────────────────────────────────────────────
    try:
        m = get_mongo()
        resultados["mongodb"] = {
            "ciudadanos":           m.ciudadanos.count_documents({}),
            "tramites":             m.tramites.count_documents({}),
            "organismos":           m.organismos.count_documents({}),
            "tipos_tramite":        m.tipos_tramite.count_documents({}),
            "documentos":           m.documentos.count_documents({}),
            "tramites_en_proceso":  m.tramites.count_documents({"estado_actual": "en_proceso"}),
            "tramites_resueltos":   m.tramites.count_documents({"estado_actual": "resuelto"}),
        }
    except Exception as e:
        resultados["mongodb"] = {"error": str(e)}

    # ── Neo4j ───────────────────────────────────────────────────
    try:
        with get_neo4j().session() as session:
            r1 = session.run(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS total ORDER BY label"
            )
            nodos = {row["label"]: row["total"] for row in r1}

            r2 = session.run(
                "MATCH ()-[r]->() RETURN type(r) AS tipo, count(r) AS total ORDER BY tipo"
            )
            relaciones = {row["tipo"]: row["total"] for row in r2}

        resultados["neo4j"] = {"nodos": nodos, "relaciones": relaciones}
    except Exception as e:
        resultados["neo4j"] = {"error": str(e)}

    # ── Cassandra ───────────────────────────────────────────────
    # Nota: contar sin partition key es un scan completo.
    # En producción se usarían estimaciones o contadores materialized views.
    try:
        cass   = get_cassandra()
        tablas = [
            "eventos_tramite",
            "eventos_por_tramite",
            "metricas_organismo",
            "notificaciones_ciudadano",
            "demanda_tipo_tramite",
        ]
        conteos = {}
        for tabla in tablas:
            try:
                rows = list(cass.get_table(tabla).find({}, limit=10000))
                conteos[tabla] = len(rows)
            except Exception as te:
                conteos[tabla] = f"error: {te}"
        resultados["cassandra"] = conteos
    except Exception as e:
        resultados["cassandra"] = {"error": str(e)}

    # ── Coherencia cross-motor ─────────────────────────────────
    cross = {}
    try:
        mongo_ids = set(
            t["numero_tramite"]
            for t in get_mongo().tramites.find({}, {"numero_tramite": 1, "_id": 0})
        )
        with get_neo4j().session() as session:
            r = session.run("MATCH (t:Tramite) RETURN t.numero AS n")
            neo4j_ids = set(row["n"] for row in r)

        solo_mongo = mongo_ids - neo4j_ids
        solo_neo4j = neo4j_ids - mongo_ids

        cross["tramites_en_mongo"]       = len(mongo_ids)
        cross["tramites_en_neo4j"]       = len(neo4j_ids)
        cross["coherencia_tramites"]     = (
            "✅ COHERENTE — mismos IDs en ambos motores"
            if not solo_mongo and not solo_neo4j
            else f"⚠️ DIVERGENCIA — {len(solo_mongo)} solo en Mongo / {len(solo_neo4j)} solo en Neo4j"
        )
        if solo_mongo:
            cross["solo_en_mongo_muestra"] = list(solo_mongo)[:5]
        if solo_neo4j:
            cross["solo_en_neo4j_muestra"] = list(solo_neo4j)[:5]

        # Coherencia ciudadanos
        mongo_ciu = set(
            c["dni"]
            for c in get_mongo().ciudadanos.find({}, {"dni": 1, "_id": 0})
        )
        with get_neo4j().session() as session:
            r2 = session.run("MATCH (c:Ciudadano) RETURN c.dni AS dni")
            neo4j_ciu = set(row["dni"] for row in r2)

        cross["coherencia_ciudadanos"] = (
            "✅ COHERENTE"
            if mongo_ciu == neo4j_ciu
            else f"⚠️ DIVERGENCIA — {len(mongo_ciu - neo4j_ciu)} ciudadanos solo en Mongo"
        )

    except Exception as e:
        cross["error"] = str(e)

    resultados["cross_motor"] = cross
    return resultados


# ══════════════════════════════════════════════════════════════
# FLASK — RUTAS API
# ══════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/status")
def api_status():
    return jsonify(motor_status())


@app.route("/api/organismos")
def api_organismos():
    return jsonify(ORGANISMOS)


@app.route("/api/op1", methods=["POST"])
def api_op1():
    try:
        data = request.get_json()
        return ok(op1_panel_ciudadano(data["ciudadano_dni"]))
    except Exception as e:
        return err(e)


@app.route("/api/op2", methods=["POST"])
def api_op2():
    try:
        data = request.get_json()
        return ok(op2_procesar_evento(
            data["tramite_id"],
            data["organismo_id"],
            data["tipo_evento"],
            data["agente_id"],
            int(data["duracion_min"]),
        ))
    except Exception as e:
        return err(e)


@app.route("/api/op3", methods=["POST"])
def api_op3():
    try:
        data = request.get_json()
        return ok(op3_panel_desempeno(data["organismo_id"], data["anio_mes"]))
    except Exception as e:
        return err(e)


@app.route("/api/op4", methods=["POST"])
def api_op4():
    try:
        data = request.get_json()
        return ok(op4_cuellos_de_botella(data["anio_mes"]))
    except Exception as e:
        return err(e)


@app.route("/api/op5", methods=["POST"])
def api_op5():
    try:
        data = request.get_json()
        return ok(op5_reporte_ejecutivo(data["anio_mes"]))
    except Exception as e:
        return err(e)


@app.route("/api/verificacion")
def api_verificacion():
    try:
        return ok(verificacion_integridad())
    except Exception as e:
        return err(e)


# ══════════════════════════════════════════════════════════════
# TEMPLATE HTML — Frontend Bootstrap 5
# ══════════════════════════════════════════════════════════════
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Municipio Digital — Panel de Gestión</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root {
      --muni-blue:    #1a3a6b;
      --muni-light:   #2563a8;
      --muni-accent:  #f0a500;
      --sidebar-w:    260px;
    }
    body { background: #f0f2f5; font-family: 'Segoe UI', system-ui, sans-serif; }

    /* ── Sidebar ── */
    #sidebar {
      position: fixed; top: 0; left: 0;
      width: var(--sidebar-w); height: 100vh;
      background: var(--muni-blue);
      display: flex; flex-direction: column;
      box-shadow: 4px 0 12px rgba(0,0,0,0.15);
      z-index: 100;
    }
    #sidebar .brand {
      padding: 24px 20px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    #sidebar .brand h5 { color: #fff; margin: 0; font-weight: 700; font-size: 1rem; letter-spacing: 0.3px; }
    #sidebar .brand small { color: rgba(255,255,255,0.55); font-size: 0.72rem; }
    #sidebar .nav-link {
      color: rgba(255,255,255,0.75);
      padding: 10px 20px;
      border-radius: 6px;
      margin: 2px 10px;
      font-size: 0.875rem;
      font-weight: 500;
      transition: all 0.15s;
      display: flex; align-items: center; gap: 10px;
    }
    #sidebar .nav-link:hover  { color: #fff; background: rgba(255,255,255,0.1); }
    #sidebar .nav-link.active { color: #fff; background: var(--muni-light); }
    #sidebar .nav-link .badge { font-size: 0.65rem; }
    .motor-dots { padding: 16px 20px; margin-top: auto; border-top: 1px solid rgba(255,255,255,0.1); }
    .motor-dot  { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.7); font-size: 0.78rem; margin-bottom: 4px; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #6c757d; }
    .dot.on  { background: #28a745; box-shadow: 0 0 6px #28a745; }
    .dot.off { background: #dc3545; }

    /* ── Main content ── */
    #main { margin-left: var(--sidebar-w); min-height: 100vh; }

    /* ── Top bar ── */
    #topbar {
      background: #fff;
      padding: 14px 28px;
      border-bottom: 1px solid #e2e8f0;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 50;
    }
    #topbar h4 { margin: 0; font-weight: 700; color: var(--muni-blue); font-size: 1.1rem; }

    /* ── Sections ── */
    .section { display: none; padding: 28px; }
    .section.active { display: block; }

    /* ── Cards ── */
    .op-card {
      background: #fff; border: none; border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
      margin-bottom: 20px;
      overflow: hidden;
    }
    .op-card .card-header {
      background: var(--muni-blue); color: #fff;
      padding: 14px 20px; font-weight: 600; font-size: 0.9rem;
      display: flex; align-items: center; gap: 10px;
    }
    .op-card .card-header .op-badge {
      background: var(--muni-accent); color: #000;
      font-size: 0.7rem; font-weight: 700;
      padding: 2px 8px; border-radius: 20px;
    }
    .op-card .card-body { padding: 20px; }

    /* ── Form ── */
    .form-label { font-size: 0.82rem; font-weight: 600; color: #495057; margin-bottom: 4px; }
    .form-control, .form-select {
      font-size: 0.875rem; border-radius: 8px;
      border: 1.5px solid #dee2e6;
    }
    .form-control:focus, .form-select:focus {
      border-color: var(--muni-light); box-shadow: 0 0 0 3px rgba(37,99,168,0.12);
    }
    .btn-muni {
      background: var(--muni-blue); color: #fff; border: none;
      font-weight: 600; font-size: 0.875rem; border-radius: 8px;
      padding: 8px 20px; transition: background 0.15s;
    }
    .btn-muni:hover  { background: var(--muni-light); color: #fff; }
    .btn-muni:active { background: #122b54; }

    /* ── Result box ── */
    .result-box {
      background: #1e1e2e; color: #cdd6f4;
      border-radius: 10px; padding: 16px;
      font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
      font-size: 0.8rem; line-height: 1.6;
      max-height: 480px; overflow-y: auto;
      white-space: pre-wrap; word-break: break-word;
      margin-top: 14px;
    }
    .result-box:empty { display: none; }
    .result-placeholder {
      color: rgba(205,214,244,0.4); font-style: italic;
    }

    /* ── Summary cards ── */
    .stat-card {
      background: #fff; border-radius: 10px;
      padding: 16px 18px; box-shadow: 0 1px 6px rgba(0,0,0,0.07);
      border-left: 4px solid var(--muni-blue);
    }
    .stat-card .stat-value { font-size: 1.6rem; font-weight: 700; color: var(--muni-blue); }
    .stat-card .stat-label { font-size: 0.75rem; color: #6c757d; font-weight: 500; }

    /* ── Spinner ── */
    .spin-wrap { display: none; align-items: center; gap: 8px; color: #6c757d; font-size: 0.82rem; margin-top: 10px; }
    .spin-wrap.show { display: flex; }

    /* ── Verif ── */
    .verif-motor { border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
    .verif-mongo    { background: #fff8f0; border-left: 4px solid #f0a500; }
    .verif-neo4j    { background: #f0fff4; border-left: 4px solid #28a745; }
    .verif-cass     { background: #f0f4ff; border-left: 4px solid var(--muni-light); }
    .verif-cross    { background: #fdf0f0; border-left: 4px solid #dc3545; }
    .verif-motor h6 { font-weight: 700; font-size: 0.82rem; margin-bottom: 8px; color: #333; }
    .kv-row { display: flex; justify-content: space-between; font-size: 0.8rem; padding: 2px 0; border-bottom: 1px solid rgba(0,0,0,0.05); }
    .kv-key  { color: #555; }
    .kv-val  { font-weight: 600; color: #222; }

    /* ── Log list ── */
    .log-item { font-size: 0.82rem; padding: 4px 0; border-bottom: 1px solid #f0f0f0; }
    .log-item.ok  { color: #155724; }
    .log-item.err { color: #721c24; }
  </style>
</head>
<body>

<!-- ════════════ SIDEBAR ════════════ -->
<nav id="sidebar">
  <div class="brand">
    <h5><i class="bi bi-building me-2"></i>Municipio Digital</h5>
    <small>Sistema de Gestión de Trámites</small>
  </div>
  <div class="mt-3">
    <div class="px-3 mb-1" style="font-size:0.68rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;">Operaciones</div>
    <a class="nav-link active" onclick="show('op1')" href="#" id="nav-op1">
      <i class="bi bi-person-lines-fill"></i> Panel Ciudadano
      <span class="badge bg-secondary ms-auto">OP-1</span>
    </a>
    <a class="nav-link" onclick="show('op2')" href="#" id="nav-op2">
      <i class="bi bi-arrow-right-circle-fill"></i> Procesar Evento
      <span class="badge bg-secondary ms-auto">OP-2</span>
    </a>
    <a class="nav-link" onclick="show('op3')" href="#" id="nav-op3">
      <i class="bi bi-bar-chart-fill"></i> Panel Desempeño
      <span class="badge bg-secondary ms-auto">OP-3</span>
    </a>
    <a class="nav-link" onclick="show('op4')" href="#" id="nav-op4">
      <i class="bi bi-exclamation-triangle-fill"></i> Cuellos de Botella
      <span class="badge bg-secondary ms-auto">OP-4</span>
    </a>
    <a class="nav-link" onclick="show('op5')" href="#" id="nav-op5">
      <i class="bi bi-file-earmark-bar-graph-fill"></i> Reporte Ejecutivo
      <span class="badge bg-secondary ms-auto">OP-5</span>
    </a>
    <div class="px-3 mt-3 mb-1" style="font-size:0.68rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;">Sistema</div>
    <a class="nav-link" onclick="show('verif')" href="#" id="nav-verif">
      <i class="bi bi-shield-check"></i> Verificación
    </a>
  </div>
  <div class="motor-dots">
    <div class="mb-2" style="font-size:0.68rem;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;">Motores</div>
    <div class="motor-dot"><span class="dot" id="dot-mongodb"></span> MongoDB (Atlas)</div>
    <div class="motor-dot"><span class="dot" id="dot-neo4j"></span> Neo4j (Aura)</div>
    <div class="motor-dot"><span class="dot" id="dot-cassandra"></span> Cassandra (Astra)</div>
  </div>
</nav>

<!-- ════════════ MAIN ════════════ -->
<div id="main">
  <div id="topbar">
    <h4 id="section-title"><i class="bi bi-person-lines-fill me-2"></i>Panel del Ciudadano</h4>
    <span class="badge bg-primary" style="font-size:0.75rem;">UADE · Ing. Datos II · Entrega 2</span>
  </div>

  <!-- ── OP-1: Panel Ciudadano ── -->
  <div class="section active" id="sec-op1">
    <div class="row mb-3">
      <div class="col-12">
        <div class="alert alert-light border" style="font-size:0.82rem;">
          <strong>Motores:</strong> MongoDB → Cassandra → Neo4j &nbsp;|&nbsp;
          <strong>Consulta:</strong> Trámites del ciudadano, historial de eventos y etapas restantes del flujo.
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="op-card">
          <div class="card-header"><span class="op-badge">OP-1</span> Panel del Ciudadano</div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">DNI del Ciudadano</label>
              <input type="text" id="op1-dni" class="form-control" value="30000001" placeholder="ej. 30000001">
            </div>
            <button class="btn btn-muni w-100" onclick="runOp1()">
              <i class="bi bi-search me-2"></i>Consultar
            </button>
            <div class="spin-wrap" id="spin-op1">
              <div class="spinner-border spinner-border-sm text-secondary"></div> Consultando los 3 motores...
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="op-card">
          <div class="card-header"><i class="bi bi-code-square"></i> Resultado</div>
          <div class="card-body">
            <div class="result-box" id="res-op1"><span class="result-placeholder">Los resultados aparecerán aquí...</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── OP-2: Procesar Evento ── -->
  <div class="section" id="sec-op2">
    <div class="row mb-3">
      <div class="col-12">
        <div class="alert alert-light border" style="font-size:0.82rem;">
          <strong>Motores:</strong> Cassandra → MongoDB → Neo4j &nbsp;|&nbsp;
          <strong>Acción:</strong> Registra un evento en el log (Cassandra), actualiza el trámite (MongoDB) y el grafo (Neo4j).
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="op-card">
          <div class="card-header"><span class="op-badge">OP-2</span> Procesar Evento</div>
          <div class="card-body">
            <div class="mb-2">
              <label class="form-label">ID del Trámite</label>
              <input type="text" id="op2-tramite" class="form-control" value="TRA-2026-000001" placeholder="TRA-2026-000001">
            </div>
            <div class="mb-2">
              <label class="form-label">Organismo</label>
              <select id="op2-organismo" class="form-select">
                <option value="Mesa de Entradas">Mesa de Entradas</option>
                <option value="Direccion de Habilitaciones">Dirección de Habilitaciones</option>
                <option value="Secretaria de Desarrollo Social">Secretaría Desarrollo Social</option>
                <option value="Secretaria de Obras Publicas">Secretaría Obras Públicas</option>
                <option value="Direccion de Transito">Dirección de Tránsito</option>
                <option value="Tesoreria Municipal">Tesorería Municipal</option>
                <option value="Inspeccion General">Inspección General</option>
                <option value="Direccion Ambiental">Dirección Ambiental</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label">Tipo de Evento</label>
              <select id="op2-tipo" class="form-select">
                <option value="recepcion">Recepción</option>
                <option value="derivacion">Derivación</option>
                <option value="resolucion">Resolución</option>
                <option value="rechazo">Rechazo</option>
                <option value="observacion">Observación</option>
              </select>
            </div>
            <div class="mb-2">
              <label class="form-label">Agente ID</label>
              <input type="text" id="op2-agente" class="form-control" value="agente_001">
            </div>
            <div class="mb-3">
              <label class="form-label">Duración (minutos)</label>
              <input type="number" id="op2-duracion" class="form-control" value="90" min="1">
            </div>
            <button class="btn btn-muni w-100" onclick="runOp2()">
              <i class="bi bi-send me-2"></i>Procesar
            </button>
            <div class="spin-wrap" id="spin-op2">
              <div class="spinner-border spinner-border-sm text-secondary"></div> Escribiendo en los 3 motores...
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="op-card">
          <div class="card-header"><i class="bi bi-journal-check"></i> Log de operación</div>
          <div class="card-body">
            <div id="op2-log-container" style="display:none;">
              <div id="op2-log-list"></div>
            </div>
            <div class="result-box" id="res-op2"><span class="result-placeholder">Los resultados aparecerán aquí...</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── OP-3: Panel Desempeño ── -->
  <div class="section" id="sec-op3">
    <div class="row mb-3">
      <div class="col-12">
        <div class="alert alert-light border" style="font-size:0.82rem;">
          <strong>Motores:</strong> MongoDB + Cassandra &nbsp;|&nbsp;
          <strong>Consulta:</strong> Trámites activos con alertas SLA (Mongo) y métricas diarias del mes (Cassandra).
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="op-card">
          <div class="card-header"><span class="op-badge">OP-3</span> Panel de Desempeño</div>
          <div class="card-body">
            <div class="mb-2">
              <label class="form-label">Organismo</label>
              <select id="op3-organismo" class="form-select">
                <option value="Mesa de Entradas">Mesa de Entradas</option>
                <option value="Direccion de Habilitaciones">Dirección de Habilitaciones</option>
                <option value="Secretaria de Desarrollo Social">Secretaría Desarrollo Social</option>
                <option value="Secretaria de Obras Publicas">Secretaría Obras Públicas</option>
                <option value="Direccion de Transito">Dirección de Tránsito</option>
                <option value="Tesoreria Municipal">Tesorería Municipal</option>
                <option value="Inspeccion General">Inspección General</option>
                <option value="Direccion Ambiental">Dirección Ambiental</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">Período (YYYY-MM)</label>
              <input type="text" id="op3-mes" class="form-control" value="2026-03">
            </div>
            <button class="btn btn-muni w-100" onclick="runOp3()">
              <i class="bi bi-bar-chart me-2"></i>Ver Panel
            </button>
            <div class="spin-wrap" id="spin-op3">
              <div class="spinner-border spinner-border-sm text-secondary"></div> Consultando Mongo y Cassandra...
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div id="op3-summary" class="row g-3 mb-3" style="display:none!important;"></div>
        <div class="op-card">
          <div class="card-header"><i class="bi bi-code-square"></i> Resultado</div>
          <div class="card-body">
            <div class="result-box" id="res-op3"><span class="result-placeholder">Los resultados aparecerán aquí...</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── OP-4: Cuellos de Botella ── -->
  <div class="section" id="sec-op4">
    <div class="row mb-3">
      <div class="col-12">
        <div class="alert alert-light border" style="font-size:0.82rem;">
          <strong>Motores:</strong> Cassandra → Neo4j &nbsp;|&nbsp;
          <strong>Análisis:</strong> Ranking de organismos con más SLA incumplidos (Cassandra) y su centralidad en el grafo (Neo4j).
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="op-card">
          <div class="card-header"><span class="op-badge">OP-4</span> Cuellos de Botella</div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Período (YYYY-MM)</label>
              <input type="text" id="op4-mes" class="form-control" value="2026-03">
            </div>
            <button class="btn btn-muni w-100" onclick="runOp4()">
              <i class="bi bi-funnel me-2"></i>Analizar
            </button>
            <div class="spin-wrap" id="spin-op4">
              <div class="spinner-border spinner-border-sm text-secondary"></div> Analizando Cassandra y Neo4j...
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="op-card">
          <div class="card-header"><i class="bi bi-code-square"></i> Resultado</div>
          <div class="card-body">
            <div class="result-box" id="res-op4"><span class="result-placeholder">Los resultados aparecerán aquí...</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── OP-5: Reporte Ejecutivo ── -->
  <div class="section" id="sec-op5">
    <div class="row mb-3">
      <div class="col-12">
        <div class="alert alert-light border" style="font-size:0.82rem;">
          <strong>Motores:</strong> Cassandra + MongoDB + Neo4j &nbsp;|&nbsp;
          <strong>Reporte:</strong> Demanda por tipo/zona (Cassandra), estados del sistema (MongoDB) y complejidad de flujos (Neo4j).
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="op-card">
          <div class="card-header"><span class="op-badge">OP-5</span> Reporte Ejecutivo</div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Período (YYYY-MM)</label>
              <input type="text" id="op5-mes" class="form-control" value="2026-03">
            </div>
            <button class="btn btn-muni w-100" onclick="runOp5()">
              <i class="bi bi-file-earmark-bar-graph me-2"></i>Generar Reporte
            </button>
            <div class="spin-wrap" id="spin-op5">
              <div class="spinner-border spinner-border-sm text-secondary"></div> Consolidando los 3 motores...
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="op-card">
          <div class="card-header"><i class="bi bi-code-square"></i> Resultado</div>
          <div class="card-body">
            <div class="result-box" id="res-op5"><span class="result-placeholder">Los resultados aparecerán aquí...</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── Verificación ── -->
  <div class="section" id="sec-verif">
    <div class="row mb-3">
      <div class="col-12">
        <div class="alert alert-light border" style="font-size:0.82rem;">
          Comprueba los conteos de documentos/nodos en los 3 motores y verifica la coherencia cross-motor de los IDs.
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="op-card">
          <div class="card-header"><i class="bi bi-shield-check"></i> Verificación de Integridad</div>
          <div class="card-body">
            <p style="font-size:0.82rem;color:#666;">Ejecuta conteos en MongoDB, Neo4j y Cassandra, y cruza los IDs de trámites y ciudadanos entre motores.</p>
            <button class="btn btn-muni w-100" onclick="runVerif()">
              <i class="bi bi-check2-all me-2"></i>Verificar integridad
            </button>
            <div class="spin-wrap" id="spin-verif">
              <div class="spinner-border spinner-border-sm text-secondary"></div> Verificando los 3 motores...
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div id="verif-result"></div>
      </div>
    </div>
  </div>

</div><!-- /main -->

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
// ── Nav ──────────────────────────────────────────────────────
const SECTIONS = { op1:'Panel del Ciudadano', op2:'Procesar Evento',
                   op3:'Panel de Desempeño', op4:'Cuellos de Botella',
                   op5:'Reporte Ejecutivo', verif:'Verificación de Integridad' };
const ICONS    = { op1:'person-lines-fill', op2:'arrow-right-circle-fill',
                   op3:'bar-chart-fill', op4:'exclamation-triangle-fill',
                   op5:'file-earmark-bar-graph-fill', verif:'shield-check' };

function show(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('#sidebar .nav-link').forEach(l => l.classList.remove('active'));
  document.getElementById('sec-' + id).classList.add('active');
  document.getElementById('nav-' + id).classList.add('active');
  document.getElementById('section-title').innerHTML =
    '<i class="bi bi-' + ICONS[id] + ' me-2"></i>' + SECTIONS[id];
  return false;
}

// ── Motor status ─────────────────────────────────────────────
function refreshStatus() {
  fetch('/api/status').then(r => r.json()).then(data => {
    ['mongodb','neo4j','cassandra'].forEach(m => {
      const dot = document.getElementById('dot-' + m);
      dot.className = 'dot ' + (data[m] ? 'on' : 'off');
    });
  });
}
refreshStatus();
setInterval(refreshStatus, 30000);

// ── Helpers ──────────────────────────────────────────────────
function setResult(id, data) {
  const el = document.getElementById(id);
  el.innerHTML = JSON.stringify(data, null, 2);
}

function spin(id, show) {
  const el = document.getElementById('spin-' + id);
  if (el) el.className = 'spin-wrap' + (show ? ' show' : '');
}

async function callApi(endpoint, body, spinId, resultId) {
  spin(spinId, true);
  try {
    const r = await fetch(endpoint, {
      method: body ? 'POST' : 'GET',
      headers: {'Content-Type': 'application/json'},
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await r.json();
    if (resultId) setResult(resultId, data.ok ? data.data : data);
    return data;
  } catch(e) {
    if (resultId) setResult(resultId, {error: e.toString()});
  } finally {
    spin(spinId, false);
  }
}

// ── OP-1 ─────────────────────────────────────────────────────
function runOp1() {
  callApi('/api/op1', {ciudadano_dni: document.getElementById('op1-dni').value}, 'op1', 'res-op1');
}

// ── OP-2 ─────────────────────────────────────────────────────
async function runOp2() {
  const data = await callApi('/api/op2', {
    tramite_id:   document.getElementById('op2-tramite').value,
    organismo_id: document.getElementById('op2-organismo').value,
    tipo_evento:  document.getElementById('op2-tipo').value,
    agente_id:    document.getElementById('op2-agente').value,
    duracion_min: parseInt(document.getElementById('op2-duracion').value),
  }, 'op2', 'res-op2');

  // También mostramos el log visualmente
  if (data && data.ok && data.data && data.data.log) {
    const cont = document.getElementById('op2-log-container');
    const list = document.getElementById('op2-log-list');
    cont.style.display = 'block';
    list.innerHTML = data.data.log.map(l =>
      `<div class="log-item ${l.startsWith('✅') ? 'ok' : 'err'}">${l}</div>`
    ).join('');
  }
}

// ── OP-3 ─────────────────────────────────────────────────────
async function runOp3() {
  const data = await callApi('/api/op3', {
    organismo_id: document.getElementById('op3-organismo').value,
    anio_mes:     document.getElementById('op3-mes').value,
  }, 'op3', 'res-op3');

  if (data && data.ok && data.data && data.data.resumen) {
    const r = data.data.resumen;
    const sumEl = document.getElementById('op3-summary');
    sumEl.style.display = 'flex';
    const stats = [
      ['tramites_activos', 'Trámites activos'],
      ['alertas_sla_activas', 'Alertas SLA'],
      ['tramites_procesados_mes', 'Procesados en el mes'],
      ['tasa_cumplimiento_sla', 'Tasa SLA'],
    ];
    sumEl.innerHTML = stats.map(([k, label]) =>
      `<div class="col-6 col-md-3">
        <div class="stat-card">
          <div class="stat-value">${r[k] ?? '-'}</div>
          <div class="stat-label">${label}</div>
        </div>
      </div>`
    ).join('');
  }
}

// ── OP-4 ─────────────────────────────────────────────────────
function runOp4() {
  callApi('/api/op4', {anio_mes: document.getElementById('op4-mes').value}, 'op4', 'res-op4');
}

// ── OP-5 ─────────────────────────────────────────────────────
function runOp5() {
  callApi('/api/op5', {anio_mes: document.getElementById('op5-mes').value}, 'op5', 'res-op5');
}

// ── VERIFICACIÓN ─────────────────────────────────────────────
async function runVerif() {
  spin('verif', true);
  const container = document.getElementById('verif-result');
  container.innerHTML = '';
  try {
    const r    = await fetch('/api/verificacion');
    const data = await r.json();
    const d    = data.ok ? data.data : data;

    const sections = [
      { key: 'mongodb',    cls: 'verif-mongo', icon: 'database-fill',      label: 'MongoDB' },
      { key: 'neo4j',      cls: 'verif-neo4j', icon: 'diagram-3-fill',     label: 'Neo4j' },
      { key: 'cassandra',  cls: 'verif-cass',  icon: 'server',             label: 'Cassandra' },
      { key: 'cross_motor',cls: 'verif-cross', icon: 'arrow-left-right',   label: 'Coherencia Cross-Motor' },
    ];

    sections.forEach(({key, cls, icon, label}) => {
      const val = d[key];
      if (!val) return;
      let rows = '';
      if (key === 'neo4j' && val.nodos) {
        rows += '<div style="font-size:0.75rem;color:#888;margin-bottom:2px;">NODOS</div>';
        Object.entries(val.nodos).forEach(([k, v]) =>
          rows += `<div class="kv-row"><span class="kv-key">${k}</span><span class="kv-val">${v}</span></div>`);
        rows += '<div style="font-size:0.75rem;color:#888;margin:6px 0 2px;">RELACIONES</div>';
        Object.entries(val.relaciones).forEach(([k, v]) =>
          rows += `<div class="kv-row"><span class="kv-key">${k}</span><span class="kv-val">${v}</span></div>`);
      } else if (val.error) {
        rows = `<div style="color:#dc3545;font-size:0.8rem;">❌ ${val.error}</div>`;
      } else {
        Object.entries(val).forEach(([k, v]) => {
          const display = typeof v === 'object' ? JSON.stringify(v) : v;
          rows += `<div class="kv-row"><span class="kv-key">${k}</span><span class="kv-val">${display}</span></div>`;
        });
      }
      container.innerHTML +=
        `<div class="verif-motor ${cls}">
          <h6><i class="bi bi-${icon} me-2"></i>${label}</h6>
          ${rows}
        </div>`;
    });
  } catch(e) {
    container.innerHTML = `<div class="alert alert-danger">${e}</div>`;
  } finally {
    spin('verif', false);
  }
}
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═" * 62)
    print("  MUNICIPIO DIGITAL — Capa de Persistencia Políglota")
    print("  TPO Ingeniería de Datos II · UADE")
    print("═" * 62)
    print("\n  Verificando conexiones a los motores de base de datos...\n")

    status = motor_status()
    labels = {"mongodb": "MongoDB  (Atlas)", "neo4j": "Neo4j    (Aura) ", "cassandra": "Cassandra (Astra)"}
    for key, label in labels.items():
        icon = "✅" if status[key] else "❌"
        print(f"    {icon}  {label}")

    conectados = sum(status.values())
    print(f"\n  {conectados}/3 motores disponibles.", end=" ")

    if conectados == 0:
        print("\n  Sin conexiones — revisá las credenciales en .env\n")
    else:
        import socket
        port = _select_initial_port()
        print("Sistema listo.")
        print(f"\n  🌐  http://localhost:{port}\n")
        print("═" * 62 + "\n")
        app.run(debug=False, host="0.0.0.0", port=port)
