from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

# Ventana mínima antes del vuelo para permitir cancelaciones/modificaciones (FR-005.2)
VENTANA_MINIMA_HORAS = 8


@dataclass(frozen=True)
class ReservaVuelo:
    """Un tramo dentro de una reserva multi-leg."""
    reserva_vuelo_id: UUID
    reserva_id: UUID
    vuelo_instancia_id: UUID
    monto_tarifa: Decimal
    numero_boleto: str | None = None


@dataclass
class Reserva:
    """
    Agregado raíz del dominio.
    Contiene toda la lógica de negocio relacionada con el ciclo de vida
    de una reserva: creación, modificación y cancelación.
    """
    reserva_id: UUID
    pasajero_id: UUID
    estado: str                    # 'pending_payment' | 'confirmed' | 'cancelled' | 'modified'
    monto_total: Decimal
    fecha_reserva: datetime
    vuelos: list[ReservaVuelo] = field(default_factory=list)
    gestionada_por_usuario: UUID | None = None

    # ------------------------------------------------------------------ #
    # Reglas de negocio                                                    #
    # ------------------------------------------------------------------ #

    def puede_modificarse(self, fecha_salida_primer_vuelo: datetime, ahora: datetime) -> bool:
        """
        FR-005.2: no se puede modificar en las 8 horas previas al vuelo.
        """
        if self.estado in ("cancelled",):
            return False
        limite = fecha_salida_primer_vuelo - timedelta(hours=VENTANA_MINIMA_HORAS)
        return ahora < limite

    def puede_cancelarse(self, fecha_salida_primer_vuelo: datetime, ahora: datetime) -> bool:
        """Misma regla que modificación (FR-005.2)."""
        return self.puede_modificarse(fecha_salida_primer_vuelo, ahora)

    def confirmar(self) -> None:
        """Transición de estado tras pago exitoso."""
        if self.estado != "pending_payment":
            raise ValueError(f"No se puede confirmar una reserva en estado '{self.estado}'.")
        self.estado = "confirmed"

    def cancelar(self) -> None:
        if self.estado == "cancelled":
            raise ValueError("La reserva ya está cancelada.")
        self.estado = "cancelled"

    def es_multitramo(self) -> bool:
        return len(self.vuelos) > 1
