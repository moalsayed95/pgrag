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
    setMessages((prev) => [...prev, userMsg, { role: "assistant", content: "" }]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.content }),
      });
      if (!res.ok || !res.body) throw new Error("Request failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const eventMatch = part.match(/^event: (.+)$/m);
          const dataMatch = part.match(/^data: (.+)$/m);
          if (!eventMatch || !dataMatch) continue;

          const eventType = eventMatch[1];
          const data = JSON.parse(dataMatch[1]);

          if (eventType === "text_delta") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = { ...last, content: last.content + data.delta };
              return updated;
            });
          } else if (eventType === "sources") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = { ...last, sources: data.sources };
              return updated;
            });
          } else if (eventType === "error") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = { role: "assistant", content: data.message || "Something went wrong." };
              return updated;
            });
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last?.role === "assistant" && last.content === "") {
          updated[updated.length - 1] = { role: "assistant", content: "Something went wrong. Please try again." };
        } else {
          updated.push({ role: "assistant", content: "Something went wrong. Please try again." });
        }
        return updated;
      });
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

        {loading && messages[messages.length - 1]?.content === "" && (
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
