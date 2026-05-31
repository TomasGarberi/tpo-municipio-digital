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
# trámite.
# ══════════════════════════════════════════════════════════════
def historial_tramite(db, tramite_id: str) -> list:
    """
    Devuelve todos los eventos de un trámite en orden cronológico.
    Filtra por PK = tramite_id.
    """
    tabla = db.get_table("eventos_por_tramite")
    eventos = list(tabla.find({"tramite_id": tramite_id}))
    return sorted(eventos, key=lambda e: str(e.get("timestamp", "")))


# ══════════════════════════════════════════════════════════════
# TABLA: eventos_tramite
# PK: (organismo_id, fecha) | CK: timestamp DESC, tramite_id ASC
#
# Caso de uso: actividad diaria de un organismo.
# ══════════════════════════════════════════════════════════════
def eventos_organismo_fecha(db, organismo_id: str, fecha: str) -> list:
    """
    Devuelve todos los eventos procesados por un organismo en una fecha.
    Filtra por PK = (organismo_id, fecha).
    """
    tabla = db.get_table("eventos_tramite")
    eventos = list(tabla.find({"organismo_id": organismo_id, "fecha": fecha}))
    return sorted(eventos, key=lambda e: str(e.get("timestamp", "")))


# ══════════════════════════════════════════════════════════════
# TABLA: metricas_organismo
# PK: (organismo_id, anio_mes) | CK: fecha ASC
#
# Caso de uso: panel de desempeño mensual.
# ══════════════════════════════════════════════════════════════
def metricas_organismo_mes(db, organismo_id: str, anio_mes: str) -> list:
    """
    Devuelve las métricas diarias de un organismo en un mes.
    Filtra por PK = (organismo_id, anio_mes).
    """
    tabla = db.get_table("metricas_organismo")
    filas = list(tabla.find({"organismo_id": organismo_id, "anio_mes": anio_mes}))
    return sorted(filas, key=lambda r: str(r.get("fecha", "")))


def resumen_metricas(db, organismo_id: str, anio_mes: str) -> dict:
    """
    Agrega las métricas del mes para un organismo.
    Retorna totales y tasa de cumplimiento SLA.
    """
    filas = metricas_organismo_mes(db, organismo_id, anio_mes)

    procesados = sum(f.get("tramites_procesados", 0) or 0 for f in filas)
    sla_cumplidos = sum(f.get("sla_cumplidos", 0) or 0 for f in filas)
    sla_incumplidos = sum(f.get("sla_incumplidos", 0) or 0 for f in filas)
    tasa = (sla_cumplidos / (procesados or 1)) * 100

    return {
        "organismo": organismo_id,
        "periodo": anio_mes,
        "tramites_procesados": procesados,
        "sla_cumplidos": sla_cumplidos,
        "sla_incumplidos": sla_incumplidos,
        "tasa_cumplimiento_sla": f"{tasa:.1f}%",
        "dias_con_datos": len(filas),
    }


# ══════════════════════════════════════════════════════════════
# TABLA: demanda_tipo_tramite
# PK: (tipo_tramite, anio_mes) | CK: fecha ASC, zona ASC
#
# Caso de uso: análisis de demanda mensual por tipo y zona.
# ══════════════════════════════════════════════════════════════
def demanda_tipo_mes(db, tipo_tramite: str, anio_mes: str) -> list:
    """
    Devuelve la demanda diaria por zona para un tipo de trámite en un mes.
    Filtra por PK = (tipo_tramite, anio_mes).
    """
    tabla = db.get_table("demanda_tipo_tramite")
    filas = list(tabla.find({"tipo_tramite": tipo_tramite, "anio_mes": anio_mes}))
    return sorted(
        filas,
        key=lambda r: (str(r.get("fecha", "")), str(r.get("zona", ""))),
    )


def demanda_total_por_zona(db, tipo_tramite: str, anio_mes: str) -> dict:
    """
    Agrega la demanda por zona para un tipo de trámite en el mes.
    """
    filas = demanda_tipo_mes(db, tipo_tramite, anio_mes)
    zonas = {}

    for f in filas:
        zona = f.get("zona", "Desconocida")
        cantidad = f.get("cantidad", f.get("total", 0)) or 0
        zonas[zona] = zonas.get(zona, 0) + cantidad

    return {
        "tipo_tramite": tipo_tramite,
        "periodo": anio_mes,
        "total": sum(zonas.values()),
        "por_zona": zonas,
    }


# ══════════════════════════════════════════════════════════════
# TABLA: notificaciones_ciudadano
# PK: ciudadano_id | CK: timestamp DESC
#
# Caso de uso: buzón de notificaciones del ciudadano.
# ══════════════════════════════════════════════════════════════
def notificaciones_ciudadano(db, ciudadano_id: str, limit: int = 20) -> list:
    """
    Devuelve las notificaciones de un ciudadano.
    Filtra por PK = ciudadano_id.
    """
    tabla = db.get_table("notificaciones_ciudadano")
    filas = list(tabla.find({"ciudadano_id": ciudadano_id}))
    filas.sort(key=lambda n: str(n.get("timestamp", "")), reverse=True)
    return filas[:limit]


def notificaciones_no_leidas(db, ciudadano_id: str) -> list:
    """
    Devuelve solo las notificaciones no leídas del ciudadano.
    """
    return [
        n
        for n in notificaciones_ciudadano(db, ciudadano_id)
        if not n.get("leida")
    ]


