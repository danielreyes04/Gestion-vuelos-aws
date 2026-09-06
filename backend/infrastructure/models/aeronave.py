from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from infrastructure.database import Base


class AeronaveModel(Base):
    __tablename__ = "aeronave"

    aeronave_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    modelo = Column(String(100), nullable=False)
    total_asientos = Column(Integer, nullable=False)
    fabricante = Column(String(100), nullable=True)
