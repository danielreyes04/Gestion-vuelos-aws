from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.exceptions import TarifaNoEncontradaError
from app.domain.ports.outbound.tarifa_repository_port import TarifaRepositoryPort
from infrastructure.models.regla_tarifa import ReglaTarifaModel
from infrastructure.models.vuelo_programado import VueloProgramadoModel


class TarifaRepository(TarifaRepositoryPort):
    """
    Adaptador outbound: calcula el precio de un asiento según
    la regla de tarifa vigente (FR-003 / RF-003).
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def calcular_precio(
        self,
        vuelo_programado_id: UUID,
        clase: str,
        fecha_vuelo: date,
        fecha_compra: date,
    ) -> Decimal:
        """
        Busca la ReglasTarifa cuyo rango de días de anticipación
        contiene (fecha_vuelo - fecha_compra).dias y multiplica
        por el precio_base del VueloProgramado.

        Si no hay regla aplicable lanza TarifaNoEncontradaError (→ HTTP 422).
        """
        dias_anticipacion = (fecha_vuelo - fecha_compra).days

        regla = (
            self._db.query(ReglaTarifaModel)
            .filter(
                ReglaTarifaModel.vuelo_programado_id == vuelo_programado_id,
                ReglaTarifaModel.clase == clase,
                ReglaTarifaModel.dias_anticipacion_min <= dias_anticipacion,
                ReglaTarifaModel.dias_anticipacion_max >= dias_anticipacion,
            )
            .first()
        )

        if regla is None:
            raise TarifaNoEncontradaError(
                f"No existe regla de tarifa para vuelo={vuelo_programado_id}, "
                f"clase='{clase}', días_anticipación={dias_anticipacion}."
            )

        vuelo_prog = self._db.get(VueloProgramadoModel, vuelo_programado_id)
        if vuelo_prog is None:
            raise TarifaNoEncontradaError(
                f"VueloProgramado {vuelo_programado_id} no encontrado."
            )

        return Decimal(str(vuelo_prog.precio_base)) * Decimal(str(regla.multiplicador))
