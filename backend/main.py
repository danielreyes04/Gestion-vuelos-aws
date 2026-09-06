from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.api.exception_handlers import register_exception_handlers
from adapters.inbound.api.routes.reservas_router import router as reservas_router
from adapters.inbound.api.routes.vuelos_router import router as vuelos_router

app = FastAPI(
    title="Gestión de Vuelos API",
    description=(
        "Backend del sistema de reservas de aerolínea regional. "
        "Arquitectura hexagonal sobre Aurora PostgreSQL. "
        "Implementa optimistic locking + bloqueo temporal para prevenir sobreventa (RNF-004/RNF-006)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — ajustar origins en producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejadores globales de excepciones de dominio
register_exception_handlers(app)

# Routers
app.include_router(vuelos_router, prefix="/api/v1")
app.include_router(reservas_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de salud para ALB / monitoreo."""
    return {"status": "ok"}
