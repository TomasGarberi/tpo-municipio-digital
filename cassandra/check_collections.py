from astrapy import DataAPIClient
from pathlib import Path
import json
from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ============================================================
# CONEXIÓN
# ============================================================

TOKEN    = os.getenv("ASTRA_TOKEN")
ENDPOINT = os.getenv("ASTRA_ENDPOINT")
KEYSPACE = os.getenv("ASTRA_KEYSPACE")

client = DataAPIClient(TOKEN)

db = client.get_database_by_api_endpoint(ENDPOINT, keyspace=KEYSPACE)

print("---Conectado a Astra DB---")
print("Listando colecciones/tablas disponibles...")

try:
    collections = db.list_collection_names()
    tables = db.list_table_names()
    print("Tablas encontradas:")
    for table in tables:
        print("-", table)
except Exception as e:
    print("No se pudieron listar colecciones con list_collection_names().")
    print("Error:", e)