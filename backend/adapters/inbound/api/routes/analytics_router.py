"""
Router de analítica para Athena (Requerimiento R7).
Consulta la tabla/vista route_month_metrics en Amazon Athena y responde en < 10 s.
"""
import time
import boto3
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from infrastructure.config import settings

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Configuración de clientes AWS
try:
    _athena_client = boto3.client(
        "athena",
        region_name=getattr(settings, "AWS_REGION", "us-east-1"),
    )
except Exception:
    _athena_client = None


def get_athena_client():
    global _athena_client
    if _athena_client is None:
        _athena_client = boto3.client(
            "athena",
            region_name=getattr(settings, "AWS_REGION", "us-east-1"),
        )
    return _athena_client


class OccupancyOut(BaseModel):
    route:          str
    month:          str
    seats_capacity: int
    seats_sold:     int
    occupancy:      float


@router.get(
    "/occupancy",
    response_model=OccupancyOut,
    status_code=status.HTTP_200_OK,
)
def get_occupancy(
    route: str = Query(..., description="Ruta del vuelo, ej. BOG-MDE"),
    month: str = Query(..., description="Mes en formato YYYY-MM, ej. 2023-05"),
):
    clean_route = route.replace("'", "''").replace(" ", "").strip().upper()
    clean_month = month.replace("'", "''").strip()

    # Consulta SQL contra la vista/tabla analítica route_month_metrics
    query = f"""
        SELECT 
            route,
            month,
            seats_capacity,
            seats_sold,
            occupancy
        FROM route_month_metrics
        WHERE upper(replace(route, ' ', '')) = '{clean_route}' 
          AND month = '{clean_month}'
        LIMIT 1;
    """

    db_name = getattr(settings, "ATHENA_DATABASE", "vuelos_db")
    s3_output = getattr(settings, "ATHENA_S3_OUTPUT", "s3://s3vuelosparcial/results/")
    workgroup = getattr(settings, "ATHENA_WORKGROUP", "primary")

    client = get_athena_client()

    try:
        # 1. Iniciar la consulta en Athena
        exec_kwargs = {
            "QueryString": query,
            "QueryExecutionContext": {"Database": db_name},
            "ResultConfiguration": {"OutputLocation": s3_output},
        }
        if workgroup:
            exec_kwargs["WorkGroup"] = workgroup

        response = client.start_query_execution(**exec_kwargs)
        query_execution_id = response["QueryExecutionId"]

        # 2. Polling con Timeout (< 10 segundos exigido por R7)
        timeout = 9.0
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_resp = client.get_query_execution(QueryExecutionId=query_execution_id)
            state = status_resp["QueryExecution"]["Status"]["State"]

            if state == "SUCCEEDED":
                break
            elif state in ["FAILED", "CANCELLED"]:
                reason = status_resp["QueryExecution"]["Status"].get(
                    "StateChangeReason", "Error desconocido en Athena"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Falló la consulta en Athena: {reason}",
                )

            time.sleep(0.2)
        else:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tiempo de espera agotado al consultar Athena (< 10s)",
            )

        # 3. Obtener resultados
        results = client.get_query_results(QueryExecutionId=query_execution_id)
        rows = results["ResultSet"]["Rows"]

        # Si solo está el encabezado o no hay datos (404 exigido por R7)
        if len(rows) <= 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron métricas para la ruta '{route}' y mes '{month}'",
            )

        # Extraer celdas de la primera fila de datos
        data_cells = rows[1]["Data"]

        return OccupancyOut(
            route=data_cells[0].get("VarCharValue", route.upper()),
            month=data_cells[1].get("VarCharValue", month),
            seats_capacity=int(float(data_cells[2].get("VarCharValue", 0))),
            seats_sold=int(float(data_cells[3].get("VarCharValue", 0))),
            occupancy=float(data_cells[4].get("VarCharValue", 0.0)),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al interactuar con Athena: {str(e)}",
        )
