import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from adapters.inbound.api.exception_handlers import register_exception_handlers
from adapters.inbound.api.routes.reservas_router import router as reservas_router
from adapters.inbound.api.routes.vuelos_router import router as vuelos_router
from adapters.inbound.api.routes.harness_router import router as harness_router

app = FastAPI(
    title="Gestión de Vuelos API",
    description=(
        "Backend del sistema de reservas de aerolínea regional. "
        "Arquitectura hexagonal sobre Aurora PostgreSQL. "
        "Implementa optimistic locking + bloqueo temporal para prevenir sobreventa (RNF-004/RNF-006)."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejadores globales de excepciones de dominio
register_exception_handlers(app)

# Routers primer parcial (se mantienen)
app.include_router(vuelos_router, prefix="/api/v1")
app.include_router(reservas_router, prefix="/api/v1")

# Routers segundo parcial — contratos exactos del Appendix A
app.include_router(harness_router)


# ------------------------------------------------------------------ #
# Frontend Web (Requisitos R8 y R9)                                  #
# ------------------------------------------------------------------ #

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static-frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="static-frontend")


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def serve_customer_page():
    """Vista Cliente (R8) - Búsqueda y Reserva."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h2>Frontend no encontrado</h2>", status_code=404)


@app.get("/manager", response_class=HTMLResponse, tags=["Frontend"])
def serve_manager_page():
    """Vista Gerencial (R9) - Panel de Ocupación con Athena."""
    manager_file = FRONTEND_DIR / "manager.html"
    if manager_file.exists():
        return FileResponse(manager_file)
    return HTMLResponse("<h2>Panel Gerencial no encontrado</h2>", status_code=404)


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de salud para ALB / monitoreo."""
    return {"status": "ok"}
