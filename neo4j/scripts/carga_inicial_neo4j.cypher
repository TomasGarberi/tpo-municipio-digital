// ============================================================
// LIMPIEZA INICIAL
// ============================================================
MATCH (n)
DETACH DELETE n;

// ============================================================
// CONSTRAINTS E INDICES
// ============================================================
CREATE CONSTRAINT ciudadano_dni IF NOT EXISTS
  FOR (c:Ciudadano) REQUIRE c.dni IS UNIQUE;

CREATE CONSTRAINT organismo_nombre IF NOT EXISTS
  FOR (o:Organismo) REQUIRE o.nombre IS UNIQUE;

CREATE CONSTRAINT tramite_numero IF NOT EXISTS
  FOR (t:Tramite) REQUIRE t.numero IS UNIQUE;

CREATE INDEX tipo_tramite_nombre IF NOT EXISTS
  FOR (tt:TipoTramite) ON (tt.nombre);

// ============================================================
// ORGANISMOS
// ============================================================
CREATE
  (me:Organismo  {nombre: 'Mesa de Entradas',               area: 'Administracion General', responsable: 'Laura Martinez',   sla_dias: 2}),
  (hab:Organismo {nombre: 'Direccion de Habilitaciones',     area: 'Produccion y Comercio',  responsable: 'Carlos Ramirez',   sla_dias: 5}),
  (ds:Organismo  {nombre: 'Secretaria de Desarrollo Social', area: 'Desarrollo Humano',      responsable: 'Mariana Lopez',    sla_dias: 7}),
  (op:Organismo  {nombre: 'Secretaria de Obras Publicas',    area: 'Infraestructura',        responsable: 'Diego Suarez',     sla_dias: 6}),
  (tro:Organismo {nombre: 'Direccion de Transito',           area: 'Movilidad',              responsable: 'Sofia Benitez',    sla_dias: 4}),
  (tes:Organismo {nombre: 'Tesoreria Municipal',             area: 'Hacienda',               responsable: 'Fernando Castro',  sla_dias: 3}),
  (ig:Organismo  {nombre: 'Inspeccion General',              area: 'Control Urbano',         responsable: 'Patricia Molina',  sla_dias: 5}),
  (amb:Organismo {nombre: 'Direccion Ambiental',             area: 'Ambiente',               responsable: 'Gabriel Herrera',  sla_dias: 6});

// ============================================================
// TIPOS DE TRAMITE
// ============================================================
CREATE
  (tt1:TipoTramite  {nombre: 'Habilitacion comercial',  tiempo_estimado_dias: 20}),
  (tt2:TipoTramite  {nombre: 'Solicitud de beca',        tiempo_estimado_dias: 15}),
  (tt3:TipoTramite  {nombre: 'Reclamo de obra publica',  tiempo_estimado_dias: 12}),
  (tt4:TipoTramite  {nombre: 'Licencia de conducir',     tiempo_estimado_dias: 10}),
  (tt5:TipoTramite  {nombre: 'Renovacion de licencia',   tiempo_estimado_dias:  7}),
  (tt6:TipoTramite  {nombre: 'Subsidio habitacional',    tiempo_estimado_dias: 18}),
  (tt7:TipoTramite  {nombre: 'Permiso de obra menor',    tiempo_estimado_dias: 14}),
  (tt8:TipoTramite  {nombre: 'Permiso de evento',        tiempo_estimado_dias:  9}),
  (tt9:TipoTramite  {nombre: 'Denuncia ambiental',       tiempo_estimado_dias: 11}),
  (tt10:TipoTramite {nombre: 'Exencion impositiva',      tiempo_estimado_dias: 13});

// ============================================================
// FLUJO: TipoTramite → Organismos  (con orden en PASA_POR)
// ============================================================
MATCH
  (me:Organismo  {nombre: 'Mesa de Entradas'}),
  (hab:Organismo {nombre: 'Direccion de Habilitaciones'}),
  (ds:Organismo  {nombre: 'Secretaria de Desarrollo Social'}),
  (op:Organismo  {nombre: 'Secretaria de Obras Publicas'}),
  (tro:Organismo {nombre: 'Direccion de Transito'}),
  (tes:Organismo {nombre: 'Tesoreria Municipal'}),
  (ig:Organismo  {nombre: 'Inspeccion General'}),
  (amb:Organismo {nombre: 'Direccion Ambiental'}),
  (tt1:TipoTramite  {nombre: 'Habilitacion comercial'}),
  (tt2:TipoTramite  {nombre: 'Solicitud de beca'}),
  (tt3:TipoTramite  {nombre: 'Reclamo de obra publica'}),
  (tt4:TipoTramite  {nombre: 'Licencia de conducir'}),
  (tt5:TipoTramite  {nombre: 'Renovacion de licencia'}),
  (tt6:TipoTramite  {nombre: 'Subsidio habitacional'}),
  (tt7:TipoTramite  {nombre: 'Permiso de obra menor'}),
  (tt8:TipoTramite  {nombre: 'Permiso de evento'}),
  (tt9:TipoTramite  {nombre: 'Denuncia ambiental'}),
  (tt10:TipoTramite {nombre: 'Exencion impositiva'})
