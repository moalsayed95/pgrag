import { useState } from "react";
import DocumentUpload from "./components/DocumentUpload";
import ChatPanel from "./components/ChatPanel";

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">
          🐘 <span>PG-RAG</span>
        </div>
        <div className="header-sub">Retrieval Augmented Generation with PostgreSQL</div>
      </header>
      <div className="main">
        <aside className="sidebar">
          <DocumentUpload onUpload={() => setRefreshKey((k) => k + 1)} />
        </aside>
        <ChatPanel key={refreshKey} />
      </div>
    </div>
  );
}

export default App;
