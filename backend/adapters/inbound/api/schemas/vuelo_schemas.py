from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ------------------------------------------------------------------ #
# Request schemas                                                      #
# ------------------------------------------------------------------ #

class BuscarVuelosRequest(BaseModel):
    origen_codigo: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        examples=["BOG"],
        description="Código IATA del aeropuerto de origen (3 letras mayúsculas).",
    )
    destino_codigo: str = Field(
        ...,
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        examples=["MED"],
        description="Código IATA del aeropuerto de destino.",
    )
    fecha: date = Field(
        ...,
        description="Fecha de salida deseada (YYYY-MM-DD).",
    )
    num_pasajeros: int = Field(
        default=1,
        ge=1,
        le=9,
        description="Número de asientos requeridos.",
    )

    @field_validator("fecha")
    @classmethod
    def fecha_no_pasada(cls, v: date) -> date:
        from datetime import date as date_type
        if v < date_type.today():
            raise ValueError("La fecha de búsqueda no puede ser en el pasado.")
        return v


# ------------------------------------------------------------------ #
# Response schemas                                                     #
# ------------------------------------------------------------------ #

class VueloInstanciaResponse(BaseModel):
    vuelo_instancia_id: UUID
    vuelo_programado_id: UUID
    fecha_salida: datetime
    fecha_llegada: datetime
    asientos_disponibles: int

    model_config = {"from_attributes": True}


class AsientoResponse(BaseModel):
    asiento_id: UUID
    numero_asiento: str
    clase: str
    esta_disponible: bool
    bloqueado_hasta: datetime | None = None

    model_config = {"from_attributes": True}