CREATE
  (tt1)-[:INICIA_EN]->(me),  (tt1)-[:PASA_POR {orden: 2}]->(hab), (tt1)-[:PASA_POR {orden: 3}]->(ig),
  (tt2)-[:INICIA_EN]->(me),  (tt2)-[:PASA_POR {orden: 2}]->(ds),  (tt2)-[:PASA_POR {orden: 3}]->(tes),
  (tt3)-[:INICIA_EN]->(me),  (tt3)-[:PASA_POR {orden: 2}]->(op),
  (tt4)-[:INICIA_EN]->(me),  (tt4)-[:PASA_POR {orden: 2}]->(tro),
  (tt5)-[:INICIA_EN]->(me),  (tt5)-[:PASA_POR {orden: 2}]->(tro),
  (tt6)-[:INICIA_EN]->(me),  (tt6)-[:PASA_POR {orden: 2}]->(ds),
  (tt7)-[:INICIA_EN]->(me),  (tt7)-[:PASA_POR {orden: 2}]->(op),
  (tt8)-[:INICIA_EN]->(me),  (tt8)-[:PASA_POR {orden: 2}]->(ig),
  (tt9)-[:INICIA_EN]->(me),  (tt9)-[:PASA_POR {orden: 2}]->(amb),
  (tt10)-[:INICIA_EN]->(me), (tt10)-[:PASA_POR {orden: 2}]->(tes);

// ============================================================
// DERIVACIONES ENTRE ORGANISMOS
// ============================================================
MATCH
  (me:Organismo  {nombre: 'Mesa de Entradas'}),
  (hab:Organismo {nombre: 'Direccion de Habilitaciones'}),
  (ds:Organismo  {nombre: 'Secretaria de Desarrollo Social'}),
  (op:Organismo  {nombre: 'Secretaria de Obras Publicas'}),
  (tro:Organismo {nombre: 'Direccion de Transito'}),
  (tes:Organismo {nombre: 'Tesoreria Municipal'}),
  (ig:Organismo  {nombre: 'Inspeccion General'}),
  (amb:Organismo {nombre: 'Direccion Ambiental'})
CREATE
  (me)-[:DERIVA_A  {condicion: 'tramite comercial'}]->(hab),
  (hab)-[:DERIVA_A {condicion: 'requiere inspeccion'}]->(ig),
  (me)-[:DERIVA_A  {condicion: 'tramite social'}]->(ds),
  (ds)-[:DERIVA_A  {condicion: 'aprobacion economica'}]->(tes),
  (me)-[:DERIVA_A  {condicion: 'reclamo urbano'}]->(op),
  (me)-[:DERIVA_A  {condicion: 'tramite de transito'}]->(tro),
  (me)-[:DERIVA_A  {condicion: 'tramite impositivo'}]->(tes),
  (me)-[:DERIVA_A  {condicion: 'tramite ambiental'}]->(amb);

// ============================================================
// CIUDADANOS (subset representativo — mismos DNI que MongoDB)
// ============================================================
CREATE
  (c1:Ciudadano  {dni: '30000001', nombre: 'Juan',      apellido: 'Perez',     ciudad: 'Municipio Central'}),
  (c2:Ciudadano  {dni: '30000002', nombre: 'Maria',     apellido: 'Gomez',     ciudad: 'Municipio Norte'}),
  (c3:Ciudadano  {dni: '30000003', nombre: 'Lucas',     apellido: 'Fernandez', ciudad: 'Municipio Sur'}),
  (c4:Ciudadano  {dni: '30000004', nombre: 'Sofia',     apellido: 'Lopez',     ciudad: 'Municipio Oeste'}),
  (c5:Ciudadano  {dni: '30000005', nombre: 'Pedro',     apellido: 'Garcia',    ciudad: 'Municipio Central'}),
  (c6:Ciudadano  {dni: '30000006', nombre: 'Lucia',     apellido: 'Martinez',  ciudad: 'Municipio Norte'}),
  (c7:Ciudadano  {dni: '30000007', nombre: 'Martin',    apellido: 'Suarez',    ciudad: 'Municipio Sur'}),
  (c8:Ciudadano  {dni: '30000008', nombre: 'Camila',    apellido: 'Romero',    ciudad: 'Municipio Oeste'}),
  (c9:Ciudadano  {dni: '30000009', nombre: 'Tomas',     apellido: 'Diaz',      ciudad: 'Municipio Central'}),
  (c10:Ciudadano {dni: '30000010', nombre: 'Valentina', apellido: 'Castro',    ciudad: 'Municipio Norte'});

