from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

# Tabla de usuarios (empleados, jefes y RRHH)
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)  # empleado, jefe, rrhh

    solicitudes = relationship("Solicitud", back_populates="empleado")

# Tabla de solicitudes de vacaciones
class Solicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    empleado_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    motivo = Column(String, nullable=False)
    estado = Column(String, default="pendiente_jefe")
    comentario_jefe = Column(Text, nullable=True)
    comentario_rrhh = Column(Text, nullable=True)
    dias_solicitados = Column(Integer, nullable=False)

    empleado = relationship("Usuario", back_populates="solicitudes")