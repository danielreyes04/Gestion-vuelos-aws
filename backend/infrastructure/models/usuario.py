from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from infrastructure.database import Base


class UsuarioModel(Base):
    __tablename__ = "usuario"

    usuario_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    # Roles: 'passenger' | 'admin' | 'agency_agent'
    rol = Column(String(30), nullable=False, default="passenger")
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
