from datetime import date, datetime, timezone
from uuid import UUID

from app.domain.entities.asiento import Asiento
from app.domain.entities.vuelo_instancia import VueloInstancia
from app.domain.exceptions import VueloNoEncontradoError
from app.domain.ports.inbound.vuelo_service_port import VueloServicePort
from app.domain.ports.outbound.vuelo_repository_port import VueloRepositoryPort


class VueloService(VueloServicePort):
    """
    Implementación del puerto inbound VueloServicePort.
    Depende únicamente de la abstracción VueloRepositoryPort,
    nunca de SQLAlchemy directamente (principio de inversión de dependencias).
    """

    def __init__(self, vuelo_repo: VueloRepositoryPort) -> None:
        self._vuelo_repo = vuelo_repo

    def buscar_vuelos_disponibles(
        self,
        origen_codigo: str,
        destino_codigo: str,
        fecha: date,
        num_pasajeros: int = 1,
    ) -> list[VueloInstancia]:
        """
        RF-002 / FR-002: delega la consulta al repositorio.
        El repositorio filtra asientos_disponibles >= num_pasajeros.
        """
        return self._vuelo_repo.buscar_instancias_disponibles(
            aeropuerto_origen_codigo=origen_codigo.upper().strip(),
            aeropuerto_destino_codigo=destino_codigo.upper().strip(),
            fecha=fecha,
            num_pasajeros=num_pasajeros,
        )

    def obtener_asientos_disponibles(self, vuelo_instancia_id: UUID) -> list[Asiento]:
        """
        FR-004.1: verifica que la instancia exista y retorna asientos libres.
        Filtra los que tienen bloqueo temporal aún vigente (comparando con NOW).
        """
        instancia = self._vuelo_repo.obtener_instancia_por_id(vuelo_instancia_id)
        if instancia is None:
            raise VueloNoEncontradoError(
                f"No existe la instancia de vuelo {vuelo_instancia_id}."
            )

        ahora = datetime.now(timezone.utc)
        asientos = self._vuelo_repo.obtener_asientos_libres(vuelo_instancia_id)

        # Filtro adicional en dominio: descarta asientos con bloqueo vigente
        # que el repositorio puede no haber excluido por desfase de reloj.
        return [a for a in asientos if not a.esta_bloqueado(ahora)]
