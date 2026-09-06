from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class PasajeroModel(Base):
    __tablename__ = "pasajero"

    pasajero_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuario.usuario_id"),
        nullable=False,
        unique=True,
    )
    agente_agencia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agente_agencia.agente_id"),
        nullable=True,   # NULL si el pasajero se registró directamente
    )
    telefono = Column(String(30), nullable=True)
    tipo_documento = Column(String(30), nullable=True)
    numero_documento = Column(String(50), nullable=True)

    usuario = relationship("UsuarioModel")
    agente = relationship("AgenteAgenciaModel")
    reservas = relationship("ReservaModel", back_populates="pasajero")
