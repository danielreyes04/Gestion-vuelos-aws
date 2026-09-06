from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from adapters.inbound.api.schemas.vuelo_schemas import (
    AsientoResponse,
    BuscarVuelosRequest,
    VueloInstanciaResponse,
)
from adapters.outbound.persistence.dependencies import (
    get_buscar_vuelos_uc,
    get_obtener_asientos_uc,
)
from app.application.use_cases.buscar_vuelos import BuscarVuelosInput, BuscarVuelosUseCase
from app.application.use_cases.obtener_asientos import (
    ObtenerAsientosInput,
    ObtenerAsientosUseCase,
)
from app.domain.exceptions import VueloNoEncontradoError

router = APIRouter(prefix="/vuelos", tags=["Vuelos"])


@router.get(
    "/disponibles",
    response_model=list[VueloInstanciaResponse],
    status_code=status.HTTP_200_OK,
    summary="Buscar vuelos disponibles",
    description=(
        "Retorna las instancias de vuelo disponibles para la ruta, fecha "
        "y número de pasajeros indicados. "
        "Tiempo de respuesta objetivo < 2 s (RNF-001)."
    ),
)
def buscar_vuelos(
    origen: str = Query(..., min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
    destino: str = Query(..., min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    num_pasajeros: int = Query(default=1, ge=1, le=9),
    uc: BuscarVuelosUseCase = Depends(get_buscar_vuelos_uc),
) -> list[VueloInstanciaResponse]:
    from datetime import date
    fecha_date = date.fromisoformat(fecha)

    instancias = uc.execute(
        BuscarVuelosInput(
            origen_codigo=origen.upper(),
            destino_codigo=destino.upper(),
            fecha=fecha_date,
            num_pasajeros=num_pasajeros,
        )
    )
    return [
        VueloInstanciaResponse(
            vuelo_instancia_id=i.vuelo_instancia_id,
            vuelo_programado_id=i.vuelo_programado_id,
            fecha_salida=i.fecha_salida,
            fecha_llegada=i.fecha_llegada,
            asientos_disponibles=i.asientos_disponibles,
        )
        for i in instancias
    ]


@router.get(
    "/{vuelo_instancia_id}/asientos",
    response_model=list[AsientoResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtener asientos disponibles de un vuelo",
    description=(
        "Lista los asientos libres y sin bloqueo temporal vigente "
        "para el vuelo indicado (FR-004.1). "
        "Notificación de asiento no disponible en < 2 s (RNF-003)."
    ),
    responses={404: {"description": "Instancia de vuelo no encontrada"}},
)
def obtener_asientos(
    vuelo_instancia_id: UUID,
    uc: ObtenerAsientosUseCase = Depends(get_obtener_asientos_uc),
) -> list[AsientoResponse]:
    from fastapi import HTTPException
    try:
        asientos = uc.execute(ObtenerAsientosInput(vuelo_instancia_id=vuelo_instancia_id))
    except VueloNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return [
        AsientoResponse(
            asiento_id=a.asiento_id,
            numero_asiento=a.numero_asiento,
            clase=a.clase,
            esta_disponible=a.esta_disponible,
            bloqueado_hasta=a.bloqueado_hasta,
        )
        for a in asientos
    ]
