import { useState, useEffect } from "react";
import { api } from "../api";

const PROPERTY_OPTIONS = ["solubility", "lipophilicity", "toxicity"];

const INTERPRETATION_BADGE = {
  high: "badge-green", moderate: "badge-yellow", low: "badge-gray",
  "low risk": "badge-green", "moderate risk": "badge-yellow", "high risk": "badge-red",
};

export default function MoleculePredictor() {
  const [smiles, setSmiles]         = useState("");
  const [properties, setProperties] = useState(PROPERTY_OPTIONS);
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
  const [examples, setExamples]     = useState([]);

  useEffect(() => {
    api.exampleMolecules().then(d => setExamples(d.examples)).catch(() => {});
  }, []);

  const toggleProp = (p) =>
    setProperties(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);

  const predict = async () => {
    if (!smiles.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await api.predict(smiles.trim(), properties);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const lipinski = result?.predictions?.lipinski_rule_of_five;

  return (
    <div>
      <h1 className="page-title">Molecular Property Predictor</h1>
      <p className="page-sub">Enter a SMILES string to predict solubility, lipophilicity, and toxicity using a PyTorch MLP on Morgan fingerprints.</p>

      <div className="card">
        <div className="card-title">Input</div>

        <label>SMILES string</label>
        <div className="row" style={{ marginBottom: 16 }}>
          <input
            className="flex1"
            value={smiles}
            onChange={e => setSmiles(e.target.value)}
            placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
            onKeyDown={e => e.key === "Enter" && predict()}
          />
          <button className="btn btn-primary" onClick={predict} disabled={loading || !smiles.trim()}>
            {loading && <span className="spinner" />}
            {loading ? "Predicting..." : "Predict"}
          </button>
        </div>

        <label>Properties</label>
        <div className="chip-row">
          {PROPERTY_OPTIONS.map(p => (
            <span key={p} className={`chip ${properties.includes(p) ? "active" : ""}`} onClick={() => toggleProp(p)}>
              {p}
            </span>
          ))}
        </div>

        {examples.length > 0 && (
          <>
            <label style={{ marginTop: 12 }}>Examples</label>
            <div className="chip-row">
              {examples.map(ex => (
                <span key={ex.name} className="chip" onClick={() => setSmiles(ex.smiles)}>{ex.name}</span>
              ))}
            </div>
          </>
        )}

        {error && <div className="error-box">{error}</div>}
      </div>

      {result && (
        <>
          <div className="card">
            <div className="card-title">Predicted Properties</div>
            {Object.entries(result.predictions.properties).map(([name, data]) => (
              <div className="prop-row" key={name}>
                <div>
                  <span className="prop-name" style={{ textTransform: "capitalize" }}>{name}</span>
                  <span className="prop-unit">{data.unit}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="prop-value">{data.value}</span>
                  <span className={`badge ${INTERPRETATION_BADGE[data.interpretation] || "badge-gray"}`}>
                    {data.interpretation}
                  </span>
                </div>
              </div>
            ))}
            <div style={{ marginTop: 12, fontSize: 12, color: "#9ca3af" }}>
              Latency: {result.latency_ms}ms
            </div>
          </div>

          <div className="card">
            <div className="card-title">Molecular Descriptors</div>
            <div className="desc-row">
              {Object.entries(result.predictions.descriptors).map(([k, v]) => (
                <div className="desc-item" key={k}>
                  <span>{k.replace(/_/g, " ")}: </span>
                  <strong>{v}</strong>
                </div>
              ))}
            </div>
          </div>

          {lipinski && (
            <div className="card">
              <div className="card-title">Lipinski Rule of Five</div>
              <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                <span className={`badge ${lipinski.passes ? "badge-green" : "badge-red"}`} style={{ fontSize: 14, padding: "4px 12px" }}>
                  {lipinski.passes ? "Passes" : "Fails"} Rule of Five
                </span>
                <span style={{ fontSize: 13, color: "#6b7280" }}>
                  {lipinski.violations} violation{lipinski.violations !== 1 ? "s" : ""}
                </span>
                <span className={`badge ${lipinski.drug_like ? "badge-green" : "badge-yellow"}`}>
                  {lipinski.drug_like ? "Drug-like" : "Not drug-like"}
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
