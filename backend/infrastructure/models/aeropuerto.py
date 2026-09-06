from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from infrastructure.database import Base


class AeropuertoModel(Base):
    __tablename__ = "aeropuerto"

    aeropuerto_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(10), nullable=False, unique=True)   # IATA p.ej. BOG
    nombre = Column(String(100), nullable=False)
    ciudad = Column(String(100), nullable=False)
    pais = Column(String(100), nullable=False)
