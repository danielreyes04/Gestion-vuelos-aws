-- Tablas para el harness del segundo parcial
-- Ejecutar en DBeaver sobre Aurora (base: postgres)

CREATE TABLE IF NOT EXISTS flight (
    flight_id        VARCHAR(100) PRIMARY KEY,
    route            VARCHAR(20)  NOT NULL,
    flight_date      VARCHAR(10)  NOT NULL,
    capacity         INTEGER      NOT NULL,
    seats_available  INTEGER      NOT NULL,
    price_cents      BIGINT       NOT NULL
);

CREATE TABLE IF NOT EXISTS reservation (
    reservation_id   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    flight_id        VARCHAR(100) NOT NULL REFERENCES flight(flight_id),
    passenger_name   VARCHAR(255) NOT NULL,
    fare_class       VARCHAR(50)  NOT NULL,
    status           VARCHAR(20)  NOT NULL DEFAULT 'CONFIRMED'
);

-- Índice para acelerar búsqueda de vuelos (R1: p95 < 1s)
CREATE INDEX IF NOT EXISTS idx_flight_route_date
    ON flight(route, flight_date);

-- Índice para búsqueda por origin/destination extraído de route
CREATE INDEX IF NOT EXISTS idx_flight_date
    ON flight(flight_date);
