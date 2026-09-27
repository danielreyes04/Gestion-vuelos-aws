# Gestión de Vuelos AWS

Sistema de gestión de reservas de vuelos para una aerolínea regional, desarrollado como una API REST con Python y FastAPI. El proyecto integra lógica de negocio, persistencia relacional y patrones de arquitectura en capas para gestionar vuelos, asientos, reservas, pagos y auditoría.

El backend está diseñado sobre una arquitectura hexagonal con separación clara entre:
- dominio
- casos de uso
- adaptadores de entrada/salida
- infraestructura y persistencia

Además, usa PostgreSQL/Aurora y aplica mecanismos de control de concurrencia para evitar sobreventa y bloquear asientos temporalmente durante reservas en proceso.

## Características principales

- Búsqueda de vuelos disponibles por origen, destino, fecha y número de pasajeros
- Consulta de asientos disponibles por instancia de vuelo
- Creación de reservas con bloqueo temporal de asientos
- Confirmación de pagos
- Cancelación de reservas según reglas de negocio
- Soporte para itinerarios multi-tramo
- Auditoría de cambios y eventos de negocio
- Arquitectura basada en casos de uso y entidades de dominio
- Compatibilidad con PostgreSQL/Aurora en AWS

## Stack tecnológico

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL / Aurora PostgreSQL
- Pydantic
- Pydantic Settings
- Uvicorn
- Python-dotenv

## Estructura del proyecto

```text
Gestion-vuelos-aws/
├── Diagramas/
├── backend/
│   ├── adapters/
│   │   ├── inbound/
│   │   │   └── api/
│   │   │       ├── routes/
│   │   │       ├── schemas/
│   │   │       └── exception_handlers.py
│   │   └── outbound/
│   │       └── persistence/
│   ├── app/
│   │   ├── application/
│   │   │   └── use_cases/
│   │   └── domain/
│   │       ├── entities/
│   │       ├── ports/
│   │       ├── services/
│   │       └── exceptions.py
│   ├── infrastructure/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── models/
│   ├── main.py
│   ├── requirements.txt
│   ├── seed_data.sql
│   └── .env.example
```

### Capas principales

#### `app/domain`

Contiene el núcleo del negocio, incluyendo entidades, servicios de dominio, puertos o interfaces, excepciones específicas y reglas relacionadas con vuelos, reservas, asientos y pagos.

#### `app/application`

Contiene los casos de uso de la aplicación:

- Buscar vuelos.
- Obtener asientos.
- Crear reservas.
- Consultar reservas.
- Confirmar pagos.
- Cancelar reservas.

#### `adapters/inbound`

Contiene los adaptadores que reciben solicitudes externas. Actualmente incluye la API HTTP construida con FastAPI.

#### `adapters/outbound`

Contiene los adaptadores de salida, principalmente los relacionados con la persistencia de datos.

#### `infrastructure`

Contiene la configuración técnica del sistema, la creación de sesiones de base de datos, la configuración de SQLAlchemy y los modelos ORM.

#### `Diagramas`

Contiene los diagramas relacionados con el diseño y la arquitectura del sistema.

## Requisitos previos

- Python 3.10 o superior.
- `pip`.
- PostgreSQL o acceso a una instancia de Aurora PostgreSQL.
- Git.

Puedes comprobar las versiones instaladas con:

```bash
python --version
pip --version
```

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/danielreyes04/Gestion-vuelos-aws.git
cd Gestion-vuelos-aws/backend
```

Crea y activa un entorno virtual:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux o macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración de variables de entorno

Copia el archivo de ejemplo:

### Windows

```bash
copy .env.example .env
```

### Linux o macOS

```bash
cp .env.example .env
```

Edita el archivo `.env` y configura los valores correspondientes:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu_password

APP_ENV=development
SECRET_KEY=cambia_esto_en_produccion

SEAT_LOCK_TIMEOUT_SECONDS=600
```

### Variables disponibles

