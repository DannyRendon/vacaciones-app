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
def crear_usuario(nombre: str, correo: str, rol: str, db: Session = Depends(obtener_db)):
    # Verificar que el correo no exista
    existe = db.query(models.Usuario).filter(models.Usuario.correo == correo).first()
    if existe:
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")
    
    nuevo = models.Usuario(nombre=nombre, correo=correo, rol=rol)
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