"""
Endpoints del Appendix A — segundo parcial.
Contratos exactos que verifica el harness automático.

Rutas:
  POST /admin/flights               → crea vuelo de prueba
  GET  /flights/search              → busca vuelos disponibles  (R1)
  POST /reservations                → crea reserva con OL       (R2)
  GET  /reservations/{id}           → consulta reserva           (R3)
  GET  /analytics/occupancy         → ocup. desde Athena         (R7)
  GET  /health                      → ya existe en main.py
"""
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text, update
from sqlalchemy.orm import Session

from adapters.inbound.api.routes.analytics_router import router as analytics_router
from infrastructure.database import get_db
from infrastructure.events import (
    build_reservation_event,
    build_search_event,
    publisher,
)
from infrastructure.models.flight import FlightModel
from infrastructure.models.reservation import ReservationModel

router = APIRouter(tags=["Harness"])


# ------------------------------------------------------------------ #
# Schemas Pydantic                                                     #
# ------------------------------------------------------------------ #

class FlightIn(BaseModel):
    flight_id:   str
    route:       str
    flight_date: str        # "YYYY-MM-DD"
    capacity:    int
    price_cents: int


class FlightOut(BaseModel):
    flight_id:       str
    route:           str
    flight_date:     str
    seats_available: int
    price_cents:     int

    model_config = {"from_attributes": True}


class ReservationIn(BaseModel):
    flight_id:      str
    passenger_name: str
    fare_class:     str


class ReservationOut(BaseModel):
    reservation_id: str
    flight_id:      str
    status:         str
    passenger_name: str

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ #
# POST /admin/flights                                                  #
# Crea un vuelo de prueba. 201 ok, 409 si el id ya existe.            #
# El harness llama esto antes de R1 y R2.                             #
# ------------------------------------------------------------------ #

@router.post(
    "/admin/flights",
    status_code=status.HTTP_201_CREATED,
    response_model=FlightOut,
)
def create_flight(body: FlightIn, db: Session = Depends(get_db)):
    existing = db.get(FlightModel, body.flight_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Flight {body.flight_id} already exists.",
        )
    flight = FlightModel(
        flight_id=body.flight_id,
        route=body.route,
        flight_date=body.flight_date,
        capacity=body.capacity,
        seats_available=body.capacity,   # al crear, todos los asientos libres
        price_cents=body.price_cents,
    )
    db.add(flight)
    db.commit()
    db.refresh(flight)
    return flight


# ------------------------------------------------------------------ #
# GET /flights/search?origin=&destination=&date=                      #
# R1: p95 < 1.0 s bajo 20 clientes concurrentes.                     #
# Retorna vuelos con seats_available > 0.                             #
# ------------------------------------------------------------------ #

