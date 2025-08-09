from fastapi import FastAPI
from pydantic import BaseModel
import os, httpx

ORDERS_API = os.getenv("ORDERS_API_URL", "http://orders-api:8000")
BILLING_API = os.getenv("BILLING_API_URL", "http://billing-api:8000")
INVENTORY_API = os.getenv("INVENTORY_API_URL", "http://inventory-api:8000")
POLICY_API = os.getenv("POLICY_API_URL", "http://policy-api:8000")

app = FastAPI(title="chatbot")

class ChatIn(BaseModel):
    message: str
    order_id: int | None = None
    sku: str | None = None
    lang: str | None = "es"

class ChatOut(BaseModel):
    response: str
    tools_used: list[str] = []
    evidence: dict = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn):
    tools_used = []
    evidence = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        # demo: si el mensaje menciona "pedido" o hay order_id -> consulta order
        if (body.order_id is not None) or ("pedido" in body.message.lower()):
            oid = body.order_id or 1
            r = await client.get(f"{ORDERS_API}/orders/{oid}")
            if r.status_code == 200:
                tools_used.append("orders-api")
                evidence["order"] = r.json()
                # si está delayed, trae policy
                if evidence["order"]["status"] == "delayed":
                    pr = await client.get(f"{POLICY_API}/policy/delayed_order_disclaimer")
                    if pr.status_code == 200:
                        tools_used.append("policy-api")
                        evidence["policy"] = pr.json()["value"]

        # demo: si menciona "factura" -> consulta billing
        if ("factura" in body.message.lower()) and evidence.get("order"):
            oid = evidence["order"]["id"]
            r = await client.get(f"{BILLING_API}/invoices/by-order/{oid}")
            if r.status_code == 200:
                tools_used.append("billing-api")
                evidence["invoice"] = r.json()

        # demo: si menciona "sku" o hay sku -> inventario
        if (body.sku is not None) or ("sku" in body.message.lower()):
            sku = body.sku or "SKU-001"
            r = await client.get(f"{INVENTORY_API}/inventory/{sku}")
            if r.status_code == 200:
                tools_used.append("inventory-api")
                evidence["inventory"] = r.json()

    # Respuesta rudimentaria (placeholder de LLM)
    parts = []
    if "order" in evidence:
        o = evidence["order"]
        seg = f"Pedido #{o['id']} está en estado '{o['status']}' con ETA {o['eta']}."
        parts.append(seg)
        if "policy" in evidence:
            parts.append(evidence["policy"]["text"])
    if "invoice" in evidence:
        i = evidence["invoice"]
        parts.append(f"Factura: {i['amount']} {i['currency']}, vence {i['due_date']}.")
    if "inventory" in evidence:
        it = evidence["inventory"]
        staleness = " (ADVERTENCIA: ficha desactualizada)" if it.get("valid_to") else ""
        parts.append(f"Inventario {it['sku']} - {it['name']}: stock {it['stock']}, "
                     f"precio {it['price']} {it['currency']}{staleness}.")

    if not parts:
        parts.append("¿En qué puedo ayudarle? Puedes consultar pedidos, facturas o inventario (por SKU).")

    return ChatOut(response=" ".join(parts), tools_used=tools_used, evidence=evidence)

