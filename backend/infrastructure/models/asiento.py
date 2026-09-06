from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class AsientoModel(Base):
    __tablename__ = "asiento"

    asiento_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vuelo_instancia_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vuelo_instancia.vuelo_instancia_id"),
        nullable=False,
    )
    numero_asiento = Column(String(10), nullable=False)   # p.ej. "12A"
    clase = Column(String(20), nullable=False)            # 'economy' | 'business'
    esta_disponible = Column(Boolean, nullable=False, default=True)
    # Bloqueo temporal durante el flujo de pago (RNF-006: 10 min).
    # NULL significa que no hay bloqueo activo.
    bloqueado_hasta = Column(DateTime(timezone=True), nullable=True)
    # Versión para optimistic locking (RNF-004).
    # El UPDATE incluye WHERE version = :version_leida para detectar conflictos.
    version = Column(Integer, nullable=False, default=0)

    vuelo_instancia = relationship("VueloInstanciaModel", back_populates="asientos")
