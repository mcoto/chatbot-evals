# Evaluation Report — rag_ficha_tecnica

- Timestamp (UTC): 2025-08-09T21:20:05.971459Z
- Risk weight: 0.6

## Checks
- **rag_used** (`not_null`): ❌ FAIL
  - info: `{"value": null}`
- **citation_in_text** (`contains`): ❌ FAIL
  - info: `{"haystack": "Inventario SKU-001 - Router AC1200: stock 12, precio 49.99 USD.", "needle": "Fuente:"}`
- **rag_sku_match** (`equals`): ❌ FAIL
  - info: `{"left": null, "right": "SKU-001"}`

## KPIs
- Total checks: **3**
- Passed checks: **0**
- Factual failures: **2**
- Compliance failures: **1**
- RFI (risk-weighted factuality): **0.400**
- EDR (escalation deflection): **1.000**
- NCS (net compliance score): **-1.000**