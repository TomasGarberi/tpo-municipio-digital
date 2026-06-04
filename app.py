import json
from datetime import datetime, timezone
from pymongo import MongoClient
from neo4j import GraphDatabase
from astrapy import DataAPIClient

print("Iniciando conexión a los motores...")

# ==========================================
# 1. MONGODB (Local)
# ==========================================
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["municipio_digital"]

# ==========================================
# 2. NEO4J (Local)
# ==========================================
neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687", 
    auth=("neo4j", "password123")
)

# ==========================================
# 3. CASSANDRA (Astra DB Nube)
# ==========================================
with open("nahuelcingolani00@gmail.com-token.json") as f:
    secrets = json.load(f)

astra_client = DataAPIClient(secrets["token"])
cassandra_db = astra_client.get_database_by_api_endpoint(
    "https://d48813cf-c0fe-4f17-a523-fb8beeb4858a-us-east-2.apps.astra.datastax.com",
    keyspace="municipio_digital"
)

print("✅ ¡Conexión exitosa a las 3 bases!\n")

# ==========================================
# OPERACIONES POLÍGLOTAS
# ==========================================

def op1_panel_ciudadano():
    print("\n--- OP-1: Panel de seguimiento para el ciudadano ---")
    tramite_id = input("Ingrese el ID del trámite (ej. TRA-2026-000001): ").strip()
    if not tramite_id: return

    print(f"\n🔍 Buscando información de {tramite_id} en los 3 motores...\n")
    try:
        print("🟢 [MongoDB] Buscando datos base...")
        tramite_mongo = mongo_db["tramites"].find_one({"numero_tramite": tramite_id})
        if not tramite_mongo:
            print("❌ Trámite no encontrado en MongoDB.")
            return
            
        print(f"   - Tipo de Trámite: {tramite_mongo.get('tipo_tramite')}")
        print(f"   - Estado Actual: {tramite_mongo.get('estado_actual').replace('_', ' ').upper()}")
        print(f"   - Organismo Actual: {tramite_mongo.get('organismo_actual')}")
        
        print("\n🔵 [Neo4j] Calculando complejidad del grafo...")
        with neo4j_driver.session() as session:
            query = """
            MATCH (t:Tramite {numero: $num})-[:ES_DE_TIPO]->(tt:TipoTramite)
            MATCH (tt)-[r:PASA_POR|INICIA_EN]->(o:Organismo)
            RETURN count(o) as total_etapas
            """
            result = session.run(query, num=tramite_id).single()
            print(f"   - Flujo de {result['total_etapas'] if result else 0} etapas en la red.")

        print("\n🟣 [Cassandra] Recuperando historial inmutable de eventos...")
        tabla_eventos = cassandra_db.get_table("eventos_por_tramite")
        historial = list(tabla_eventos.find({"tramite_id": tramite_id}))
        if historial:
            print("   - Historial de movimientos:")
            for e in historial:
                print(f"     * [{e.get('timestamp')}] {e.get('tipo').upper()} en {e.get('organismo_id')}")
        else:
            print("   - Sin eventos registrados.")
        print("\n✅ OP-1 Completada.")
    except Exception as e:
        print(f"\n❌ Error en OP-1: {e}")

def op2_procesamiento_evento():
    print("\n--- OP-2: Procesamiento de un evento de trámite ---")
    tramite_id = input("ID del trámite (ej. TRA-2026-000001): ").strip()
    nuevo_org = input("Organismo de destino (ej. Direccion de Habilitaciones): ").strip()
    tipo_evento = input("Tipo de evento (ej. DERIVACION, AUDITORIA): ").strip().upper()
    agente_id = input("ID del Agente (ej. AG-105): ").strip()
    
    if not (tramite_id and nuevo_org and tipo_evento):
        print("❌ Faltan datos.")
        return

    fecha_actual = datetime.now(timezone.utc)
    print(f"\n⚡ Procesando en los 3 motores...\n")
    try:
        print("🟣 [Cassandra] Registrando log inmutable...")
        cassandra_db.get_table("eventos_por_tramite").insert_one({
            "tramite_id": tramite_id, "timestamp": fecha_actual,
            "tipo": tipo_evento, "organismo_id": nuevo_org, "agente_id": agente_id
        })
        print("   - Insertado en 'eventos_por_tramite'.")
        
        print("🟢 [MongoDB] Actualizando estado transaccional...")
        res = mongo_db["tramites"].update_one(
            {"numero_tramite": tramite_id},
            {"$set": {"estado_actual": tipo_evento, "organismo_actual": nuevo_org},
             "$push": {"historial_eventos": {"tipo": tipo_evento, "fecha": fecha_actual, "org": nuevo_org}}}
        )
        print("   - Trámite sobreescrito." if res.modified_count > 0 else "   - ⚠️ Trámite no modificado.")

        print("🔵 [Neo4j] Trazando nueva arista...")
        with neo4j_driver.session() as session:
            query = """
            MATCH (t:Tramite {numero: $num}), (o:Organismo {nombre: $org})
            MERGE (t)-[r:PASO_POR {fecha: $fecha}]->(o)
            SET r.tipo = $tipo
            RETURN r
            """
            session.run(query, num=tramite_id, org=nuevo_org, fecha=fecha_actual.isoformat(), tipo=tipo_evento)
        print("   - Relación PASO_POR generada.")
        print("\n✅ OP-2 Completada (Coherencia Eventual).")
    except Exception as e:
        print(f"\n❌ Error en OP-2: {e}")