// ============================================================
// TRAMITES (25 representativos — mismos numeros que MongoDB)
// ============================================================
CREATE
  (tr01:Tramite {numero: 'TRA-2026-000001', estado: 'pendiente',   fecha_inicio: date('2026-03-02')}),
  (tr02:Tramite {numero: 'TRA-2026-000002', estado: 'en_revision', fecha_inicio: date('2026-03-03')}),
  (tr03:Tramite {numero: 'TRA-2026-000003', estado: 'resuelto',    fecha_inicio: date('2026-03-04')}),
  (tr04:Tramite {numero: 'TRA-2026-000004', estado: 'pendiente',   fecha_inicio: date('2026-03-05')}),
  (tr05:Tramite {numero: 'TRA-2026-000005', estado: 'en_revision', fecha_inicio: date('2026-03-06')}),
  (tr06:Tramite {numero: 'TRA-2026-000006', estado: 'resuelto',    fecha_inicio: date('2026-03-07')}),
  (tr07:Tramite {numero: 'TRA-2026-000007', estado: 'pendiente',   fecha_inicio: date('2026-03-08')}),
  (tr08:Tramite {numero: 'TRA-2026-000008', estado: 'en_revision', fecha_inicio: date('2026-03-09')}),
  (tr09:Tramite {numero: 'TRA-2026-000009', estado: 'resuelto',    fecha_inicio: date('2026-03-10')}),
  (tr10:Tramite {numero: 'TRA-2026-000010', estado: 'pendiente',   fecha_inicio: date('2026-03-11')}),
  (tr11:Tramite {numero: 'TRA-2026-000011', estado: 'en_revision', fecha_inicio: date('2026-03-12')}),
  (tr12:Tramite {numero: 'TRA-2026-000012', estado: 'resuelto',    fecha_inicio: date('2026-03-13')}),
  (tr13:Tramite {numero: 'TRA-2026-000013', estado: 'pendiente',   fecha_inicio: date('2026-03-14')}),
  (tr14:Tramite {numero: 'TRA-2026-000014', estado: 'en_revision', fecha_inicio: date('2026-03-15')}),
  (tr15:Tramite {numero: 'TRA-2026-000015', estado: 'resuelto',    fecha_inicio: date('2026-03-16')}),
  (tr16:Tramite {numero: 'TRA-2026-000016', estado: 'pendiente',   fecha_inicio: date('2026-03-17')}),
  (tr17:Tramite {numero: 'TRA-2026-000017', estado: 'en_revision', fecha_inicio: date('2026-03-18')}),
  (tr18:Tramite {numero: 'TRA-2026-000018', estado: 'resuelto',    fecha_inicio: date('2026-03-19')}),
  (tr19:Tramite {numero: 'TRA-2026-000019', estado: 'pendiente',   fecha_inicio: date('2026-03-20')}),
  (tr20:Tramite {numero: 'TRA-2026-000020', estado: 'en_revision', fecha_inicio: date('2026-03-21')}),
  (tr21:Tramite {numero: 'TRA-2026-000021', estado: 'resuelto',    fecha_inicio: date('2026-03-22')}),
  (tr22:Tramite {numero: 'TRA-2026-000022', estado: 'pendiente',   fecha_inicio: date('2026-03-23')}),
  (tr23:Tramite {numero: 'TRA-2026-000023', estado: 'en_revision', fecha_inicio: date('2026-03-24')}),
  (tr24:Tramite {numero: 'TRA-2026-000024', estado: 'resuelto',    fecha_inicio: date('2026-03-25')}),
  (tr25:Tramite {numero: 'TRA-2026-000025', estado: 'pendiente',   fecha_inicio: date('2026-03-26')});

