from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# En producción (Render) esta variable la inyecta el servicio automáticamente.
# En local, si no existe, usa la conexión de siempre como respaldo.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:DannyRc@localhost:5432/vacaciones_db"
)

engine = create_engine(DATABASE_URL)

# Cada petición abre y cierra su propia sesión
SesionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Función para obtener la sesión en cada endpoint
def obtener_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()