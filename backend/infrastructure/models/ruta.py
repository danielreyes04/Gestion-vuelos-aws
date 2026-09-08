from sqlalchemy import Column, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class RutaModel(Base):
    __tablename__ = "ruta"

    ruta_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # En Aurora estas columnas son varchar (códigos IATA), no UUID FK.
    # El seed confirmó que se insertan como 'BOG', 'MED', 'CTG'.
    aeropuerto_origen = Column(String(10), nullable=False)
    aeropuerto_destino = Column(String(10), nullable=False)

    # FK al aeropuerto (según el seed, Aurora tiene una columna aeropuerto_id
    # que apunta al aeropuerto de destino)
    aeropuerto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("aeropuerto.aeropuerto_id"),
        nullable=True,
    )

    distancia_km = Column(Numeric(10, 2), nullable=True)

    aeropuerto = relationship("AeropuertoModel", foreign_keys=[aeropuerto_id])
