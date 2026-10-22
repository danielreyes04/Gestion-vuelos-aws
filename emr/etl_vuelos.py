"""
Job PySpark (EMR) — Segundo parcial, requisitos R4/R5/R6.

Lee los CSV crudos de S3, aplica las reglas de limpieza C1–C5 y escribe:
  1. reservations_curated  -> Parquet particionado por month (24 particiones)
  2. route_month_metrics   -> Parquet sin particionar (tabla de métricas para Athena)

Uso (paso de EMR):
  spark-submit s3://s3vuelosparcial/EMR/etl_vuelos.py \
      --bucket s3vuelosparcial
"""
import argparse

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--bucket", default="s3vuelosparcial")
args = parser.parse_args()

RAW = f"s3://{args.bucket}/raw"
CURATED = f"s3://{args.bucket}/curated/reservations_curated"
METRICS = f"s3://{args.bucket}/curated/route_month_metrics"

spark = SparkSession.builder.appName("AirlinesETL_Parcial2").getOrCreate()

# ------------------------------------------------------------------ #
# Lectura (todo como string para controlar los casts)                 #
# ------------------------------------------------------------------ #
flights_raw = spark.read.option("header", "true").csv(f"{RAW}/flights.csv")
res_raw = spark.read.option("header", "true").csv(f"{RAW}/reservations.csv")

# Orden original del archivo, necesario para "keep first" en C5.
res_raw = res_raw.withColumn("_row", F.monotonically_increasing_id())

# ------------------------------------------------------------------ #
# Vuelos: C1 + mes del vuelo                                          #
# ------------------------------------------------------------------ #
# C1: quitar TODO el whitespace (no solo los extremos) y pasar a mayúsculas.
flights = flights_raw.select(
    F.col("flight_id").cast("string").alias("flight_id"),
    F.upper(F.regexp_replace("route", r"\s+", "")).alias("route"),
    F.substring("flight_date", 1, 7).alias("month"),
    F.col("capacity").cast("bigint").alias("capacity"),
)

# ------------------------------------------------------------------ #
# Reservas: C2–C5                                                     #
# ------------------------------------------------------------------ #
res = (
    res_raw
    # C2: status sin espacios y en mayúsculas
    .withColumn("status", F.upper(F.trim("status")))
    # C3: solo CONFIRMED / CANCELLED
    .filter(F.col("status").isin("CONFIRMED", "CANCELLED"))
    # C4: price_cents presente y > 0
    .withColumn("price_cents", F.col("price_cents").cast("double"))
    .filter(F.col("price_cents").isNotNull() & (F.col("price_cents") > 0))
)

# C5: duplicados de reservation_id, conservando la primera aparición
w = Window.partitionBy("reservation_id").orderBy("_row")
res = res.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1")

# ------------------------------------------------------------------ #
# Tabla 1: reservations_curated                                       #
# ------------------------------------------------------------------ #
curated = (
    res.join(flights.select("flight_id", "route", "month"), on="flight_id", how="inner")
    .select(
        F.col("reservation_id").cast("string"),
        F.col("flight_id").cast("string"),
        "route",
        "fare_class",
        F.col("price_cents").cast("bigint"),
        "status",
        "month",
    )
)
curated.cache()
curated.write.mode("overwrite").partitionBy("month").parquet(CURATED)

# ------------------------------------------------------------------ #
# Tabla 2: route_month_metrics                                        #
# seats_capacity = suma de la capacidad de los vuelos de la ruta/mes  #
# ------------------------------------------------------------------ #
capacity = flights.groupBy("route", "month").agg(F.sum("capacity").alias("seats_capacity"))

confirmed = F.col("status") == "CONFIRMED"
sales = curated.groupBy("route", "month").agg(
    F.count(F.when(confirmed, 1)).alias("seats_sold"),
    F.sum(F.when(confirmed, F.col("price_cents"))).alias("revenue_cents"),
    F.count(F.when(confirmed, 1)).alias("bookings"),
    F.count(F.when(F.col("status") == "CANCELLED", 1)).alias("cancellations"),
)

metrics = (
    capacity.join(sales, on=["route", "month"], how="left")
    .na.fill(0, ["seats_sold", "revenue_cents", "bookings", "cancellations"])
    .select(
        "route",
        "month",
        F.col("seats_capacity").cast("bigint"),
        F.col("seats_sold").cast("bigint"),
        (F.col("seats_sold") / F.col("seats_capacity")).cast("double").alias("occupancy"),
        F.col("revenue_cents").cast("bigint"),
        F.col("bookings").cast("bigint"),
        F.col("cancellations").cast("bigint"),
    )
)
metrics.coalesce(1).write.mode("overwrite").parquet(METRICS)

print("curated rows:", curated.count(), "| metrics rows:", metrics.count())
spark.stop()
