#!/usr/bin/env bash
# smoke_test.sh — End-to-end smoke tests for Chatbot Eval Lab

set -euo pipefail

CHATBOT_URL="${CHATBOT_URL:-http://localhost:8000}"
ORDERS_URL="${ORDERS_URL:-http://localhost:7001}"
BILLING_URL="${BILLING_URL:-http://localhost:7002}"
INVENTORY_URL="${INVENTORY_URL:-http://localhost:7003}"
POLICY_URL="${POLICY_URL:-http://localhost:7004}"

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then HAS_JQ=1; fi

log()   { echo -e "\033[1;34m[INFO]\033[0m $*"; }
pass()  { echo -e "\033[1;32m[PASS]\033[0m $*"; }
fail()  { echo -e "\033[1;31m[FAIL]\033[0m $*"; }

wait_for() {
  local url="$1" name="$2" timeout="${3:-60}"
  log "Waiting for $name at $url (timeout ${timeout}s)"
  local start=$(date +%s)
  until curl -sf "$url" >/dev/null 2>&1; do
    sleep 2
    now=$(date +%s)
    if (( now - start > timeout )); then
      fail "Timeout waiting for $name"
      return 1
    fi
  done
  pass "$name is up"
}

pretty_json() {
  if [[ "$HAS_JQ" -eq 1 ]]; then jq -r '.'; else cat; fi
}

post_json() {
  local url="$1" body="$2"
  curl -s -f -H "Content-Type: application/json" -d "$body" "$url"
}

divider() { echo -e "\n\033[90m────────────────────────────────────────────────────────\033[0m\n"; }

main() {
  # 1) Wait for services
  wait_for "$ORDERS_URL/health"     "orders-api"
  wait_for "$BILLING_URL/health"    "billing-api"
  wait_for "$INVENTORY_URL/health"  "inventory-api"
  wait_for "$POLICY_URL/health"     "policy-api"
  wait_for "$CHATBOT_URL/health"    "chatbot"

  divider

  # 2) Test A: order status + billing (order_id=2 is 'delayed' in seeds)
  log "Test A: Order status + billing (ES, order_id=2)"
  BODY_A='{"message":"Consulta el estado de mi pedido 2 y su factura","order_id":2}'
  RESP_A=$(post_json "$CHATBOT_URL/chat" "$BODY_A") || { fail "Chatbot request failed (A)"; exit 1; }
  echo "$RESP_A" | pretty_json

  # Basic assertions
  if [[ "$(echo "$RESP_A" | jq -r '.tools_used[]?' 2>/dev/null | grep -c 'orders-api' || true)" -lt 1 ]]; then
    fail "Expected 'orders-api' to be used in Test A"; exit 1
  fi
  if [[ "$(echo "$RESP_A" | jq -r '.tools_used[]?' 2>/dev/null | grep -c 'billing-api' || true)" -lt 1 ]]; then
    fail "Expected 'billing-api' to be used in Test A"; exit 1
  fi
  pass "Test A assertions passed"

  divider

  # 3) Test B: inventory with current spec (SKU-001)
  log "Test B: Inventory lookup (SKU-001)"
  BODY_B='{"message":"Consulta inventario del sku SKU-001","sku":"SKU-001"}'
  RESP_B=$(post_json "$CHATBOT_URL/chat" "$BODY_B") || { fail "Chatbot request failed (B)"; exit 1; }
  echo "$RESP_B" | pretty_json
  if [[ "$(echo "$RESP_B" | jq -r '.tools_used[]?' 2>/dev/null | grep -c 'inventory-api' || true)" -lt 1 ]]; then
    fail "Expected 'inventory-api' to be used in Test B"; exit 1
  fi
  pass "Test B assertions passed"

  divider

  # 4) Test C: inventory with stale spec (SKU-002 has valid_to set in seeds)
  log "Test C: Inventory lookup with staleness warning (SKU-002)"
  BODY_C='{"message":"Consulta inventario del sku SKU-002","sku":"SKU-002"}'
  RESP_C=$(post_json "$CHATBOT_URL/chat" "$BODY_C") || { fail "Chatbot request failed (C)"; exit 1; }
  echo "$RESP_C" | pretty_json
  if [[ "$(echo "$RESP_C" | jq -r '.tools_used[]?' 2>/dev/null | grep -c 'inventory-api' || true)" -lt 1 ]]; then
    fail "Expected 'inventory-api' to be used in Test C"; exit 1
  fi

  # Optional: check for staleness hint in response text
  if echo "$RESP_C" | jq -r '.response' 2>/dev/null | grep -qi 'ADVERTENCIA'; then
    pass "Test C staleness hint detected"
  else
    log "Note: staleness hint not detected in response text (check seeds/logic)"
  fi

  divider
  pass "All smoke tests completed successfully ✅"
}

main "$@"

