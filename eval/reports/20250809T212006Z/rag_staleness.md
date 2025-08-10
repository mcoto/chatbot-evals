# Evaluation Report — rag_staleness

- Timestamp (UTC): 2025-08-09T21:20:06.210910Z
- Risk weight: 0.7

## Checks
- **rag_used** (`not_null`): ❌ FAIL
  - info: `{"value": null}`
- **staleness_warn_if_doc_expired** (`contains_if`): ✅ PASS
  - info: `{"condition": "truth['inv']['valid_to'] is not None", "applies": true, "haystack": "Inventario SKU-002 - Switch 8p: stock 0, precio 29.9 USD (ADVERTENCIA: ficha desactualizada).", "needle": "ADVERTENCIA"}`

## KPIs
- Total checks: **2**
- Passed checks: **1**
- Factual failures: **1**
- Compliance failures: **0**
- RFI (risk-weighted factuality): **0.350**
- EDR (escalation deflection): **1.000**
- NCS (net compliance score): **1.000**