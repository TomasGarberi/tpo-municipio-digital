"""
seed_cassandra.py
Carga de datos iniciales en Cassandra (Astra DB) para el TP Municipio Digital.
Totalmente alineado con los identificadores de MongoDB y Neo4j.
"""

from astrapy import DataAPIClient
from datetime import datetime, date, timedelta

import json

from pathlib import Path
import json

import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ============================================================
# CONEXIÓN
# ============================================================

with open("nahuelcingolani00@gmail.com-token.json") as f:
    secrets = json.load(f)

TOKEN    = secrets["token"]
ENDPOINT = "https://d48813cf-c0fe-4f17-a523-fb8beeb4858a-us-east-2.apps.astra.datastax.com"
KEYSPACE = "municipio_digital"
TOKEN    = os.getenv("ASTRA_TOKEN")
ENDPOINT = os.getenv("ASTRA_ENDPOINT")
KEYSPACE = os.getenv("ASTRA_KEYSPACE")

client = DataAPIClient(TOKEN)
db     = client.get_database_by_api_endpoint(ENDPOINT, keyspace=KEYSPACE)

print("✅ Conectado a Astra DB")

# ============================================================
# DATOS DE DOMINIO ALINEADOS A MONGO/NEO4J
# ============================================================

ORGANISMOS = {
    "Mesa de Entradas":                "Mesa de Entradas",
    "Direccion de Habilitaciones":     "Direccion de Habilitaciones",
    "Secretaria de Desarrollo Social": "Secretaria de Desarrollo Social",
    "Secretaria de Obras Publicas":    "Secretaria de Obras Publicas",
    "Direccion de Transito":           "Direccion de Transito",
    "Tesoreria Municipal":             "Tesoreria Municipal",
    "Inspeccion General":              "Inspeccion General",
    "Direccion Ambiental":             "Direccion Ambiental",
}

SLA_DIAS = {
    "Mesa de Entradas":                2,
    "Direccion de Habilitaciones":     5,
    "Secretaria de Desarrollo Social": 7,
    "Secretaria de Obras Publicas":    6,
    "Direccion de Transito":           4,
    "Tesoreria Municipal":             3,
    "Inspeccion General":              5,
    "Direccion Ambiental":             6,
}

FLUJO_TRAMITES = {
    "Habilitacion comercial":   ["Mesa de Entradas", "Direccion de Habilitaciones", "Inspeccion General"],
    "Solicitud de beca":        ["Mesa de Entradas", "Secretaria de Desarrollo Social", "Tesoreria Municipal"],
    "Reclamo de obra publica":  ["Mesa de Entradas", "Secretaria de Obras Publicas"],
    "Licencia de conducir":     ["Mesa de Entradas", "Direccion de Transito"],
    "Renovacion de licencia":   ["Mesa de Entradas", "Direccion de Transito"],
    "Subsidio habitacional":    ["Mesa de Entradas", "Secretaria de Desarrollo Social"],
    "Permiso de obra menor":    ["Mesa de Entradas", "Secretaria de Obras Publicas"],
    "Permiso de evento":        ["Mesa de Entradas", "Inspeccion General"],
    "Denuncia ambiental":       ["Mesa de Entradas", "Direccion Ambiental"],
    "Exencion impositiva":      ["Mesa de Entradas", "Tesoreria Municipal"],
}

TIPOS_TRAMITE = list(FLUJO_TRAMITES.keys())
ZONAS = ["Municipio Central", "Municipio Norte", "Municipio Sur", "Municipio Oeste"]

# DNIs idénticos a los generados en el script de MongoDB y Cypher (30000001 al 30000010)
CIUDADANOS = [str(30000000 + i) for i in range(1, 11)]

# ============================================================
# HELPER
# ============================================================

def ts(base_date: date, offset_hours: int = 0) -> str:
    dt = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=offset_hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# ============================================================
# TABLA: eventos_tramite + eventos_por_tramite
# ============================================================

print("\n📝 Cargando eventos_tramite y eventos_por_tramite...")

col_et  = db.get_table("eventos_tramite")
col_ept = db.get_table("eventos_por_tramite")

fecha_base = date(2026, 3, 1)