// ============================================================
// Ciudadano -[:INICIO]-> Tramite
// ============================================================
MATCH
  (c1:Ciudadano {dni:'30000001'}),   (c2:Ciudadano {dni:'30000002'}),
  (c3:Ciudadano {dni:'30000003'}),   (c4:Ciudadano {dni:'30000004'}),
  (c5:Ciudadano {dni:'30000005'}),   (c6:Ciudadano {dni:'30000006'}),
  (c7:Ciudadano {dni:'30000007'}),   (c8:Ciudadano {dni:'30000008'}),
  (c9:Ciudadano {dni:'30000009'}),   (c10:Ciudadano{dni:'30000010'}),
  (tr01:Tramite {numero:'TRA-2026-000001'}),(tr02:Tramite {numero:'TRA-2026-000002'}),
  (tr03:Tramite {numero:'TRA-2026-000003'}),(tr04:Tramite {numero:'TRA-2026-000004'}),
  (tr05:Tramite {numero:'TRA-2026-000005'}),(tr06:Tramite {numero:'TRA-2026-000006'}),
  (tr07:Tramite {numero:'TRA-2026-000007'}),(tr08:Tramite {numero:'TRA-2026-000008'}),
  (tr09:Tramite {numero:'TRA-2026-000009'}),(tr10:Tramite {numero:'TRA-2026-000010'}),
  (tr11:Tramite {numero:'TRA-2026-000011'}),(tr12:Tramite {numero:'TRA-2026-000012'}),
  (tr13:Tramite {numero:'TRA-2026-000013'}),(tr14:Tramite {numero:'TRA-2026-000014'}),
  (tr15:Tramite {numero:'TRA-2026-000015'}),(tr16:Tramite {numero:'TRA-2026-000016'}),
  (tr17:Tramite {numero:'TRA-2026-000017'}),(tr18:Tramite {numero:'TRA-2026-000018'}),
  (tr19:Tramite {numero:'TRA-2026-000019'}),(tr20:Tramite {numero:'TRA-2026-000020'}),
  (tr21:Tramite {numero:'TRA-2026-000021'}),(tr22:Tramite {numero:'TRA-2026-000022'}),
  (tr23:Tramite {numero:'TRA-2026-000023'}),(tr24:Tramite {numero:'TRA-2026-000024'}),
  (tr25:Tramite {numero:'TRA-2026-000025'})
CREATE
  (c1)-[:INICIO]->(tr01),  (c2)-[:INICIO]->(tr02),  (c3)-[:INICIO]->(tr03),
  (c4)-[:INICIO]->(tr04),  (c5)-[:INICIO]->(tr05),  (c6)-[:INICIO]->(tr06),
  (c7)-[:INICIO]->(tr07),  (c8)-[:INICIO]->(tr08),  (c9)-[:INICIO]->(tr09),
  (c10)-[:INICIO]->(tr10), (c1)-[:INICIO]->(tr11),  (c2)-[:INICIO]->(tr12),
  (c3)-[:INICIO]->(tr13),  (c4)-[:INICIO]->(tr14),  (c5)-[:INICIO]->(tr15),
  (c6)-[:INICIO]->(tr16),  (c7)-[:INICIO]->(tr17),  (c8)-[:INICIO]->(tr18),
  (c9)-[:INICIO]->(tr19),  (c10)-[:INICIO]->(tr20), (c1)-[:INICIO]->(tr21),
  (c2)-[:INICIO]->(tr22),  (c3)-[:INICIO]->(tr23),  (c4)-[:INICIO]->(tr24),
  (c5)-[:INICIO]->(tr25);

