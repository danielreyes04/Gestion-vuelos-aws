"""
Publicación de eventos a Amazon Kinesis (Parcial 3 — R1, R2).

Diseño:
- `publish()` solo encola en memoria (O(1), nunca bloquea ni lanza): publicar no
  debe frenar la API (R2). Un hilo en segundo plano agrupa los eventos y los envía
  con `put_records` (hasta 500 por llamada).
- Si la cola se llena o Kinesis falla tras los reintentos, el evento se descarta y se
  registra en el log. Aceptable para búsquedas; para reservas, en producción habría
  que usar un patrón outbox (ver documento, sección 5).
- Los eventos NUNCA llevan datos personales (sin passenger_name).
"""
import json
import logging
import queue
import threading
import time
import uuid
from datetime import datetime, timezone

import boto3

from infrastructure.config import settings

log = logging.getLogger("events")

SCHEMA_VERSION = 1
_BATCH_MAX = 500          # límite de put_records
_BATCH_WAIT_SECONDS = 0.2  # cuánto esperar para completar un lote
_MAX_ATTEMPTS = 3


def _now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ #
# Constructores de eventos (contrato: contract/EVENTS.md)              #
# ------------------------------------------------------------------ #

def build_search_event(
    session_id: str, origin: str, destination: str, travel_date: str, results_count: int
) -> tuple[str, dict]:
    """Devuelve (partition_key, evento). Partition key = session_id."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "search_performed",
        "event_ts": _now_ts(),
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "origin": origin,
        "destination": destination,
        "travel_date": travel_date,
        "results_count": int(results_count),
    }
    return session_id, event


def build_reservation_event(
    event_type: str,
    reservation_id: str,
    flight_id: str,
    route: str,
    flight_date: str,
    fare_class: str,
    price_cents: int,
) -> tuple[str, dict]:
    """event_type: 'reservation_created' | 'reservation_cancelled'. Partition key = flight_id."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_ts": _now_ts(),
        "schema_version": SCHEMA_VERSION,
        "reservation_id": reservation_id,
        "flight_id": flight_id,
        "route": route,
        "flight_date": flight_date,
        "fare_class": fare_class.upper(),
        "price_cents": int(price_cents),
    }
    return flight_id, event


# ------------------------------------------------------------------ #
# Publicador asíncrono                                                 #
# ------------------------------------------------------------------ #

class EventPublisher:
    def __init__(self, stream_name: str, region: str, enabled: bool = True) -> None:
        self._stream = stream_name
        self._region = region
        self._enabled = enabled
        self._queue: queue.Queue = queue.Queue(maxsize=20000)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._client = None

    def start(self) -> None:
        if not self._enabled or self._thread:
            return
        self._client = boto3.client("kinesis", region_name=self._region)
        self._thread = threading.Thread(target=self._run, name="event-publisher", daemon=True)
        self._thread.start()
        log.info("EventPublisher iniciado (stream=%s)", self._stream)

    def stop(self) -> None:
        """Vacía lo pendiente (máx. ~5 s) y detiene el hilo."""
        if not self._thread:
            return
        deadline = time.time() + 5
        while not self._queue.empty() and time.time() < deadline:
            time.sleep(0.05)
        self._stop.set()
        self._thread.join(timeout=3)
        self._thread = None

    def publish(self, partition_key: str, event: dict) -> None:
        """No bloquea y no lanza excepciones hacia el endpoint."""
        if not self._enabled:
            return
        try:
            self._queue.put_nowait((partition_key, event))
        except queue.Full:
            log.warning("Cola de eventos llena: se descarta %s", event.get("event_id"))

    # -- hilo de envío ------------------------------------------------ #

    def _run(self) -> None:
        while not self._stop.is_set():
            batch = self._next_batch()
            if batch:
                self._send(batch)

    def _next_batch(self) -> list[tuple[str, dict]]:
        try:
            batch = [self._queue.get(timeout=0.5)]
        except queue.Empty:
            return []
        deadline = time.time() + _BATCH_WAIT_SECONDS
        while len(batch) < _BATCH_MAX:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                batch.append(self._queue.get(timeout=remaining))
            except queue.Empty:
                break
        return batch

    def _send(self, batch: list[tuple[str, dict]]) -> None:
        pending = batch
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            records = [
                {"Data": (json.dumps(ev, separators=(",", ":")) + "\n").encode("utf-8"), "PartitionKey": pk}
                for pk, ev in pending
            ]
            try:
                resp = self._client.put_records(StreamName=self._stream, Records=records)
                if resp.get("FailedRecordCount", 0) == 0:
                    return
                # Reintenta solo los registros rechazados (p. ej. throttling del shard)
                pending = [p for p, r in zip(pending, resp["Records"]) if "ErrorCode" in r]
            except Exception as exc:  # noqa: BLE001 — nunca debe tumbar el hilo
                log.warning("put_records falló (intento %d): %s", attempt, exc)
            time.sleep(0.2 * attempt)
        log.error("Se perdieron %d eventos tras %d intentos", len(pending), _MAX_ATTEMPTS)


publisher = EventPublisher(
    settings.KINESIS_STREAM_NAME, settings.AWS_REGION, enabled=settings.EVENTS_ENABLED
)