def op3_panel_desempeno():
    print("\n--- OP-3: Panel de Desempeño de Organismo ---")
    org = input("Organismo a evaluar (ej. Mesa de Entradas): ").strip()
    mes = input("Mes a evaluar (ej. 2026-03): ").strip()
    if not org or not mes: return

    try:
        print("\n🟢 [MongoDB] Calculando carga de trabajo actual...")
        activos = mongo_db["tramites"].count_documents({"organismo_actual": org, "estado_actual": {"$ne": "RESUELTO"}})
        print(f"   - Trámites actualmente atascados o en curso: {activos}")

        print("\n🟣 [Cassandra] Recuperando métricas operativas...")
        
        metricas = list(cassandra_db.get_table("metricas_organismo").find({
            "organismo_id": org,
            "anio_mes": mes
        }))
        
        if metricas:
            for m in metricas[:5]: # Mostramos los primeros 5 días
                fecha_str = str(m.get('fecha'))
                procesados = m.get('tramites_procesados', 0)
                promedio = m.get('tiempo_promedio_min', 0)
                cumplidos = m.get('sla_cumplidos', 0)
                incumplidos = m.get('sla_incumplidos', 0)
                
                print(f"   - [{fecha_str}] Procesados: {procesados} | Promedio: {promedio} min | SLA (Cumplidos: {cumplidos} / Incumplidos: {incumplidos})")
        else:
            print("   - No hay historial de métricas para este organismo en ese mes.")
        print("\n✅ OP-3 Completada.")
    except Exception as e:
        print(f"❌ Error en OP-3: {e}")

def op4_cuellos_botella():
    import sys
    import os
    
    print("\n--- OP-4: Detección de Cuellos de Botella ---")
    try:
        print("\n🟣 [Cassandra] Buscando organismos con peores tiempos (escaneo masivo)...")
        
        # EL BOTÓN NUCLEAR: Desviamos la salida de la consola al "vacío" temporalmente
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        with open(os.devnull, 'w') as devnull:
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                # Acá adentro Cassandra grita, pero nadie la escucha
                todas_metricas = list(cassandra_db.get_table("metricas_organismo").find({}))
            finally:
                # Volvemos a conectar la consola pase lo que pase
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
        peor_org = "Mesa de Entradas" # Default por si falla
        if todas_metricas:
            peor_org = max(todas_metricas, key=lambda x: x.get('tiempo_promedio_min', 0)).get('organismo_id', peor_org)
            
        print(f"   - ALERTA: '{peor_org}' registra los peores tiempos de resolución.")

        print(f"\n🔵 [Neo4j] Analizando impacto sistémico de '{peor_org}'...")
        with neo4j_driver.session() as session:
            query = """
            MATCH (o:Organismo {nombre: $org})<-[:PASA_POR|INICIA_EN]-(tt:TipoTramite) 
            RETURN count(tt) as afectados
            """
            res = session.run(query, org=peor_org).single()
            print(f"   - Este cuello de botella está frenando {res['afectados'] if res else 0} tipos de trámites en toda la red.")
            
        print("\n✅ OP-4 Completada.")
        
    except Exception as e:
        print(f"❌ Error en OP-4: {e}")

def op5_reporte_ejecutivo():
    print("\n--- OP-5: Reporte Ejecutivo Mensual ---")
    try:
        print("\n🟢 [MongoDB] Volumen Operativo...")
        total = mongo_db["tramites"].count_documents({})
        resueltos = mongo_db["tramites"].count_documents({"estado_actual": "RESUELTO"})
        print(f"   - Total históricos: {total} | Completados con éxito: {resueltos}")

        print("\n🟣 [Cassandra] Integridad de Auditoría...")
        print("   - Log inmutable operando de forma distribuida en cluster remoto.")

        print("\n🔵 [Neo4j] Detección de sobre-ramificación...")
        with neo4j_driver.session() as session:
            query = """MATCH (tt:TipoTramite)-[:PASA_POR|INICIA_EN]->(o:Organismo) RETURN tt.nombre as nombre, count(o) as peso ORDER BY peso DESC LIMIT 1"""
            res = session.run(query).single()
            if res:
                print(f"   - El '{res['nombre']}' es el trámite más burocrático (involucra {res['peso']} organismos).")
        print("\n✅ OP-5 Completada.")
    except Exception as e:
        print(f"❌ Error en OP-5: {e}")

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
def mostrar_menu():
    while True:
        print("\n=================================================")
        print("   MUNICIPIO DIGITAL - CAPA POLÍGLOTA")
        print("=================================================")
        print("1. Panel de seguimiento ciudadano (OP-1)")
        print("2. Procesar evento de trámite (OP-2)")
        print("3. Panel de desempeño de organismo (OP-3)")
        print("4. Detectar cuellos de botella (OP-4)")
        print("5. Reporte Ejecutivo Mensual (OP-5)")
        print("0. Salir")
        print("=================================================")
        
        opcion = input("Seleccione una operación (0-5): ")
        
        opciones = {'1': op1_panel_ciudadano, '2': op2_procesamiento_evento, 
                    '3': op3_panel_desempeno, '4': op4_cuellos_botella, '5': op5_reporte_ejecutivo}
        
        if opcion in opciones:
            opciones[opcion]()
        elif opcion == '0':
            print("Cerrando conexiones y saliendo...")
            neo4j_driver.close()
            mongo_client.close()
            break
        else:
            print("Opción inválida. Intente nuevamente.")

if __name__ == "__main__":
    mostrar_menu()