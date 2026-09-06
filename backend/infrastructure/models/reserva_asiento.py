from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReservaAsientoModel(Base):
    """
    Asigna un asiento a una reserva.
    fecha_asignacion registra cuándo se confirmó (post-pago),
    lo que la distingue del bloqueo temporal en AsientoModel.bloqueado_hasta.
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

    reserva = relationship(
        "ReservaModel",
        secondary="reserva_vuelo",
        primaryjoin="ReservaAsientoModel.reserva_vuelo_id == ReservaVueloModel.reserva_vuelo_id",
        secondaryjoin="ReservaVueloModel.reserva_id == ReservaModel.reserva_id",
        viewonly=True,
    )
    reserva_vuelo = relationship("ReservaVueloModel")
    asiento = relationship("AsientoModel")
