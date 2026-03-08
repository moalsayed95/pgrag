import { useState, useRef, useEffect } from "react";

interface Source {
  content: string;
  chunk_index: number;
  document_filename: string;
  score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const toggleSources = (index: number) => {
    setExpandedSources((prev) => {
      const next = new Set(prev);
      next.has(index) ? next.delete(index) : next.add(index);
      return next;
    });
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.content }),
      });
      if (!res.ok) throw new Error("Request failed");
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat">
      <div className="chat-messages">
        {messages.length === 0 && !loading && (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <div className="chat-empty-text">Ask anything about your documents</div>
            <div className="chat-empty-hint">Upload a document first, then start asking questions</div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-bubble">
              {msg.content}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                <button className="sources-toggle" onClick={() => toggleSources(i)}>
                  {expandedSources.has(i) ? "▾" : "▸"} {msg.sources.length} sources
                </button>
                {expandedSources.has(i) && (
                  <div className="source-list">
                    {msg.sources.map((s, j) => (
                      <div key={j} className="source-item">
                        <div className="source-header">
                          <span className="source-file">📄 {s.document_filename}</span>
                          <span className="source-score">{Math.round(s.score * 100)}% match</span>
                        </div>
                        <div className="source-content">{s.content}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-bubble">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <form className="chat-form" onSubmit={handleAsk}>
          <input
            className="chat-input"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about your documents..."
            disabled={loading}
          />
          <button type="submit" className="btn-send" disabled={loading || !question.trim()}>
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}