// ============================================================
// Tramite -[:ES_DE_TIPO]-> TipoTramite
// ============================================================
MATCH
  (tt1:TipoTramite  {nombre:'Habilitacion comercial'}),
  (tt2:TipoTramite  {nombre:'Solicitud de beca'}),
  (tt3:TipoTramite  {nombre:'Reclamo de obra publica'}),
  (tt4:TipoTramite  {nombre:'Licencia de conducir'}),
  (tt5:TipoTramite  {nombre:'Renovacion de licencia'}),
  (tt6:TipoTramite  {nombre:'Subsidio habitacional'}),
  (tt7:TipoTramite  {nombre:'Permiso de obra menor'}),
  (tt8:TipoTramite  {nombre:'Permiso de evento'}),
  (tt9:TipoTramite  {nombre:'Denuncia ambiental'}),
  (tt10:TipoTramite {nombre:'Exencion impositiva'}),
  (tr01:Tramite {numero:'TRA-2026-000001'}),(tr02:Tramite {numero:'TRA-2026-000002'}),
  (tr03:Tramite {numero:'TRA-2026-000003'}),(tr04:Tramite {numero:'TRA-2026-000004'}),
  (tr05:Tramite {numero:'TRA-2026-000005'}),(tr06:Tramite {numero:'TRA-2026-000006'}),
  (tr07:Tramite {numero:'TRA-2026-000007'}),(tr08:Tramite {numero:'TRA-2026-000008'}),
  (tr09:Tramite {numero:'TRA-2026-000009'}),(tr10:Tramite {numero:'TRA-2026-000010'}),
  (tr11:Tramite {numero:'TRA-2026-000011'}),(tr12:Tramite {numero:'TRA-2026-000012'}),
  (tr13:Tramite {numero:'TRA-2026-000013'}),(tr14:Tramite {numero:'TRA-2026-000014'}),
  (tr15:Tramite {numero:'TRA-2026-000015'}),(tr16:Tramite {numero:'TRA-2026-000016'}),
  (tr17:Tramite {numero:'TRA-2026-000017'}),(tr18:Tramite {numero:'TRA-2026-000018'}),
  (tr19:Tramite {numero:'TRA-2026-000019'}),(tr20:Tramite {numero:'TRA-2026-000020'}),
  (tr21:Tramite {numero:'TRA-2026-000021'}),(tr22:Tramite {numero:'TRA-2026-000022'}),
  (tr23:Tramite {numero:'TRA-2026-000023'}),(tr24:Tramite {numero:'TRA-2026-000024'}),
  (tr25:Tramite {numero:'TRA-2026-000025'})
CREATE
  (tr01)-[:ES_DE_TIPO]->(tt1),  (tr02)-[:ES_DE_TIPO]->(tt2),
  (tr03)-[:ES_DE_TIPO]->(tt3),  (tr04)-[:ES_DE_TIPO]->(tt4),
  (tr05)-[:ES_DE_TIPO]->(tt5),  (tr06)-[:ES_DE_TIPO]->(tt6),
  (tr07)-[:ES_DE_TIPO]->(tt7),  (tr08)-[:ES_DE_TIPO]->(tt8),
  (tr09)-[:ES_DE_TIPO]->(tt9),  (tr10)-[:ES_DE_TIPO]->(tt10),
  (tr11)-[:ES_DE_TIPO]->(tt1),  (tr12)-[:ES_DE_TIPO]->(tt2),
  (tr13)-[:ES_DE_TIPO]->(tt3),  (tr14)-[:ES_DE_TIPO]->(tt4),
  (tr15)-[:ES_DE_TIPO]->(tt5),  (tr16)-[:ES_DE_TIPO]->(tt6),
  (tr17)-[:ES_DE_TIPO]->(tt7),  (tr18)-[:ES_DE_TIPO]->(tt8),
  (tr19)-[:ES_DE_TIPO]->(tt9),  (tr20)-[:ES_DE_TIPO]->(tt10),
  (tr21)-[:ES_DE_TIPO]->(tt1),  (tr22)-[:ES_DE_TIPO]->(tt2),
  (tr23)-[:ES_DE_TIPO]->(tt3),  (tr24)-[:ES_DE_TIPO]->(tt4),
  (tr25)-[:ES_DE_TIPO]->(tt5);

