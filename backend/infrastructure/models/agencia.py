from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class AgenciaModel(Base):
    __tablename__ = "agencia"

    agencia_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(150), nullable=False)
    contacto = Column(String(255), nullable=True)
    # Porcentaje de comisión, p.ej. 0.08 = 8%
    tasa_comision = Column(Numeric(5, 4), nullable=False, default=0.0)

    agentes = relationship("AgenteAgenciaModel", back_populates="agencia")
