from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class VueloInstancia:
    """
    Representa un vuelo concreto en una fecha específica.
    Separado de VueloProgramado para modelar vuelos recurrentes
    sin duplicar la configuración base (decisión 5.3).
    """
    vuelo_instancia_id: UUID
    vuelo_programado_id: UUID
    aeronave_id: UUID
    fecha_salida: datetime
    fecha_llegada: datetime
    # Contador de asientos libres. Es la fuente de verdad para
    # prevenir sobreventa (RNF-004/RNF-005).
    asientos_disponibles: int

    def tiene_disponibilidad(self) -> bool:
        return self.asientos_disponibles > 0
