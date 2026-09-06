from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class Pago:
    """
    El sistema nunca almacena datos de tarjeta.
    id_transaccion es el token retornado por la pasarela PCI DSS (RNF-008).
    """
    pago_id: UUID
    reserva_id: UUID
    monto: Decimal
    estado: str                     # 'pending' | 'approved' | 'rejected' | 'refunded'
    fecha_pago: datetime | None = None
    id_transaccion: str | None = None   # token de la pasarela, nunca número de tarjeta

    def esta_aprobado(self) -> bool:
        return self.estado == "approved"
