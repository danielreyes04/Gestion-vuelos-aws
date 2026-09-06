"""
Manejadores globales de excepciones registrados en la app FastAPI.
Traducen excepciones de dominio a respuestas HTTP estándar,
evitando que cada router repita el mismo try/except.
"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    DomainError,
    ModificacionNoPermitidaError,
    PagoInvalidoError,
    ReservaNotFoundError,
    SeatUnavailableError,
    TarifaNoEncontradaError,
    VueloNoEncontradoError,
)

# Mapa excepción → código HTTP
_EXCEPTION_STATUS_MAP = {
    SeatUnavailableError: 409,
    ReservaNotFoundError: 404,
    VueloNoEncontradoError: 404,
    ModificacionNoPermitidaError: 422,
    TarifaNoEncontradaError: 422,
    PagoInvalidoError: 422,
}


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    status_code = _EXCEPTION_STATUS_MAP.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app) -> None:
    """Registra todos los manejadores en la instancia FastAPI."""
    app.add_exception_handler(DomainError, domain_exception_handler)
