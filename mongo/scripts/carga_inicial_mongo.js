use("municipio_digital")

db.ciudadanos.deleteMany({})
db.organismos.deleteMany({})
db.tipos_tramite.deleteMany({})
db.tramites.deleteMany({})
db.documentos.deleteMany({})

// ======================
// ORGANISMOS
// ======================

const organismos = [
  {
    nombre: "Mesa de Entradas",
    area_gobierno: "Administracion General",
    responsable: "Laura Martinez",
    tramites_que_procesa: [
      "Habilitacion comercial",
      "Solicitud de beca",
      "Reclamo de obra publica",
      "Licencia de conducir",
      "Subsidio habitacional"
    ],
    sla_dias_habiles_por_etapa: 2
  },
  {
    nombre: "Direccion de Habilitaciones",
    area_gobierno: "Produccion y Comercio",
    responsable: "Carlos Ramirez",
    tramites_que_procesa: [
      "Habilitacion comercial",
      "Renovacion de habilitacion"
    ],
    sla_dias_habiles_por_etapa: 5
  },
  {
    nombre: "Secretaria de Desarrollo Social",
    area_gobierno: "Desarrollo Humano",
    responsable: "Mariana Lopez",
    tramites_que_procesa: [
      "Solicitud de beca",
      "Subsidio habitacional",
      "Asistencia alimentaria"
    ],
    sla_dias_habiles_por_etapa: 7
  },
  {
    nombre: "Secretaria de Obras Publicas",
    area_gobierno: "Infraestructura",
    responsable: "Diego Suarez",
    tramites_que_procesa: [
      "Reclamo de obra publica",
      "Permiso de obra menor"
    ],
    sla_dias_habiles_por_etapa: 6
  },
  {
    nombre: "Direccion de Transito",
    area_gobierno: "Movilidad",
    responsable: "Sofia Benitez",
    tramites_que_procesa: [
      "Licencia de conducir",
      "Renovacion de licencia"
    ],
    sla_dias_habiles_por_etapa: 4
  },
  {
    nombre: "Tesoreria Municipal",
    area_gobierno: "Hacienda",
    responsable: "Fernando Castro",
    tramites_que_procesa: [
      "Solicitud de beca",
      "Exencion impositiva"
    ],
    sla_dias_habiles_por_etapa: 3
  },
  {
    nombre: "Inspeccion General",
    area_gobierno: "Control Urbano",
    responsable: "Patricia Molina",
    tramites_que_procesa: [
      "Habilitacion comercial",
      "Permiso de evento"
    ],
    sla_dias_habiles_por_etapa: 5
  },
  {
    nombre: "Direccion Ambiental",
    area_gobierno: "Ambiente",
    responsable: "Gabriel Herrera",
    tramites_que_procesa: [
      "Denuncia ambiental",
      "Poda de arboles"
    ],
    sla_dias_habiles_por_etapa: 6
  }
]

db.organismos.insertMany(organismos)

// ======================
// TIPOS DE TRAMITE
// ======================

