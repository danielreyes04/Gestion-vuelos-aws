"""
Funciones puras que convierten modelos ORM → entidades de dominio.
El dominio nunca conoce los modelos SQLAlchemy; los mappers son
la frontera entre infraestructura y dominio.
"""
from app.domain.entities.asiento import Asiento
from app.domain.entities.pago import Pago
from app.domain.entities.reserva import Reserva, ReservaVuelo
from app.domain.entities.vuelo_instancia import VueloInstancia
from infrastructure.models.asiento import AsientoModel
from infrastructure.models.pago import PagoModel
from infrastructure.models.reserva import ReservaModel
from infrastructure.models.reserva_vuelo import ReservaVueloModel
from infrastructure.models.vuelo_instancia import VueloInstanciaModel


def vuelo_instancia_to_entity(m: VueloInstanciaModel) -> VueloInstancia:
    return VueloInstancia(
        vuelo_instancia_id=m.vuelo_instancia_id,
        vuelo_programado_id=m.vuelo_programado_id,
        aeronave_id=m.aeronave_id,
        fecha_salida=m.fecha_salida,
        fecha_llegada=m.fecha_llegada,
        asientos_disponibles=m.asientos_disponibles,
    )


def asiento_to_entity(m: AsientoModel) -> Asiento:
    return Asiento(
        asiento_id=m.asiento_id,
        vuelo_instancia_id=m.vuelo_instancia_id,
        numero_asiento=m.numero_asiento,
        clase=m.clase,
        esta_disponible=m.esta_disponible,
        version=m.version,
        bloqueado_hasta=m.bloqueado_hasta,
    )


def reserva_vuelo_to_entity(m: ReservaVueloModel) -> ReservaVuelo:
    return ReservaVuelo(
        reserva_vuelo_id=m.reserva_vuelo_id,
        reserva_id=m.reserva_id,
        vuelo_instancia_id=m.vuelo_instancia_id,
        monto_tarifa=m.monto_tarifa,
        numero_boleto=m.numero_boleto,
    )


def reserva_to_entity(m: ReservaModel) -> Reserva:
    vuelos = [reserva_vuelo_to_entity(rv) for rv in (m.vuelos or [])]
    return Reserva(
        reserva_id=m.reserva_id,
        pasajero_id=m.pasajero_id,
        estado=m.estado,
        monto_total=m.monto_total,
        fecha_reserva=m.fecha_reserva,
        vuelos=vuelos,
        gestionada_por_usuario=m.gestionada_por_usuario,
    )


def pago_to_entity(m: PagoModel) -> Pago:
    return Pago(
        pago_id=m.pago_id,
        reserva_id=m.reserva_id,
        monto=m.monto,
        estado=m.estado,
        fecha_pago=m.fecha_pago,
        id_transaccion=m.id_transaccion,
    )
