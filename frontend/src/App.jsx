import { useState } from "react";
import MoleculePredictor from "./components/MoleculePredictor";
import ProteinSearch from "./components/ProteinSearch";
import Dashboard from "./components/Dashboard";
import "./App.css";

const TABS = [
  { id: "predict", label: "Molecule Predictor" },
  { id: "search",  label: "Protein Search" },
  { id: "dash",    label: "Analytics Dashboard" },
];

export default function App() {
  const [tab, setTab] = useState("predict");

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⬡</span>
            <span className="logo-text">MolecularML Platform</span>
          </div>
          <nav className="nav">
            {TABS.map(t => (
              <button
                key={t.id}
                className={`nav-btn ${tab === t.id ? "active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="main">
        {tab === "predict" && <MoleculePredictor />}
        {tab === "search"  && <ProteinSearch />}
        {tab === "dash"    && <Dashboard />}
      </main>

      <footer className="footer">
        <span>MolecularML Platform · FastAPI + PyTorch + ESM + RDKit</span>
      </footer>
    </div>
  );
}