@router.get(
    "/flights/search",
    response_model=list[FlightOut],
    status_code=status.HTTP_200_OK,
)
def search_flights(
    origin:      str,
    destination: str,
    date:        str,
    x_session_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    # route se almacena como "ORIGIN-DESTINATION" en mayúsculas
    origin_c = origin.upper().strip()
    destination_c = destination.upper().strip()
    route = f"{origin_c}-{destination_c}"
    flights = (
        db.query(FlightModel)
        .filter(
            FlightModel.route == route,
            FlightModel.flight_date == date,
            FlightModel.seats_available > 0,
        )
        .all()
    )

    # Parcial 3 (R1/R2): un evento por búsqueda, encolado sin bloquear la respuesta.
    pk, event = build_search_event(
        session_id=(x_session_id or "").strip() or str(uuid.uuid4()),
        origin=origin_c,
        destination=destination_c,
        travel_date=date,
        results_count=len(flights),
    )
    publisher.publish(pk, event)
    return flights


# ------------------------------------------------------------------ #
# POST /reservations                                                 #
# R2: no overselling — optimistic locking con UPDATE atómico.         #
# 201 si logró reservar, 409 si no hay seats, 404 si el vuelo         #
# no existe.                                                          #
# K=150: el harness lanza 150 requests simultáneos al mismo vuelo.   #
# ------------------------------------------------------------------ #

@router.post(
    "/reservations",
    status_code=status.HTTP_201_CREATED,
    response_model=ReservationOut,
)
def create_reservation(body: ReservationIn, db: Session = Depends(get_db)):
    # 1. Verificar que el vuelo existe
    flight = db.get(FlightModel, body.flight_id)
    if flight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flight {body.flight_id} not found.",
        )

    # Datos del vuelo para el evento (se leen antes del commit, que expira el objeto)
    f_route, f_date, f_price = flight.route, flight.flight_date, flight.price_cents

    # 2. Optimistic locking: UPDATE atómico que solo procede si
    #    seats_available > 0. Si rowcount == 0 → otro request se adelantó → 409.
    #    Esto garantiza que exactamente K de K requests simultáneos reciban 201
    #    y el resto 409, sin race condition (R2).
    result = db.execute(
        update(FlightModel)
        .where(
            FlightModel.flight_id == body.flight_id,
            FlightModel.seats_available > 0,
        )
        .values(seats_available=FlightModel.seats_available - 1)
    )
    db.flush()

    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No seats available for this flight.",
        )

    # 3. Crear la reserva
    reservation = ReservationModel(
        reservation_id=uuid.uuid4(),
        flight_id=body.flight_id,
        passenger_name=body.passenger_name,
        fare_class=body.fare_class,
        status="CONFIRMED",
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    # Parcial 3 (R1): el evento se publica DESPUÉS de guardar la reserva.
    # Sin datos personales (no se incluye passenger_name).
    pk, event = build_reservation_event(
        "reservation_created", str(reservation.reservation_id), reservation.flight_id,
        f_route, f_date, reservation.fare_class, f_price,
    )
    publisher.publish(pk, event)

    return ReservationOut(
        reservation_id=str(reservation.reservation_id),
        flight_id=reservation.flight_id,
        status=reservation.status,
        passenger_name=reservation.passenger_name,
    )


# ------------------------------------------------------------------ #
# POST /reservations/{id}/cancel                                       #
# Parcial 3: 200 CANCELLED, 404 desconocida, 409 ya cancelada.        #
# Libera el asiento y publica reservation_cancelled.                  #
# ------------------------------------------------------------------ #

@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=ReservationOut,
    status_code=status.HTTP_200_OK,
)
def cancel_reservation(reservation_id: str, db: Session = Depends(get_db)):
    try:
        rid = uuid.UUID(reservation_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid reservation id format.")

    reservation = db.get(ReservationModel, rid)
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation {reservation_id} not found.",
        )

    flight_id = reservation.flight_id
    passenger_name = reservation.passenger_name
    fare_class = reservation.fare_class

    # UPDATE atómico: solo cancela si sigue CONFIRMED. Dos cancelaciones
    # simultáneas -> exactamente una gana, la otra recibe 409.
    result = db.execute(
        update(ReservationModel)
        .where(
            ReservationModel.reservation_id == rid,
            ReservationModel.status == "CONFIRMED",
        )
        .values(status="CANCELLED")
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation is already cancelled.",
        )

    # Libera el asiento
    db.execute(
        update(FlightModel)
        .where(FlightModel.flight_id == flight_id)
        .values(seats_available=FlightModel.seats_available + 1)
    )
    flight = db.get(FlightModel, flight_id)
    f_route, f_date, f_price = flight.route, flight.flight_date, flight.price_cents
    db.commit()

    pk, event = build_reservation_event(
        "reservation_cancelled", str(rid), flight_id, f_route, f_date, fare_class, f_price,
    )
    publisher.publish(pk, event)

    return ReservationOut(
        reservation_id=str(rid),
        flight_id=flight_id,
        status="CANCELLED",
        passenger_name=passenger_name,
    )


# ------------------------------------------------------------------ #
# GET /reservations/{id}                                           #
# R3: 200 con la reserva o 404 si no existe.                         #
# ------------------------------------------------------------------ #

@router.get(
    "/reservations/{reservation_id}",
    response_model=ReservationOut,
    status_code=status.HTTP_200_OK,
)
def get_reservation(reservation_id: str, db: Session = Depends(get_db)):
    try:
        rid = uuid.UUID(reservation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid reservation id format.",
        )

    reservation = db.get(ReservationModel, rid)
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation {reservation_id} not found.",
        )

    return ReservationOut(
        reservation_id=str(reservation.reservation_id),
        flight_id=reservation.flight_id,
        status=reservation.status,
        passenger_name=reservation.passenger_name,
    )


# ------------------------------------------------------------------ #
# GET /analytics/occupancy?route=&month=                              #
# R7: lee de Athena, responde en < 10 s.                             #
# Definido e implementado en analytics_router.                       #
# ------------------------------------------------------------------ #
router.include_router(analytics_router)
