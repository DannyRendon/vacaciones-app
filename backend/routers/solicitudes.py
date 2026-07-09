from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import obtener_db
from datetime import date
from ia import resumir_solicitud_para_jefe, sugerir_comentario_rrhh
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
        raise HTTPException(status_code=400, detail="La fecha fin debe ser mayor o igual a la fecha inicio")

    empleado = db.query(models.Usuario).filter(models.Usuario.id == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    if dias > empleado.dias_disponibles:
        raise HTTPException(
            status_code=400,
            detail=f"No tienes suficientes días disponibles (te quedan {empleado.dias_disponibles})"
        )

    # Verificar que no se crucen fechas con solicitudes activas
    cruce = db.query(models.Solicitud).filter(
        models.Solicitud.empleado_id == empleado_id,
        models.Solicitud.estado.in_(["pendiente_jefe", "pendiente_rrhh", "confirmada"]),
        or_(
            and_(models.Solicitud.fecha_inicio <= fecha_inicio, models.Solicitud.fecha_fin >= fecha_inicio),
            and_(models.Solicitud.fecha_inicio <= fecha_fin, models.Solicitud.fecha_fin >= fecha_fin),
            and_(models.Solicitud.fecha_inicio >= fecha_inicio, models.Solicitud.fecha_fin <= fecha_fin)
        )
    ).first()

    if cruce:
        raise HTTPException(
            status_code=400,
            detail=f"Ya tienes una solicitud que cubre esas fechas (solicitud #{cruce.id})"
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

# Ver solicitudes del equipo de un jefe
@router.get("/jefe/{jefe_id}")
def solicitudes_del_equipo(jefe_id: int, db: Session = Depends(obtener_db)):
    return (
        db.query(models.Solicitud)
        .join(models.Usuario, models.Solicitud.empleado_id == models.Usuario.id)
        .filter(models.Usuario.jefe_id == jefe_id)
        .all()
    )

# Jefe aprueba o rechaza
@router.put("/{solicitud_id}/jefe")
def decision_jefe(
    solicitud_id: int,
    decision: str,
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
    decision: str,
    comentario: str = "",
    db: Session = Depends(obtener_db)
):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != "pendiente_rrhh":
        raise HTTPException(status_code=400, detail="Esta solicitud no está pendiente de RRHH")

    if decision == "confirmar":
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

# Resumen de IA para el jefe
@router.get("/{solicitud_id}/resumen-jefe")
def resumen_para_jefe(solicitud_id: int, db: Session = Depends(obtener_db)):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    empleado = db.query(models.Usuario).filter(models.Usuario.id == solicitud.empleado_id).first()
    
    # Contar solicitudes anteriores
    total = db.query(models.Solicitud).filter(
        models.Solicitud.empleado_id == solicitud.empleado_id
    ).count()
    
    resumen = resumir_solicitud_para_jefe(
        nombre_empleado=empleado.nombre,
        dias_solicitados=solicitud.dias_solicitados,
        fecha_inicio=str(solicitud.fecha_inicio),
        fecha_fin=str(solicitud.fecha_fin),
        motivo=solicitud.motivo,
        dias_disponibles=empleado.dias_disponibles,
        total_solicitudes=total
    )
    
    return {"resumen": resumen}

# Sugerencia de comentario para RRHH
@router.get("/{solicitud_id}/sugerencia-rrhh")
def sugerencia_para_rrhh(solicitud_id: int, decision: str, db: Session = Depends(obtener_db)):
    solicitud = db.query(models.Solicitud).filter(models.Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    empleado = db.query(models.Usuario).filter(models.Usuario.id == solicitud.empleado_id).first()
    
    sugerencia = sugerir_comentario_rrhh(
        nombre_empleado=empleado.nombre,
        dias_solicitados=solicitud.dias_solicitados,
        fecha_inicio=str(solicitud.fecha_inicio),
        fecha_fin=str(solicitud.fecha_fin),
        dias_disponibles=empleado.dias_disponibles,
        decision=decision
    )
    
    return {"sugerencia": sugerencia}