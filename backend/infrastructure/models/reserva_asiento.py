from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReservaAsientoModel(Base):
    """
    Asigna un asiento a un tramo de reserva (reserva_vuelo).
    La relación con Reserva se navega a través de reserva_vuelo.
    """
    __tablename__ = "reserva_asiento"

    reserva_asiento_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reserva_vuelo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reserva_vuelo.reserva_vuelo_id"),
        nullable=False,
    )
    asiento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("asiento.asiento_id"),
        nullable=False,
    )
    fecha_asignacion = Column(DateTime(timezone=True), nullable=True)

    reserva_vuelo = relationship("ReservaVueloModel")
    asiento = relationship("AsientoModel")
