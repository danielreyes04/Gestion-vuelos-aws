from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from infrastructure.database import Base


class ReservationModel(Base):
    """
    Tabla de reservas para el harness del segundo parcial.
    Schema mínimo según Appendix A.1:
      POST /reservations → {flight_id, passenger_name, fare_class}
      GET  /reservations/{id} → {reservation_id, flight_id, status, passenger_name}
    """
    __tablename__ = "reservation"

    reservation_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    flight_id      = Column(String(100), ForeignKey("flight.flight_id"), nullable=False)
    passenger_name = Column(String(255), nullable=False)
    fare_class     = Column(String(50),  nullable=False)
    # El harness espera "CONFIRMED" o "CANCELLED" en mayúsculas
    status         = Column(String(20),  nullable=False, default="CONFIRMED")

    flight = relationship("FlightModel")
