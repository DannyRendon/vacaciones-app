from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import obtener_db
import models

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Obtener todos los usuarios
@router.get("/")
def listar_usuarios(db: Session = Depends(obtener_db)):
    usuarios = db.query(models.Usuario).all()
    return usuarios

# Crear un usuario nuevo
@router.post("/")
def crear_usuario(
    nombre: str,
    correo: str,
    rol: str,
    jefe_id: int = None,
    db: Session = Depends(obtener_db)
):
    existe = db.query(models.Usuario).filter(models.Usuario.correo == correo).first()
    if existe:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")

    nuevo = models.Usuario(nombre=nombre, correo=correo, rol=rol, jefe_id=jefe_id)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# Obtener un usuario por id
@router.get("/{usuario_id}")
def obtener_usuario(usuario_id: int, db: Session = Depends(obtener_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# Asignar o cambiar el jefe de un empleado
@router.put("/{usuario_id}/jefe")
def asignar_jefe(usuario_id: int, jefe_id: int, db: Session = Depends(obtener_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.jefe_id = jefe_id
    db.commit()
    db.refresh(usuario)
    return usuario