for i in range(1, 26):
    # Formato alineado: TRA-2026-000001
    tramite_id    = f"TRA-2026-{str(i).zfill(6)}"
    tipo_tramite  = TIPOS_TRAMITE[(i - 1) % len(TIPOS_TRAMITE)]
    flujo         = FLUJO_TRAMITES[tipo_tramite]
    fecha_tramite = fecha_base + timedelta(days=(i % 28))
    hora_offset   = 0

    for j, organismo in enumerate(flujo):
        org_id       = ORGANISMOS[organismo]
        # Formato alineado al insert de Mongo: agente_001
        agente_id    = f"agente_{str(i).zfill(3)}" 
        duracion_min = 60 + (i * 7 + j * 13) % 480
        tipo_ev      = "recepcion" if j == 0 else ("resolucion" if j == len(flujo) - 1 else "derivacion")
        detalle      = f"Evento {tipo_ev} en {organismo} para tramite {tramite_id}"
        timestamp    = ts(fecha_tramite, hora_offset)
        hora_offset += duracion_min // 60 + 1

        col_et.insert_one({
            "organismo_id": org_id,
            "fecha":        fecha_tramite.isoformat(),
            "timestamp":    timestamp,
            "tramite_id":   tramite_id,
            "tipo":         tipo_ev,
            "agente_id":    agente_id,
            "duracion_min": duracion_min,
            "detalle":      detalle,
        })

        col_ept.insert_one({
            "tramite_id":   tramite_id,
            "timestamp":    timestamp,
            "organismo_id": org_id,
            "tipo":         tipo_ev,
            "agente_id":    agente_id,
            "duracion_min": duracion_min,
            "detalle":      detalle,
        })

print("   ✅ Eventos cargados en eventos_tramite y eventos_por_tramite")

# ============================================================
# TABLA: metricas_organismo
# ============================================================

print("\n📊 Cargando metricas_organismo...")

col_mo = db.get_table("metricas_organismo")

for org_nombre, org_id in ORGANISMOS.items():
    for mes_num, anio_mes, dias_mes in [(3, "2026-03", 31), (4, "2026-04", 30)]:
        for dia in range(1, dias_mes + 1):
            fecha_dia       = date(2026, mes_num, dia)
            # Usamos el string del id del organismo para generar la semilla de hash
            procesados      = 5 + (hash(f"{org_id}{dia}") % 20)
            tiempo_promedio = 120 + (hash(f"{org_id}{dia}x") % 360)
            sla_c           = int(procesados * (0.6 + (hash(f"{org_id}{dia}s") % 40) / 100))
            sla_i           = procesados - sla_c

            col_mo.insert_one({
                "organismo_id":        org_id,
                "anio_mes":            anio_mes,
                "fecha":               fecha_dia.isoformat(),
                "tramites_procesados": procesados,
                "tiempo_promedio_min": float(tiempo_promedio),
                "sla_cumplidos":       sla_c,
                "sla_incumplidos":     sla_i,
            })

print(f"   ✅ Metricas cargadas para {len(ORGANISMOS)} organismos x 2 meses")

# ============================================================
# TABLA: demanda_tipo_tramite — YA CARGADA, SE OMITE
# ============================================================

print("\n📈 demanda_tipo_tramite ya cargada (1670 filas) — omitida")

# ============================================================
# TABLA: notificaciones_ciudadano
# ============================================================

print("\n🔔 Cargando notificaciones_ciudadano...")

col_nc = db.get_table("notificaciones_ciudadano")

TIPOS_NOTIF = ["cambio_estado", "vencimiento", "resolucion"]
CANALES     = ["email", "sms", "push"]

for idx, ciudadano_id in enumerate(CIUDADANOS):
    for n in range(3 + idx % 3):
        # Aseguramos que el trámite caiga en el rango de los 25 que creamos (1 al 25)
        tramite_num = (idx + 1 + n) % 25
        if tramite_num == 0:
            tramite_num = 25
            
        tramite_id  = f"TRA-2026-{str(tramite_num).zfill(6)}"
        tipo_notif  = TIPOS_NOTIF[n % len(TIPOS_NOTIF)]
        canal       = CANALES[n % len(CANALES)]
        timestamp   = ts(date(2026, 3, 1 + tramite_num % 28), n * 2)

        col_nc.insert_one({
            "ciudadano_id": ciudadano_id,
            "timestamp":    timestamp,
            "tramite_id":   tramite_id,
            "tipo":         tipo_notif,
            "canal":        canal,
            "mensaje":      f"Su tramite {tramite_id} tiene una actualizacion: {tipo_notif}",
            "leida":        n % 2 == 0,
        })

print(f"   ✅ Notificaciones cargadas para {len(CIUDADANOS)} ciudadanos")

# ============================================================
# RESUMEN
# ============================================================

print("\n" + "="*50)
print("✅ CARGA COMPLETA")
print("="*50)
print("\nVerifica en CQL Console:")
print("  SELECT COUNT(*) FROM municipio_digital.eventos_tramite;")
print("  SELECT COUNT(*) FROM municipio_digital.eventos_por_tramite;")
print("  SELECT COUNT(*) FROM municipio_digital.metricas_organismo;")
print("  SELECT COUNT(*) FROM municipio_digital.notificaciones_ciudadano;")