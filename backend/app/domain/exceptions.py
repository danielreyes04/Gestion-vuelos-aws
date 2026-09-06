"""
Excepciones de dominio.
Los adaptadores inbound (routers FastAPI) las capturan y las
traducen al código HTTP correspondiente.
"""


class DomainError(Exception):
    """Base para todas las excepciones del dominio."""


class SeatUnavailableError(DomainError):
    """
    El asiento ya fue tomado por otro usuario concurrente.
    → HTTP 409 Conflict (RNF-004 / RNF-005)
    """


class ReservaNotFoundError(DomainError):
    """La reserva solicitada no existe. → HTTP 404"""


class ModificacionNoPermitidaError(DomainError):
    """
    Intento de modificar/cancelar dentro de las 8 horas previas
    al vuelo. → HTTP 422 Unprocessable Entity (FR-005.2)
    """


class TarifaNoEncontradaError(DomainError):
    """No existe regla de tarifa aplicable para la combinación
    clase / días de anticipación. → HTTP 422"""


class PagoInvalidoError(DomainError):
    """El pago no corresponde al monto esperado o ya fue procesado.
    → HTTP 422"""


class VueloNoEncontradoError(DomainError):
    """La instancia de vuelo solicitada no existe. → HTTP 404"""
