from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from infrastructure.config import settings

# pool_pre_ping valida la conexión antes de entregarla — importante con Aurora
# ya que puede haber failovers que dejan conexiones muertas en el pool.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # K=150 requests simultáneos (R2) — pool debe aguantar la carga.
    # pool_size=50 conexiones base + max_overflow=120 = 170 conexiones máx.
    # Aurora db.t3.micro soporta ~85 conexiones; si hay problemas bajar a 30+60.
    pool_size=50,
    max_overflow=120,
    pool_timeout=30,
    echo=(settings.APP_ENV == "development"),
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM del proyecto."""
    pass


def get_db():
    """
    Dependency de FastAPI. Entrega una sesión de BD y garantiza
    que se cierre al terminar el request, incluso si hay excepción.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
