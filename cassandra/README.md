# Cassandra / Astra DB

Este módulo corresponde a la implementación del tercer motor NoSQL utilizado en la segunda entrega del TPO: Cassandra mediante Astra DB.

## Objetivo

Cassandra se incorpora para almacenar información orientada a eventos, métricas y consultas de alto volumen, complementando el modelo documental de MongoDB y el modelo de grafos de Neo4j.

## Uso dentro del TPO

En el esquema de persistencia políglota del proyecto:

- MongoDB almacena la información principal de trámites, ciudadanos, organismos y documentos.
- Neo4j representa relaciones, flujos, dependencias y derivaciones entre entidades.
- Cassandra/Astra DB se utiliza para registrar eventos, métricas y datos de consulta frecuente asociados al funcionamiento del sistema.

## Archivos

- `connect_database.py`: script utilizado para validar la conexión con Astra DB.
- `check_collections.py`: script de prueba utilizado inicialmente para intentar listar colecciones mediante Data API.
- `README.md`: descripción del módulo Cassandra/Astra DB.

## Archivos pendientes

A confirmar según el script de carga utilizado:

- `schema.cql` o script equivalente de creación de tablas.
- `carga_inicial_cassandra.py`.
- `consultas_cassandra.py`.

## Seguridad

El archivo de token de acceso no debe subirse al repositorio. Debe mantenerse localmente y estar excluido mediante `.gitignore`.