-- =============================================================
-- SEED DATA — Sistema de Gestión de Vuelos
-- Ejecutar en DBeaver conectado a Aurora (base: postgres)
-- Roles válidos en Aurora: 'admin' | 'cliente' | 'agencia'
-- =============================================================

-- Limpiar datos previos (orden inverso de FK)
TRUNCATE TABLE auditoria, pago, reserva_agencia, reserva_asiento,
               reserva_vuelo, reserva, asiento, vuelo_instancia,
               regla_tarifa, vuelo_programado, agente_agencia,
               pasajero, ruta, agencia, aeronave, aeropuerto, usuario
CASCADE;

-- =============================================================
-- 1. AEROPUERTOS
-- =============================================================
INSERT INTO aeropuerto (aeropuerto_id, codigo, nombre, ciudad, pais) VALUES
  ('a1000000-0000-0000-0000-000000000001', 'BOG', 'El Dorado Internacional', 'Bogotá',    'Colombia'),
  ('a1000000-0000-0000-0000-000000000002', 'MED', 'José María Córdova',      'Medellín',  'Colombia'),
  ('a1000000-0000-0000-0000-000000000003', 'CTG', 'Rafael Núñez',            'Cartagena', 'Colombia');

-- =============================================================
-- 2. AERONAVES
-- =============================================================
INSERT INTO aeronave (aeronave_id, modelo, total_asientos, fabricante) VALUES
  ('b1000000-0000-0000-0000-000000000001', 'Airbus A320', 150, 'Airbus'),
  ('b1000000-0000-0000-0000-000000000002', 'Boeing 737',  160, 'Boeing');

-- =============================================================
-- 3. USUARIOS
-- Roles válidos según constraint Aurora: admin | cliente | agencia
-- =============================================================
INSERT INTO usuario (usuario_id, nombre, email, password_hash, rol, activo) VALUES
  ('c1000000-0000-0000-0000-000000000001', 'Carlos Pérez',  'carlos@test.com',   '$2b$12$placeholder', 'cliente',  true),
  ('c1000000-0000-0000-0000-000000000002', 'Ana Gómez',     'ana@test.com',      '$2b$12$placeholder', 'cliente',  true),
  ('c1000000-0000-0000-0000-000000000003', 'Admin Sistema', 'admin@test.com',    '$2b$12$placeholder', 'admin',    true),
  ('c1000000-0000-0000-0000-000000000004', 'Pedro Agente',  'pedro@agencia.com', '$2b$12$placeholder', 'agencia',  true);

-- =============================================================
-- 4. AGENCIA
-- =============================================================
INSERT INTO agencia (agencia_id, nombre, contacto, tasa_comision) VALUES
  ('d1000000-0000-0000-0000-000000000001', 'Viajes Rápido', 'contacto@viajesrapido.com', 0.0800);

-- =============================================================
-- 5. RUTAS
-- =============================================================
INSERT INTO ruta (ruta_id, aeropuerto_origen, aeropuerto_destino, distancia_km) VALUES
  ('e1000000-0000-0000-0000-000000000001',
   'a1000000-0000-0000-0000-000000000001',
   'a1000000-0000-0000-0000-000000000002',
   245.00),
  ('e1000000-0000-0000-0000-000000000002',
   'a1000000-0000-0000-0000-000000000001',
   'a1000000-0000-0000-0000-000000000003',
   1050.00);

-- =============================================================
-- 6. AGENTE DE AGENCIA
-- =============================================================
INSERT INTO agente_agencia (agente_id, usuario_id, agencia_id) VALUES
  ('f1000000-0000-0000-0000-000000000001',
   'c1000000-0000-0000-0000-000000000004',
   'd1000000-0000-0000-0000-000000000001');

-- =============================================================
-- 7. PASAJEROS
-- =============================================================
INSERT INTO pasajero (pasajero_id, usuario_id, agente_agencia_id, telefono, tipo_documento, numero_documento) VALUES
  ('g1000000-0000-0000-0000-000000000001',
   'c1000000-0000-0000-0000-000000000001',
   NULL, '3001234567', 'CC', '1023456789'),
  ('g1000000-0000-0000-0000-000000000002',
   'c1000000-0000-0000-0000-000000000002',
   NULL, '3109876543', 'CC', '987654321');

-- =============================================================
-- 8. VUELOS PROGRAMADOS
-- =============================================================
INSERT INTO vuelo_programado (vuelo_programado_id, ruta_id, aeronave_id, hora_salida, hora_llegada, precio_base) VALUES
  ('h1000000-0000-0000-0000-000000000001',
   'e1000000-0000-0000-0000-000000000001',
   'b1000000-0000-0000-0000-000000000001',
   '08:00:00', '09:00:00', 200000.00),
  ('h1000000-0000-0000-0000-000000000002',
   'e1000000-0000-0000-0000-000000000002',
   'b1000000-0000-0000-0000-000000000002',
   '14:00:00', '15:30:00', 350000.00);

