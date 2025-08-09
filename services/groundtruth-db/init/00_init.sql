-- Tablas mínimas
CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(id),
  status TEXT NOT NULL,
  eta DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoices (
  id SERIAL PRIMARY KEY,
  order_id INT REFERENCES orders(id),
  amount NUMERIC(12,2) NOT NULL,
  currency TEXT NOT NULL,
  due_date DATE NOT NULL,
  paid BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS inventory (
  sku TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  stock INT NOT NULL,
  price NUMERIC(12,2) NOT NULL,
  currency TEXT NOT NULL,
  valid_from DATE NOT NULL DEFAULT CURRENT_DATE,
  valid_to DATE
);

CREATE TABLE IF NOT EXISTS policies (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL
);

-- Datos demo
INSERT INTO customers (name, email) VALUES
  ('Ana Gómez', 'ana@example.com'),
  ('Juan Pérez', 'juan@example.com')
ON CONFLICT DO NOTHING;

INSERT INTO orders (customer_id, status, eta)
VALUES
  (1, 'processing', CURRENT_DATE + INTERVAL '3 day'),
  (2, 'delayed',    CURRENT_DATE + INTERVAL '7 day')
ON CONFLICT DO NOTHING;

INSERT INTO invoices (order_id, amount, currency, due_date, paid) VALUES
  (1, 125.50, 'USD', CURRENT_DATE + INTERVAL '10 day', false),
  (2, 98000.00, 'CRC', CURRENT_DATE - INTERVAL '2 day', false)
ON CONFLICT DO NOTHING;

INSERT INTO inventory (sku, name, stock, price, currency, valid_from, valid_to) VALUES
  ('SKU-001', 'Router AC1200', 12, 49.99, 'USD', CURRENT_DATE - 30, NULL),
  ('SKU-002', 'Switch 8p',      0, 29.90, 'USD', CURRENT_DATE - 90, CURRENT_DATE - 5)
ON CONFLICT DO NOTHING;

INSERT INTO policies (key, value) VALUES
  ('delayed_order_disclaimer', '{"text":"Su pedido está retrasado. Podemos escalar al equipo humano si lo desea."}')
ON CONFLICT DO NOTHING;