const tiposTramite = [
  {
    nombre: "Habilitacion comercial",
    descripcion: "Solicitud para obtener la habilitacion municipal de un comercio.",
    organismos_involucrados: ["Mesa de Entradas", "Direccion de Habilitaciones", "Inspeccion General"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Revision documental" },
      { orden: 3, nombre: "Inspeccion" },
      { orden: 4, nombre: "Resolucion" }
    ],
    documentacion_requerida: ["DNI", "Constancia de CUIL", "Plano del local", "Constancia de AFIP"],
    tiempo_estimado_resolucion_dias: 20
  },
  {
    nombre: "Solicitud de beca",
    descripcion: "Solicitud de asistencia economica para estudios.",
    organismos_involucrados: ["Mesa de Entradas", "Secretaria de Desarrollo Social", "Tesoreria Municipal"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Evaluacion socioeconomica" },
      { orden: 3, nombre: "Aprobacion" },
      { orden: 4, nombre: "Notificacion" }
    ],
    documentacion_requerida: ["DNI", "Constancia de alumno regular", "Recibo de ingresos del grupo familiar"],
    tiempo_estimado_resolucion_dias: 15
  },
  {
    nombre: "Reclamo de obra publica",
    descripcion: "Reclamo ciudadano vinculado a infraestructura publica.",
    organismos_involucrados: ["Mesa de Entradas", "Secretaria de Obras Publicas"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Evaluacion tecnica" },
      { orden: 3, nombre: "Resolucion" }
    ],
    documentacion_requerida: ["DNI", "Descripcion del problema", "Ubicacion", "Fotografia"],
    tiempo_estimado_resolucion_dias: 12
  },
  {
    nombre: "Licencia de conducir",
    descripcion: "Solicitud de emision de licencia de conducir.",
    organismos_involucrados: ["Mesa de Entradas", "Direccion de Transito"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Validacion documental" },
      { orden: 3, nombre: "Examen" },
      { orden: 4, nombre: "Emision" }
    ],
    documentacion_requerida: ["DNI", "Apto medico", "Comprobante de domicilio"],
    tiempo_estimado_resolucion_dias: 10
  },
  {
    nombre: "Renovacion de licencia",
    descripcion: "Solicitud de renovacion de licencia de conducir.",
    organismos_involucrados: ["Mesa de Entradas", "Direccion de Transito"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Validacion documental" },
      { orden: 3, nombre: "Emision" }
    ],
    documentacion_requerida: ["DNI", "Licencia anterior", "Apto medico"],
    tiempo_estimado_resolucion_dias: 7
  },
  {
    nombre: "Subsidio habitacional",
    descripcion: "Solicitud de asistencia para vivienda.",
    organismos_involucrados: ["Mesa de Entradas", "Secretaria de Desarrollo Social"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Evaluacion social" },
      { orden: 3, nombre: "Resolucion" }
    ],
    documentacion_requerida: ["DNI", "Informe socioeconomico", "Constancia de residencia"],
    tiempo_estimado_resolucion_dias: 18
  },
  {
    nombre: "Permiso de obra menor",
    descripcion: "Solicitud de permiso para obra menor domiciliaria.",
    organismos_involucrados: ["Mesa de Entradas", "Secretaria de Obras Publicas"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Revision tecnica" },
      { orden: 3, nombre: "Aprobacion" }
    ],
    documentacion_requerida: ["DNI", "Plano", "Descripcion de obra"],
    tiempo_estimado_resolucion_dias: 14
  },
  {
    nombre: "Permiso de evento",
    descripcion: "Solicitud de autorizacion para evento en espacio publico.",
    organismos_involucrados: ["Mesa de Entradas", "Inspeccion General"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Revision" },
      { orden: 3, nombre: "Aprobacion" }
    ],
    documentacion_requerida: ["DNI", "Descripcion del evento", "Seguro"],
    tiempo_estimado_resolucion_dias: 9
  },
  {
    nombre: "Denuncia ambiental",
    descripcion: "Denuncia vinculada a contaminacion o daño ambiental.",
    organismos_involucrados: ["Mesa de Entradas", "Direccion Ambiental"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Inspeccion" },
      { orden: 3, nombre: "Resolucion" }
    ],
    documentacion_requerida: ["DNI", "Descripcion", "Ubicacion", "Prueba fotografica"],
    tiempo_estimado_resolucion_dias: 11
  },
  {
    nombre: "Exencion impositiva",
    descripcion: "Solicitud de exencion de tasas municipales.",
    organismos_involucrados: ["Mesa de Entradas", "Tesoreria Municipal"],
    etapas: [
      { orden: 1, nombre: "Recepcion" },
      { orden: 2, nombre: "Analisis" },
      { orden: 3, nombre: "Resolucion" }
    ],
    documentacion_requerida: ["DNI", "Comprobantes de ingresos", "Formulario de solicitud"],
    tiempo_estimado_resolucion_dias: 13
  }
]

db.tipos_tramite.insertMany(tiposTramite)

// ======================
// CIUDADANOS
// ======================

const nombres = ["Juan", "Maria", "Lucas", "Sofia", "Pedro", "Lucia", "Martin", "Camila", "Tomas", "Valentina"]
const apellidos = ["Perez", "Gomez", "Fernandez", "Lopez", "Garcia", "Martinez", "Suarez", "Romero", "Diaz", "Castro"]
const ciudades = ["Municipio Central", "Municipio Norte", "Municipio Sur", "Municipio Oeste"]