-- =============================================================
-- 9. REGLAS DE TARIFA
-- =============================================================
INSERT INTO regla_tarifa (regla_tarifa_id, vuelo_programado_id, clase, dias_anticipacion_min, dias_anticipacion_max, multiplicador) VALUES
  ('i1000000-0000-0000-0000-000000000001', 'h1000000-0000-0000-0000-000000000001', 'economy',  0,   7,   1.50),
  ('i1000000-0000-0000-0000-000000000002', 'h1000000-0000-0000-0000-000000000001', 'economy',  8,   30,  1.00),
  ('i1000000-0000-0000-0000-000000000003', 'h1000000-0000-0000-0000-000000000001', 'economy',  31,  365, 0.80),
  ('i1000000-0000-0000-0000-000000000004', 'h1000000-0000-0000-0000-000000000001', 'business', 0,   365, 2.00),
  ('i1000000-0000-0000-0000-000000000005', 'h1000000-0000-0000-0000-000000000002', 'economy',  0,   7,   1.50),
  ('i1000000-0000-0000-0000-000000000006', 'h1000000-0000-0000-0000-000000000002', 'economy',  8,   365, 1.00),
  ('i1000000-0000-0000-0000-000000000007', 'h1000000-0000-0000-0000-000000000002', 'business', 0,   365, 2.00);

-- =============================================================
-- 10. VUELOS INSTANCIA (fechas futuras)
-- =============================================================
INSERT INTO vuelo_instancia (vuelo_instancia_id, vuelo_programado_id, aeronave_id, fecha_salida, fecha_llegada, asientos_disponibles) VALUES
  ('j1000000-0000-0000-0000-000000000001',
   'h1000000-0000-0000-0000-000000000001',
   'b1000000-0000-0000-0000-000000000001',
   NOW() + INTERVAL '1 day'  + INTERVAL '8 hours',
   NOW() + INTERVAL '1 day'  + INTERVAL '9 hours',
   148),
  ('j1000000-0000-0000-0000-000000000002',
   'h1000000-0000-0000-0000-000000000001',
   'b1000000-0000-0000-0000-000000000001',
   NOW() + INTERVAL '10 days' + INTERVAL '8 hours',
   NOW() + INTERVAL '10 days' + INTERVAL '9 hours',
   150),
  ('j1000000-0000-0000-0000-000000000003',
   'h1000000-0000-0000-0000-000000000002',
   'b1000000-0000-0000-0000-000000000002',
   NOW() + INTERVAL '5 days' + INTERVAL '14 hours',
   NOW() + INTERVAL '5 days' + INTERVAL '15 hours 30 minutes',
   158);

-- =============================================================
-- 11. ASIENTOS
-- =============================================================
INSERT INTO asiento (asiento_id, vuelo_instancia_id, numero_asiento, clase, esta_disponible, bloqueado_hasta, version) VALUES
  ('k1000000-0000-0000-0000-000000000001', 'j1000000-0000-0000-0000-000000000001', '12A', 'economy',  true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000002', 'j1000000-0000-0000-0000-000000000001', '12B', 'economy',  true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000003', 'j1000000-0000-0000-0000-000000000001', '12C', 'economy',  true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000004', 'j1000000-0000-0000-0000-000000000001', '2A',  'business', true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000005', 'j1000000-0000-0000-0000-000000000001', '2B',  'business', true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000006', 'j1000000-0000-0000-0000-000000000002', '15A', 'economy',  true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000007', 'j1000000-0000-0000-0000-000000000002', '15B', 'economy',  true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000008', 'j1000000-0000-0000-0000-000000000003', '10A', 'economy',  true, NULL, 0),
  ('k1000000-0000-0000-0000-000000000009', 'j1000000-0000-0000-0000-000000000003', '10B', 'economy',  true, NULL, 0);

-- =============================================================
-- VERIFICACIÓN
-- =============================================================
SELECT 'aeropuerto'     AS tabla, COUNT(*) FROM aeropuerto
UNION ALL SELECT 'aeronave',        COUNT(*) FROM aeronave
UNION ALL SELECT 'usuario',         COUNT(*) FROM usuario
UNION ALL SELECT 'agencia',         COUNT(*) FROM agencia
UNION ALL SELECT 'ruta',            COUNT(*) FROM ruta
UNION ALL SELECT 'agente_agencia',  COUNT(*) FROM agente_agencia
UNION ALL SELECT 'pasajero',        COUNT(*) FROM pasajero
UNION ALL SELECT 'vuelo_programado',COUNT(*) FROM vuelo_programado
UNION ALL SELECT 'regla_tarifa',    COUNT(*) FROM regla_tarifa
UNION ALL SELECT 'vuelo_instancia', COUNT(*) FROM vuelo_instancia
UNION ALL SELECT 'asiento',         COUNT(*) FROM asiento;
