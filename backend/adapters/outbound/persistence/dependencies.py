"""
Contenedor de dependencias para FastAPI.

Este módulo es el único lugar donde se ensamblan las capas:
    Router → UseCase → Service → Repository → DB session

Cada función es una FastAPI dependency que recibe la sesión de BD
y construye el grafo de objetos completo. Los routers solo dependen
de los use cases, nunca de repositorios o servicios directamente.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from adapters.outbound.persistence.reserva_repository import ReservaRepository
from adapters.outbound.persistence.tarifa_repository import TarifaRepository
from adapters.outbound.persistence.vuelo_repository import VueloRepository
from app.application.use_cases.buscar_vuelos import BuscarVuelosUseCase
from app.application.use_cases.cancelar_reserva import CancelarReservaUseCase
from app.application.use_cases.confirmar_pago import ConfirmarPagoUseCase
from app.application.use_cases.crear_reserva import CrearReservaUseCase
from app.application.use_cases.obtener_asientos import ObtenerAsientosUseCase
from app.application.use_cases.obtener_reserva import ObtenerReservaUseCase
from app.domain.services.reserva_service import ReservaService
from app.domain.services.vuelo_service import VueloService
from infrastructure.database import get_db


# ------------------------------------------------------------------ #
# Repositorios                                                         #
# ------------------------------------------------------------------ #

def get_vuelo_repo(db: Session = Depends(get_db)) -> VueloRepository:
    return VueloRepository(db)


def get_reserva_repo(db: Session = Depends(get_db)) -> ReservaRepository:
    return ReservaRepository(db)


def get_tarifa_repo(db: Session = Depends(get_db)) -> TarifaRepository:
    return TarifaRepository(db)


# ------------------------------------------------------------------ #
# Servicios de dominio                                                 #
# ------------------------------------------------------------------ #

def get_vuelo_service(
    vuelo_repo: VueloRepository = Depends(get_vuelo_repo),
) -> VueloService:
    return VueloService(vuelo_repo)


def get_reserva_service(
    reserva_repo: ReservaRepository = Depends(get_reserva_repo),
    vuelo_repo: VueloRepository = Depends(get_vuelo_repo),
    tarifa_repo: TarifaRepository = Depends(get_tarifa_repo),
) -> ReservaService:
    return ReservaService(reserva_repo, vuelo_repo, tarifa_repo)


# ------------------------------------------------------------------ #
# Casos de uso                                                         #
# ------------------------------------------------------------------ #

def get_buscar_vuelos_uc(
    service: VueloService = Depends(get_vuelo_service),
) -> BuscarVuelosUseCase:
    return BuscarVuelosUseCase(service)


def get_obtener_asientos_uc(
    service: VueloService = Depends(get_vuelo_service),
) -> ObtenerAsientosUseCase:
    return ObtenerAsientosUseCase(service)


def get_crear_reserva_uc(
    service: ReservaService = Depends(get_reserva_service),
) -> CrearReservaUseCase:
    return CrearReservaUseCase(service)


def get_confirmar_pago_uc(
    service: ReservaService = Depends(get_reserva_service),
) -> ConfirmarPagoUseCase:
    return ConfirmarPagoUseCase(service)


def get_obtener_reserva_uc(
    service: ReservaService = Depends(get_reserva_service),
) -> ObtenerReservaUseCase:
    return ObtenerReservaUseCase(service)


def get_cancelar_reserva_uc(
    service: ReservaService = Depends(get_reserva_service),
) -> CancelarReservaUseCase:
    return CancelarReservaUseCase(service)
