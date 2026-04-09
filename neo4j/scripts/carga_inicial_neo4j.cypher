MATCH (n)
DETACH DELETE n;

CREATE
  (me:Organismo {nombre: 'Mesa de Entradas', area: 'Administracion General', responsable: 'Laura Martinez', sla_dias: 2}),
  (hab:Organismo {nombre: 'Direccion de Habilitaciones', area: 'Produccion y Comercio', responsable: 'Carlos Ramirez', sla_dias: 5}),
  (ds:Organismo {nombre: 'Secretaria de Desarrollo Social', area: 'Desarrollo Humano', responsable: 'Mariana Lopez', sla_dias: 7}),
  (op:Organismo {nombre: 'Secretaria de Obras Publicas', area: 'Infraestructura', responsable: 'Diego Suarez', sla_dias: 6}),
  (tr:Organismo {nombre: 'Direccion de Transito', area: 'Movilidad', responsable: 'Sofia Benitez', sla_dias: 4}),
  (tes:Organismo {nombre: 'Tesoreria Municipal', area: 'Hacienda', responsable: 'Fernando Castro', sla_dias: 3}),
  (ig:Organismo {nombre: 'Inspeccion General', area: 'Control Urbano', responsable: 'Patricia Molina', sla_dias: 5}),
  (amb:Organismo {nombre: 'Direccion Ambiental', area: 'Ambiente', responsable: 'Gabriel Herrera', sla_dias: 6});

CREATE
  (t1:TipoTramite {nombre: 'Habilitacion comercial', tiempo_estimado_dias: 20}),
  (t2:TipoTramite {nombre: 'Solicitud de beca', tiempo_estimado_dias: 15}),
  (t3:TipoTramite {nombre: 'Reclamo de obra publica', tiempo_estimado_dias: 12}),
  (t4:TipoTramite {nombre: 'Licencia de conducir', tiempo_estimado_dias: 10}),
  (t5:TipoTramite {nombre: 'Renovacion de licencia', tiempo_estimado_dias: 7}),
  (t6:TipoTramite {nombre: 'Subsidio habitacional', tiempo_estimado_dias: 18}),
  (t7:TipoTramite {nombre: 'Permiso de obra menor', tiempo_estimado_dias: 14}),
  (t8:TipoTramite {nombre: 'Permiso de evento', tiempo_estimado_dias: 9}),
  (t9:TipoTramite {nombre: 'Denuncia ambiental', tiempo_estimado_dias: 11}),
  (t10:TipoTramite {nombre: 'Exencion impositiva', tiempo_estimado_dias: 13});

MATCH
  (me:Organismo {nombre: 'Mesa de Entradas'}),
  (hab:Organismo {nombre: 'Direccion de Habilitaciones'}),
  (ds:Organismo {nombre: 'Secretaria de Desarrollo Social'}),
  (op:Organismo {nombre: 'Secretaria de Obras Publicas'}),
  (tr:Organismo {nombre: 'Direccion de Transito'}),
  (tes:Organismo {nombre: 'Tesoreria Municipal'}),
  (ig:Organismo {nombre: 'Inspeccion General'}),
  (amb:Organismo {nombre: 'Direccion Ambiental'}),
  (t1:TipoTramite {nombre: 'Habilitacion comercial'}),
  (t2:TipoTramite {nombre: 'Solicitud de beca'}),
  (t3:TipoTramite {nombre: 'Reclamo de obra publica'}),
  (t4:TipoTramite {nombre: 'Licencia de conducir'}),
  (t5:TipoTramite {nombre: 'Renovacion de licencia'}),
  (t6:TipoTramite {nombre: 'Subsidio habitacional'}),
  (t7:TipoTramite {nombre: 'Permiso de obra menor'}),
  (t8:TipoTramite {nombre: 'Permiso de evento'}),
  (t9:TipoTramite {nombre: 'Denuncia ambiental'}),
  (t10:TipoTramite {nombre: 'Exencion impositiva'})
