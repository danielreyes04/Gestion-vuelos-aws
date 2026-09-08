from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


# Roles válidos del sistema (deben coincidir con el check constraint de Aurora)
ROL_PASAJERO = "cliente"
ROL_ADMIN = "admin"
ROL_AGENTE = "agencia"

ROLES_VALIDOS = {ROL_PASAJERO, ROL_ADMIN, ROL_AGENTE}


@dataclass(frozen=True)
class Usuario:
    """
    Representa un usuario autenticado del sistema.

    El dominio necesita esta entidad para aplicar reglas de acceso:
    - Un pasajero solo puede ver/cancelar sus propias reservas (FR-005.1).
    - Un admin puede operar sobre cualquier reserva (RF-004, RF-005.1).
    - Un agente opera en nombre de un pasajero dentro de su agencia (FR-001 agente).

    password_hash NO se expone en esta entidad — vive solo en el modelo ORM.
    El dominio nunca necesita comparar contraseñas; eso es responsabilidad
    de la capa de autenticación (middleware/JWT).
    """
    usuario_id: UUID
    nombre: str
    email: str
    rol: str          # 'passenger' | 'admin' | 'agency_agent'
    activo: bool
    fecha_creacion: datetime | None = None

    def es_admin(self) -> bool:
        return self.rol == ROL_ADMIN

    def es_agente(self) -> bool:
        return self.rol == ROL_AGENTE

    def es_pasajero(self) -> bool:
        return self.rol == ROL_PASAJERO

    def puede_gestionar_reserva(self, propietario_usuario_id: UUID) -> bool:
        """
        Regla de acceso del dominio (FR-005.1 / RF-005.1):
        - Admin: puede gestionar cualquier reserva.
        - Agente: puede gestionar reservas de sus clientes
          (la validación de agencia la hace AgenteAgencia.pertenece_a_agencia).
        - Pasajero: solo puede gestionar sus propias reservas.
        """
        if self.es_admin():
            return True
        return self.usuario_id == propietario_usuario_id
