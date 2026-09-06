from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.reserva import Reserva
from app.domain.ports.inbound.reserva_service_port import ReservaServicePort


@dataclass(frozen=True)
class CancelarReservaInput:
    reserva_id: UUID
    usuario_id: UUID   # quien solicita la cancelación (pasajero o admin)


class CancelarReservaUseCase:
    """
    Caso de uso: cancelar una reserva existente (FR-005 / FR-005.1–FR-005.4).

    El servicio de dominio verifica:
    - Que la reserva no esté ya cancelada.
    - La regla de 8 horas antes del vuelo (FR-005.2).
    - Registra en auditoría con actor y timestamp (FR-005.4 / RNF-010).
    """

    def __init__(self, reserva_service: ReservaServicePort) -> None:
        self._reserva_service = reserva_service

    def execute(self, input_data: CancelarReservaInput) -> Reserva:
        return self._reserva_service.cancelar_reserva(
            reserva_id=input_data.reserva_id,
            usuario_id=input_data.usuario_id,
        )
