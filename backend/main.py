from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import logging

from models.property_predictor import PropertyPredictor
from models.protein_search import ProteinSearch
from monitoring import log_request, get_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MolecularML Platform",
    description="End-to-end scientific ML platform for molecular property prediction and protein similarity search",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

property_predictor = PropertyPredictor()
protein_search = ProteinSearch()

START_TIME = time.time()


class MoleculeRequest(BaseModel):
    smiles: str
    properties: Optional[list[str]] = ["solubility", "lipophilicity", "toxicity"]


class ProteinRequest(BaseModel):
    sequence: str
    top_k: Optional[int] = 5


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "models_loaded": {
            "property_predictor": property_predictor.is_loaded(),
            "protein_search": protein_search.is_loaded(),
        },
        "version": "1.0.0"
    }


@app.get("/metrics")
def metrics():
    return get_metrics()


@app.post("/predict")
def predict_properties(req: MoleculeRequest):
    start = time.time()
    try:
        result = property_predictor.predict(req.smiles, req.properties)
        latency = round((time.time() - start) * 1000, 2)
        log_request("predict", req.smiles[:20], latency, success=True)
        return {"smiles": req.smiles, "predictions": result, "latency_ms": latency}
    except ValueError as e:
        log_request("predict", req.smiles[:20], 0, success=False)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")


@app.post("/search")
def search_proteins(req: ProteinRequest):
    start = time.time()
    try:
        results = protein_search.search(req.sequence, req.top_k)
        latency = round((time.time() - start) * 1000, 2)
        log_request("search", req.sequence[:20], latency, success=True)
        return {
            "query_sequence": req.sequence[:50] + "..." if len(req.sequence) > 50 else req.sequence,
            "results": results,
            "latency_ms": latency
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/molecules/examples")
def get_example_molecules():
    return {"examples": [
        {"name": "Aspirin",     "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
        {"name": "Caffeine",    "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C"},
        {"name": "Ibuprofen",   "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O"},
        {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1"},
        {"name": "Penicillin G","smiles": "CC1(C)SC2C(NC(=O)Cc3ccccc3)C(=O)N2C1C(=O)O"},
    ]}


@app.get("/proteins/examples")
def get_example_proteins():
    return {"examples": [
        {"name": "Insulin (partial)",  "sequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT"},
        {"name": "Lysozyme (partial)", "sequence": "KVFGRCELAAAMKRHGLDNYRGYSLGNWVCAAKFESNFNTQATNRNTDGSTDYGILQINSRWWCNDGRTPGSRNLCNIPCSALLSSDITASVNCAKKIVSDGNGMNAWVAWRNRCKGTDVQAWIRGCRL"},
        {"name": "GFP (partial)",      "sequence": "MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTLTYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYK"},
    ]}
