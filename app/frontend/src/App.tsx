import { useState, useEffect } from "react";
import DocumentUpload from "./components/DocumentUpload";
import ChatPanel from "./components/ChatPanel";
import { Crosshair, Sun, Moon } from "./components/icons";

type Theme = "dark" | "light";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem("pgrag-theme") as Theme | null;
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [docCount, setDocCount] = useState(0);
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("pgrag-theme", theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            <Crosshair size={16} />
          </span>
          <div>
            <div className="brand-word">
              pg<em>·</em>rag
            </div>
          </div>
          <div className="brand-sub">
            Retrieval
            <br />
            Terminal
          </div>
        </div>
        <div className="meta">
          <span>
            <span className="dot" />
            pgvector · online
          </span>
          <span>idx / {String(docCount).padStart(3, "0")}</span>
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>
      </header>

      <div className="main">
        <aside className="sidebar">
          <div className="rail">
            <DocumentUpload
              onUpload={() => setRefreshKey((k) => k + 1)}
              onDocCount={setDocCount}
            />
          </div>
        </aside>
        <ChatPanel key={refreshKey} />
      </div>
    </div>
  );
}

export default App;
