# Modelo inicial - TPO Municipio Digital

## Alcance de la primera entrega
En esta primera entrega se trabajará con MongoDB y Neo4j de forma independiente, pero manteniendo coherencia entre los datos para facilitar la integración poliglota en la segunda entrega.

## MongoDB
Colecciones previstas:
- ciudadanos
- tramites
- tipos_tramite
- organismos
- documentos

### Decisiones iniciales
- Los eventos del historial se guardarán embebidos dentro de cada trámite.
- El ciudadano se referenciará desde el trámite.
- El tipo de trámite se referenciará desde el trámite.
- El organismo actual se referenciará desde el trámite.
- Los documentos se modelarán en una colección separada.

### Justificación inicial
Se decide embebir los eventos porque forman parte del historial propio del trámite y normalmente se consultan junto con él.
Se decide referenciar ciudadanos, tipos de trámite y organismos porque son entidades compartidas entre múltiples trámites.
Los documentos se separan porque pueden crecer en cantidad y tener validaciones propias.

## Neo4j
Nodos previstos:
- Ciudadano
- Tramite
- TipoTramite
- Organismo

Relaciones previstas:
- (Ciudadano)-[:INICIO]->(Tramite)
- (Tramite)-[:ES_DE_TIPO]->(TipoTramite)
- (Tramite)-[:ESTA_EN]->(Organismo)
- (Organismo)-[:DERIVA_A]->(Organismo)
- (Tramite)-[:DEPENDE_DE]->(Tramite)

## Criterio general
MongoDB se usará para almacenar la información operativa y documental de los trámites.
Neo4j se usará para representar y consultar el flujo de derivaciones, las dependencias entre trámites y la detección de cuellos de botella.
