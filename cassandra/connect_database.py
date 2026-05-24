from astrapy import DataAPIClient
import json
from pathlib import Path

print("Iniciando conexión...")

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "nahuel-token.json"

with open(TOKEN_FILE, "r", encoding="utf-8") as f:
    secrets = json.load(f)

TOKEN = secrets["token"]

client = DataAPIClient(TOKEN)

db = client.get_database_by_api_endpoint(
    "https://d48813cf-c0fe-4f17-a523-fb8beeb4858a-us-east-2.apps.astra.datastax.com",
    keyspace="municipio_digital"
)

print("✅ Conectado a Astra DB")
print("Endpoint:", db.api_endpoint)
print("Keyspace: municipio_digital")