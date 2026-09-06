from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.entities.reserva import Reserva
from app.domain.ports.inbound.reserva_service_port import ReservaServicePort


@dataclass(frozen=True)
class ConfirmarPagoInput:
    """
    DTO de entrada para confirmar el pago de una reserva.

    id_transaccion: token retornado por la pasarela PCI DSS.
    El sistema nunca recibe ni almacena datos de tarjeta (RNF-008).
    """
    reserva_id: UUID
    id_transaccion: str
    monto: Decimal


class ConfirmarPagoUseCase:
    """
    Caso de uso: confirmar el pago de una reserva (FR-004.3 / FR-004.4).

    Tras la aprobación de la pasarela externa, este caso de uso:
    - Valida el monto contra el total de la reserva.
    - Confirma los asientos (esta_disponible = False) con optimistic locking.
    - Decrementa asientos_disponibles en VueloInstancia.
    - Cambia el estado de la reserva a 'confirmed'.
    - Registra auditoría en la misma transacción (RNF-010).
    """

    def __init__(self, reserva_service: ReservaServicePort) -> None:
        self._reserva_service = reserva_service

    def execute(self, input_data: ConfirmarPagoInput) -> Reserva:
        return self._reserva_service.confirmar_pago(
            reserva_id=input_data.reserva_id,
            id_transaccion=input_data.id_transaccion,
            monto=input_data.monto,
        )
