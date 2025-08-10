# Evaluation Report — order_status_simple

- Timestamp (UTC): 2025-08-09T19:28:12.864513Z
- Risk weight: 0.8

## Checks
- **order_status_exact** (`equals`): ✅ PASS
  - info: `{"left": "delayed", "right": "delayed"}`
- **eta_exists** (`not_null`): ✅ PASS
  - info: `{"value": "2025-08-16"}`
- **invoice_amount_format** (`regex`): ✅ PASS
  - info: `{"value": 98000.0, "pattern": "^[0-9]+(\\.[0-9]{1,2})?$"}`
- **delayed_disclaimer_required** (`required_if`): ✅ PASS
  - info: `{"condition": "truth['order']['status'] == 'delayed'", "applies": true, "haystack": "Pedido #2 está en estado 'delayed' con ETA 2025-08-16. Su pedido está retrasado. Podemos escalar al equipo humano si lo desea. Factura: 98000.0 CRC, vence 2025-08-07.", "needle": "retrasado"}`

## KPIs
- Total checks: **4**
- Passed checks: **4**
- Factual failures: **0**
- Compliance failures: **0**
- RFI (risk-weighted factuality): **0.000**
- EDR (escalation deflection): **1.000**
- NCS (net compliance score): **1.000**