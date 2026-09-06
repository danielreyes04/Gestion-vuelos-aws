from dataclasses import dataclass
from datetime import date

from app.domain.entities.vuelo_instancia import VueloInstancia
from app.domain.ports.inbound.vuelo_service_port import VueloServicePort


@dataclass(frozen=True)
class BuscarVuelosInput:
    """DTO de entrada para el caso de uso de búsqueda."""
    origen_codigo: str       # Código IATA del aeropuerto de origen
    destino_codigo: str      # Código IATA del aeropuerto de destino
    fecha: date
    num_pasajeros: int = 1


class BuscarVuelosUseCase:
    """
    Caso de uso: buscar vuelos disponibles (FR-002 / RF-002).

    Orquesta la llamada al servicio de dominio y retorna la lista
    de instancias de vuelo disponibles para la ruta, fecha y
    cantidad de pasajeros solicitados.
    """

    def __init__(self, vuelo_service: VueloServicePort) -> None:
        self._vuelo_service = vuelo_service

    def execute(self, input_data: BuscarVuelosInput) -> list[VueloInstancia]:
        return self._vuelo_service.buscar_vuelos_disponibles(
            origen_codigo=input_data.origen_codigo,
            destino_codigo=input_data.destino_codigo,
            fecha=input_data.fecha,
            num_pasajeros=input_data.num_pasajeros,
        )
