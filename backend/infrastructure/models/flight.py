from sqlalchemy import Column, String, Integer, BigInteger, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid

from infrastructure.database import Base


class FlightModel(Base):
    """
    Tabla simplificada para el harness del segundo parcial.
    El harness crea vuelos con POST /admin/flights y luego
    prueba búsqueda y reservas contra ellos.
    Coexiste con el modelo hexagonal del primer parcial.
    """
    __tablename__ = "flight"

    flight_id   = Column(String(100), primary_key=True)   # el harness envía su propio id
    route       = Column(String(20),  nullable=False)      # p.ej. "BOG-MDE"
    flight_date = Column(String(10),  nullable=False)      # "YYYY-MM-DD"
    capacity    = Column(Integer,     nullable=False)
    seats_available = Column(Integer, nullable=False)
    price_cents = Column(BigInteger,  nullable=False)