CREATE
  (t1)-[:INICIA_EN]->(me),
  (t1)-[:PASA_POR]->(hab),
  (t1)-[:PASA_POR]->(ig),

  (t2)-[:INICIA_EN]->(me),
  (t2)-[:PASA_POR]->(ds),
  (t2)-[:PASA_POR]->(tes),

  (t3)-[:INICIA_EN]->(me),
  (t3)-[:PASA_POR]->(op),

  (t4)-[:INICIA_EN]->(me),
  (t4)-[:PASA_POR]->(tr),

  (t5)-[:INICIA_EN]->(me),
  (t5)-[:PASA_POR]->(tr),

  (t6)-[:INICIA_EN]->(me),
  (t6)-[:PASA_POR]->(ds),

  (t7)-[:INICIA_EN]->(me),
  (t7)-[:PASA_POR]->(op),

  (t8)-[:INICIA_EN]->(me),
  (t8)-[:PASA_POR]->(ig),

  (t9)-[:INICIA_EN]->(me),
  (t9)-[:PASA_POR]->(amb),

  (t10)-[:INICIA_EN]->(me),
  (t10)-[:PASA_POR]->(tes);

MATCH
  (me:Organismo {nombre: 'Mesa de Entradas'}),
  (hab:Organismo {nombre: 'Direccion de Habilitaciones'}),
  (ds:Organismo {nombre: 'Secretaria de Desarrollo Social'}),
  (op:Organismo {nombre: 'Secretaria de Obras Publicas'}),
  (tr:Organismo {nombre: 'Direccion de Transito'}),
  (tes:Organismo {nombre: 'Tesoreria Municipal'}),
  (ig:Organismo {nombre: 'Inspeccion General'}),
  (amb:Organismo {nombre: 'Direccion Ambiental'})
CREATE
  (me)-[:DERIVA_A {condicion: 'tramite comercial'}]->(hab),
  (hab)-[:DERIVA_A {condicion: 'requiere inspeccion'}]->(ig),
  (me)-[:DERIVA_A {condicion: 'tramite social'}]->(ds),
  (ds)-[:DERIVA_A {condicion: 'aprobacion economica'}]->(tes),
  (me)-[:DERIVA_A {condicion: 'reclamo urbano'}]->(op),
  (me)-[:DERIVA_A {condicion: 'tramite de transito'}]->(tr),
  (me)-[:DERIVA_A {condicion: 'tramite ambiental'}]->(amb);

CREATE
  (tr1:Tramite {numero: 'TRA-001', estado: 'pendiente'}),
  (tr2:Tramite {numero: 'TRA-002', estado: 'en_revision'}),
  (tr3:Tramite {numero: 'TRA-003', estado: 'pendiente'});

MATCH
  (tt1:TipoTramite {nombre: 'Habilitacion comercial'}),
  (tt2:TipoTramite {nombre: 'Solicitud de beca'}),
  (tt3:TipoTramite {nombre: 'Reclamo de obra publica'}),
  (me2:Organismo {nombre: 'Mesa de Entradas'}),
  (hab2:Organismo {nombre: 'Direccion de Habilitaciones'}),
  (ds2:Organismo {nombre: 'Secretaria de Desarrollo Social'}),
  (op2:Organismo {nombre: 'Secretaria de Obras Publicas'}),
  (tr1:Tramite {numero: 'TRA-001'}),
  (tr2:Tramite {numero: 'TRA-002'}),
  (tr3:Tramite {numero: 'TRA-003'})
CREATE
  (tr1)-[:ES_DE_TIPO]->(tt1),
  (tr1)-[:ESTA_EN]->(me2),
  (tr1)-[:PASA_POR]->(hab2),
  (tr2)-[:ES_DE_TIPO]->(tt2),
  (tr2)-[:ESTA_EN]->(ds2),
  (tr3)-[:ES_DE_TIPO]->(tt3),
  (tr3)-[:ESTA_EN]->(op2);