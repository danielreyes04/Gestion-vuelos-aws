"""
Ejecuta athena_tables.sql en Athena (R5) y verifica el resultado contra los valores esperados.

Uso:  python emr/setup_athena.py
"""
import time
from pathlib import Path

import boto3

DATABASE = "vuelos_db"
OUTPUT = "s3://s3vuelosparcial/results/"

athena = boto3.client("athena", region_name="us-east-1")


def run(sql):
    qid = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": OUTPUT},
    )["QueryExecutionId"]
    while True:
        st = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if st["State"] not in ("QUEUED", "RUNNING"):
            break
        time.sleep(0.5)
    if st["State"] != "SUCCEEDED":
        raise RuntimeError(f"{sql[:60]}... -> {st.get('StateChangeReason')}")
    rows = athena.get_query_results(QueryExecutionId=qid)["ResultSet"]["Rows"]
    return [[d.get("VarCharValue") for d in r["Data"]] for r in rows]


# Quitar comentarios y separar sentencias
text = "\n".join(
    line for line in Path(__file__).with_name("athena_tables.sql").read_text(encoding="utf-8").splitlines()
    if not line.strip().startswith("--")
)
for stmt in filter(None, (s.strip() for s in text.split(";"))):
    print(">>", stmt.splitlines()[0])
    run(stmt)

print(run("SELECT count(*), count(DISTINCT month), count(DISTINCT route) FROM reservations_curated"))
print("  esperado: 2012313, 24, 10")
print(run("SELECT * FROM route_month_metrics WHERE route = 'ADZ-MDE' AND month = '2023-01'"))
print("  esperado: seats_capacity 10500, seats_sold 8694, occupancy 0.828")
