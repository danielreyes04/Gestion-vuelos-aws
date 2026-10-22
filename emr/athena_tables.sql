-- Tablas del contrato (Apéndice A.2) en vuelos_db. Ejecutar en Athena DESPUÉS del job de EMR,
-- una sentencia a la vez.

DROP VIEW IF EXISTS route_month_metrics;
DROP TABLE IF EXISTS reservations_curated;

CREATE EXTERNAL TABLE reservations_curated (
  reservation_id string,
  flight_id      string,
  route          string,
  fare_class     string,
  price_cents    bigint,
  status         string
)
PARTITIONED BY (month string)
STORED AS PARQUET
LOCATION 's3://s3vuelosparcial/curated/reservations_curated/';

MSCK REPAIR TABLE reservations_curated;

CREATE EXTERNAL TABLE route_month_metrics (
  route          string,
  month          string,
  seats_capacity bigint,
  seats_sold     bigint,
  occupancy      double,
  revenue_cents  bigint,
  bookings       bigint,
  cancellations  bigint
)
STORED AS PARQUET
LOCATION 's3://s3vuelosparcial/curated/route_month_metrics/';

-- Verificación esperada (seed actual): 2012313 filas, 24 meses, 10 rutas, 240 filas de métricas.
-- SELECT count(*), count(DISTINCT month), count(DISTINCT route) FROM reservations_curated;
-- SELECT * FROM route_month_metrics WHERE route = 'ADZ-MDE' AND month = '2023-01';
--   -> seats_capacity 10500, seats_sold 8694, occupancy 0.828
