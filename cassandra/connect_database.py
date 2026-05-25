from astrapy import DataAPIClient
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