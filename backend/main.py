from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de salud para ALB / monitoreo."""
    return {"status": "ok"}
