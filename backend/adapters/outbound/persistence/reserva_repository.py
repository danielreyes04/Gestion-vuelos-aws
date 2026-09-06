from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, joinedload

from adapters.outbound.persistence.mappers import pago_to_entity, reserva_to_entity
from app.domain.entities.pago import Pago
from app.domain.entities.reserva import Reserva, ReservaVuelo
from app.domain.ports.outbound.reserva_repository_port import ReservaRepositoryPort
from infrastructure.models.auditoria import AuditoriaModel
from infrastructure.models.pago import PagoModel
from infrastructure.models.reserva import ReservaModel
from infrastructure.models.reserva_vuelo import ReservaVueloModel


class ReservaRepository(ReservaRepositoryPort):
    """
    Adaptador outbound: implementación SQLAlchemy del ReservaRepositoryPort.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def guardar_reserva(self, reserva: Reserva, vuelos: list[ReservaVuelo]) -> Reserva:
        """
        Persiste la reserva y sus tramos en una sola unidad de trabajo.
        El commit lo gestiona el adaptador HTTP (router) al finalizar el request,
        lo que permite que la auditoría quede en la misma transacción (RNF-010).
        """
        reserva_orm = ReservaModel(
            reserva_id=reserva.reserva_id,
            pasajero_id=reserva.pasajero_id,
            gestionada_por_usuario=reserva.gestionada_por_usuario,
            fecha_reserva=reserva.fecha_reserva,
            estado=reserva.estado,
            monto_total=reserva.monto_total,
        )
        self._db.add(reserva_orm)

        for tramo in vuelos:
            self._db.add(ReservaVueloModel(
                reserva_vuelo_id=tramo.reserva_vuelo_id,
                reserva_id=tramo.reserva_id,
                vuelo_instancia_id=tramo.vuelo_instancia_id,
                monto_tarifa=tramo.monto_tarifa,
                numero_boleto=tramo.numero_boleto,
            ))

        self._db.flush()
        return reserva

    def obtener_por_id(self, reserva_id: UUID) -> Reserva | None:
        m = (
            self._db.query(ReservaModel)
            .options(joinedload(ReservaModel.vuelos))
            .filter(ReservaModel.reserva_id == reserva_id)
            .first()
        )
        return reserva_to_entity(m) if m else None

    def actualizar_estado(self, reserva_id: UUID, nuevo_estado: str) -> None:
        m = self._db.get(ReservaModel, reserva_id)
        if m:
            m.estado = nuevo_estado
            self._db.flush()

    def guardar_pago(self, pago: Pago) -> Pago:
        """
        Solo guarda el token de la pasarela. Nunca recibe ni persiste
        datos de tarjeta (RNF-008).
        """
        self._db.add(PagoModel(
            pago_id=pago.pago_id,
            reserva_id=pago.reserva_id,
            monto=pago.monto,
            fecha_pago=pago.fecha_pago,
            estado=pago.estado,
            id_transaccion=pago.id_transaccion,
        ))
        self._db.flush()
        return pago

    def registrar_auditoria(
        self,
        reserva_id: UUID,
        usuario_id: UUID | None,
        tipo_cambio: str,
        valor_anterior: dict | None,
        valor_nuevo: dict | None,
    ) -> None:
        """
        RNF-010: auditoría dentro de la misma transacción que el cambio.
        Como usamos flush() y el commit es al final del request, todo
        queda atómico: si algo falla antes del commit, el rollback
        descarta también esta fila de auditoría.
        """
        self._db.add(AuditoriaModel(
            auditoria_id=uuid4(),
            reserva_id=reserva_id,
            usuario_id=usuario_id,
            tipo_cambio=tipo_cambio,
            fecha_cambio=datetime.now(timezone.utc),
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
        ))
        self._db.flush()

    def obtener_reservas_por_pasajero(self, pasajero_id: UUID) -> list[Reserva]:
        modelos = (
            self._db.query(ReservaModel)
            .options(joinedload(ReservaModel.vuelos))
            .filter(ReservaModel.pasajero_id == pasajero_id)
            .order_by(ReservaModel.fecha_reserva.desc())
            .all()
        )
        return [reserva_to_entity(m) for m in modelos]
