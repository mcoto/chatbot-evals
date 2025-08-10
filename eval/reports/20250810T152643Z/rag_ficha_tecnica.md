# Evaluation Report — rag_ficha_tecnica

- Timestamp (UTC): 2025-08-10T15:26:43.371899Z
- Risk weight: 0.6

## Checks
- **rag_used** (`not_null`): ✅ PASS
  - info: `{"value": [{"text": "Especificaciones actualizadas del SKU-001:\n- WiFi 2.4/5 GHz con MU-MIMO\n- 4 puertos LAN Gigabit\n- Garantía 24 meses", "score": 0.84093964, "source": "manual_sku001_v2.pdf", "sku": "SKU-001", "lang": "es", "valid_from": "2025-08-01", "valid_to": null, "version": "v2", "section_id": null, "tags": ["specs", "router"]}]}`
- **citation_in_text** (`contains`): ❌ FAIL
  - info: `{"haystack": "Inventario SKU-001 - Router AC1200: stock 12, precio 49.99 USD.", "needle": "Fuente:"}`
- **rag_sku_match** (`equals`): ✅ PASS
  - info: `{"left": "SKU-001", "right": "SKU-001"}`

## KPIs
- Total checks: **3**
- Passed checks: **2**
- Factual failures: **0**
- Compliance failures: **1**
- RFI (risk-weighted factuality): **0.000**
- EDR (escalation deflection): **1.000**
- NCS (net compliance score): **-1.000**