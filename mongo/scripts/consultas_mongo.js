use("municipio_digital")

// ============================================================
// CONSULTAS MONGODB — TPO Municipio Digital
// ============================================================


// ------------------------------------------------------------
// A) Historial completo de un trámite con eventos y documentos
// ------------------------------------------------------------
// Devuelve toda la información del trámite incluyendo eventos
// y documentación asociada.
db.tramites.find(
  { numero_tramite: "TRA-2026-000001" },
  {
    _id: 0
  }
).forEach(printjson);


// ------------------------------------------------------------
// B) Lista de trámites de un ciudadano
// ------------------------------------------------------------
// Incluye tipo, estado actual y fecha estimada de resolución.
db.tramites.find(
  { ciudadano_dni: "30000001" },
  {
    numero_tramite: 1,
    tipo_tramite: 1,
    estado_actual: 1,
    fecha_estimada_resolucion: 1,
    _id: 0
  }
).sort({ fecha_inicio: 1 }).forEach(printjson);


// ------------------------------------------------------------
// C) Trámites fuera de SLA en la etapa actual
// ------------------------------------------------------------
// Calcula cuánto tiempo lleva el trámite en su etapa actual
// y lo compara contra el SLA definido por el organismo.
db.tramites.aggregate([
  {
    $addFields: {
      ultimo_evento: { $arrayElemAt: ["$eventos", -1] }
    }
  },
  {
    $lookup: {
      from: "organismos",
      localField: "organismo_actual",
      foreignField: "nombre",
      as: "org"
    }
  },
  {
    $unwind: "$org"
  },
  {
    $project: {
      numero_tramite: 1,
      tipo_tramite: 1,
      organismo_actual: 1,
      estado_actual: 1,
      sla_dias: "$org.sla_dias_habiles_por_etapa",
      dias_en_etapa: {
        $divide: [
          { $subtract: [new Date(), "$ultimo_evento.timestamp"] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  },
  {
    $match: {
      $expr: {
        $gt: ["$dias_en_etapa", "$sla_dias"]
      }
    }
  },
  {
    $sort: { dias_en_etapa: -1 }
  }
]).forEach(printjson);


// ------------------------------------------------------------
// D) Cantidad de trámites iniciados por tipo en un período
// ------------------------------------------------------------
// Agrupa por tipo de trámite dentro de un rango de fechas.
db.tramites.aggregate([
  {
    $match: {
      fecha_inicio: {
        $gte: new Date("2026-03-01"),
        $lte: new Date("2026-03-31")
      }
    }
  },
  {
    $group: {
      _id: "$tipo_tramite",
      cantidad: { $sum: 1 }
    }
  },
  {
    $sort: { cantidad: -1 }
  }
]).forEach(printjson);


// ------------------------------------------------------------
// E) Tiempo promedio de resolución por tipo de trámite
// ------------------------------------------------------------
// Calcula el promedio en días para trámites finalizados.
db.tramites.aggregate([
  {
    $match: {
      estado_actual: "resuelto",
      fecha_estimada_resolucion: { $ne: null }
    }
  },
  {
    $project: {
      tipo_tramite: 1,
      dias_resolucion: {
        $divide: [
          { $subtract: ["$fecha_estimada_resolucion", "$fecha_inicio"] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  },
  {
    $group: {
      _id: "$tipo_tramite",
      promedio_dias: { $avg: "$dias_resolucion" }
    }
  },
  {
    $sort: { promedio_dias: -1 }
  }
]).forEach(printjson);
