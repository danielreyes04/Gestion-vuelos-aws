from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReglaTarifaModel(Base):
    __tablename__ = "regla_tarifa"

    regla_tarifa_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vuelo_programado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vuelo_programado.vuelo_programado_id"),
        nullable=False,
    )
    # Clase de cabina: 'economy' | 'business'
    clase = Column(String(20), nullable=False)
    dias_anticipacion_min = Column(Integer, nullable=False)
    dias_anticipacion_max = Column(Integer, nullable=False)
    # Multiplicador sobre el precio_base del vuelo programado
    multiplicador = Column(Numeric(5, 2), nullable=False, default=1.0)

    vuelo_programado = relationship("VueloProgramadoModel", back_populates="reglas_tarifa")
