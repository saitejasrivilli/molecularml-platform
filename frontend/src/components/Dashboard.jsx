import { useState, useEffect, useCallback } from "react";
import { api } from "../api";

export default function Dashboard() {
  const [metrics, setMetrics]   = useState(null);
  const [health, setHealth]     = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);

  const load = useCallback(async () => {
    try {
      const [m, h] = await Promise.all([api.metrics(), api.health()]);
      setMetrics(m);
      setHealth(h);
      setLastRefresh(new Date().toLocaleTimeString());
      setError(null);
    } catch (e) {
      setError("Could not reach API — is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, [load]);

  const totalRequests = metrics
    ? Object.values(metrics.endpoints).reduce((s, e) => s + e.total, 0)
    : 0;
  const totalSuccess = metrics
    ? Object.values(metrics.endpoints).reduce((s, e) => s + e.success, 0)
    : 0;
  const avgLatency = metrics && Object.keys(metrics.endpoints).length > 0
    ? (Object.values(metrics.endpoints).reduce((s, e) => s + e.avg_latency_ms, 0) /
       Object.keys(metrics.endpoints).length).toFixed(1)
    : "—";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <h1 className="page-title">Analytics Dashboard</h1>
          <p className="page-sub">Real-time API metrics and system health. Auto-refreshes every 15s.</p>
        </div>
        <button className="btn btn-secondary" onClick={load} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && <div className="error-box" style={{ marginBottom: 20 }}>{error}</div>}

      {health && (
        <div className="card">
          <div className="card-title">System Health</div>
          <div className="grid4">
            <div className="metric-card">
              <div className="metric-val" style={{ color: health.status === "healthy" ? "#166534" : "#991b1b" }}>
                {health.status}
              </div>
              <div className="metric-label">API status</div>
            </div>
            <div className="metric-card">
              <div className="metric-val">{Math.round(health.uptime_seconds)}s</div>
              <div className="metric-label">Uptime</div>
            </div>
            <div className="metric-card">
              <div className="metric-val" style={{ color: health.models_loaded.property_predictor ? "#166534" : "#991b1b" }}>
                {health.models_loaded.property_predictor ? "loaded" : "error"}
              </div>
              <div className="metric-label">Property predictor</div>
            </div>
            <div className="metric-card">
              <div className="metric-val" style={{ color: health.models_loaded.protein_search ? "#166534" : "#991b1b" }}>
                {health.models_loaded.protein_search ? "loaded" : "error"}
              </div>
              <div className="metric-label">Protein search</div>
            </div>
          </div>
        </div>
      )}

      {metrics && (
        <>
          <div className="card">
            <div className="card-title">Request Summary</div>
            <div className="grid3">
              <div className="metric-card">
                <div className="metric-val">{totalRequests}</div>
                <div className="metric-label">Total requests</div>
              </div>
              <div className="metric-card">
                <div className="metric-val">
                  {totalRequests > 0 ? ((totalSuccess / totalRequests) * 100).toFixed(1) : "—"}%
                </div>
                <div className="metric-label">Success rate</div>
              </div>
              <div className="metric-card">
                <div className="metric-val">{avgLatency}ms</div>
                <div className="metric-label">Avg latency</div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-title">Endpoint Metrics</div>
            {Object.keys(metrics.endpoints).length === 0 ? (
              <p style={{ color: "#9ca3af", fontSize: 14 }}>No requests yet — make some predictions or searches first.</p>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
                    {["Endpoint", "Total", "Success", "Failed", "P50 (ms)", "P95 (ms)", "Avg (ms)"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "8px 12px", color: "#6b7280", fontWeight: 500 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(metrics.endpoints).map(([name, data]) => (
                    <tr key={name} style={{ borderBottom: "1px solid #f3f4f6" }}>
                      <td style={{ padding: "10px 12px", fontWeight: 500 }}>/{name}</td>
                      <td style={{ padding: "10px 12px" }}>{data.total}</td>
                      <td style={{ padding: "10px 12px", color: "#166534" }}>{data.success}</td>
                      <td style={{ padding: "10px 12px", color: data.failed > 0 ? "#991b1b" : "#9ca3af" }}>{data.failed}</td>
                      <td style={{ padding: "10px 12px" }}>{data.p50_latency_ms}</td>
                      <td style={{ padding: "10px 12px" }}>{data.p95_latency_ms}</td>
                      <td style={{ padding: "10px 12px" }}>{data.avg_latency_ms}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {metrics.recent_requests?.length > 0 && (
            <div className="card">
              <div className="card-title">Recent Requests</div>
              {metrics.recent_requests.slice().reverse().map((r, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #f3f4f6", fontSize: 13 }}>
                  <div>
                    <span style={{ fontFamily: "monospace", background: "#f3f4f6", padding: "2px 6px", borderRadius: 4 }}>/{r.endpoint}</span>
                    <span style={{ color: "#6b7280", marginLeft: 8 }}>{r.input_preview}...</span>
                  </div>
                  <div style={{ display: "flex", gap: 12, color: "#9ca3af" }}>
                    <span>{r.latency_ms}ms</span>
                    <span style={{ color: r.success ? "#166534" : "#991b1b" }}>{r.success ? "ok" : "err"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {lastRefresh && (
        <p style={{ fontSize: 12, color: "#9ca3af", textAlign: "right" }}>Last updated: {lastRefresh}</p>
      )}
    </div>
  );
}
