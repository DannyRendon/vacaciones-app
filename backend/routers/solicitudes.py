from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import obtener_db
from datetime import date
import models

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])

# Empleado crea una solicitud
@router.post("/")
def crear_solicitud(
    empleado_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    motivo: str,
    db: Session = Depends(obtener_db)
):
    # Calcular días solicitados
    dias = (fecha_fin - fecha_inicio).days + 1
    if dias <= 0:
        raise HTTPException(status_code=400, detail="La fecha fin debe ser mayor a la fecha inicio")

    empleado = db.query(models.Usuario).filter(models.Usuario.id == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    if dias > empleado.dias_disponibles:
        raise HTTPException(
            status_code=400,
            detail=f"No tienes suficientes días disponibles (te quedan {empleado.dias_disponibles})"
        )

    solicitud = models.Solicitud(
        empleado_id=empleado_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        motivo=motivo,
        dias_solicitados=dias,
        estado="pendiente_jefe"
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud

# Ver todas las solicitudes (jefe y rrhh)
@router.get("/")
def listar_solicitudes(db: Session = Depends(obtener_db)):
    return db.query(models.Solicitud).all()

# Ver solicitudes de un empleado
@router.get("/empleado/{empleado_id}")
def solicitudes_empleado(empleado_id: int, db: Session = Depends(obtener_db)):
    return db.query(models.Solicitud).filter(models.Solicitud.empleado_id == empleado_id).all()

# Jefe aprueba o rechaza
@router.put("/{solicitud_id}/jefe")
def decision_jefe(
    solicitud_id: int,
    decision: str,  # "aprobar" o "rechazar"
    comentario: str = "",
    db: Session = Depends(obtener_db)
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != "pendiente_jefe":
        raise HTTPException(status_code=400, detail="Esta solicitud ya fue procesada por el jefe")

    if decision == "aprobar":
        solicitud.estado = "pendiente_rrhh"
    elif decision == "rechazar":
        solicitud.estado = "rechazada_jefe"
    else:
        raise HTTPException(status_code=400, detail="Decisión inválida, use aprobar o rechazar")

    solicitud.comentario_jefe = comentario
    db.commit()
    db.refresh(solicitud)
    return solicitud

# RRHH confirma o rechaza
@router.put("/{solicitud_id}/rrhh")
def decision_rrhh(
    solicitud_id: int,
    decision: str,  # "confirmar" o "rechazar"
    comentario: str = "",
    db: Session = Depends(obtener_db)
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != "pendiente_rrhh":
        raise HTTPException(status_code=400, detail="Esta solicitud no está pendiente de RRHH")

    if decision == "confirmar":
        # Se revalida el saldo aquí (no solo al crear la solicitud), porque puede
        # haber cambiado si RRHH ya confirmó otras solicitudes del mismo empleado.
        empleado = db.query(models.Usuario).filter(models.Usuario.id == solicitud.empleado_id).first()
        if solicitud.dias_solicitados > empleado.dias_disponibles:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente: el empleado solo tiene {empleado.dias_disponibles} días disponibles"
            )
        empleado.dias_disponibles -= solicitud.dias_solicitados
        solicitud.estado = "confirmada"
    elif decision == "rechazar":
        solicitud.estado = "rechazada_rrhh"
    else:
        raise HTTPException(status_code=400, detail="Decisión inválida, use confirmar o rechazar")

    solicitud.comentario_rrhh = comentario
    db.commit()
    db.refresh(solicitud)
    return solicitud