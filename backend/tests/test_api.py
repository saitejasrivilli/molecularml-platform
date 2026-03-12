import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert "models_loaded" in data


def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200


def test_example_molecules():
    r = client.get("/molecules/examples")
    assert r.status_code == 200
    assert len(r.json()["examples"]) > 0


def test_example_proteins():
    r = client.get("/proteins/examples")
    assert r.status_code == 200
    assert len(r.json()["examples"]) > 0


def test_predict_valid_smiles():
    r = client.post("/predict", json={"smiles": "CC(=O)Oc1ccccc1C(=O)O"})
    assert r.status_code == 200
    data = r.json()
    assert "predictions" in data
    assert "latency_ms" in data


def test_predict_invalid_smiles():
    r = client.post("/predict", json={"smiles": "NOT_A_SMILES_STRING!!!"})
    assert r.status_code in [400, 200]


def test_search_valid_sequence():
    r = client.post("/search", json={"sequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT", "top_k": 3})
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert len(data["results"]) <= 3


def test_search_short_sequence():
    r = client.post("/search", json={"sequence": "MAL"})
    assert r.status_code == 400


def test_metrics_after_requests():
    client.post("/predict", json={"smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C"})
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "endpoints" in data
