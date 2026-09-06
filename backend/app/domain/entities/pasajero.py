from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Pasajero:
    pasajero_id: UUID
    usuario_id: UUID
    telefono: str | None = None
    tipo_documento: str | None = None
    numero_documento: str | None = None
    agente_agencia_id: UUID | None = None  # None si es pasajero directo
