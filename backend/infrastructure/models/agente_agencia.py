from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class AgenteAgenciaModel(Base):
    __tablename__ = "agente_agencia"

    agente_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuario.usuario_id"),
        nullable=False,
        unique=True,
    )
    agencia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agencia.agencia_id"),
        nullable=False,
    )

    usuario = relationship("UsuarioModel")
    agencia = relationship("AgenciaModel", back_populates="agentes")
