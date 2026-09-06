from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class VueloProgramado:
    vuelo_programado_id: UUID
    ruta_id: UUID
    aeronave_id: UUID
    hora_salida: time
    hora_llegada: time
    precio_base: Decimal
