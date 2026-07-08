from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Conexión a la base de datos local
DATABASE_URL = "postgresql://postgres:DannyRc@localhost:5432/vacaciones_db"

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