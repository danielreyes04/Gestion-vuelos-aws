from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.reserva import Reserva
from app.domain.ports.inbound.reserva_service_port import ReservaServicePort


@dataclass(frozen=True)
class ObtenerReservaInput:
    reserva_id: UUID


class ObtenerReservaUseCase:
    """
    Caso de uso: consultar una reserva existente por su ID (RF-001 / FR-005).

    Lanza ReservaNotFoundError si no existe → traducido a HTTP 404 por el router.
    """

    def __init__(self, reserva_service: ReservaServicePort) -> None:
        self._reserva_service = reserva_service

    def execute(self, input_data: ObtenerReservaInput) -> Reserva:
        return self._reserva_service.obtener_reserva(
            reserva_id=input_data.reserva_id,
        )
