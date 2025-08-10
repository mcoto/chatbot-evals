# apps/chatbot/main.py
from __future__ import annotations

import os
import glob
import yaml
import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from rag.retriever import Retriever

# ---------- Config ----------
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme")
ORDERS_API = os.getenv("ORDERS_API_URL", "http://orders-api:8000")
BILLING_API = os.getenv("BILLING_API_URL", "http://billing-api:8000")
INVENTORY_API = os.getenv("INVENTORY_API_URL", "http://inventory-api:8000")
POLICY_API = os.getenv("POLICY_API_URL", "http://policy-api:8000")

app = FastAPI(title="chatbot")

# ---------- RAG retriever (lazy) ----------
_retriever: Retriever | None = None
def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()  # usa QDRANT_URL / RAG_COLLECTION del entorno
    return _retriever

# ---------- Modelos ----------
class ChatIn(BaseModel):
    message: str
    order_id: int | None = None
    sku: str | None = None
    lang: str | None = "es"

class ChatOut(BaseModel):
    response: str
    tools_used: list[str] = []
    evidence: dict = {}

# ---------- Utilidades ----------
def _read_with_front_matter(path: str) -> dict:
    """
    Lee archivos .md/.txt con front-matter YAML opcional:
    ---
    sku: SKU-001
    source: manual_sku001_v2.pdf
    lang: es
    valid_from: 2025-08-01
    valid_to:
    version: v2
    tags: [specs, router]
    ---
    <texto libre...>
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    meta = {}
    body = text
    if text.startswith("---"):
        try:
            _, fm, body = text.split("---", 2)
            meta = yaml.safe_load(fm) or {}
        except Exception:
            body = text  # si falla el parseo, usa todo como cuerpo
    meta = meta if isinstance(meta, dict) else {}
    return {"meta": meta, "text": body.strip()}

# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/admin/rag/ingest")
def admin_rag_ingest(
    path: str = "/app/data/rag_corpus",
    pattern: str = "**/*",
    x_admin_token: str | None = Header(None, alias="X-Admin-Token"),
):
    # Auth básica por header
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid admin token")

    exts = (".md", ".txt")
    files = [
        p for p in glob.glob(os.path.join(path, pattern), recursive=True)
        if p.lower().endswith(exts)
    ]
    if not files:
        return {"ingested": 0, "files": []}

    docs = []
    for p in files:
        data = _read_with_front_matter(p)
        meta = data["meta"]
        docs.append({
            "id": None,
            "text": data["text"],
            "sku": meta.get("sku"),
            "source": meta.get("source") or os.path.basename(p),
            "lang": meta.get("lang", "es"),
            "valid_from": meta.get("valid_from"),
            "valid_to": meta.get("valid_to"),
            "version": meta.get("version"),
            "section_id": meta.get("section_id"),
            "tags": meta.get("tags") or [],
        })

    get_retriever().ingest(docs)
    return {"ingested": len(docs), "files": files}

@app.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn):
    tools_used: list[str] = []
    evidence: dict = {}
    parts: list[str] = []  # ¡inicializado antes de usar!

    msg = (body.message or "").lower()
    sku_param = body.sku

    async with httpx.AsyncClient(timeout=5.0) as client:
        # --- Orders ---
        if (body.order_id is not None) or ("pedido" in msg):
            oid = body.order_id or 1
            r = await client.get(f"{ORDERS_API}/orders/{oid}")
            if r.status_code == 200:
                tools_used.append("orders-api")
                evidence["order"] = r.json()
                # Policy si delayed
                if evidence["order"]["status"] == "delayed":
                    pr = await client.get(f"{POLICY_API}/policy/delayed_order_disclaimer")
                    if pr.status_code == 200:
                        tools_used.append("policy-api")
                        evidence["policy"] = pr.json()["value"]

        # --- Billing ---
        if ("factura" in msg) and evidence.get("order"):
            oid = evidence["order"]["id"]
            r = await client.get(f"{BILLING_API}/invoices/by-order/{oid}")
            if r.status_code == 200:
                tools_used.append("billing-api")
                evidence["invoice"] = r.json()

        # --- Inventory ---
        if (sku_param is not None) or ("sku" in msg):
            sku = sku_param or "SKU-001"
            r = await client.get(f"{INVENTORY_API}/inventory/{sku}")
            if r.status_code == 200:
                tools_used.append("inventory-api")
                evidence["inventory"] = r.json()

        # --- RAG (buscar ficha/manual/especificaciones o si hay SKU) ---
        if ("ficha" in msg) or ("manual" in msg) or ("especific" in msg) or (sku_param is not None):
            try:
                rtr = get_retriever()
                q = body.message or (f"Especificaciones del {sku_param}" if sku_param else "ficha técnica")
                flt = {"sku": sku_param} if sku_param else None
                hits = rtr.search(q, top_k=3, filters=flt)
                if hits:
                    tools_used.append("rag")
                    evidence["rag"] = hits
                    top = hits[0]
                    text = top.get("text") or ""
                    first_line = text.splitlines()[0] if text else "(sin contenido)"
                    stale_note = " (ADVERTENCIA: documento desactualizado)" if top.get("valid_to") else ""
                    parts.append(f"Ficha técnica (SKU {top.get('sku')}): {first_line}{stale_note}.")
                    if top.get("source"):
                        parts.append(f"Fuente: {top.get('source')}")
            except Exception as e:
                # No tumbar la respuesta; solo registrar
                evidence["rag_error"] = str(e)

    # --- Ensamblado de respuesta ---
    if "order" in evidence:
        o = evidence["order"]
        parts.append(f"Pedido #{o['id']} está en estado '{o['status']}' con ETA {o['eta']}.")
        if "policy" in evidence:
            parts.append(evidence["policy"]["text"])

    if "invoice" in evidence:
        i = evidence["invoice"]
        parts.append(f"Factura: {i['amount']} {i['currency']}, vence {i['due_date']}.")

    if "inventory" in evidence:
        it = evidence["inventory"]
        stale_inv = " (ADVERTENCIA: ficha desactualizada)" if it.get("valid_to") else ""
        parts.append(
            f"Inventario {it['sku']} - {it['name']}: stock {it['stock']}, "
            f"precio {it['price']} {it['currency']}{stale_inv}."
        )

    if not parts:
        parts.append("¿En qué puedo ayudarle? Puedes consultar pedidos, facturas o inventario (por SKU).")

    return ChatOut(response=" ".join(parts), tools_used=tools_used, evidence=evidence)

