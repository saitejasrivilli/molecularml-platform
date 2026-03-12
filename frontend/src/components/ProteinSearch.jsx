import { useState, useEffect } from "react";
import { api } from "../api";

export default function ProteinSearch() {
  const [sequence, setSequence] = useState("");
  const [topK, setTopK]         = useState(5);
  const [results, setResults]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [examples, setExamples] = useState([]);

  useEffect(() => {
    api.exampleProteins().then(d => setExamples(d.examples)).catch(() => {});
  }, []);

  const search = async () => {
    if (!sequence.trim()) return;
    setLoading(true); setError(null); setResults(null);
    try {
      const data = await api.search(sequence.trim(), topK);
      setResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (score) => {
    if (score > 0.8) return "#166534";
    if (score > 0.5) return "#854d0e";
    return "#374151";
  };

  return (
    <div>
      <h1 className="page-title">Protein Similarity Search</h1>
      <p className="page-sub">Enter an amino acid sequence to find similar proteins using ESM-2 embeddings and FAISS vector search.</p>

      <div className="card">
        <div className="card-title">Query Sequence</div>

        <label>Amino acid sequence (single-letter code)</label>
        <textarea
          value={sequence}
          onChange={e => setSequence(e.target.value)}
          placeholder="MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT"
          style={{ marginBottom: 16 }}
        />

        <div className="row" style={{ marginBottom: 16 }}>
          <div className="flex1">
            <label>Top-K results</label>
            <select value={topK} onChange={e => setTopK(Number(e.target.value))}>
              {[3, 5, 8].map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <button className="btn btn-primary" onClick={search} disabled={loading || !sequence.trim()}>
            {loading && <span className="spinner" />}
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {examples.length > 0 && (
          <>
            <label>Examples</label>
            <div className="chip-row">
              {examples.map(ex => (
                <span key={ex.name} className="chip" onClick={() => setSequence(ex.sequence)}>{ex.name}</span>
              ))}
            </div>
          </>
        )}

        {error && <div className="error-box">{error}</div>}
      </div>

      {results && (
        <div className="card">
          <div className="card-title">
            Similar Proteins
            <span style={{ fontSize: 13, color: "#9ca3af", fontWeight: 400, marginLeft: 8 }}>
              {results.latency_ms}ms
            </span>
          </div>
          {results.results.map((r) => (
            <div className="result-card" key={r.rank}>
              <div className="result-rank">Rank #{r.rank}</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div className="result-name">{r.name}</div>
                  <div className="result-org">{r.organism} · {r.uniprot_id}</div>
                  <div className="result-func">{r.function}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 20, fontWeight: 600, color: scoreColor(r.similarity_score) }}>
                    {(r.similarity_score * 100).toFixed(1)}%
                  </div>
                  <div style={{ fontSize: 11, color: "#9ca3af" }}>similarity</div>
                </div>
              </div>
              <div className="result-seq">{r.sequence_preview}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
