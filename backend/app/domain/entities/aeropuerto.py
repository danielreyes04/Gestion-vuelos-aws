from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Aeropuerto:
    aeropuerto_id: UUID
    codigo: str        # Código IATA, p.ej. "BOG"
    nombre: str
    ciudad: str
    pais: str
