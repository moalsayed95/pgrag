import { useState, useEffect, useRef } from "react";
import { Upload, Doc, Close, Check, Warning } from "./icons";

interface Props {
  onUpload: () => void;
  onDocCount?: (n: number) => void;
}

interface DocItem {
  id: string;
  filename: string;
  created_at: string;
  chunk_count: number;
}

export default function DocumentUpload({ onUpload, onDocCount }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "ok" | "err" } | null>(null);
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [isDrag, setIsDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dismissTimer = useRef<number | null>(null);

  const fetchDocs = async () => {
    try {
      const res = await fetch("/api/documents/");
      if (res.ok) {
        const data = await res.json();
        setDocs(data);
        onDocCount?.(data.length);
      }
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    fetchDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const scheduleDismiss = () => {
    if (dismissTimer.current) window.clearTimeout(dismissTimer.current);
    dismissTimer.current = window.setTimeout(() => setMessage(null), 4500);
  };

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
      setMessage({
        text: `Indexed "${data.filename}" — ${data.chunk_count} chunks embedded`,
        type: "ok",
      });
      scheduleDismiss();
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      fetchDocs();
      onUpload();
    } catch {
      setMessage({ text: "Upload failed. Please try again.", type: "err" });
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDrag(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  };

  return (
    <>
      <section className="section">
        <div className="section-head">
          <span className="section-num">§01</span>
          <span className="section-title">Ingest</span>
          <span className="section-rule" />
        </div>

        <form onSubmit={handleSubmit}>
          <label
            className={`upload${isDrag ? " is-drag" : ""}${file ? " has-file" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDrag(true);
            }}
            onDragLeave={() => setIsDrag(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".txt,.md,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              aria-label="Upload document"
            />
            <span className="upload-icon">
              <Upload size={18} />
            </span>
            <div className="upload-text">
              <div className="upload-title">
                {file ? "Ready to embed" : "Drop a file to index"}
              </div>
              <div className="upload-hint">TXT · MD · PDF</div>
            </div>
          </label>

          {file && (
            <div className="file-chip">
              <Doc size={14} />
              <span className="file-chip-name">{file.name}</span>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  setFile(null);
                  if (inputRef.current) inputRef.current.value = "";
                }}
                aria-label="Remove file"
              >
                <Close size={14} />
              </button>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={!file || uploading}
          >
            {uploading ? "Embedding…" : "Index Document"}
          </button>
        </form>

        {message && (
          <div className={`status ${message.type}`} role="status">
            {message.type === "ok" ? <Check size={14} /> : <Warning size={14} />}
            <span>{message.text}</span>
          </div>
        )}
      </section>

      <section className="section library">
        <div className="section-head">
          <span className="section-num">§02</span>
          <span className="section-title">Corpus</span>
          <span className="section-rule" />
        </div>

        {docs.length === 0 ? (
          <div className="library-empty">No documents indexed yet</div>
        ) : (
          <div className="doc-list">
            {docs.map((doc, i) => (
              <div key={doc.id} className="doc-row">
                <div className="doc-index">{String(i + 1).padStart(2, "0")}</div>
                <div className="doc-body">
                  <div className="doc-name">{doc.filename}</div>
                  <div className="doc-meta">
                    {formatDate(doc.created_at)}
                  </div>
                </div>
                <div className="doc-chunks">{doc.chunk_count} chunks</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      year: "2-digit",
      month: "short",
      day: "2-digit",
    }).toUpperCase();
  } catch {
    return "";
  }
}
