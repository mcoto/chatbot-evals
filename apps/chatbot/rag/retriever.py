# apps/chatbot/rag/retriever.py
from __future__ import annotations
import os, math, uuid
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Embeddings (multilingüe, sirve para ES/EN)
from sentence_transformers import SentenceTransformer
import numpy as np

def _l2_normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12
    return v / n

@dataclass
class RagConfig:
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    collection: str = os.getenv("RAG_COLLECTION", "docs")
    embed_model_name: str = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-base")  # bueno para ES/EN
    vector_size: int = int(os.getenv("RAG_VECTOR_DIM", "768"))  # e5-base = 768

class Retriever:
    """
    Maneja ingest y búsqueda en Qdrant. Convención E5:
      - query => "query: <texto>"
      - doc   => "passage: <texto>"
    Guarda payloads útiles: sku, source, lang, valid_from, valid_to, version, section_id.
    """
    def __init__(self, cfg: Optional[RagConfig] = None):
        self.cfg = cfg or RagConfig()
        self.client = QdrantClient(url=self.cfg.qdrant_url, prefer_grpc=False)
        self.model = SentenceTransformer(self.cfg.embed_model_name)
        self._ensure_collection()

    # ---------- Infra ----------
    def _ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.cfg.collection not in existing:
            self.client.recreate_collection(
                collection_name=self.cfg.collection,
                vectors_config=VectorParams(size=self.cfg.vector_size, distance=Distance.COSINE),
            )

    # ---------- Embeddings ----------
    def _embed_docs(self, texts: List[str]) -> np.ndarray:
        # Convención E5
        inputs = [f"passage: {t}" for t in texts]
        emb = self.model.encode(inputs, convert_to_numpy=True, normalize_embeddings=False, batch_size=32, show_progress_bar=False)
        return _l2_normalize(emb)

    def _embed_query(self, text: str) -> np.ndarray:
        inp = f"query: {text}"
        vec = self.model.encode([inp], convert_to_numpy=True, normalize_embeddings=False)
        return _l2_normalize(vec)[0]

    # ---------- Ingest ----------
    def ingest(self, docs: Iterable[dict], batch: int = 64):
        """
        docs: iterable de dicts con llaves:
          - text (str) [requerido]
          - id (str)   opcional (si no, se genera UUID)
          - sku, source, lang, valid_from, valid_to, version, section_id, tags (opcionales)
        """
        buf_texts, buf_payloads, buf_ids = [], [], []
        for d in docs:
            if not d.get("text"):
                continue
            buf_texts.append(d["text"])
            payload = {
                "text": d["text"],
                "sku": d.get("sku"),
                "source": d.get("source"),
                "lang": d.get("lang", "es"),
                "valid_from": d.get("valid_from"),
                "valid_to": d.get("valid_to"),
                "version": d.get("version"),
                "section_id": d.get("section_id"),
                "tags": d.get("tags", []),
            }
            buf_payloads.append(payload)
            buf_ids.append(d.get("id") or str(uuid.uuid4()))

            if len(buf_texts) >= batch:
                self._flush(buf_ids, buf_texts, buf_payloads)
                buf_texts, buf_payloads, buf_ids = [], [], []

        if buf_texts:
            self._flush(buf_ids, buf_texts, buf_payloads)

    def _flush(self, ids: List[str], texts: List[str], payloads: List[dict]):
        vecs = self._embed_docs(texts)
        points = [
            PointStruct(id=ids[i], vector=vecs[i].tolist(), payload=payloads[i])
            for i in range(len(texts))
        ]
        self.client.upsert(collection_name=self.cfg.collection, points=points)

    # ---------- Query ----------
    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[dict]:
        """
        Devuelve lista de dicts con: text, score, source, sku, valid_to, valid_from, lang.
        filters (opcional): {"sku":"SKU-001", "lang":"es", "tags":["specs"]}
        """
        vec = self._embed_query(query)
        flt: Optional[Filter] = None
        if filters:
            conds = []
            for k, v in filters.items():
                if v is None:
                    continue
                if isinstance(v, list):
                    # match cualquiera (OR)
                    for item in v:
                        conds.append(FieldCondition(key=k, match=MatchValue(value=item)))
                else:
                    conds.append(FieldCondition(key=k, match=MatchValue(value=v)))
            if conds:
                flt = Filter(must=conds)

        res = self.client.search(
            collection_name=self.cfg.collection,
            query_vector=vec.tolist(),
            limit=top_k,
            query_filter=flt,
            with_payload=True,
            with_vectors=False,
        )
        out = []
        for r in res:
            p = r.payload or {}
            out.append({
                "text": p.get("text"),
                "score": float(r.score),
                "source": p.get("source"),
                "sku": p.get("sku"),
                "lang": p.get("lang"),
                "valid_from": p.get("valid_from"),
                "valid_to": p.get("valid_to"),
                "version": p.get("version"),
                "section_id": p.get("section_id"),
                "tags": p.get("tags", []),
            })
        return out

# ---------- Semilla demo desde CLI ----------
DEMO_TEXT_SKU001 = """Especificaciones del SKU-001 (Router AC1200):
- WiFi de doble banda 2.4/5 GHz
- 4 puertos LAN
- Garantía 12 meses
"""
DEMO_TEXT_SKU002_OLD = """Especificaciones del SKU-002 (Switch 8 puertos):
- 8 puertos 10/100/1000
- QoS básica
- Manual versión 2023-02
"""

def seed_demo():
    cfg = RagConfig()
    retr = Retriever(cfg)
    retr.ingest([
        {
            "sku": "SKU-001",
            "source": "manual_sku001_v1.pdf",
            "lang": "es",
            "valid_from": "2025-06-01",
            "valid_to": None,
            "version": "v1",
            "section_id": "specs",
            "tags": ["specs", "router"],
            "text": DEMO_TEXT_SKU001.strip(),
        },
        {
            "sku": "SKU-002",
            "source": "manual_sku002_v1.pdf",
            "lang": "es",
            "valid_from": "2023-02-01",
            "valid_to": "2025-06-30",  # para provocar staleness
            "version": "v1",
            "section_id": "specs",
            "tags": ["specs", "switch"],
            "text": DEMO_TEXT_SKU002_OLD.strip(),
        },
    ])
    print("✅ RAG demo seeded into Qdrant collection:", cfg.collection)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--seed-demo":
        seed_demo()
    else:
        print("Usage: python -m apps.chatbot.rag.retriever --seed-demo")

