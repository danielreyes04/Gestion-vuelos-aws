from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class AuditoriaModel(Base):
    """
    Registro inmutable de cada cambio sobre una reserva.
    valor_anterior y valor_nuevo como JSONB permiten capturar
    cualquier campo sin alterar el esquema (RNF-010).
    """
    __tablename__ = "auditoria"

    auditoria_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reserva_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reserva.reserva_id"),
        nullable=False,
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuario.usuario_id"),
        nullable=True,   # NULL si fue acción del sistema
    )
    # Tipos: 'created' | 'modified' | 'cancelled' | 'payment_confirmed'
    tipo_cambio = Column(String(50), nullable=False)
    fecha_cambio = Column(DateTime(timezone=True), server_default=func.now())
    valor_anterior = Column(JSONB, nullable=True)
    valor_nuevo = Column(JSONB, nullable=True)

    reserva = relationship("ReservaModel", back_populates="auditorias")
    usuario = relationship("UsuarioModel")
