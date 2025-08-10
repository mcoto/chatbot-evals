import os
import glob
import subprocess
from pathlib import Path
import requests
import streamlit as st

CHATBOT_BASE_URL = os.getenv("CHATBOT_BASE_URL", "http://chatbot:8000")
DEFAULT_ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "supersecret")
DEFAULT_DB_URL = os.getenv("DB_URL", "postgresql+psycopg://gtuser:gtpass@db:5432/groundtruth")

st.set_page_config(page_title="Chatbot Eval Lab — UI", layout="wide")
st.title("Chatbot Eval Lab — Demo UI")

tabs = st.tabs(["💬 Chat", "🧪 Evaluations", "🛠 Admin"])

# ---------------------- Chat ----------------------
with tabs[0]:
    with st.sidebar:
        st.header("Settings")
        chatbot_url = st.text_input("Chatbot URL", value=CHATBOT_BASE_URL)

    st.subheader("Chat")
    with st.form("chat_form"):
        message = st.text_input("Mensaje", value="Muéstrame la ficha técnica del SKU-001")
        order_id = st.number_input("order_id (opcional)", min_value=1, value=2)
        sku = st.text_input("sku (opcional)", value="SKU-001")
        submitted = st.form_submit_button("Enviar")

    if submitted:
        payload = {"message": message}
        if order_id: payload["order_id"] = int(order_id)
        if sku: payload["sku"] = sku
        try:
            resp = requests.post(f"{chatbot_url}/chat", json=payload, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            st.error(f"Error connecting to chatbot: {e}")
        else:
            data = resp.json()
            st.markdown("### Respuesta")
            st.write(data.get("response", ""))

            st.markdown("### Herramientas usadas")
            tools = data.get("tools_used") or []
            st.write(", ".join(tools) if tools else "—")

            st.markdown("### Evidencias")
            ev = data.get("evidence") or {}
            for k in ["order", "invoice", "inventory"]:
                if ev.get(k):
                    st.markdown(f"**{k.capitalize()}**")
                    st.json(ev[k])

            if ev.get("rag"):
                st.markdown("**RAG (top hits)**")
                for i, hit in enumerate(ev["rag"], 1):
                    with st.expander(f"Hit #{i} — {hit.get('source','?')}  (score={hit.get('score',0):.3f})", expanded=(i==1)):
                        st.write(hit.get("text", ""))
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"SKU: `{hit.get('sku')}`")
                        c2.write(f"valid_to: `{hit.get('valid_to')}`")
                        c3.write(f"tags: `{', '.join(hit.get('tags', []))}`")
            if ev.get("rag_error"):
                st.warning(f"RAG error: {ev['rag_error']}")

# ---------------------- Evaluations ----------------------
with tabs[1]:
    st.subheader("Run evaluations (harness)")

    # Paths y defaults
    specs_dir = Path("/app/eval/specs")
    reports_dir = Path("/app/eval/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    colA, colB = st.columns([2, 1])
    with colA:
        spec_files = sorted([str(p) for p in specs_dir.rglob("*.yml")])
        if not spec_files:
            st.info("No spec files found under /app/eval/specs. Mount your repo's eval/specs.")
        spec_path = st.selectbox("Spec file", spec_files, index=0 if spec_files else None)

        chatbot_url_eval = st.text_input("Chatbot URL (override)", value=CHATBOT_BASE_URL)
        db_url_eval = st.text_input("DB URL (override)", value=DEFAULT_DB_URL)

        run_btn = st.button("Run spec")
        if run_btn and spec_path:
            # Ejecuta el harness runner.py como subproceso
            st.write(f"Running: {spec_path}")
            cmd = [
                "python", "eval/harness/runner.py",
                "--spec", spec_path,
                "--chatbot-url", chatbot_url_eval,
                "--db-url", db_url_eval
            ]
            try:
                proc = subprocess.run(
                    cmd, cwd="/app", capture_output=True, text=True, timeout=180
                )
                st.code(" ".join(cmd), language="bash")
                if proc.returncode != 0:
                    st.error("Runner failed")
                    st.code(proc.stderr or proc.stdout)
                else:
                    st.success("Runner completed")
                    st.code(proc.stdout)
            except subprocess.TimeoutExpired:
                st.error("Runner timed out (increase timeout if needed)")

    with colB:
        st.markdown("#### Recent reports")
        # lista los informes más recientes
        report_md = sorted([p for p in reports_dir.rglob("*.md")], key=lambda p: p.stat().st_mtime, reverse=True)
        if report_md:
            selected = st.selectbox("Open report", [str(p) for p in report_md], index=0)
            if selected:
                md_text = Path(selected).read_text(encoding="utf-8")
                st.markdown("---")
                st.markdown(f"**{selected.replace('/app/','')}**")
                st.markdown(md_text)
        else:
            st.info("No reports yet. Run a spec to generate one.")

# ---------------------- Admin ----------------------
with tabs[2]:
    st.subheader("RAG Ingest")
    chatbot_url_admin = st.text_input("Chatbot URL", value=CHATBOT_BASE_URL, key="admin_chatbot_url")
    admin_token = st.text_input("Admin Token", value=DEFAULT_ADMIN_TOKEN, type="password")
    rag_path = st.text_input("Path", "/app/data/rag_corpus")
    rag_pattern = st.text_input("Pattern", "**/*.md")
    if st.button("Ingest RAG now"):
        try:
            r = requests.post(
                f"{chatbot_url_admin}/admin/rag/ingest",
                headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
                json={"path": rag_path, "pattern": rag_pattern},
                timeout=300,
            )
            if r.ok:
                st.success(f"Ingest OK: {r.json()}")
            else:
                st.error(f"Ingest error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")

    st.subheader("Health")
    try:
        r = requests.get(f"{chatbot_url_admin}/health", timeout=5)
        st.json(r.json() if r.ok else {"error": r.text})
    except Exception as e:
        st.error(f"Health check failed: {e}")