const ciudadanos = []

for (let i = 1; i <= 300; i++) {
  const dni = (30000000 + i).toString()
  ciudadanos.push({
    dni: dni,
    cuil: `20-${dni}-3`,
    nombre: nombres[i % nombres.length],
    apellido: apellidos[i % apellidos.length],
    domicilio: {
      calle: `Calle ${i}`,
      ciudad: ciudades[i % ciudades.length],
      codigo_postal: `${1000 + (i % 50)}`
    },
    email: `ciudadano${i}@mail.com`,
    telefono: `11${String(50000000 + i).slice(-8)}`
  })
}

db.ciudadanos.insertMany(ciudadanos)

// ======================
// TRAMITES
// ======================

const tipos = tiposTramite.map(t => t.nombre)
const estados = ["pendiente", "en_revision", "resuelto"]

const tramites = []

for (let i = 1; i <= 500; i++) {
  const tipo = tipos[i % tipos.length]
  const ciudadano = ciudadanos[i % ciudadanos.length]
  const organismo = tipo === "Habilitacion comercial"
    ? "Direccion de Habilitaciones"
    : tipo === "Solicitud de beca"
    ? "Secretaria de Desarrollo Social"
    : tipo === "Reclamo de obra publica"
    ? "Secretaria de Obras Publicas"
    : "Mesa de Entradas"

  const fechaInicio = new Date(2026, 2, (i % 28) + 1)
  const fechaEstimada = new Date(fechaInicio)
  fechaEstimada.setDate(fechaInicio.getDate() + ((i % 15) + 5))

  tramites.push({
    numero_tramite: `TRA-2026-${String(i).padStart(6, "0")}`,
    tipo_tramite: tipo,
    ciudadano_dni: ciudadano.dni,
    fecha_inicio: fechaInicio,
    estado_actual: estados[i % estados.length],
    organismo_actual: organismo,
    fecha_estimada_resolucion: fechaEstimada,
    datos_especificos: {
      referencia: `Dato especifico ${i}`,
      prioridad: i % 2 === 0 ? "media" : "alta"
    },
    eventos: [
      {
        timestamp: fechaInicio,
        tipo_evento: "recepcion",
        organismo: "Mesa de Entradas",
        agente: `agente_${String(i).padStart(3, "0")}`,
        detalle: "Tramite recibido"
      },
      {
        timestamp: new Date(fechaInicio.getTime() + 86400000),
        tipo_evento: "derivacion",
        organismo: "Mesa de Entradas",
        agente: `agente_${String(i + 1).padStart(3, "0")}`,
        detalle: `Derivado a ${organismo}`
      }
    ]
  })
}

db.tramites.insertMany(tramites)

// ======================
// DOCUMENTOS
// ======================

const documentos = []

for (let i = 1; i <= 100; i++) {
  documentos.push({
    tramite_numero: `TRA-2026-${String(i).padStart(6, "0")}`,
    tipo: i % 2 === 0 ? "DNI" : "Formulario",
    nombre_archivo: `documento_${i}.pdf`,
    fecha_carga: new Date(2026, 3, (i % 28) + 1),
    estado_validacion: i % 3 === 0 ? "pendiente" : "validado",
    organismo_validador: i % 2 === 0 ? "Mesa de Entradas" : "Direccion de Habilitaciones"
  })
}

db.documentos.insertMany(documentos)

// ======================
// INDICES
// ======================

db.tramites.createIndex({ numero_tramite: 1 }, { name: "idx_numero_tramite", unique: true })
db.tramites.createIndex({ ciudadano_dni: 1 }, { name: "idx_ciudadano_dni" })
db.tramites.createIndex({ estado_actual: 1, organismo_actual: 1 }, { name: "idx_estado_organismo" })

print("Carga inicial finalizada correctamente.")
print("Ciudadanos:", db.ciudadanos.countDocuments())
print("Organismos:", db.organismos.countDocuments())
print("Tipos de tramite:", db.tipos_tramite.countDocuments())
print("Tramites:", db.tramites.countDocuments())
print("Documentos:", db.documentos.countDocuments())