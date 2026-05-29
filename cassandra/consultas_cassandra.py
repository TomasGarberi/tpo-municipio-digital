"""
╔══════════════════════════════════════════════════════════════╗
║  CONSULTAS CASSANDRA / ASTRA DB — TPO Municipio Digital      ║
║  Motor: Apache Cassandra (vía DataStax Astra DB)             ║
║  Keyspace: municipio_digital                                 ║
║                                                              ║
║  Cada función encapsula una query que responde a un patrón   ║
║  de acceso definido por la Partition Key de la tabla.        ║
║  No existe ninguna consulta que no filtre por PK.            ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from astrapy import DataAPIClient

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# ══════════════════════════════════════════════════════════════
# CONEXIÓN
# ══════════════════════════════════════════════════════════════
def conectar() -> object:
    """Retorna la instancia de la base de datos Astra DB."""
    client = DataAPIClient(os.getenv("ASTRA_TOKEN"))
    return client.get_database_by_api_endpoint(
        os.getenv("ASTRA_ENDPOINT"),
        keyspace=os.getenv("ASTRA_KEYSPACE", "municipio_digital"),
    )


# ══════════════════════════════════════════════════════════════
# TABLA: eventos_por_tramite
# PK: tramite_id | CK: timestamp ASC
#
# Caso de uso: reconstruir el historial cronológico de un
# trámite (vista ciudadano / panel OP-1).
# Lectura O(1) independiente del volumen total de la tabla.
# ══════════════════════════════════════════════════════════════
def historial_tramite(db, tramite_id: str) -> list:
    """
    Devuelve todos los eventos de un trámite en orden cronológico.
    Filtra por PK = tramite_id → lectura de una sola partición.
    """
    tabla  = db.get_table("eventos_por_tramite")
    eventos = list(tabla.find({"tramite_id": tramite_id}))
    # Orden cronológico ascendente (clustering key: timestamp ASC)
    return sorted(eventos, key=lambda e: str(e.get("timestamp", "")))


# ══════════════════════════════════════════════════════════════
# TABLA: eventos_tramite
# PK: (organismo_id, fecha) | CK: timestamp DESC, tramite_id ASC
#
# Caso de uso: actividad diaria de un organismo (panel OP-3).
# ══════════════════════════════════════════════════════════════
def eventos_organismo_fecha(db, organismo_id: str, fecha: str) -> list:
    """
    Devuelve todos los eventos procesados por un organismo en una fecha.
    Filtra por PK = (organismo_id, fecha).

    Args:
        fecha: string ISO 'YYYY-MM-DD', ej. '2026-03-15'
    """
    tabla = db.get_table("eventos_tramite")
    return list(tabla.find({"organismo_id": organismo_id, "fecha": fecha}))


# ══════════════════════════════════════════════════════════════
# TABLA: metricas_organismo
# PK: (organismo_id, anio_mes) | CK: fecha ASC
#
# Caso de uso: panel de desempeño mensual (OP-3) y ranking
# de cuellos de botella (OP-4).
# ══════════════════════════════════════════════════════════════
def metricas_organismo_mes(db, organismo_id: str, anio_mes: str) -> list:
    """
    Devuelve las métricas diarias de un organismo en un mes.
    Filtra por PK = (organismo_id, anio_mes).

    Args:
        anio_mes: string 'YYYY-MM', ej. '2026-03'
    """
    tabla = db.get_table("metricas_organismo")
    filas = list(tabla.find({"organismo_id": organismo_id, "anio_mes": anio_mes}))
    return sorted(filas, key=lambda r: str(r.get("fecha", "")))


def resumen_metricas(db, organismo_id: str, anio_mes: str) -> dict:
    """
    Agrega las métricas del mes para un organismo.
    Retorna totales y tasa de cumplimiento SLA.
    """
    filas         = metricas_organismo_mes(db, organismo_id, anio_mes)
    procesados    = sum(f.get("tramites_procesados", 0) or 0 for f in filas)
    sla_cumplidos = sum(f.get("sla_cumplidos",       0) or 0 for f in filas)
    sla_no        = sum(f.get("sla_incumplidos",      0) or 0 for f in filas)
    tasa          = (sla_cumplidos / (procesados or 1)) * 100

    return {
        "organismo":               organismo_id,
        "periodo":                 anio_mes,
        "tramites_procesados":     procesados,
        "sla_cumplidos":           sla_cumplidos,
        "sla_incumplidos":         sla_no,
        "tasa_cumplimiento_sla":   f"{tasa:.1f}%",
        "dias_con_datos":          len(filas),
    }


# ══════════════════════════════════════════════════════════════
# TABLA: demanda_tipo_tramite
# PK: (tipo_tramite, anio_mes) | CK: fecha ASC, zona ASC
#
# Caso de uso: análisis de demanda mensual por tipo y zona
# geográfica (OP-5 reporte ejecutivo).
# ══════════════════════════════════════════════════════════════
def demanda_tipo_mes(db, tipo_tramite: str, anio_mes: str) -> list:
    """
    Devuelve la demanda diaria por zona para un tipo de trámite en un mes.
    Filtra por PK = (tipo_tramite, anio_mes).
    """
    tabla = db.get_table("demanda_tipo_tramite")
    return list(tabla.find({"tipo_tramite": tipo_tramite, "anio_mes": anio_mes}))


def demanda_total_por_zona(db, tipo_tramite: str, anio_mes: str) -> dict:
    """
    Agrega la demanda por zona para un tipo de trámite en el mes.
    Útil para el mapa de calor del reporte ejecutivo.
    """
    filas = demanda_tipo_mes(db, tipo_tramite, anio_mes)
    zonas: dict = {}
    for f in filas:
        zona  = f.get("zona", "Desconocida")
        total = f.get("total", 0) or 0
        zonas[zona] = zonas.get(zona, 0) + total
    return {
        "tipo_tramite": tipo_tramite,
        "periodo":      anio_mes,
        "total":        sum(zonas.values()),
        "por_zona":     zonas,
    }


# ══════════════════════════════════════════════════════════════
# TABLA: notificaciones_ciudadano
# PK: ciudadano_id | CK: timestamp DESC
#
# Caso de uso: buzón de notificaciones del ciudadano (OP-1).
# ══════════════════════════════════════════════════════════════
def notificaciones_ciudadano(db, ciudadano_id: str, limit: int = 20) -> list:
    """
    Devuelve las notificaciones de un ciudadano (más recientes primero).
    Filtra por PK = ciudadano_id.
    """
    tabla  = db.get_table("notificaciones_ciudadano")
    filas  = list(tabla.find({"ciudadano_id": ciudadano_id}))
    # Orden descendente por timestamp (clustering key: timestamp DESC)
    filas.sort(key=lambda n: str(n.get("timestamp", "")), reverse=True)
    return filas[:limit]


def notificaciones_no_leidas(db, ciudadano_id: str) -> list:
    """
    Devuelve solo las notificaciones no leídas del ciudadano.
    Filtra en memoria (no existe índice secundario en esta tabla).
    """
    return [n for n in notificaciones_ciudadano(db, ciudadano_id) if not n.get("leida")]


# ══════════════════════════════════════════════════════════════
# ESCRITURAS — Registro de evento (OP-2)
# ══════════════════════════════════════════════════════════════
def insertar_evento(
    db,
    tramite_id:   str,
    organismo_id: str,
    fecha:        str,
    timestamp:    str,
    tipo:         str,
    agente_id:    str,
    duracion_min: int,
    detalle:      str = "",
) -> dict:
    """
    Inserta un evento en las DOS tablas de eventos (desnormalización intencional).
    Garantiza que ambos patrones de acceso (por trámite y por organismo) estén cubiertos.

    Desnormalización intencional:
      - eventos_tramite:    acceso por (organismo_id, fecha)  → OP-3 panel diario
      - eventos_por_tramite: acceso por tramite_id            → OP-1 historial
    """
    evento_base = {
        "tramite_id":   tramite_id,
        "organismo_id": organismo_id,
        "tipo":         tipo,
        "agente_id":    agente_id,
        "duracion_min": int(duracion_min),
        "detalle":      detalle or f"Evento '{tipo}' registrado en {organismo_id}",
        "timestamp":    timestamp,
    }

    # Tabla 1: eventos_tramite (agrega fecha para PK compuesta)
    db.get_table("eventos_tramite").insert_one({**evento_base, "fecha": fecha})

    # Tabla 2: eventos_por_tramite (sin fecha, solo tramite_id como PK)
    db.get_table("eventos_por_tramite").insert_one(evento_base)

    return {"ok": True, "tablas_escritas": ["eventos_tramite", "eventos_por_tramite"]}


# ══════════════════════════════════════════════════════════════
# DEMO — Ejecutar desde la terminal para probar las consultas
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  DEMO — Consultas Cassandra / Astra DB")
    print("═" * 55)

    db = conectar()
    print("✅ Conectado a Astra DB\n")

    # ── Historial de un trámite ──────────────────────────────
    print("1. Historial trámite TRA-2026-000001:")
    eventos = historial_tramite(db, "TRA-2026-000001")
    for e in eventos[:3]:
        print(f"   [{e.get('timestamp','')}] {e.get('tipo','')} — {e.get('organismo_id','')}")
    print(f"   → {len(eventos)} eventos totales\n")

    # ── Métricas organismo ───────────────────────────────────
    print("2. Resumen métricas Mesa de Entradas (2026-03):")
    resumen = resumen_metricas(db, "Mesa de Entradas", "2026-03")
    for k, v in resumen.items():
        print(f"   {k}: {v}")
    print()

    # ── Notificaciones ciudadano ─────────────────────────────
    print("3. Notificaciones ciudadano 30000001:")
    notifs = notificaciones_ciudadano(db, "30000001")
    for n in notifs[:3]:
        leida = "leída" if n.get("leida") else "no leída"
        print(f"   [{n.get('timestamp','')}] {n.get('tipo','')} — {leida}")
    print(f"   → {len(notifs)} notificaciones totales\n")

    print("═" * 55 + "\n")
