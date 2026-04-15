import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Brackets, Chevron, Sparkle } from "./icons";

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
  /** True once streaming finishes (used to decide between caret / mode pill / sources). */
  done?: boolean;
  /** "grounded" if the backend returned sources, "general" if it answered without retrieval. */
  mode?: "grounded" | "general";
}

const SUGGESTIONS = [
  "Summarize the key points of the uploaded documents",
  "What concepts are defined in the corpus?",
  "Find evidence for a specific claim and cite the source",
];

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // autosize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [question]);

  const send = async (text: string) => {
    const q = text.trim();
    if (!q || loading) return;

    const userMsg: Message = { role: "user", content: q, done: true };
    setMessages((prev) => [
      ...prev,
      userMsg,
      { role: "assistant", content: "", done: false },
    ]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
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
              updated[updated.length - 1] = {
                ...last,
                content: last.content + data.delta,
              };
              return updated;
            });
          } else if (eventType === "sources") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              const sources: Source[] = data.sources;
              updated[updated.length - 1] = {
                ...last,
                sources,
                mode: sources.length > 0 ? "grounded" : "general",
              };
              return updated;
            });
          } else if (eventType === "error") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: "assistant",
                content: data.message || "Something went wrong.",
                done: true,
              };
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
          updated[updated.length - 1] = {
            role: "assistant",
            content: "Something went wrong. Please try again.",
            done: true,
          };
        } else {
          updated.push({
            role: "assistant",
            content: "Something went wrong. Please try again.",
            done: true,
          });
        }
        return updated;
      });
    } finally {
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.role === "assistant") {
          updated[updated.length - 1] = { ...last, done: true };
        }
        return updated;
      });
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(question);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(question);
    }
  };

  return (
    <div className="chat">
      <div className="transcript">
        {messages.length === 0 && !loading ? (
          <div className="empty">
            <div className="empty-tag">
              <Sparkle size={12} /> Retrieval · standby
            </div>
            <h1 className="empty-head">
              Query your corpus with <em>precision</em>. Ground every answer in
              the source.
            </h1>
            <p className="empty-sub">
              Upload documents on the left, then ask a question below.
              General questions are answered directly; questions about your
              documents are grounded with cited passages.
            </p>
            <div className="empty-suggests" role="list">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  className="suggest"
                  onClick={() => send(s)}
                  role="listitem"
                >
                  <span className="suggest-num">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span>{s}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="transcript-inner">
            {messages.map((msg, i) => (
              <MessageBlock key={i} msg={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <div className="composer-inner">
          <span className="composer-prompt" aria-hidden>
            &gt;
          </span>
          <textarea
            ref={textareaRef}
            className="composer-textarea"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your corpus…"
            rows={1}
            disabled={loading}
            aria-label="Ask a question"
          />
          <button
            type="submit"
            className="composer-send"
            disabled={loading || !question.trim()}
            aria-label="Send"
          >
            <Send size={16} />
          </button>
        </div>
        <div className="composer-hint">
          <span>
            <kbd>↵</kbd> send
          </span>
          <span>
            <kbd>⇧</kbd> <kbd>↵</kbd> newline
          </span>
        </div>
      </form>
    </div>
  );
}

function MessageBlock({ msg }: { msg: Message }) {
  const isAssistant = msg.role === "assistant";
  const streaming = isAssistant && !msg.done;
  const showThinking = streaming && msg.content === "";

  return (
    <div className={`msg ${msg.role}`}>
      <div className="msg-role">
        <span>{isAssistant ? "Response" : "Query"}</span>
      </div>

      {showThinking ? (
        <div className="msg-body">
          <span className="thinking">
            <span className="thinking-dots">
              <span />
              <span />
              <span />
            </span>
            retrieving
          </span>
        </div>
      ) : (
        <div className={`msg-body${isAssistant ? " md" : ""}`}>
          {isAssistant ? (
            <>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
              {streaming && <span className="caret" aria-hidden />}
            </>
          ) : (
            msg.content
          )}
        </div>
      )}

      {isAssistant && msg.done && msg.mode && (
        <ModePill mode={msg.mode} count={msg.sources?.length ?? 0} />
      )}

      {isAssistant && msg.sources && msg.sources.length > 0 && (
        <SourcesBlock sources={msg.sources} />
      )}
    </div>
  );
}

function ModePill({
  mode,
  count,
}: {
  mode: "grounded" | "general";
  count: number;
}) {
  if (mode === "grounded") {
    return (
      <span className={`mode grounded`}>
        <Brackets size={11} /> Grounded · {count} source{count !== 1 ? "s" : ""}
      </span>
    );
  }
  return <span className="mode general">General knowledge</span>;
}

function SourcesBlock({ sources }: { sources: Source[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="sources">
      <button
        type="button"
        className={`sources-head${open ? " is-open" : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="sources-count">{sources.length}</span>
        <span>Cited Passages</span>
        <Chevron size={14} />
      </button>
      {open && (
        <div className="source-list">
          {sources.map((s, i) => (
            <SourceCard key={i} s={s} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}

function SourceCard({ s, index }: { s: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(s.score * 100);
  return (
    <div className="source">
      <div className="source-head">
        <span className="source-serial">
          [{String(index + 1).padStart(2, "0")}]
        </span>
        <span className="source-file">{s.document_filename}</span>
        <span className="source-chunk">chunk {s.chunk_index}</span>
        <span className="source-score">
          <span
            className="score-bar"
            style={{ ["--w" as string]: `${pct}%` }}
          />
          {pct}%
        </span>
      </div>
      <div
        className={`source-content${expanded ? " is-expanded" : ""}`}
        onClick={() => setExpanded((v) => !v)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") setExpanded((v) => !v);
        }}
      >
        {s.content}
      </div>
    </div>
  );
}
