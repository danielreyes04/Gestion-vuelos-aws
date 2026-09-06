from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.reserva import Reserva
from app.domain.ports.inbound.reserva_service_port import (
    CrearReservaCommand,
    ReservaServicePort,
)


@dataclass(frozen=True)
class CrearReservaInput:
    """
    DTO de entrada para el caso de uso de creación de reserva.

    tramos: lista de (vuelo_instancia_id, asiento_id, clase) — permite
    modelar itinerarios multi-tramo en una sola transacción (sección 5.3).
    """
    pasajero_id: UUID
    tramos: list[tuple[UUID, UUID, str]]
    gestionada_por_usuario_id: UUID | None = None
    agencia_id: UUID | None = None


class CrearReservaUseCase:
    """
    Caso de uso: crear una reserva con bloqueo temporal de asientos (FR-004).

    Delega al ReservaService toda la lógica de concurrencia (optimistic locking
    + bloqueo temporal) y cálculo de tarifas. Este use case solo adapta
    el DTO de entrada al Command del dominio.
    """

    def __init__(self, reserva_service: ReservaServicePort) -> None:
        self._reserva_service = reserva_service

    def execute(self, input_data: CrearReservaInput) -> Reserva:
        command = CrearReservaCommand(
            pasajero_id=input_data.pasajero_id,
            tramos=input_data.tramos,
            gestionada_por_usuario_id=input_data.gestionada_por_usuario_id,
            agencia_id=input_data.agencia_id,
        )
        return self._reserva_service.crear_reserva(command)