# ══════════════════════════════════════════════════════════════
# ESCRITURAS — Registro de evento
# ══════════════════════════════════════════════════════════════
def insertar_evento(
    db,
    tramite_id: str,
    organismo_id: str,
    fecha: str,
    timestamp: str,
    tipo: str,
    agente_id: str,
    duracion_min: int,
    detalle: str = "",
) -> dict:
    """
    Inserta un evento en las dos tablas de eventos.
    Esto responde a la desnormalización intencional de Cassandra:
    - eventos_tramite: acceso por organismo y fecha
    - eventos_por_tramite: acceso por trámite
    """
    evento_base = {
        "tramite_id": tramite_id,
        "organismo_id": organismo_id,
        "tipo": tipo,
        "agente_id": agente_id,
        "duracion_min": int(duracion_min),
        "detalle": detalle or f"Evento '{tipo}' registrado en {organismo_id}",
        "timestamp": timestamp,
    }

    db.get_table("eventos_tramite").insert_one(
        {**evento_base, "fecha": fecha}
    )

    db.get_table("eventos_por_tramite").insert_one(evento_base)

    return {
        "ok": True,
        "tablas_escritas": ["eventos_tramite", "eventos_por_tramite"],
    }


# ══════════════════════════════════════════════════════════════
# DEMO — Ejecutar desde la terminal para probar las consultas
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  DEMO — Consultas Cassandra / Astra DB")
    print("═" * 55)

    db = conectar()
    print("✅ Conectado a Astra DB\n")

    # 1. Historial de un trámite
    print("1. Historial trámite TRA-2026-000001:")
    eventos = historial_tramite(db, "TRA-2026-000001")
    for e in eventos[:3]:
        print(
            f"   [{e.get('timestamp', '')}] "
            f"{e.get('tipo', e.get('tipo_evento', ''))} — "
            f"{e.get('organismo_id', '')}"
        )
    print(f"   → {len(eventos)} eventos totales\n")

    # 2. Eventos por organismo y fecha
    print("2. Eventos Mesa de Entradas (2026-03-02):")
    eventos_org = eventos_organismo_fecha(db, "Mesa de Entradas", "2026-03-02")
    for e in eventos_org[:3]:
        print(
            f"   [{e.get('timestamp', '')}] "
            f"{e.get('tipo', e.get('tipo_evento', ''))} — "
            f"{e.get('tramite_id', '')}"
        )
    print(f"   → {len(eventos_org)} eventos totales\n")

    # 3. Métricas organismo
    print("3. Resumen métricas Mesa de Entradas (2026-03):")
    resumen = resumen_metricas(db, "Mesa de Entradas", "2026-03")
    for k, v in resumen.items():
        print(f"   {k}: {v}")
    print()

    # 4. Demanda por tipo de trámite
    print("4. Demanda Habilitacion comercial (2026-03):")
    demanda = demanda_tipo_mes(db, "Habilitacion comercial", "2026-03")
    for d in demanda[:3]:
        print(
            f"   [{d.get('fecha', '')}] "
            f"{d.get('zona', '')} — "
            f"cantidad: {d.get('cantidad', d.get('total', ''))}"
        )
    print(f"   → {len(demanda)} registros de demanda\n")

    # 5. Notificaciones ciudadano
    print("5. Notificaciones ciudadano 30000001:")
    notifs = notificaciones_ciudadano(db, "30000001")
    for n in notifs[:3]:
        leida = "leída" if n.get("leida") else "no leída"
        print(
            f"   [{n.get('timestamp', '')}] "
            f"{n.get('tipo', '')} — {leida}"
        )
    print(f"   → {len(notifs)} notificaciones totales\n")

    print("═" * 55 + "\n")

# ── SECCIÓN 3.2 — Métricas de desempeño ──────────────────
    print("── Sección 3.2 ─────────────────────────────────────")

    print("\n3.2.b Reporte mensual Mesa de Entradas (2026-03):")
    resumen = resumen_metricas(db, "Mesa de Entradas", "2026-03")
    for k, v in resumen.items():
        print(f"   {k}: {v}")

    print("\n3.2.b Reporte mensual Direccion de Habilitaciones (2026-03):")
    resumen2 = resumen_metricas(db, "Direccion de Habilitaciones", "2026-03")
    for k, v in resumen2.items():
        print(f"   {k}: {v}")

    print("\n3.2.d Organismos con SLA crítico >20% (2026-03):")
    for org in ["Mesa de Entradas", "Direccion de Habilitaciones",
                "Secretaria de Desarrollo Social", "Secretaria de Obras Publicas",
                "Direccion de Transito", "Tesoreria Municipal",
                "Inspeccion General", "Direccion Ambiental"]:
        r = resumen_metricas(db, org, "2026-03")
        procesados = r["tramites_procesados"]
        incumplidos = r["sla_incumplidos"]
        if procesados > 0 and (incumplidos / procesados) > 0.20:
            print(f"   ⚠ {org}: {r['tasa_cumplimiento_sla']} cumplimiento")

    # ── SECCIÓN 3.3 — Demanda ciudadana ──────────────────────
    print("\n── Sección 3.3 ─────────────────────────────────────")

    print("\n3.3.a Demanda mensual 'Licencia de conducir' (últimos meses):")
    demanda = demanda_total_por_zona(db, "Licencia de conducir", "2026-03")
    print(f"   Total: {demanda['total']}")
    for zona, cant in demanda["por_zona"].items():
        print(f"   {zona}: {cant}")

    print("\n3.3.c Zonas con mayor demanda de 'Habilitacion comercial' (2026-03):")
    dem2 = demanda_total_por_zona(db, "Habilitacion comercial", "2026-03")
    print(f"   Total: {dem2['total']}")
    for zona, cant in dem2["por_zona"].items():
        print(f"   {zona}: {cant}")

    print("\n3.3.d Demanda 'Solicitud de beca' (2026-03):")
    dem3 = demanda_total_por_zona(db, "Solicitud de beca", "2026-03")
    for zona, cant in dem3["por_zona"].items():
        print(f"   {zona}: {cant}")