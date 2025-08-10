# Evaluation Report — inventory_staleness

- Timestamp (UTC): 2025-08-09T19:28:34.355845Z
- Risk weight: 0.5

## Checks
- **inventory_sku_match** (`equals`): ✅ PASS
  - info: `{"left": "SKU-002", "right": "SKU-002"}`
- **inventory_price_format** (`regex`): ✅ PASS
  - info: `{"value": 29.9, "pattern": "^[0-9]+(\\.[0-9]{1,2})?$"}`
- **staleness_warning_if_expired** (`contains_if`): ✅ PASS
  - info: `{"condition": "truth['item']['is_stale'] == True", "applies": true, "haystack": "Inventario SKU-002 - Switch 8p: stock 0, precio 29.9 USD (ADVERTENCIA: ficha desactualizada).", "needle": "ADVERTENCIA"}`

## KPIs
- Total checks: **3**
- Passed checks: **3**
- Factual failures: **0**
- Compliance failures: **0**
- RFI (risk-weighted factuality): **0.000**
- EDR (escalation deflection): **1.000**
- NCS (net compliance score): **1.000**