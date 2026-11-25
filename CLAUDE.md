# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repo

API REST de reservas de vuelos (FastAPI + SQLAlchemy + Aurora PostgreSQL) más un harness de pruebas del "segundo parcial" (`parcial2-harness/`) que califica backend, pipeline de datos en AWS (EMR/Glue/Athena), frontend y costos. Código y dominio están en español. Hay dos "generaciones" de API conviviendo en el mismo backend (ver abajo).

## Comandos

Todo el backend se corre desde `backend/` (los imports son absolutos desde esa carpeta: `adapters.*`, `app.*`, `infrastructure.*`).

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env                              # configurar DB_* y demás
uvicorn main:app --reload                           # http://127.0.0.1:8000 (/docs, /redoc, /health)
```

- BD: no hay migraciones (ni Alembic ni `create_all`). El esquema/datos se cargan a mano con `psql -f backend/seed_data.sql` y `backend/create_harness_tables.sql` (tablas `flight` y `reservation` del parcial 2).
- Backend: **no hay tests ni linter configurados**.
- Harness (`parcial2-harness/`, separado, con su propio `requirements.txt`):
  ```bash
  pip install -r requirements.txt && playwright install chromium
  cp config.example.yaml config.yaml                # seed, URLs, base/tablas Athena (config.yaml puede tener datos del equipo: no commitear)
  python -m airline_data.generate --seed <SEED> --rows 2000000 --out raw/
  pytest                                            # escribe report.json y report.md
  pytest tests/test_backend.py -k <nombre>          # un solo test
  ```
  No editar `thresholds.yaml`, `harness/` ni `tests/` (el instructor usa su copia). Los contratos exactos están en `parcial2-harness/contract/` (`API.md`, `DATA.md`, `FRONTEND.md`, `COST_PROJECTION.md`). Cada test lleva `@pytest.mark.req("R#")` (R1–R12) y conftest agrega el puntaje.

## Arquitectura (hexagonal)

Flujo de una petición: `router → UseCase → Service (dominio) → Repository (adapter) → Session SQLAlchemy`.

- `app/domain/`: entidades (dataclasses, sin ORM), `exceptions.py`, **puertos** (`ports/inbound` = interfaces de servicios, `ports/outbound` = interfaces de repositorios) y `services/` con la lógica de negocio (`ReservaService`, `VueloService`).
- `app/application/use_cases/`: un caso de uso por operación; delgados, solo delegan al servicio.
- `adapters/inbound/api/`: routers FastAPI, schemas Pydantic y `exception_handlers.py` (mapea excepciones de dominio a HTTP: p. ej. `SeatUnavailableError` → 409).
- `adapters/outbound/persistence/`: repositorios SQLAlchemy que implementan los puertos; `mappers.py` convierte modelo ORM ↔ entidad de dominio.
- `adapters/outbound/persistence/dependencies.py`: **único lugar donde se cablea todo** (cadena de `Depends`). Para añadir un caso de uso: puerto → servicio → use case → dependencia aquí → router.
- `infrastructure/`: `config.py` (pydantic-settings; lee `.env` de `backend/`, raíz del repo o cwd), `database.py` (engine, `get_db`, `Base`), `models/` (ORM).
- `main.py` monta routers, CORS (`*`), handlers de excepciones y sirve `frontend/index.html` (`/`) y `frontend/manager.html` (`/manager`) como estáticos.

### Dos APIs en un mismo backend

1. **Parcial 1** (`/api/v1/vuelos`, `/api/v1/reservas`): modelo completo en español (VueloInstancia, Asiento, Reserva, Pago, auditoría, tarifas) con arquitectura hexagonal.
2. **Parcial 2** (`/admin/flights`, `/flights/search`, `/reservations`, `/analytics/occupancy`): contrato exacto que verifica el harness. Vive en `routes/harness_router.py` (incluye `analytics_router.py`), **no usa hexagonal**: accede directo a `infrastructure/models/flight.py` y `reservation.py` (tablas `flight`/`reservation`, distintas de las del parcial 1). Respetar el contrato de `contract/API.md`; nunca devolver 5xx bajo concurrencia ("sin cupo" = 409).

### Concurrencia (parte crítica)

- Parcial 1: doble mecanismo en `Asiento` — bloqueo temporal (`bloqueado_hasta`, `SEAT_LOCK_TIMEOUT_SECONDS`=600) + optimistic locking (`version`, `UPDATE ... WHERE version = :v`, `rowcount == 1`). `ReservaService.crear_reserva` reintenta hasta `MAX_RETRIES=3`. Reserva nace `pending_payment`; `confirmar_pago` la pasa a `confirmed`; cancelar se prohíbe <8 h antes de la salida. Cada cambio registra auditoría en la misma transacción.
- Parcial 2: `UPDATE flight SET seats_available = seats_available - 1 WHERE seats_available > 0`; `rowcount == 0` → rollback y 409 (K=150 requests simultáneos).
- `database.py` usa pool 50 + overflow 120 por esa carga; Aurora `db.t3.micro` soporta ~85 conexiones (el comentario sugiere bajar a 30+60 si falla).

### Analytics (R7)

`/analytics/occupancy` consulta Athena (`route_month_metrics`) con `boto3` (start_query_execution + polling con timeout de 9 s → 504). Config `ATHENA_*`/`AWS_REGION` en `settings`. Debe ir realmente a Athena (el harness inspecciona el historial de queries).

## Problemas conocidos del código (verificados al leer)

- `ReservaService.confirmar_pago` llama `obtener_asiento_por_id(tramo.vuelo_instancia_id)`: pasa un id de vuelo donde se espera un id de asiento, así que devuelve `None` y el bloque `if asiento:` se omite → los asientos nunca se confirman ni se decrementa `asientos_disponibles`. Falta resolver el asiento vía `reserva_asiento`.
- En `crear_reserva`, `vuelo_programado = obtener_instancia_por_id(...)` es una consulta redundante sin uso.
- `analytics_router.py` interpola `route`/`month` en SQL con escape manual de comillas (preferir validar con regex `^[A-Z]{3}-[A-Z]{3}$` / `^\d{4}-\d{2}$`) y crea el cliente boto3 al importar el módulo.
- `README.md` menciona `.env.example` y `SECRET_KEY`; CORS `allow_origins=["*"]` está pendiente de restringir antes de producción.
- Convive `infrastructure/models/reserva.py` (parcial 1) con `reservation.py` (parcial 2); no confundirlos.
