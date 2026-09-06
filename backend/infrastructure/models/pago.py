from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class PagoModel(Base):
    __tablename__ = "pago"

    pago_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reserva_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reserva.reserva_id"),
        nullable=False,
        unique=True,
    )
    monto = Column(Numeric(10, 2), nullable=False)
    fecha_pago = Column(DateTime(timezone=True), nullable=True)
    # Estados: 'pending' | 'approved' | 'rejected' | 'refunded'
    estado = Column(String(20), nullable=False, default="pending")
    # Token retornado por la pasarela PCI DSS — nunca almacenamos datos de tarjeta (RNF-008)
    id_transaccion = Column(String(255), nullable=True)

    reserva = relationship("ReservaModel", back_populates="pago")
