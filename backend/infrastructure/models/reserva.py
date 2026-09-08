from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReservaModel(Base):
    __tablename__ = "reserva"

    reserva_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pasajero_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pasajero.pasajero_id"),
        nullable=False,
    )
    # usuario que creó la reserva (puede ser el pasajero o un agente)
    gestionada_por_usuario = Column(
        UUID(as_uuid=True),
        ForeignKey("usuario.usuario_id"),
        nullable=True,
    )
    fecha_reserva = Column(DateTime(timezone=True), server_default=func.now())
    # Estados: 'pending_payment' | 'confirmed' | 'cancelled' | 'modified'
    estado = Column(String(30), nullable=False, default="pending_payment")
    monto_total = Column(Numeric(10, 2), nullable=False, default=0)

    pasajero = relationship("PasajeroModel", back_populates="reservas")
    gestionada_por = relationship("UsuarioModel", foreign_keys=[gestionada_por_usuario])
    vuelos = relationship("ReservaVueloModel", back_populates="reserva")
    pago = relationship("PagoModel", back_populates="reserva", uselist=False)
    agencia_info = relationship("ReservaAgenciaModel", back_populates="reserva", uselist=False)
    auditorias = relationship("AuditoriaModel", back_populates="reserva")
