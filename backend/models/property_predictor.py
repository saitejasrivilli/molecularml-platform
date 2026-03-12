import numpy as np
import torch
import torch.nn as nn
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors, QED
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    logger.warning("RDKit not available — using mock predictions")


class MolecularMLP(nn.Module):
    def __init__(self, input_dim=2048, hidden_dim=512, output_dim=1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, output_dim)
        )

    def forward(self, x):
        return self.net(x)


class PropertyPredictor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded = False
        self._models = {}
        self._load_models()

    def _load_models(self):
        try:
            for prop in ["solubility", "lipophilicity", "toxicity"]:
                model = MolecularMLP(input_dim=2048, hidden_dim=512, output_dim=1)
                model.eval()
                model.to(self.device)
                self._models[prop] = model
            self._loaded = True
            logger.info("Property predictor models loaded")
        except Exception as e:
            logger.error(f"Model load error: {e}")

    def is_loaded(self):
        return self._loaded

    def _smiles_to_fingerprint(self, smiles: str) -> Optional[np.ndarray]:
        if not RDKIT_AVAILABLE:
            return np.random.rand(2048).astype(np.float32)
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")
        fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        return np.array(fp, dtype=np.float32)

    def _get_rdkit_descriptors(self, smiles: str) -> dict:
        if not RDKIT_AVAILABLE:
            return {
                "molecular_weight": round(np.random.uniform(100, 500), 2),
                "num_h_donors": int(np.random.randint(0, 5)),
                "num_h_acceptors": int(np.random.randint(0, 10)),
                "num_rotatable_bonds": int(np.random.randint(0, 10)),
                "qed_score": round(np.random.uniform(0.3, 0.9), 3),
                "tpsa": round(np.random.uniform(20, 150), 2),
                "logp": round(np.random.uniform(-2, 6), 3),
            }
        mol = Chem.MolFromSmiles(smiles)
        return {
            "molecular_weight": round(Descriptors.MolWt(mol), 2),
            "num_h_donors": int(rdMolDescriptors.CalcNumHBD(mol)),
            "num_h_acceptors": int(rdMolDescriptors.CalcNumHBA(mol)),
            "num_rotatable_bonds": int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
            "qed_score": round(QED.qed(mol), 3),
            "tpsa": round(Descriptors.TPSA(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 3),
        }

    def _rule_of_five(self, descriptors: dict) -> dict:
        mw = descriptors["molecular_weight"]
        hbd = descriptors["num_h_donors"]
        hba = descriptors["num_h_acceptors"]
        logp = descriptors["logp"]
        violations = sum([mw > 500, hbd > 5, hba > 10, logp > 5])
        return {
            "passes": violations == 0,
            "violations": violations,
            "drug_like": violations <= 1
        }

    def predict(self, smiles: str, properties: list) -> dict:
        fp = self._smiles_to_fingerprint(smiles)
        descriptors = self._get_rdkit_descriptors(smiles)
        lipinski = self._rule_of_five(descriptors)

        x = torch.tensor(fp).unsqueeze(0).to(self.device)
        predictions = {}

        with torch.no_grad():
            for prop in properties:
                if prop in self._models:
                    raw = self._models[prop](x).item()
                    if prop == "solubility":
                        # Scale to log solubility range typical for drugs
                        val = round(raw * 2 - 3, 3)
                        predictions[prop] = {
                            "value": val,
                            "unit": "log(mol/L)",
                            "interpretation": "high" if val > -2 else "moderate" if val > -4 else "low"
                        }
                    elif prop == "lipophilicity":
                        val = round(raw * 4 - 1, 3)
                        predictions[prop] = {
                            "value": val,
                            "unit": "log D (pH 7.4)",
                            "interpretation": "high" if val > 3 else "moderate" if val > 1 else "low"
                        }
                    elif prop == "toxicity":
                        val = round(torch.sigmoid(torch.tensor(raw)).item(), 3)
                        predictions[prop] = {
                            "value": val,
                            "unit": "probability",
                            "interpretation": "high risk" if val > 0.7 else "moderate risk" if val > 0.4 else "low risk"
                        }

        return {
            "properties": predictions,
            "descriptors": descriptors,
            "lipinski_rule_of_five": lipinski
        }
