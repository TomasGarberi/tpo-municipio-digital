use("municipio_digital")

// ============================================================
// CONSULTAS MONGODB — TPO Municipio Digital
// ============================================================

// --- C1: Tramites agrupados por estado ----------------------
// Cuantos tramites hay en cada estado (pendiente/en_revision/resuelto).
print("=== C1: Tramites por estado ===")
db.tramites.aggregate([
  { $group: { _id: "$estado_actual", total: { $sum: 1 } } },
  { $sort: { total: -1 } }
]).forEach(printjson)

// --- C2: Tramites de un ciudadano especifico ----------------
// Todos los tramites iniciados por un ciudadano dado su DNI.
print("\n=== C2: Tramites del ciudadano DNI 30000001 ===")
db.tramites.find(
  { ciudadano_dni: "30000001" },
  { numero_tramite: 1, tipo_tramite: 1, estado_actual: 1, fecha_inicio: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).forEach(printjson)

// --- C3: Carga activa por organismo -------------------------
// Cuantos tramites pendientes o en revision tiene cada organismo.
print("\n=== C3: Carga activa por organismo ===")
db.tramites.aggregate([
  { $match: { estado_actual: { $in: ["pendiente", "en_revision"] } } },
  { $group: { _id: "$organismo_actual", tramites_activos: { $sum: 1 } } },
  { $sort: { tramites_activos: -1 } }
]).forEach(printjson)

// --- C4: Tramites con fecha estimada de resolucion vencida --
// Tramites que no fueron resueltos y ya superaron su fecha estimada.
print("\n=== C4: Tramites con SLA vencido ===")
db.tramites.find(
  {
    estado_actual: { $ne: "resuelto" },
    fecha_estimada_resolucion: { $lt: new Date() }
  },
  { numero_tramite: 1, tipo_tramite: 1, organismo_actual: 1,
    estado_actual: 1, fecha_estimada_resolucion: 1, _id: 0 }
).sort({ fecha_estimada_resolucion: 1 }).forEach(printjson)

// --- C5: Historial de eventos de un tramite -----------------
// Muestra todos los eventos embebidos de un tramite especifico.
print("\n=== C5: Historial de eventos del tramite TRA-2026-000001 ===")
db.tramites.find(
  { numero_tramite: "TRA-2026-000001" },
  { numero_tramite: 1, tipo_tramite: 1, estado_actual: 1, eventos: 1, _id: 0 }
).forEach(printjson)

// --- C6: Documentos pendientes de validacion ----------------
// Documentos que todavia no fueron validados, con su organismo validador.
print("\n=== C6: Documentos pendientes de validacion ===")
db.documentos.find(
  { estado_validacion: "pendiente" },
  { tramite_numero: 1, tipo: 1, nombre_archivo: 1, organismo_validador: 1, _id: 0 }
).sort({ tramite_numero: 1 }).forEach(printjson)

// --- C7: Tipos de tramite mas solicitados -------------------
// Ranking de tipos de tramite por cantidad de tramites iniciados.
print("\n=== C7: Tipos de tramite mas solicitados ===")
db.tramites.aggregate([
  { $group: { _id: "$tipo_tramite", cantidad: { $sum: 1 } } },
  { $sort: { cantidad: -1 } }
]).forEach(printjson)

// --- C8: Ciudadanos con mas tramites iniciados --------------
print("\n=== C8: Ciudadanos con mas tramites (top 5) ===")
db.tramites.aggregate([
  { $group: { _id: "$ciudadano_dni", total: { $sum: 1 } } },
  { $sort: { total: -1 } },
  { $limit: 5 },
  {
    $lookup: {
      from: "ciudadanos",
      localField: "_id",
      foreignField: "dni",
      as: "datos_ciudadano"
    }
  },
  {
    $project: {
      _id: 0,
      dni: "$_id",
      total_tramites: "$total",
      nombre: { $arrayElemAt: ["$datos_ciudadano.nombre", 0] },
      apellido: { $arrayElemAt: ["$datos_ciudadano.apellido", 0] }
    }
  }
]).forEach(printjson)

// --- C9: Tramites resueltos con tiempo real de resolucion ---
// Solo tramites resueltos: diferencia entre fecha inicio y estimada.
print("\n=== C9: Tramites resueltos — tiempo de resolucion (dias) ===")
db.tramites.aggregate([
  { $match: { estado_actual: "resuelto" } },
  {
    $project: {
      numero_tramite: 1,
      tipo_tramite: 1,
      organismo_actual: 1,
      dias_resolucion: {
        $divide: [
          { $subtract: ["$fecha_estimada_resolucion", "$fecha_inicio"] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  },
  { $sort: { dias_resolucion: -1 } },
  { $limit: 10 }
]).forEach(printjson)

// --- C10: Organismos y sus SLA configurados -----------------
print("\n=== C10: SLA configurado por organismo ===")
db.organismos.find(
  {},
  { nombre: 1, area_gobierno: 1, sla_dias_habiles_por_etapa: 1, _id: 0 }
).sort({ sla_dias_habiles_por_etapa: 1 }).forEach(printjson)

print("\nConsultas finalizadas.")