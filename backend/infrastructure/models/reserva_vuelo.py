from sqlalchemy import Column, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReservaVueloModel(Base):
    """
    Tabla puente entre Reserva y VueloInstancia.
    Permite itinerarios multi-tramo: una reserva puede tener N vuelos.
    """
    __tablename__ = "reserva_vuelo"

    reserva_vuelo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reserva_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reserva.reserva_id"),
        nullable=False,
    )
    vuelo_instancia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vuelo_instancia.vuelo_instancia_id"),
        nullable=False,
    )
    monto_tarifa = Column(Numeric(10, 2), nullable=False)
    numero_boleto = Column(String(50), nullable=True)

    reserva = relationship("ReservaModel", back_populates="vuelos")
    vuelo_instancia = relationship("VueloInstanciaModel")
