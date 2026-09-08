from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, update
from sqlalchemy.orm import Session, joinedload

from adapters.outbound.persistence.mappers import (
    asiento_to_entity,
    vuelo_instancia_to_entity,
)
from app.domain.entities.asiento import Asiento
from app.domain.entities.vuelo_instancia import VueloInstancia
from app.domain.ports.outbound.vuelo_repository_port import VueloRepositoryPort
from infrastructure.models.asiento import AsientoModel
from infrastructure.models.ruta import RutaModel
from infrastructure.models.vuelo_instancia import VueloInstanciaModel
from infrastructure.models.vuelo_programado import VueloProgramadoModel


class VueloRepository(VueloRepositoryPort):
    """
    Adaptador outbound: implementación SQLAlchemy del VueloRepositoryPort.
    Traduce las operaciones de dominio a queries sobre Aurora PostgreSQL.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Búsqueda de vuelos                                                   #
    # ------------------------------------------------------------------ #

    def buscar_instancias_disponibles(
        self,
        aeropuerto_origen_codigo: str,
        aeropuerto_destino_codigo: str,
        fecha: date,
        num_pasajeros: int,
    ) -> list[VueloInstancia]:
        """
        JOIN: VueloInstancia → VueloProgramado → Ruta → Aeropuerto (origen/destino).
        Filtra por fecha de salida y asientos_disponibles >= num_pasajeros.
        Respuesta esperada < 2 s (RNF-001) gracias a los índices en
        aeropuerto.codigo y vuelo_instancia.fecha_salida.
        """
        inicio_dia = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0,
                              tzinfo=timezone.utc)
        fin_dia = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59,
                           tzinfo=timezone.utc)

        # En Aurora, ruta.aeropuerto_origen y ruta.aeropuerto_destino son
        # varchar con códigos IATA — filtro directo sin resolver UUID.
        instancias = (
            self._db.query(VueloInstanciaModel)
            .join(VueloProgramadoModel,
                  VueloInstanciaModel.vuelo_programado_id
                  == VueloProgramadoModel.vuelo_programado_id)
            .join(RutaModel,
                  VueloProgramadoModel.ruta_id == RutaModel.ruta_id)
            .filter(
                RutaModel.aeropuerto_origen == aeropuerto_origen_codigo,
                RutaModel.aeropuerto_destino == aeropuerto_destino_codigo,
                VueloInstanciaModel.fecha_salida >= inicio_dia,
                VueloInstanciaModel.fecha_salida <= fin_dia,
                VueloInstanciaModel.asientos_disponibles >= num_pasajeros,
            )
            .order_by(VueloInstanciaModel.fecha_salida)
            .all()
        )

        return [vuelo_instancia_to_entity(i) for i in instancias]

    def obtener_instancia_por_id(self, vuelo_instancia_id: UUID) -> VueloInstancia | None:
        m = self._db.get(VueloInstanciaModel, vuelo_instancia_id)
        return vuelo_instancia_to_entity(m) if m else None

    # ------------------------------------------------------------------ #
    # Asientos                                                             #
    # ------------------------------------------------------------------ #

    def obtener_asientos_libres(self, vuelo_instancia_id: UUID) -> list[Asiento]:
        """
        Retorna asientos disponibles y sin bloqueo temporal vigente.
        El filtro de bloqueado_hasta en BD reduce el trabajo del dominio.
        """
        ahora = datetime.now(timezone.utc)
        asientos = (
            self._db.query(AsientoModel)
            .filter(
                AsientoModel.vuelo_instancia_id == vuelo_instancia_id,
                AsientoModel.esta_disponible.is_(True),
                and_(
                    # Sin bloqueo activo: bloqueado_hasta es NULL o ya expiró
                    (AsientoModel.bloqueado_hasta.is_(None))
                    | (AsientoModel.bloqueado_hasta < ahora)
                ),
            )
            .order_by(AsientoModel.numero_asiento)
            .all()
        )
        return [asiento_to_entity(a) for a in asientos]

    def obtener_asiento_por_id(self, asiento_id: UUID) -> Asiento | None:
        m = self._db.get(AsientoModel, asiento_id)
        return asiento_to_entity(m) if m else None

    # ------------------------------------------------------------------ #
    # Concurrencia — optimistic locking                                   #
    # ------------------------------------------------------------------ #

    def bloquear_asiento_temporal(
        self,
        asiento_id: UUID,
        version_actual: int,
        bloqueado_hasta_ts: datetime,
    ) -> bool:
        """
        UPDATE atómico con cláusula WHERE version = :version_actual.

        Si entre la lectura y este UPDATE otro request modificó el asiento,
        version ya no coincide → rowcount = 0 → retorna False → 409.
        Esto implementa el optimistic locking del RNF-004.

        También exige que el asiento siga disponible y sin bloqueo vigente,
        evitando condiciones de carrera durante el flujo de pago (RNF-006).
        """
        ahora = datetime.now(timezone.utc)
        result = self._db.execute(
            update(AsientoModel)
            .where(
                AsientoModel.asiento_id == asiento_id,
                AsientoModel.version == version_actual,
                AsientoModel.esta_disponible.is_(True),
                (AsientoModel.bloqueado_hasta.is_(None))
                | (AsientoModel.bloqueado_hasta < ahora),
            )
            .values(
                bloqueado_hasta=bloqueado_hasta_ts,
                version=AsientoModel.version + 1,
            )
        )
        self._db.flush()
        return result.rowcount == 1

    def confirmar_asiento(self, asiento_id: UUID, version_actual: int) -> bool:
        """
        Marca el asiento como ocupado de forma atómica (misma técnica OL).
        Llamado tras la aprobación del pago (FR-004.4).
        """
        result = self._db.execute(
            update(AsientoModel)
            .where(
                AsientoModel.asiento_id == asiento_id,
                AsientoModel.version == version_actual,
            )
            .values(
                esta_disponible=False,
                bloqueado_hasta=None,
                version=AsientoModel.version + 1,
            )
        )
        self._db.flush()
        return result.rowcount == 1

    def decrementar_disponibilidad(self, vuelo_instancia_id: UUID) -> None:
        """
        UPDATE atómico que nunca baja de 0.
        Mantiene el contador consistente con los asientos confirmados (RNF-004).
        """
        self._db.execute(
            update(VueloInstanciaModel)
            .where(
                VueloInstanciaModel.vuelo_instancia_id == vuelo_instancia_id,
                VueloInstanciaModel.asientos_disponibles > 0,
            )
            .values(
                asientos_disponibles=VueloInstanciaModel.asientos_disponibles - 1
            )
        )
        self._db.flush()
