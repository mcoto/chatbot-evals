# Chatbot Evaluation Lab

**A live, end-to-end environment for building, running, and evaluating enterprise chatbots under real-world constraints** — as described in the paper *Towards Reliable Evaluation of Enterprise Chatbots under Real-World Constraints*.

This repository provides:

- An **example enterprise chatbot** with:
  - **RAG** (Retrieval-Augmented Generation) stubs.
  - **Business tool integrations** (Orders, Billing, Inventory, Policies).
  - **Compliance & escalation rules**.
- A **live ground truth** layer via APIs & a PostgreSQL database.
- An **evaluation harness** (coming next) to compute business-aligned KPIs such as:
  - RFI (*Risk-Weighted Factuality Index*)
  - EDR (*Escalation Deflection Rate*)
  - NCS (*Net Compliance Score*)
  - Robustness & relevance metrics.
- A **Streamlit UI** for interaction and inspection.

---

## Motivation

Evaluation of enterprise chatbots should go beyond static accuracy checks.  
Real-world deployments involve:

- **Dynamic data** (orders, billing, inventory) from live systems.
- **Policies** that change over time (compliance, disclaimers).
- **Multi-turn and multilingual interactions**.
- **Business-aligned KPIs** that weigh the risk of errors.

This lab lets you **simulate a real enterprise environment**, generate conversation logs, and evaluate them against a **live or reproducible ground truth**.

---

## Architecture

```

User / Test Scripts
│
▼
Example Chatbot (FastAPI)
│  ├─ RAG (Qdrant + BM25)
│  ├─ Orders API
│  ├─ Billing API
│  ├─ Inventory API
│  └─ Policy API
│
▼
Ground Truth Database (PostgreSQL)
│
▼
Evaluation Harness (coming soon)
│
▼
KPI Reports (HTML / Markdown)

````

---

## Quick Start

### 1. Prerequisites
- **Docker** & **Docker Compose** installed.
- Optional: [Ollama](https://ollama.com/) models pre-pulled if you plan to integrate LLM responses.

### 2. Clone the repository
```bash
git clone https://github.com/your-org/chatbot-eval-lab.git
cd chatbot-eval-lab
````

### 3. Build & run all services

```bash
docker compose up -d --build
```

This will start:

* **PostgreSQL** (`groundtruth-db`)
* **Qdrant** vector DB
* **Ollama** LLM server
* **4 ground truth microservices** (`orders-api`, `billing-api`, `inventory-api`, `policy-api`)
* **Chatbot API** (FastAPI)
* **Evaluation UI** (Streamlit)

---

## 📍 Access Points

| Service          | URL                                                      |
| ---------------- | -------------------------------------------------------- |
| Chatbot API Docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Orders API       | [http://localhost:7001/docs](http://localhost:7001/docs) |
| Billing API      | [http://localhost:7002/docs](http://localhost:7002/docs) |
| Inventory API    | [http://localhost:7003/docs](http://localhost:7003/docs) |
| Policy API       | [http://localhost:7004/docs](http://localhost:7004/docs) |
| Evaluation UI    | [http://localhost:8501](http://localhost:8501)           |

---

## Trying the Chatbot

1. Open the **Evaluation UI** at [http://localhost:8501](http://localhost:8501).
2. Send a message like:

   ```
   Consulta el estado de mi pedido 2 y su factura
   ```
3. The bot will:

   * Call the Orders API and detect status (`delayed` → fetch policy disclaimer).
   * Call the Billing API for invoice details.
   * Return a structured answer, the tools used, and raw evidence.

---

## Project Structure

```
repo/
├── apps/                  # Chatbot code
├── services/              # Ground truth microservices & DB seeds
├── ui/                    # Streamlit UI
├── eval/                  # Evaluation harness (coming soon)
├── docker-compose.yml
└── README.md
```

---

## Environment Variables

You can set these in a `.env` file:

```
DB_NAME=groundtruth
DB_USER=gtuser
DB_PASSWORD=gtpass
MODEL_ID=llama3.1:8b
RAG_COLLECTION=docs
LANGFUSE_ENABLED=false
```

---

## Next Steps

Planned features:

* **Evaluation harness** (`eval/harness`) to run YAML-defined test specs against the chatbot or logs.
* **Hybrid RAG search** with Qdrant + BM25.
* **Multi-turn & multilingual test cases**.
* **Robustness tests** (typos, reformulations, latency injection).
* **CI/CD workflows** to run evaluations nightly and publish KPI reports.

---

## License

MIT License. See `LICENSE` for details.

---

## Related Paper

This repository accompanies the ideas in:

> **Towards Reliable Evaluation of Enterprise Chatbots under Real-World Constraints**
> Marvin Coto, 2025.

---

```

