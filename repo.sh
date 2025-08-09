#!/bin/bash
# create_project_structure.sh
# Script to create the Chatbot Evaluation Lab folder structure

mkdir -p ./{apps/chatbot/{rag,tools},services/{groundtruth-db/init,orders-api,billing-api,inventory-api,policy-api},ui,eval/{specs/{es,en},harness,reports},data/{rag_corpus,seeds,fixtures}}

# --- Root files ---
touch ./docker-compose.yml
touch ./README.md

# --- Apps / Chatbot ---
touch ./apps/chatbot/{Dockerfile,requirements.txt,main.py,agent.py}
touch ./apps/chatbot/rag/{__init__.py,retriever.py}
touch ./apps/chatbot/tools/{__init__.py,orders_client.py,billing_client.py,inventory_client.py,policy_client.py}

# --- Services ---
# DB seeds
touch ./services/groundtruth-db/init/00_init.sql

# Microservices files
for svc in orders-api billing-api inventory-api policy-api; do
  touch ./services/$svc/{Dockerfile,requirements.txt,main.py}
done

# --- UI ---
touch ./ui/{Dockerfile,requirements.txt,app.py}

# --- Eval harness ---
touch ./eval/harness/{runner.py,comparators.py,kpis.py,robustness.py}

# Specs YAML placeholders
touch ./eval/specs/es/{order_status_simple.yml,billing_disclaimer.yml}
touch ./eval/specs/en/order_status_simple.yml

# --- Data ---
touch ./data/rag_corpus/.gitkeep
touch ./data/seeds/.gitkeep
touch ./data/fixtures/.gitkeep

echo "✅ Project structure created under ././"

