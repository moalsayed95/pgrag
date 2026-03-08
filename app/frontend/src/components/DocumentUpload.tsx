import { useState, useEffect } from "react";

interface Props {
  onUpload: () => void;
}

interface Doc {
  id: string;
  filename: string;
  created_at: string;
  chunk_count: number;
}

export default function DocumentUpload({ onUpload }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);

  const fetchDocs = async () => {
    try {
      const res = await fetch("/api/documents/");
      if (res.ok) setDocs(await res.json());
    } catch { /* ignore */ }
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/documents/upload", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setMessage({ text: `"${data.filename}" uploaded — ${data.chunk_count} chunks created`, type: "success" });
      setFile(null);
      fetchDocs();
      onUpload();
    } catch {
      setMessage({ text: "Upload failed. Please try again.", type: "error" });
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div>
        <div className="section-title">Upload Document</div>
        <form onSubmit={handleSubmit}>
          <div className={`upload-zone${file ? " active" : ""}`}>
            <input
              type="file"
              accept=".txt,.md,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <div className="upload-icon">↑</div>
            <div className="upload-text">
              <strong>Click to upload</strong> or drag & drop
            </div>
            <div className="upload-hint">TXT, MD, or PDF</div>
          </div>

          {file && (
            <div className="file-selected">
              📄 {file.name}
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={!file || uploading}>
            {uploading ? "Embedding..." : "Upload & Embed"}
          </button>
        </form>

        {message && (
          <div className={`status-msg ${message.type}`}>
            {message.text}
          </div>
        )}
      </div>

      {docs.length > 0 && (
        <div>
          <div className="section-title">Documents ({docs.length})</div>
          <div className="doc-list">
            {docs.map((doc) => (
              <div key={doc.id} className="doc-item">
                <div className="doc-name">📄 {doc.filename}</div>
                <div className="doc-meta">{doc.chunk_count} chunks</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
