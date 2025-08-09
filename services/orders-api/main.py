from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://gtuser:gtpass@db:5432/groundtruth")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="orders-api")

class OrderOut(BaseModel):
    id: int
    customer_id: int | None
    status: str
    eta: str | None

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int):
    q = text("SELECT id, customer_id, status, eta::text FROM orders WHERE id=:id")
    with engine.connect() as conn:
        row = conn.execute(q, {"id": order_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="order not found")
    return row

