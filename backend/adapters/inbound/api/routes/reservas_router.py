from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.inbound.api.schemas.reserva_schemas import (
    CancelarReservaRequest,
    ConfirmarPagoRequest,
    CrearReservaRequest,
    ErrorResponse,
    ReservaResponse,
    ReservaVueloResponse,
)
from adapters.outbound.persistence.dependencies import (
    get_cancelar_reserva_uc,
    get_confirmar_pago_uc,
    get_crear_reserva_uc,
    get_obtener_reserva_uc,
)
from app.application.use_cases.cancelar_reserva import (
    CancelarReservaInput,
    CancelarReservaUseCase,
)
from app.application.use_cases.confirmar_pago import (
    ConfirmarPagoInput,
    ConfirmarPagoUseCase,
)
from app.application.use_cases.crear_reserva import CrearReservaInput, CrearReservaUseCase
from app.application.use_cases.obtener_reserva import (
    ObtenerReservaInput,
    ObtenerReservaUseCase,
)
from app.domain.exceptions import (
    ModificacionNoPermitidaError,
    PagoInvalidoError,
    ReservaNotFoundError,
    SeatUnavailableError,
    TarifaNoEncontradaError,
    VueloNoEncontradoError,
)
from infrastructure.database import get_db

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def _reserva_response(reserva) -> ReservaResponse:
    return ReservaResponse(
        reserva_id=reserva.reserva_id,
        pasajero_id=reserva.pasajero_id,
        estado=reserva.estado,
        monto_total=reserva.monto_total,
        fecha_reserva=reserva.fecha_reserva,
        vuelos=[
            ReservaVueloResponse(
                reserva_vuelo_id=v.reserva_vuelo_id,
                vuelo_instancia_id=v.vuelo_instancia_id,
                monto_tarifa=v.monto_tarifa,
                numero_boleto=v.numero_boleto,
            )
            for v in reserva.vuelos
        ],
    )


@router.post(
    "/",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva con bloqueo temporal de asientos",
    description=(
        "Crea una reserva en estado 'pending_payment' y bloquea cada asiento "
        "durante 10 minutos mientras el pasajero completa el pago (RNF-006). "
        "Implementa optimistic locking: si dos usuarios solicitan el mismo asiento "
        "simultáneamente, el segundo recibe HTTP 409 (RNF-004 / RNF-005). "
        "Soporta itinerarios multi-tramo en una sola transacción (sección 5.3)."
    ),
    responses={
        409: {"model": ErrorResponse, "description": "Asiento tomado por otro usuario"},
        404: {"model": ErrorResponse, "description": "Vuelo o asiento no encontrado"},
        422: {"model": ErrorResponse, "description": "Tarifa no disponible para la clase/anticipación"},
    },
)
def crear_reserva(
    body: CrearReservaRequest,
    uc: CrearReservaUseCase = Depends(get_crear_reserva_uc),
    db: Session = Depends(get_db),
) -> ReservaResponse:
    try:
        reserva = uc.execute(
            CrearReservaInput(
                pasajero_id=body.pasajero_id,
                tramos=[(t.vuelo_instancia_id, t.asiento_id, t.clase) for t in body.tramos],
                gestionada_por_usuario_id=body.gestionada_por_usuario_id,
                agencia_id=body.agencia_id,
            )
        )
        db.commit()
        return _reserva_response(reserva)

    except SeatUnavailableError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except VueloNoEncontradoError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TarifaNoEncontradaError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{reserva_id}",
    response_model=ReservaResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar reserva por ID",
    description="Retorna el detalle completo de una reserva y sus tramos (RF-001).",
    responses={404: {"model": ErrorResponse, "description": "Reserva no encontrada"}},
)
def obtener_reserva(
    reserva_id: UUID,
    uc: ObtenerReservaUseCase = Depends(get_obtener_reserva_uc),
) -> ReservaResponse:
    try:
        reserva = uc.execute(ObtenerReservaInput(reserva_id=reserva_id))
        return _reserva_response(reserva)
    except ReservaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{reserva_id}/pago",
    response_model=ReservaResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar pago de una reserva",
    description=(
        "Recibe el token de la pasarela PCI DSS y confirma la reserva. "
        "Marca los asientos como ocupados y decrementa disponibilidad "
        "de forma atómica (FR-004.3 / FR-004.4). "
        "El sistema nunca almacena datos de tarjeta (RNF-008)."
    ),
    responses={
        409: {"model": ErrorResponse, "description": "Conflicto de concurrencia al confirmar asiento"},
        422: {"model": ErrorResponse, "description": "Monto incorrecto o reserva en estado inválido"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"},
    },
)
def confirmar_pago(
    reserva_id: UUID,
    body: ConfirmarPagoRequest,
    uc: ConfirmarPagoUseCase = Depends(get_confirmar_pago_uc),
    db: Session = Depends(get_db),
) -> ReservaResponse:
    try:
        reserva = uc.execute(
            ConfirmarPagoInput(
                reserva_id=reserva_id,
                id_transaccion=body.id_transaccion,
                monto=body.monto,
            )
        )
        db.commit()
        return _reserva_response(reserva)

    except ReservaNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SeatUnavailableError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PagoInvalidoError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        db.rollback()
        raise


@router.delete(
    "/{reserva_id}",
    response_model=ReservaResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancelar reserva",
    description=(
        "Cancela la reserva si faltan más de 8 horas para el vuelo (FR-005.2). "
        "Registra la cancelación en auditoría con actor y timestamp (FR-005.4 / RNF-010)."
    ),
    responses={
        422: {"model": ErrorResponse, "description": "Cancelación fuera de plazo (< 8 h antes del vuelo)"},
        404: {"model": ErrorResponse, "description": "Reserva no encontrada"},
    },
)
def cancelar_reserva(
    reserva_id: UUID,
    body: CancelarReservaRequest,
    uc: CancelarReservaUseCase = Depends(get_cancelar_reserva_uc),
    db: Session = Depends(get_db),
) -> ReservaResponse:
    try:
        reserva = uc.execute(
            CancelarReservaInput(
                reserva_id=reserva_id,
                usuario_id=body.usuario_id,
            )
        )
        db.commit()
        return _reserva_response(reserva)

    except ReservaNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ModificacionNoPermitidaError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        db.rollback()
        raise