| Variable | Descripción | Valor sugerido |
|---|---|---|
| `DB_HOST` | Host de PostgreSQL o Aurora | `localhost` |
| `DB_PORT` | Puerto de la base de datos | `5432` |
| `DB_NAME` | Nombre de la base de datos | `postgres` |
| `DB_USER` | Usuario de PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña de PostgreSQL | — |
| `APP_ENV` | Entorno de ejecución | `development` |
| `SECRET_KEY` | Clave secreta de la aplicación | Cambiar en producción |
| `SEAT_LOCK_TIMEOUT_SECONDS` | Duración del bloqueo temporal de un asiento | `600` |

> No subas el archivo `.env` al repositorio. Nunca almacenes credenciales reales, claves privadas o contraseñas en el código fuente.

## Base de datos

El proyecto incluye datos iniciales en `backend/seed_data.sql`.

Con PostgreSQL instalado, puedes ejecutar el script desde la carpeta `backend` con:

```bash
psql -h localhost -U postgres -d postgres -f seed_data.sql
```

Si utilizas una base de datos remota:

```bash
psql -h <host-de-la-base-de-datos> -p 5432 -U <usuario> -d <nombre-de-la-base-de-datos> -f seed_data.sql
```

Asegúrate de que las tablas y los datos iniciales estén disponibles antes de iniciar la API.

## Ejecución de la aplicación

Desde la carpeta `backend`, ejecuta:

```bash
uvicorn main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

También puedes especificar el host y el puerto:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Documentación de la API

Una vez iniciada la aplicación, puedes consultar la documentación interactiva en:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Endpoints principales

Todos los endpoints funcionales utilizan el prefijo `/api/v1`.

### Comprobar el estado de la API

```http
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok"
}
```

### Buscar vuelos disponibles

```http
GET /api/v1/vuelos/disponibles
```

Parámetros de consulta:

| Parámetro | Descripción |
|---|---|
| `origen` | Código IATA del aeropuerto de origen |
| `destino` | Código IATA del aeropuerto de destino |
| `fecha` | Fecha en formato `YYYY-MM-DD` |
| `num_pasajeros` | Número de pasajeros, entre 1 y 9 |

Ejemplo:

```text
/api/v1/vuelos/disponibles?origen=BOG&destino=MDE&fecha=2026-10-15&num_pasajeros=2
```

### Consultar asientos disponibles

```http
GET /api/v1/vuelos/{vuelo_instancia_id}/asientos
```

La respuesta incluye el identificador, número, clase, disponibilidad y bloqueo vigente del asiento, si aplica.

### Crear una reserva

```http
POST /api/v1/reservas/
```

Crea una reserva en estado pendiente de pago y bloquea temporalmente los asientos seleccionados. Si dos usuarios intentan reservar simultáneamente el mismo asiento, uno de ellos recibirá `409 Conflict`.

### Consultar una reserva

```http
GET /api/v1/reservas/{reserva_id}
```

Devuelve el detalle de una reserva, incluyendo sus vuelos asociados, estado y monto total.

### Confirmar el pago de una reserva

```http
POST /api/v1/reservas/{reserva_id}/pago
```

Al confirmar el pago, la reserva cambia de estado, los asientos se marcan como ocupados y se actualiza la disponibilidad del vuelo. El sistema no debe almacenar datos sensibles de tarjetas.

### Cancelar una reserva

```http
DELETE /api/v1/reservas/{reserva_id}
```

Una reserva puede cancelarse si faltan más de ocho horas para la salida del vuelo. Las cancelaciones también se registran en auditoría.

## Reglas de negocio importantes

### Bloqueo temporal de asientos

Los asientos se bloquean temporalmente cuando se crea una reserva pendiente de pago. El tiempo predeterminado es de 600 segundos, equivalente a 10 minutos.

Este valor puede modificarse mediante:

```env
SEAT_LOCK_TIMEOUT_SECONDS=600
```

### Control de concurrencia

El sistema implementa optimistic locking para evitar la sobreventa de asientos. Si dos usuarios intentan reservar el mismo asiento, uno de ellos podrá completar la operación y el otro recibirá `409 Conflict`.

### Confirmación del pago

Una reserva pendiente debe confirmarse mediante el endpoint de pago. Al confirmar el pago, los asientos pasan a estar ocupados de forma permanente.

### Cancelaciones

Las reservas sólo pueden cancelarse cuando se cumple la ventana de tiempo definida por las reglas del negocio. Actualmente, la cancelación no está permitida cuando faltan menos de ocho horas para el vuelo.

## Respuestas HTTP utilizadas

| Código | Descripción |
|---|---|
| `200 OK` | Solicitud procesada correctamente |
| `201 Created` | Reserva creada correctamente |
| `404 Not Found` | Recurso no encontrado |
| `409 Conflict` | Conflicto por disponibilidad o concurrencia |
| `422 Unprocessable Entity` | Error de validación o regla de negocio |
| `500 Internal Server Error` | Error inesperado del servidor |

## Ejemplo de flujo de reserva

```text
1. Buscar vuelos disponibles.
2. Consultar los asientos del vuelo seleccionado.
3. Crear una reserva con los asientos elegidos.
4. Realizar el pago mediante una pasarela externa.
5. Confirmar el pago utilizando el identificador de transacción.
6. Consultar la reserva confirmada.
```

Si el pago no se confirma dentro del tiempo establecido, el bloqueo temporal del asiento puede expirar y permitir que otro usuario lo reserve.

## Ejemplo de uso con `curl`

Comprobar el estado de la API:

```bash
curl http://127.0.0.1:8000/health
```

Buscar vuelos:

```bash
curl "http://127.0.0.1:8000/api/v1/vuelos/disponibles?origen=BOG&destino=MDE&fecha=2026-10-15&num_pasajeros=1"
```

Consultar asientos:

```bash
curl "http://127.0.0.1:8000/api/v1/vuelos/<vuelo_instancia_id>/asientos"
```

Para consultar los formatos exactos de las solicitudes y respuestas, utiliza la documentación disponible en `/docs`.

## Consideraciones de seguridad

Para entornos productivos se recomienda:

- Cambiar `SECRET_KEY`.
- No utilizar contraseñas por defecto.
- No subir archivos `.env`.
- Configurar correctamente los orígenes permitidos de CORS.
- Utilizar HTTPS.
- Gestionar las credenciales mediante AWS Secrets Manager o un servicio equivalente.
- No almacenar números de tarjetas ni datos sensibles de pago.
- Configurar permisos mínimos para la base de datos.
- Utilizar variables de entorno independientes por ambiente.
- Revisar y restringir los logs de la aplicación.

Actualmente, la configuración de CORS permite todos los orígenes:

```python
allow_origins=["*"]
```

Esta configuración debe restringirse antes de desplegar en producción.

## Despliegue en AWS

El proyecto está preparado para utilizar Aurora PostgreSQL como base de datos mediante la variable `DB_HOST`.

Una arquitectura de despliegue posible en AWS podría incluir:

```text
Cliente
   │
   ▼
