from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.vuelo_instancia import VueloInstancia
from app.domain.entities.asiento import Asiento


class VueloServicePort(ABC):
    """
    Puerto inbound: contrato que el caso de uso de vuelos expone
    hacia el adaptador HTTP (router FastAPI).
    """

    @abstractmethod
    def buscar_vuelos_disponibles(
        self,
        origen_codigo: str,
        destino_codigo: str,
        fecha: date,
        num_pasajeros: int = 1,
    ) -> list[VueloInstancia]:
        """
        RF-002 / FR-002: busca instancias de vuelo con asientos disponibles
        para la ruta y fecha indicadas.
        Retorna lista vacía si no hay resultados.
        """
        ...

    @abstractmethod
    def obtener_asientos_disponibles(
        self,
        vuelo_instancia_id: UUID,
    ) -> list[Asiento]:
        """
        FR-004.1: retorna los asientos del vuelo que están disponibles
        y sin bloqueo temporal vigente en este momento.
        """
        ...
