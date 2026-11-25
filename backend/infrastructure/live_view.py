"""
Vista en vivo (Parcial 3 — R3): consumidor del stream de Kinesis que mantiene
contadores en memoria y responde GET /analytics/live en segundos.

- Lee el stream con get_records (no usa Athena ni S3).
- Cuenta por `event_ts` (cuándo ocurrió), no por la hora de llegada: los eventos
  viejos de un replay quedan fuera de la ventana.
- Deduplica por event_id (Kinesis es at-least-once y el replay trae duplicados).
- Estado en memoria => el backend debe correr con UN solo worker de uvicorn.
- Arranca en LATEST: solo cuenta lo publicado desde que inició el backend.
"""
import json
import logging
import threading
import time
from calendar import timegm
from datetime import datetime

import boto3

from infrastructure.config import settings

log = logging.getLogger("live_view")

_RETENTION_SECONDS = 3600     # se conserva 1 h de eventos (ventana máx. = 60 min)
_POLL_SECONDS = 0.3           # get_records admite 5 llamadas/s por shard
_COUNTED = {
    "search_performed": 0,
    "reservation_created": 1,
    "reservation_cancelled": 2,
}


def _parse_ts(ts: str) -> int | None:
    try:
        return timegm(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").timetuple())
    except (ValueError, TypeError):
        return None


class LiveView:
    def __init__(self, stream_name: str, region: str, enabled: bool = True) -> None:
        self._stream = stream_name
        self._region = region
        self._enabled = enabled
        self._lock = threading.Lock()
        self._buckets: dict[int, list[int]] = {}   # segundo (event_ts) -> [búsquedas, reservas, cancelaciones]
        self._seen: dict[str, int] = {}            # event_id -> segundo del evento
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # -- ciclo de vida ------------------------------------------------ #

    def start(self) -> None:
        if not self._enabled or self._thread:
            return
        self._thread = threading.Thread(target=self._run, name="live-view", daemon=True)
        self._thread.start()
        log.info("LiveView iniciado (stream=%s)", self._stream)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    # -- consulta ----------------------------------------------------- #

    def snapshot(self, window_minutes: int) -> dict:
        since = int(time.time()) - window_minutes * 60
        s = r = c = 0
        with self._lock:
            for sec, (bs, br, bc) in self._buckets.items():
                if sec >= since:
                    s += bs
                    r += br
                    c += bc
        return {
            "window_minutes": window_minutes,
            "searches": s,
            "reservations": r,
            "cancellations": c,
            "conversion": (r / s) if s else 0.0,
        }

    # -- consumo ------------------------------------------------------ #

    def _ingest(self, raw: bytes) -> None:
        # Un registro puede traer varios JSON concatenados/por línea.
        for line in raw.decode("utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                idx = _COUNTED.get(ev.get("event_type"))
                eid = ev.get("event_id")
                sec = _parse_ts(ev.get("event_ts"))
            except (ValueError, AttributeError):
                continue
            if idx is None or not eid or sec is None:
                continue
            if sec < time.time() - _RETENTION_SECONDS:
                continue   # evento viejo (replay): fuera de cualquier ventana
            with self._lock:
                if eid in self._seen:
                    continue
                self._seen[eid] = sec
                self._buckets.setdefault(sec, [0, 0, 0])[idx] += 1

    def _prune(self) -> None:
        limit = time.time() - _RETENTION_SECONDS
        with self._lock:
            for sec in [s for s in self._buckets if s < limit]:
                del self._buckets[sec]
            for eid in [e for e, s in self._seen.items() if s < limit]:
                del self._seen[eid]

    def _open_iterators(self, client) -> dict[str, str]:
        shards = client.list_shards(StreamName=self._stream)["Shards"]
        its = {}
        for sh in shards:
            if "EndingSequenceNumber" in sh["SequenceNumberRange"]:
                continue   # shard cerrado
            its[sh["ShardId"]] = client.get_shard_iterator(
                StreamName=self._stream, ShardId=sh["ShardId"], ShardIteratorType="LATEST"
            )["ShardIterator"]
        return its

    def _run(self) -> None:
        client = boto3.client("kinesis", region_name=self._region)
        iterators: dict[str, str] = {}
        last_prune = time.time()
        while not self._stop.is_set():
            try:
                if not iterators:
                    iterators = self._open_iterators(client)
                    if not iterators:
                        time.sleep(2)
                        continue
                for shard_id in list(iterators):
                    resp = client.get_records(ShardIterator=iterators[shard_id], Limit=1000)
                    for rec in resp["Records"]:
                        self._ingest(rec["Data"])
                    nxt = resp.get("NextShardIterator")
                    if nxt:
                        iterators[shard_id] = nxt
                    else:
                        del iterators[shard_id]
                if time.time() - last_prune > 60:
                    self._prune()
                    last_prune = time.time()
                time.sleep(_POLL_SECONDS)
            except Exception as exc:  # noqa: BLE001 — stream aún no existe, iterador vencido, etc.
                log.warning("LiveView: %s; reintentando en 2 s", exc)
                iterators = {}   # reabrir iteradores (LATEST) tras el error
                time.sleep(2)


live_view = LiveView(
    settings.KINESIS_STREAM_NAME, settings.AWS_REGION, enabled=settings.EVENTS_ENABLED
)
