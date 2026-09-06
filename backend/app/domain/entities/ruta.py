from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class Ruta:
    ruta_id: UUID
    aeropuerto_origen_id: UUID
    aeropuerto_destino_id: UUID
    distancia_km: Decimal | None = None
