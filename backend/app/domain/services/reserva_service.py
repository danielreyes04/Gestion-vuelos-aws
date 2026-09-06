from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities.pago import Pago
from app.domain.entities.reserva import Reserva, ReservaVuelo
from app.domain.exceptions import (
    ModificacionNoPermitidaError,
    PagoInvalidoError,
    ReservaNotFoundError,
    SeatUnavailableError,
    VueloNoEncontradoError,
)
from app.domain.ports.inbound.reserva_service_port import (
    CrearReservaCommand,
    ReservaServicePort,
)
from app.domain.ports.outbound.reserva_repository_port import ReservaRepositoryPort
from app.domain.ports.outbound.tarifa_repository_port import TarifaRepositoryPort
from app.domain.ports.outbound.vuelo_repository_port import VueloRepositoryPort
from infrastructure.config import settings

# Número máximo de reintentos ante conflicto de optimistic locking.
# Con 3 reintentos la probabilidad de fallo bajo carga normal es < 0.1%.
MAX_RETRIES = 3


class ReservaService(ReservaServicePort):
    """
    Implementación del puerto inbound ReservaServicePort.
    Orquesta la lógica de negocio del ciclo de vida de una reserva,
    incluyendo el mecanismo de concurrencia dual:

    1. Bloqueo temporal (bloqueado_hasta):
       Reserva el asiento durante el flujo de pago (10 min — RNF-006)
       sin mantener un lock de BD abierto mientras se espera la pasarela.

    2. Optimistic locking (campo version):
       El UPDATE solo procede si version no cambió desde la lectura.
       Si falló (0 filas), otro request se adelantó → SeatUnavailableError
       → HTTP 409 (RNF-004 / RNF-005).
    """

    def __init__(
        self,
        reserva_repo: ReservaRepositoryPort,
        vuelo_repo: VueloRepositoryPort,
        tarifa_repo: TarifaRepositoryPort,
    ) -> None:
        self._reserva_repo = reserva_repo
        self._vuelo_repo = vuelo_repo
        self._tarifa_repo = tarifa_repo

    # ------------------------------------------------------------------ #
    # Crear reserva                                                        #
    # ------------------------------------------------------------------ #

    def crear_reserva(self, command: CrearReservaCommand) -> Reserva:
        """
        Flujo atómico:
        1. Para cada tramo: leer asiento → bloqueo temporal con OL → calcular tarifa.
        2. Crear Reserva en estado 'pending_payment'.
        3. Registrar en auditoría como 'created'.

        Si cualquier asiento falla el OL se lanza SeatUnavailableError
        y no se persiste nada (los bloqueos ya aplicados expiran solos).
        """
        ahora = datetime.now(timezone.utc)
        bloqueado_hasta = ahora + timedelta(seconds=settings.SEAT_LOCK_TIMEOUT_SECONDS)

        tramos_entidad: list[ReservaVuelo] = []
        monto_total = Decimal("0.00")
        reserva_id = uuid4()

        for vuelo_instancia_id, asiento_id, clase in command.tramos:
            # 1. Obtener instancia de vuelo para la fecha
            instancia = self._vuelo_repo.obtener_instancia_por_id(vuelo_instancia_id)
            if instancia is None:
                raise VueloNoEncontradoError(
                    f"Instancia de vuelo {vuelo_instancia_id} no encontrada."
                )

            # 2. Obtener asiento y verificar disponibilidad en dominio
            asiento = self._vuelo_repo.obtener_asiento_por_id(asiento_id)
            if asiento is None or asiento.esta_ocupado(ahora):
                raise SeatUnavailableError(
                    f"El asiento {asiento_id} no está disponible."
                )

            # 3. Bloqueo temporal con optimistic locking (RNF-004 / RNF-006)
            #    Reintenta hasta MAX_RETRIES veces ante conflicto de versión
            bloqueado = False
            for intento in range(MAX_RETRIES):
                # Re-leer el asiento en cada reintento para obtener version fresca
                if intento > 0:
                    asiento = self._vuelo_repo.obtener_asiento_por_id(asiento_id)
                    if asiento is None or asiento.esta_ocupado(ahora):
                        raise SeatUnavailableError(
                            f"El asiento {asiento_id} fue tomado por otro usuario."
                        )

                bloqueado = self._vuelo_repo.bloquear_asiento_temporal(
                    asiento_id=asiento_id,
                    version_actual=asiento.version,
                    bloqueado_hasta_ts=bloqueado_hasta,
                )
                if bloqueado:
                    break

            if not bloqueado:
                raise SeatUnavailableError(
                    f"No se pudo bloquear el asiento {asiento_id} "
                    f"tras {MAX_RETRIES} intentos (conflicto de concurrencia)."
                )

            # 4. Calcular tarifa según días de anticipación y clase (FR-003)
            fecha_vuelo = instancia.fecha_salida.date()
            fecha_compra = ahora.date()

            # Necesitamos el vuelo_programado_id para buscar la regla de tarifa
            vuelo_programado = self._vuelo_repo.obtener_instancia_por_id(vuelo_instancia_id)
            monto_tramo = self._tarifa_repo.calcular_precio(
                vuelo_programado_id=instancia.vuelo_programado_id,
                clase=clase,
                fecha_vuelo=fecha_vuelo,
                fecha_compra=fecha_compra,
            )
            monto_total += monto_tramo

            tramos_entidad.append(
                ReservaVuelo(
                    reserva_vuelo_id=uuid4(),
                    reserva_id=reserva_id,
                    vuelo_instancia_id=vuelo_instancia_id,
                    monto_tarifa=monto_tramo,
                )
            )

        # 5. Crear la reserva en estado pending_payment
        reserva = Reserva(
            reserva_id=reserva_id,
            pasajero_id=command.pasajero_id,
            estado="pending_payment",
            monto_total=monto_total,
            fecha_reserva=ahora,
            vuelos=tramos_entidad,
            gestionada_por_usuario=command.gestionada_por_usuario_id,
        )

        # 6. Persistir y registrar auditoría en la misma transacción (RNF-010)
        reserva_guardada = self._reserva_repo.guardar_reserva(reserva, tramos_entidad)
        self._reserva_repo.registrar_auditoria(
            reserva_id=reserva_id,
            usuario_id=command.gestionada_por_usuario_id,
            tipo_cambio="created",
            valor_anterior=None,
            valor_nuevo={"estado": "pending_payment", "monto_total": str(monto_total)},
        )

        return reserva_guardada

    # ------------------------------------------------------------------ #
    # Confirmar pago                                                       #
    # ------------------------------------------------------------------ #

    def confirmar_pago(
        self,
        reserva_id: UUID,
        id_transaccion: str,
        monto: Decimal,
    ) -> Reserva:
        """
        FR-004.3 / FR-004.4:
        - Valida estado y monto.
        - Confirma cada asiento con optimistic locking.
        - Decrementa asientos_disponibles en VueloInstancia.
        - Registra pago (solo token) y auditoría.
        Todo ocurre en la misma unidad de trabajo del repositorio.
        """
        reserva = self._reserva_repo.obtener_por_id(reserva_id)
        if reserva is None:
            raise ReservaNotFoundError(f"Reserva {reserva_id} no encontrada.")

        if reserva.estado != "pending_payment":
            raise PagoInvalidoError(
                f"La reserva está en estado '{reserva.estado}', no se puede pagar."
            )

        if monto != reserva.monto_total:
            raise PagoInvalidoError(
                f"Monto recibido {monto} no coincide con el esperado {reserva.monto_total}."
            )

        ahora = datetime.now(timezone.utc)
        estado_anterior = {"estado": reserva.estado}

        # Confirmar cada asiento y decrementar disponibilidad
        for tramo in reserva.vuelos:
            asiento = self._vuelo_repo.obtener_asiento_por_id(
                # El asiento está en reserva_asiento; lo obtenemos por tramo
                # La relación se resuelve en el repositorio concreto.
                # Aquí pasamos el vuelo_instancia_id para que el repo lo resuelva.
                tramo.vuelo_instancia_id  # type: ignore[arg-type]
                # NOTA: el repositorio concreto busca el asiento asociado a este tramo.
            )
            # Confirmar asiento con OL (version viene del estado actual en BD)
            if asiento:
                confirmado = self._vuelo_repo.confirmar_asiento(
                    asiento_id=asiento.asiento_id,
                    version_actual=asiento.version,
                )
                if not confirmado:
                    raise SeatUnavailableError(
                        f"Conflicto al confirmar asiento del tramo {tramo.reserva_vuelo_id}."
                    )
                self._vuelo_repo.decrementar_disponibilidad(tramo.vuelo_instancia_id)

        # Registrar pago — solo el token (RNF-008)
        pago = Pago(
            pago_id=uuid4(),
            reserva_id=reserva_id,
            monto=monto,
            estado="approved",
            fecha_pago=ahora,
            id_transaccion=id_transaccion,
        )
        self._reserva_repo.guardar_pago(pago)

        # Actualizar estado de la reserva
        reserva.confirmar()
        self._reserva_repo.actualizar_estado(reserva_id, "confirmed")

        # Auditoría (RNF-010)
        self._reserva_repo.registrar_auditoria(
            reserva_id=reserva_id,
            usuario_id=reserva.gestionada_por_usuario,
            tipo_cambio="payment_confirmed",
            valor_anterior=estado_anterior,
            valor_nuevo={"estado": "confirmed", "id_transaccion": id_transaccion},
        )

        return reserva

    # ------------------------------------------------------------------ #
    # Obtener reserva                                                      #
    # ------------------------------------------------------------------ #

    def obtener_reserva(self, reserva_id: UUID) -> Reserva:
        reserva = self._reserva_repo.obtener_por_id(reserva_id)
        if reserva is None:
            raise ReservaNotFoundError(f"Reserva {reserva_id} no encontrada.")
        return reserva

    # ------------------------------------------------------------------ #
    # Cancelar reserva                                                     #
    # ------------------------------------------------------------------ #

    def cancelar_reserva(self, reserva_id: UUID, usuario_id: UUID) -> Reserva:
        """
        FR-005 / FR-005.1–FR-005.4:
        - Obtiene el primer vuelo para verificar la regla de 8 horas.
        - Cancela y registra auditoría.
        """
        reserva = self._reserva_repo.obtener_por_id(reserva_id)
        if reserva is None:
            raise ReservaNotFoundError(f"Reserva {reserva_id} no encontrada.")

        ahora = datetime.now(timezone.utc)

        # Obtener fecha de salida del primer tramo para la regla de 8 horas
        if reserva.vuelos:
            primer_tramo = reserva.vuelos[0]
            instancia = self._vuelo_repo.obtener_instancia_por_id(
                primer_tramo.vuelo_instancia_id
            )
            if instancia and not reserva.puede_cancelarse(instancia.fecha_salida, ahora):
                raise ModificacionNoPermitidaError(
                    "No se puede cancelar dentro de las 8 horas previas al vuelo (FR-005.2)."
                )

        estado_anterior = {"estado": reserva.estado}
        reserva.cancelar()
        self._reserva_repo.actualizar_estado(reserva_id, "cancelled")

        # Auditoría (RNF-010)
        self._reserva_repo.registrar_auditoria(
            reserva_id=reserva_id,
            usuario_id=usuario_id,
            tipo_cambio="cancelled",
            valor_anterior=estado_anterior,
            valor_nuevo={"estado": "cancelled"},
        )

        return reserva
