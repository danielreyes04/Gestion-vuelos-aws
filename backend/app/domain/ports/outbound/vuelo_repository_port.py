from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.vuelo_instancia import VueloInstancia
from app.domain.entities.asiento import Asiento


class VueloRepositoryPort(ABC):
    """
    Puerto outbound: abstracción de persistencia para vuelos.
    El dominio depende de esta interfaz; la infraestructura la implementa.
    """

    @abstractmethod
    def buscar_instancias_disponibles(
        self,
        aeropuerto_origen_codigo: str,
        aeropuerto_destino_codigo: str,
        fecha: date,
        num_pasajeros: int,
    ) -> list[VueloInstancia]:
        """
        Busca vuelos con asientos_disponibles >= num_pasajeros
        para la ruta y fecha dadas.
        """
        ...

    @abstractmethod
    def obtener_instancia_por_id(self, vuelo_instancia_id: UUID) -> VueloInstancia | None:
        ...

    @abstractmethod
    def obtener_asientos_libres(
        self,
        vuelo_instancia_id: UUID,
    ) -> list[Asiento]:
        """
        Retorna asientos donde esta_disponible=True y
        (bloqueado_hasta IS NULL OR bloqueado_hasta < NOW()).
        """
        ...

    @abstractmethod
    def obtener_asiento_por_id(self, asiento_id: UUID) -> Asiento | None:
        ...

    @abstractmethod
    def bloquear_asiento_temporal(
        self,
        asiento_id: UUID,
        version_actual: int,
        bloqueado_hasta_ts,
    ) -> bool:
        """
        Implementa optimistic locking:
            UPDATE asiento
            SET bloqueado_hasta = :ts, version = version + 1
            WHERE asiento_id = :id AND version = :version_actual
              AND (bloqueado_hasta IS NULL OR bloqueado_hasta < NOW())
              AND esta_disponible = TRUE
        Retorna True si actualizó 1 fila, False si hubo conflicto (0 filas).
        """
        ...

    @abstractmethod
    def confirmar_asiento(self, asiento_id: UUID, version_actual: int) -> bool:
        """
        Marca el asiento como esta_disponible=False de forma atómica.
        Mismo patrón de optimistic locking que bloquear_asiento_temporal.
        """
        ...

    @abstractmethod
    def decrementar_disponibilidad(self, vuelo_instancia_id: UUID) -> None:
        """
        UPDATE vuelo_instancia SET asientos_disponibles = asientos_disponibles - 1
        WHERE vuelo_instancia_id = :id AND asientos_disponibles > 0
        Fuerza que el contador nunca baje de 0 (RNF-004).
        """
        ...
