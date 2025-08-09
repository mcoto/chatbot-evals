import os, requests, json
import streamlit as st

CHATBOT_BASE_URL = os.getenv("CHATBOT_BASE_URL", "http://chatbot:8000")

st.title("Creai Labs - Chatbot Eval (Demo UI)")

with st.form("chat"):
    msg = st.text_input("Mensaje", value="Consulta el estado de mi pedido 2 y su factura")
    order_id = st.number_input("order_id (opcional)", min_value=1, value=2)
    sku = st.text_input("sku (opcional)", value="SKU-001")
    submitted = st.form_submit_button("Enviar")

if submitted:
    payload = {"message": msg, "order_id": int(order_id), "sku": sku}
    r = requests.post(f"{CHATBOT_BASE_URL}/chat", json=payload, timeout=10)
    if r.ok:
        data = r.json()
        st.subheader("Respuesta")
        st.write(data["response"])
        st.subheader("Herramientas usadas")
        st.write(", ".join(data["tools_used"]) or "Ninguna")
        st.subheader("Evidencias")
        st.json(data["evidence"])
    else:
        st.error(f"Error: {r.status_code} {r.text}")

