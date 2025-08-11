# apps/chatbot/llm/ollama_client.py
from __future__ import annotations
import os, httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
MODEL_ID = os.getenv("MODEL_ID", "llama3.1:8b")

async def chat_ollama(messages: list[dict], temperature: float = 0.2, timeout: float = 25.0) -> str:
    """
    Usa /api/chat de Ollama. messages = [{"role":"system"/"user"/"assistant","content":"..."}]
    """
    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        # formato típico: {"message":{"role":"assistant","content":"..."}}
        return data.get("message", {}).get("content", "").strip()

