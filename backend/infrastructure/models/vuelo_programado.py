from sqlalchemy import Column, Time, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class VueloProgramadoModel(Base):
    __tablename__ = "vuelo_programado"

    vuelo_programado_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ruta_id = Column(UUID(as_uuid=True), ForeignKey("ruta.ruta_id"), nullable=False)
    aeronave_id = Column(UUID(as_uuid=True), ForeignKey("aeronave.aeronave_id"), nullable=False)
    hora_salida = Column(Time, nullable=False)
    hora_llegada = Column(Time, nullable=False)
    precio_base = Column(Numeric(10, 2), nullable=False)

    ruta = relationship("RutaModel")
    aeronave = relationship("AeronaveModel")
    instancias = relationship("VueloInstanciaModel", back_populates="vuelo_programado")
    reglas_tarifa = relationship("ReglaTarifaModel", back_populates="vuelo_programado")
