# Variables
ADMIN_TOKEN ?= supersecret
CHATBOT_HOST ?= http://localhost:8000

.PHONY: seed_rag ingest_rag ingest_rag_all seed_demo

# Siembra los docs demo embebidos en retriever.py
seed_demo:
	docker exec -it chatbot python -m rag.retriever --seed-demo

# Ingesta desde data/rag_corpus/ usando el endpoint admin
ingest_rag:
	curl -s -X POST "$(CHATBOT_HOST)/admin/rag/ingest" \
	 -H "X-Admin-Token: $(ADMIN_TOKEN)" \
	 -H "Content-Type: application/json" \
	 -d '{"path":"/app/data/rag_corpus", "pattern":"**/*.md"}' | jq .

# Alias rápido para ingestar todo (.md y .txt)
ingest_rag_all:
	curl -s -X POST "$(CHATBOT_HOST)/admin/rag/ingest" \
	 -H "X-Admin-Token: $(ADMIN_TOKEN)" \
	 -H "Content-Type: application/json" \
	 -d '{"path":"/app/data/rag_corpus", "pattern":"**/*"}' | jq .

