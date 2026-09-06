from sqlalchemy import Column, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class RutaModel(Base):
    __tablename__ = "ruta"

    ruta_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aeropuerto_origen_id = Column(
        UUID(as_uuid=True),
        ForeignKey("aeropuerto.aeropuerto_id"),
        nullable=False,
    )
    aeropuerto_destino_id = Column(
        UUID(as_uuid=True),
        ForeignKey("aeropuerto.aeropuerto_id"),
        nullable=False,
    )
    distancia_km = Column(Numeric(10, 2), nullable=True)

    origen = relationship("AeropuertoModel", foreign_keys=[aeropuerto_origen_id])
    destino = relationship("AeropuertoModel", foreign_keys=[aeropuerto_destino_id])
