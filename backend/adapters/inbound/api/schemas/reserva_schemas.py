from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Request schemas                                                      #
# ------------------------------------------------------------------ #

class TramoRequest(BaseModel):
    """Un tramo (vuelo + asiento) dentro de una reserva multi-leg."""
    vuelo_instancia_id: UUID
    asiento_id: UUID
    clase: str = Field(
        ...,
        pattern=r"^(economy|business)$",
        description="Clase del asiento: 'economy' o 'business'.",
    )


class CrearReservaRequest(BaseModel):
    pasajero_id: UUID
    tramos: list[TramoRequest] = Field(
        ...,
        min_length=1,
        description="Lista de tramos. Mínimo 1. Permite itinerarios multi-leg.",
    )
    agencia_id: UUID | None = Field(
        default=None,
        description="ID de la agencia si la reserva es gestionada por un agente.",
    )
    gestionada_por_usuario_id: UUID | None = Field(
        default=None,
        description="ID del agente o admin que crea la reserva. None = el propio pasajero.",
    )


class ConfirmarPagoRequest(BaseModel):
    """
    El frontend envía el token retornado por la pasarela PCI DSS.
    El sistema nunca recibe datos de tarjeta (RNF-008).
    """
    id_transaccion: str = Field(
        ...,
        min_length=1,
        description="Token de transacción devuelto por la pasarela de pago.",
    )
    monto: Decimal = Field(
        ...,
        gt=0,
        description="Monto exacto cobrado por la pasarela.",
    )


class CancelarReservaRequest(BaseModel):
    usuario_id: UUID = Field(
        ...,
        description="ID del usuario que solicita la cancelación (pasajero o admin).",
    )


# ------------------------------------------------------------------ #
# Response schemas                                                     #
# ------------------------------------------------------------------ #

class ReservaVueloResponse(BaseModel):
    reserva_vuelo_id: UUID
    vuelo_instancia_id: UUID
    monto_tarifa: Decimal
    numero_boleto: str | None = None

    model_config = {"from_attributes": True}


class ReservaResponse(BaseModel):
    reserva_id: UUID
    pasajero_id: UUID
    estado: str
    monto_total: Decimal
    fecha_reserva: datetime
    vuelos: list[ReservaVueloResponse] = []

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    detail: str
