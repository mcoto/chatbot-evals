from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, json
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://gtuser:gtpass@db:5432/groundtruth")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="policy-api")

class PolicyOut(BaseModel):
    key: str
    value: dict

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status":"ok"}

@app.get("/policy/{key}", response_model=PolicyOut)
def get_policy(key: str):
    q = text("SELECT key, value::text FROM policies WHERE key=:k")
    with engine.connect() as conn:
        row = conn.execute(q, {"k": key}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="policy not found")
    return {"key": row["key"], "value": json.loads(row["value"])}

