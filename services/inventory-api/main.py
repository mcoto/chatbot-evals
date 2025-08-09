from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://gtuser:gtpass@db:5432/groundtruth")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="inventory-api")

class ItemOut(BaseModel):
    sku: str
    name: str
    stock: int
    price: float
    currency: str
    valid_from: str
    valid_to: str | None

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status":"ok"}

@app.get("/inventory/{sku}", response_model=ItemOut)
def get_item(sku: str):
    q = text("""
        SELECT sku, name, stock, price::float, currency,
               valid_from::text, valid_to::text
        FROM inventory WHERE sku=:sku
    """)
    with engine.connect() as conn:
        row = conn.execute(q, {"sku": sku}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="sku not found")
    return row

