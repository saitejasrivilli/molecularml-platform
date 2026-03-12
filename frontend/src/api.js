const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:7860";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  health:           ()         => request("/health"),
  metrics:          ()         => request("/metrics"),
  predict:          (smiles, properties) =>
    request("/predict", { method: "POST", body: JSON.stringify({ smiles, properties }) }),
  search:           (sequence, top_k) =>
    request("/search",  { method: "POST", body: JSON.stringify({ sequence, top_k }) }),
  exampleMolecules: ()         => request("/molecules/examples"),
  exampleProteins:  ()         => request("/proteins/examples"),
};