Application Load Balancer
   │
   ▼
Servicio FastAPI
   │
   ▼
Aurora PostgreSQL
```

El endpoint `/health` puede utilizarse como comprobación de estado para un balanceador de carga o servicio de monitoreo.

## Desarrollo

Para iniciar la aplicación en modo desarrollo:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

En Windows:

```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload
```

El modo `--reload` reinicia automáticamente el servidor cuando detecta cambios en el código.

## Pruebas

Actualmente, el repositorio no incluye una carpeta de pruebas automatizadas visible. Se recomienda incorporar pruebas para:

- Búsqueda de vuelos.
- Disponibilidad de asientos.
- Creación de reservas.
- Conflictos por reserva simultánea.
- Confirmación de pagos.
- Cancelación fuera del plazo permitido.
- Expiración de bloqueos temporales.
- Validación de entradas.
- Manejo de errores de dominio.

Una estructura recomendada sería:

```text
backend/
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

## Convenciones sugeridas para commits

Se recomienda utilizar mensajes descriptivos, por ejemplo:

```text
feat: agregar búsqueda de vuelos disponibles
fix: corregir bloqueo temporal de asientos
docs: actualizar instrucciones de instalación
refactor: separar lógica de reservas
test: agregar pruebas de confirmación de pago
```

## Autor

Proyecto desarrollado por [danielreyes04](https://github.com/danielreyes04).

## Repositorio

[https://github.com/danielreyes04/Gestion-vuelos-aws](https://github.com/danielreyes04/Gestion-vuelos-aws)
