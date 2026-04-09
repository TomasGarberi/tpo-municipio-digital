// Recorrido de un trámite
MATCH (t:Tramite {numero: 'TRA-001'})-[:ES_DE_TIPO]->(tipo),
      (tipo)-[:INICIA_EN|PASA_POR]->(org)
RETURN t, tipo, org;

// Flujo completo
MATCH path = (tipo:TipoTramite {nombre: 'Habilitacion comercial'})-[:INICIA_EN|PASA_POR*]->(org)
RETURN path;

// Organismos más usados
MATCH (tipo:TipoTramite)-[:PASA_POR]->(org:Organismo)
RETURN org.nombre, COUNT(*) AS cantidad
ORDER BY cantidad DESC;

// Cuellos de botella
MATCH (org:Organismo)<-[:PASA_POR]-(tipo:TipoTramite)
RETURN org.nombre, COUNT(tipo) AS carga
ORDER BY carga DESC;

// Derivaciones
MATCH (o1:Organismo)-[r:DERIVA_A]->(o2:Organismo)
RETURN o1.nombre, o2.nombre, r.condicion;