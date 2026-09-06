from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AgenteAgencia:
    """
    Vincula un Usuario con una Agencia.

    Necesario para validar en el dominio que quien crea una reserva
    en nombre de un pasajero (gestionada_por_usuario_id) efectivamente
    pertenece a la agencia indicada en agencia_id (FR-001 agente).
    """
    agente_id: UUID
    usuario_id: UUID
    agencia_id: UUID

    def pertenece_a_agencia(self, agencia_id: UUID) -> bool:
        """
        Verifica que el agente pertenece a la agencia que se indica
        en la reserva, evitando que un agente opere en nombre de
        una agencia a la que no está asociado.
        """
        return self.agencia_id == agencia_id
