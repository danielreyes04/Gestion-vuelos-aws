from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.asiento import Asiento
from app.domain.ports.inbound.vuelo_service_port import VueloServicePort


@dataclass(frozen=True)
class ObtenerAsientosInput:
    vuelo_instancia_id: UUID


class ObtenerAsientosUseCase:
    """
    Caso de uso: obtener asientos disponibles de una instancia de vuelo (FR-004.1).

    Retorna únicamente los asientos sin confirmar y sin bloqueo temporal vigente,
    para que el pasajero pueda elegir antes de iniciar la reserva.
    """

    def __init__(self, vuelo_service: VueloServicePort) -> None:
        self._vuelo_service = vuelo_service

    def execute(self, input_data: ObtenerAsientosInput) -> list[Asiento]:
        return self._vuelo_service.obtener_asientos_disponibles(
            vuelo_instancia_id=input_data.vuelo_instancia_id,
        )
