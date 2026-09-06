from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Asiento:
    """
    Mutable: su estado cambia durante el ciclo de reserva.

    Mecanismo de concurrencia dual (RNF-004, RNF-006):
    - bloqueado_hasta: bloqueo temporal de 10 min durante el pago.
      Permite que el usuario complete el pago sin perder el asiento,
      sin mantener un lock de BD abierto durante la llamada a la pasarela.
    - version: optimistic locking. El UPDATE en BD incluye
      WHERE version = :version_leida, garantizando que si otro request
      modificó el asiento entre la lectura y la escritura, la operación
      falla (0 filas actualizadas) y se retorna HTTP 409.
    """
    asiento_id: UUID
    vuelo_instancia_id: UUID
    numero_asiento: str   # p.ej. "12A"
    clase: str            # 'economy' | 'business'
    esta_disponible: bool
    version: int
    bloqueado_hasta: datetime | None = None

    def esta_bloqueado(self, ahora: datetime) -> bool:
        """Retorna True si el bloqueo temporal sigue vigente."""
        if self.bloqueado_hasta is None:
            return False
        return ahora < self.bloqueado_hasta

    def esta_ocupado(self, ahora: datetime) -> bool:
        """
        Un asiento no está disponible para una nueva reserva si:
        - ya fue confirmado (esta_disponible=False), o
        - está en bloqueo temporal activo de otro usuario.
        """
        return not self.esta_disponible or self.esta_bloqueado(ahora)