// ============================================================
// Tramite -[:ESTA_EN]-> Organismo  (organismo actual del tram.)
// ============================================================
MATCH
  (me:Organismo  {nombre:'Mesa de Entradas'}),
  (hab:Organismo {nombre:'Direccion de Habilitaciones'}),
  (ds:Organismo  {nombre:'Secretaria de Desarrollo Social'}),
  (op:Organismo  {nombre:'Secretaria de Obras Publicas'}),
  (tro:Organismo {nombre:'Direccion de Transito'}),
  (tes:Organismo {nombre:'Tesoreria Municipal'}),
  (ig:Organismo  {nombre:'Inspeccion General'}),
  (amb:Organismo {nombre:'Direccion Ambiental'}),
  (tr01:Tramite {numero:'TRA-2026-000001'}),(tr02:Tramite {numero:'TRA-2026-000002'}),
  (tr03:Tramite {numero:'TRA-2026-000003'}),(tr04:Tramite {numero:'TRA-2026-000004'}),
  (tr05:Tramite {numero:'TRA-2026-000005'}),(tr06:Tramite {numero:'TRA-2026-000006'}),
  (tr07:Tramite {numero:'TRA-2026-000007'}),(tr08:Tramite {numero:'TRA-2026-000008'}),
  (tr09:Tramite {numero:'TRA-2026-000009'}),(tr10:Tramite {numero:'TRA-2026-000010'}),
  (tr11:Tramite {numero:'TRA-2026-000011'}),(tr12:Tramite {numero:'TRA-2026-000012'}),
  (tr13:Tramite {numero:'TRA-2026-000013'}),(tr14:Tramite {numero:'TRA-2026-000014'}),
  (tr15:Tramite {numero:'TRA-2026-000015'}),(tr16:Tramite {numero:'TRA-2026-000016'}),
  (tr17:Tramite {numero:'TRA-2026-000017'}),(tr18:Tramite {numero:'TRA-2026-000018'}),
  (tr19:Tramite {numero:'TRA-2026-000019'}),(tr20:Tramite {numero:'TRA-2026-000020'}),
  (tr21:Tramite {numero:'TRA-2026-000021'}),(tr22:Tramite {numero:'TRA-2026-000022'}),
  (tr23:Tramite {numero:'TRA-2026-000023'}),(tr24:Tramite {numero:'TRA-2026-000024'}),
  (tr25:Tramite {numero:'TRA-2026-000025'})
CREATE
  (tr01)-[:ESTA_EN]->(hab),  (tr02)-[:ESTA_EN]->(ds),
  (tr03)-[:ESTA_EN]->(op),   (tr04)-[:ESTA_EN]->(tro),
  (tr05)-[:ESTA_EN]->(tro),  (tr06)-[:ESTA_EN]->(ds),
  (tr07)-[:ESTA_EN]->(op),   (tr08)-[:ESTA_EN]->(ig),
  (tr09)-[:ESTA_EN]->(amb),  (tr10)-[:ESTA_EN]->(tes),
  (tr11)-[:ESTA_EN]->(ig),   (tr12)-[:ESTA_EN]->(tes),
  (tr13)-[:ESTA_EN]->(me),   (tr14)-[:ESTA_EN]->(me),
  (tr15)-[:ESTA_EN]->(tro),  (tr16)-[:ESTA_EN]->(ds),
  (tr17)-[:ESTA_EN]->(op),   (tr18)-[:ESTA_EN]->(ig),
  (tr19)-[:ESTA_EN]->(amb),  (tr20)-[:ESTA_EN]->(tes),
  (tr21)-[:ESTA_EN]->(hab),  (tr22)-[:ESTA_EN]->(ds),
  (tr23)-[:ESTA_EN]->(op),   (tr24)-[:ESTA_EN]->(tro),
  (tr25)-[:ESTA_EN]->(me);

// ============================================================
// Tramite -[:DEPENDE_DE]-> Tramite
// Un tramite de habilitacion comercial puede depender de
// una inspeccion ambiental o permiso de obras previos.
// Una beca puede depender de una exencion impositiva vigente.
// ============================================================
MATCH
  (tr01:Tramite {numero:'TRA-2026-000001'}),
  (tr07:Tramite {numero:'TRA-2026-000007'}),
  (tr09:Tramite {numero:'TRA-2026-000009'}),
  (tr08:Tramite {numero:'TRA-2026-000008'}),
  (tr11:Tramite {numero:'TRA-2026-000011'}),
  (tr02:Tramite {numero:'TRA-2026-000002'}),
  (tr10:Tramite {numero:'TRA-2026-000010'}),
  (tr17:Tramite {numero:'TRA-2026-000017'}),
  (tr19:Tramite {numero:'TRA-2026-000019'}),
  (tr21:Tramite {numero:'TRA-2026-000021'})
CREATE
  (tr01)-[:DEPENDE_DE {motivo: 'requiere inspeccion ambiental previa'}]->(tr09),
  (tr01)-[:DEPENDE_DE {motivo: 'requiere permiso de obra menor'}]->(tr07),
  (tr11)-[:DEPENDE_DE {motivo: 'requiere inspeccion general aprobada'}]->(tr08),
  (tr02)-[:DEPENDE_DE {motivo: 'requiere exencion impositiva vigente'}]->(tr10),
  (tr21)-[:DEPENDE_DE {motivo: 'requiere permiso de obra menor'}]->(tr17),
  (tr21)-[:DEPENDE_DE {motivo: 'requiere inspeccion ambiental'}]->(tr19);