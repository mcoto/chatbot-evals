from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://gtuser:gtpass@db:5432/groundtruth")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="billing-api")

class InvoiceOut(BaseModel):
    id: int
    order_id: int
    amount: float
    currency: str
    due_date: str
    paid: bool

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/invoices/by-order/{order_id}", response_model=InvoiceOut)
def by_order(order_id: int):
    q = text("""
        SELECT id, order_id, amount::float, currency, due_date::text, paid
        FROM invoices WHERE order_id=:oid
    """)
    with engine.connect() as conn:
        row = conn.execute(q, {"oid": order_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="invoice not found")
    return row

