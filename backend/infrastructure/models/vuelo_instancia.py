from sqlalchemy import Column, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class VueloInstanciaModel(Base):
    __tablename__ = "vuelo_instancia"

    vuelo_instancia_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vuelo_programado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vuelo_programado.vuelo_programado_id"),
        nullable=False,
    )
    aeronave_id = Column(
        UUID(as_uuid=True),
        ForeignKey("aeronave.aeronave_id"),
        nullable=False,
    )
    fecha_salida = Column(DateTime(timezone=True), nullable=False)
    fecha_llegada = Column(DateTime(timezone=True), nullable=False)
    # Contador de asientos libres — es la fuente de verdad para prevenir sobreventa.
    # Se decrementa de forma atómica en el mismo UPDATE que confirma la reserva.
    asientos_disponibles = Column(Integer, nullable=False)

    vuelo_programado = relationship("VueloProgramadoModel", back_populates="instancias")
    aeronave = relationship("AeronaveModel")
    asientos = relationship("AsientoModel", back_populates="vuelo_instancia")
