from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.reserva import Reserva, ReservaVuelo
from app.domain.entities.pago import Pago


class ReservaRepositoryPort(ABC):
    """
    Puerto outbound: abstracción de persistencia para reservas, pagos
    y auditoría.
    """

    @abstractmethod
    def guardar_reserva(self, reserva: Reserva, vuelos: list[ReservaVuelo]) -> Reserva:
        """Persiste una reserva nueva junto a sus tramos."""
        ...

    @abstractmethod
    def obtener_por_id(self, reserva_id: UUID) -> Reserva | None:
        ...

    @abstractmethod
    def actualizar_estado(self, reserva_id: UUID, nuevo_estado: str) -> None:
        ...

    @abstractmethod
    def guardar_pago(self, pago: Pago) -> Pago:
        """Persiste el registro de pago (solo token — RNF-008)."""
        ...

    @abstractmethod
    def registrar_auditoria(
        self,
        reserva_id: UUID,
        usuario_id: UUID | None,
        tipo_cambio: str,
        valor_anterior: dict | None,
        valor_nuevo: dict | None,
    ) -> None:
        """
        RNF-010: toda modificación sobre una reserva queda en auditoría
        dentro de la misma transacción, con valor_anterior y valor_nuevo.
        """
        ...

    @abstractmethod
    def obtener_reservas_por_pasajero(self, pasajero_id: UUID) -> list[Reserva]:
        ...
