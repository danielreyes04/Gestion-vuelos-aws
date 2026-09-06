from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class Agencia:
    """
    Representa una agencia de viajes socia de la aerolínea.

    tasa_comision: fracción decimal aplicada sobre el monto_total
    de cada reserva gestionada por la agencia.
    Ejemplo: 0.08 = 8% de comisión (FR-003 agente / FR-003.1).
    """
    agencia_id: UUID
    nombre: str
    tasa_comision: Decimal
    contacto: str | None = None

    def calcular_comision(self, monto_reserva: Decimal) -> Decimal:
        """
        Calcula el monto de comisión para una reserva.
        Esta lógica vive en el dominio porque es una regla de negocio
        (FR-003.1: el sistema calcula la comisión por reserva gestionada).
        """
        return (monto_reserva * self.tasa_comision).quantize(Decimal("0.01"))
