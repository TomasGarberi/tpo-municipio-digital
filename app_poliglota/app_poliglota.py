"""
================
Capa de persistencia políglota — TPO Municipio Digital
Implementa las 5 operaciones de negocio integrando:
  MongoDB  → fuente de verdad histórica
  Neo4j    → flujo de derivaciones y grafos
  Cassandra (Astra DB) → log de eventos y métricas

Ejecutar: python app_poliglota.py
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ── Conexiones ────────────────────────────────────────────────────────────────

def conectar_cassandra():
    from astrapy import DataAPIClient
    print("  Conectando a Cassandra (Astra DB)...", end=" ", flush=True)
    client = DataAPIClient(os.getenv("ASTRA_TOKEN"))
    db = client.get_database_by_api_endpoint(
        os.getenv("ASTRA_ENDPOINT"),
        keyspace=os.getenv("ASTRA_KEYSPACE", "municipio_digital")
    )
    print("-->Conectado")
    return db

def conectar_mongo():
    from pymongo import MongoClient
    print("  Conectando a MongoDB (Atlas)...", end=" ", flush=True)
    client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[os.getenv("MONGO_DB", "municipio_digital")]
    print("-->Conectado")
    return db

def conectar_neo4j():
    from neo4j import GraphDatabase
    print("  Conectando a Neo4j (Aura)...", end=" ", flush=True)
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )
    driver.verify_connectivity()
    print("-->Conectado")
    return driver






def main():
    print("\n" + "═"*62)
    print("  Municipio Digital — iniciando conexiones...")
    print("═"*62)

    mongo, neo4j, cassandra = None, None, None

    print("  Conectando a Cassandra (Astra DB)...", end=" ", flush=True)
    try:
        cassandra = conectar_cassandra()
    except Exception as e:
        print(f"✗ ({e})")

    print("  Conectando a MongoDB...", end=" ", flush=True)
    try:
        mongo = conectar_mongo()
    except Exception as e:
        print(f"✗ ({e})")

    print("  Conectando a Neo4j...", end=" ", flush=True)
    try:
        neo4j = conectar_neo4j()
    except Exception as e:
        print(f"✗ ({e})")

    conectados = sum(x is not None for x in [mongo, neo4j, cassandra])
    print(f"\n  {conectados}/3 motores conectados.")

    if conectados == 0:
        print("  Sin conexiones disponibles. Revisá las credenciales.")
        return


if __name__ == "__main__":
    main()
