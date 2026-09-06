from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID


class TarifaRepositoryPort(ABC):
    """
    Puerto outbound: calcula el precio aplicable a un asiento
    según la clase y los días de anticipación (FR-003 / RF-003).
    """

    @abstractmethod
    def calcular_precio(
        self,
        vuelo_programado_id: UUID,
        clase: str,
        fecha_vuelo: date,
        fecha_compra: date,
    ) -> Decimal:
        """
        Busca la regla_tarifa cuyo rango dias_anticipacion_min–max
        contiene los días entre fecha_compra y fecha_vuelo,
        y retorna precio_base * multiplicador.
        Lanza TarifaNoEncontradaError si no hay regla aplicable.
        """
        ...
