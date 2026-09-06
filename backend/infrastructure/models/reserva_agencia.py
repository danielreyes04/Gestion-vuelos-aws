from sqlalchemy import Column, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReservaAgenciaModel(Base):
    """
    Registra la comisión de agencia para una reserva.
    Solo existe cuando la reserva fue gestionada a través de una agencia.
    """
    __tablename__ = "reserva_agencia"

    reserva_agencia_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reserva_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reserva.reserva_id"),
        nullable=False,
        unique=True,
    )
    agencia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agencia.agencia_id"),
        nullable=False,
    )
    monto_comision = Column(Numeric(10, 2), nullable=False, default=0)

    reserva = relationship("ReservaModel", back_populates="agencia_info")
    agencia = relationship("AgenciaModel")
