from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Aeronave:
    aeronave_id: UUID
    modelo: str
    total_asientos: int
    fabricante: str | None = None
