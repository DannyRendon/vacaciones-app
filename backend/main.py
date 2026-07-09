from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from routers import usuarios, solicitudes

# Crear las tablas en la base de datos al arrancar

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Vacaciones")

# Permitir que el frontend se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar las rutas
app.include_router(usuarios.router)
app.include_router(solicitudes.router)

@app.get("/")
def inicio():
    return {"mensaje": "API de vacaciones funcionando"}