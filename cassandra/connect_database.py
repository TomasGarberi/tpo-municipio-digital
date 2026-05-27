from astrapy import DataAPIClient
from pathlib import Path
import json
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
db     = client.get_database_by_api_endpoint(ENDPOINT, keyspace=KEYSPACE)

print("Conectado a Astra DB:", db.name)