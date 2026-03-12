# MolecularML Platform

End-to-end scientific ML platform for **molecular property prediction** and **protein similarity search** — built for drug discovery and computational biology workflows.

**Live Demo:** [Frontend on Vercel](#) | [API on HuggingFace Spaces](#)

## What It Does

| Feature | Details |
|---|---|
| Molecular property prediction | PyTorch MLP on Morgan fingerprints (RDKit) — solubility, lipophilicity, toxicity |
| Protein similarity search | ESM-2 embeddings + FAISS vector index — top-k similar proteins from UniProt |
| Analytics dashboard | Real-time API metrics: P50/P95/P99 latency, request counts, model health |
| Lipinski Rule of Five | Drug-likeness evaluation for every molecule |

## Architecture

```
React (Vercel)
    │
    │  REST API
    ▼
FastAPI backend (HuggingFace Spaces / Docker)
    ├── POST /predict   → RDKit fingerprints → PyTorch MLP → property scores
    ├── POST /search    → ESM-2 embeddings  → FAISS index → top-k proteins
    ├── GET  /health    → model status, uptime
    └── GET  /metrics   → P50/P95 latency, request counts, recent logs

GitHub Actions CI/CD → auto-deploys backend to HF Spaces, frontend to Vercel
Helm chart included for Kubernetes deployment
```

## Tech Stack

- **Backend:** Python, FastAPI, PyTorch, RDKit, HuggingFace Transformers (ESM-2), FAISS
- **Frontend:** React, Vite, JavaScript
- **Infrastructure:** Docker, Kubernetes (Helm), GitHub Actions CI/CD
- **Deployment:** HuggingFace Spaces (backend), Vercel (frontend)
- **Monitoring:** Custom observability with P50/P95/P99 latency tracking

## Quick Start

### Backend (local)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 7860
# API docs: http://localhost:7860/docs
```

### Frontend (local)
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:7860" > .env.local
npm run dev
# App: http://localhost:3000
```

### Docker
```bash
cd backend
docker build -t molecularml-backend .
docker run -p 7860:7860 molecularml-backend
```

## Deployment

### Backend → HuggingFace Spaces
1. Create a Space at huggingface.co (Docker SDK)
2. Add `HF_TOKEN` and `HF_USERNAME` to GitHub Secrets
3. Push to `main` — GitHub Actions deploys automatically

### Frontend → Vercel
1. Connect repo to Vercel
2. Set `VITE_API_URL` environment variable to your HF Spaces URL
3. Add `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` to GitHub Secrets
4. Push to `main` — deploys automatically

### Kubernetes (optional)
```bash
helm install molecularml ./helm --values helm/values.yaml
```

## API Reference

```
GET  /health              → system health, model status, uptime
GET  /metrics             → P50/P95/P99 latency, request counts per endpoint
POST /predict             → molecular property prediction
POST /search              → protein similarity search
GET  /molecules/examples  → example SMILES strings
GET  /proteins/examples   → example protein sequences
```

### Example: Predict molecular properties
```bash
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{"smiles": "CC(=O)Oc1ccccc1C(=O)O", "properties": ["solubility", "toxicity"]}'
```

### Example: Search similar proteins
```bash
curl -X POST http://localhost:7860/search \
  -H "Content-Type: application/json" \
  -d '{"sequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT", "top_k": 5}'
```

## Results

- Sub-second prediction latency for molecular property inference
- FAISS protein search across indexed database with cosine similarity scoring
- P50/P95/P99 latency tracked per endpoint via built-in observability
- Full CI/CD pipeline: lint → test → build → deploy on every push to main

## Project Structure

```
molecularml-platform/
├── backend/
│   ├── main.py                        # FastAPI app, all endpoints
│   ├── models/
│   │   ├── property_predictor.py      # PyTorch MLP + RDKit fingerprints
│   │   └── protein_search.py          # ESM-2 embeddings + FAISS
│   ├── monitoring.py                  # Observability: latency, request tracking
│   ├── tests/test_api.py              # API test suite
│   ├── Dockerfile                     # HuggingFace Spaces deployment
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                    # Main app + tab routing
│   │   ├── api.js                     # Centralized API client
│   │   └── components/
│   │       ├── MoleculePredictor.jsx  # SMILES input + property results
│   │       ├── ProteinSearch.jsx      # Sequence input + similarity results
│   │       └── Dashboard.jsx          # Real-time analytics dashboard
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── helm/values.yaml                   # Kubernetes Helm chart
├── scripts/deploy_hf.py               # HuggingFace deploy script
└── .github/workflows/ci.yml           # GitHub Actions CI/CD
```
