# Evaluation Report — rag_staleness

- Timestamp (UTC): 2025-08-10T15:26:53.583203Z
- Risk weight: 0.7

## Checks
- **rag_used** (`not_null`): ✅ PASS
  - info: `{"value": [{"text": "Especificaciones del SKU-002 (documento 2023):\n- 8 puertos 10/100/1000\n- QoS básica", "score": 0.8662237, "source": "manual_sku002_2023.pdf", "sku": "SKU-002", "lang": "es", "valid_from": "2023-02-01", "valid_to": "2025-06-30", "version": "v1", "section_id": null, "tags": ["specs", "switch"]}]}`
- **staleness_warn_if_doc_expired** (`contains_if`): ✅ PASS
  - info: `{"condition": "truth['inv']['valid_to'] is not None", "applies": true, "haystack": "Inventario SKU-002 - Switch 8p: stock 0, precio 29.9 USD (ADVERTENCIA: ficha desactualizada).", "needle": "ADVERTENCIA"}`

## KPIs
- Total checks: **2**
- Passed checks: **2**
- Factual failures: **0**
- Compliance failures: **0**
- RFI (risk-weighted factuality): **0.000**
- EDR (escalation deflection): **1.000**
- NCS (net compliance score): **1.000**