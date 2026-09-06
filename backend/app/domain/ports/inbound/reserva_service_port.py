from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.entities.reserva import Reserva


@dataclass(frozen=True)
class CrearReservaCommand:
    """
    Comando con todos los datos necesarios para crear una reserva.
    Puede incluir múltiples tramos (multi-leg, FR-004 / sección 5.3).
    """
    pasajero_id: UUID
    # Lista de (vuelo_instancia_id, asiento_id, clase) por tramo
    tramos: list[tuple[UUID, UUID, str]]
    gestionada_por_usuario_id: UUID | None = None   # None = el propio pasajero
    agencia_id: UUID | None = None                  # None = venta directa


class ReservaServicePort(ABC):
    """
    Puerto inbound: contrato que el caso de uso de reservas expone
    hacia el adaptador HTTP.
    """

    @abstractmethod
    def crear_reserva(self, command: CrearReservaCommand) -> Reserva:
        """
        FR-004 / FR-004.1–FR-004.4:
        - Bloquea temporalmente cada asiento (bloqueado_hasta = ahora + 10 min).
        - Crea la reserva en estado 'pending_payment'.
        - Aplica optimistic locking: si un asiento fue tomado concurrentemente
          lanza SeatUnavailableError (→ HTTP 409).
        - Calcula monto_total según regla_tarifa vigente.
        """
        ...

    @abstractmethod
    def confirmar_pago(
        self,
        reserva_id: UUID,
        id_transaccion: str,
        monto: Decimal,
    ) -> Reserva:
        """
        FR-004.3 / FR-004.4:
        - Valida que la reserva esté en 'pending_payment'.
        - Registra el pago (solo token, nunca datos de tarjeta — RNF-008).
        - Marca el asiento como esta_disponible=False de forma atómica.
        - Decrementa asientos_disponibles en VueloInstancia.
        - Cambia estado a 'confirmed'.
        - Registra en auditoría dentro de la misma transacción (RNF-010).
        """
        ...

    @abstractmethod
    def obtener_reserva(self, reserva_id: UUID) -> Reserva:
        """
        RF-001 / FR-005: consulta una reserva existente por su ID.
        Lanza ReservaNotFoundError si no existe.
        """
        ...

    @abstractmethod
    def cancelar_reserva(self, reserva_id: UUID, usuario_id: UUID) -> Reserva:
        """
        FR-005 / FR-005.1–FR-005.4:
        - Verifica la regla de 8 horas antes del vuelo (FR-005.2).
        - Aplica política de devolución si hay agencia asociada (FR-005.3).
        - Registra en auditoría (FR-005.4).
        """
        ...
