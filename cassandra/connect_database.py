from astrapy import DataAPIClient
<<<<<<< HEAD
import json

print("Iniciando conexión...")

with open("nahuelcingolani00@gmail.com-token.json") as f:
    secrets = json.load(f)

TOKEN = secrets["token"]

client = DataAPIClient(TOKEN)

db = client.get_database_by_api_endpoint(
    "https://d48813cf-c0fe-4f17-a523-fb8beeb4858a-us-east-2.apps.astra.datastax.com",
    keyspace="municipio_digital"
)

print("✅ Conectado a Astra DB:", db.name)
=======
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
>>>>>>> 63d8c301b7902a1ea1b8f77991a74b55ee603fcf
