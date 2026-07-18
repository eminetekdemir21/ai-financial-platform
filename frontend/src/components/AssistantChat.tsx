import { useState } from "react";
import { sendChatMessage } from "../api/assistant";
import Spinner from "./Spinner";

interface Message { role: "user" | "assistant"; text: string; }

const dk = {
  card: "#1a1d27", card2: "#21253a", border: "rgba(255,255,255,0.08)", border2: "rgba(255,255,255,0.12)",
  text: "#f1f1f3", muted: "#8b8fa8", hint: "#5a5e78",
  blue: "#5b8dee", blueBg: "rgba(91,141,238,0.10)",
  red: "#ff6b6b",
};

const SUGGESTED = [
  "Bu ay en cok hangi kategoriye harcama yaptim?",
  "Tasarruf oranim nasil?",
  "Supheli islem var mi?",
  "Harcamalarimi nasil azaltabilirim?",
];

function renderText(text: string) {
  // **bold** → <strong>, * liste → satır
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} style={{ color: "#fff", fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
    }
    // Satır başı * işaretlerini kaldır
    return <span key={i}>{part.replace(/^\* /gm, "• ")}</span>;
  });
}

export default function AssistantChat({ accountId }: { accountId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(text: string) {
    if (!text.trim()) return;
    setMessages(p => [...p, { role: "user", text }]);
    setInput(""); setLoading(true); setError(null);
    try {
      const res = await sendChatMessage(accountId, text);
      setMessages(p => [...p, { role: "assistant", text: res.reply }]);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Asistana ulasilamadi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ background: dk.card, border: `0.5px solid ${dk.border}`, borderRadius: "12px", overflow: "hidden" }}>
      <div style={{ padding: "12px 16px", borderBottom: `0.5px solid ${dk.border}` }}>
        <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px" }}>AI Finansal Asistan</div>
        <div style={{ fontSize: "12px", color: dk.hint, marginTop: "2px" }}>Hesabınız hakkında soru sorun</div>
      </div>

      <div style={{ padding: "16px", minHeight: "180px", maxHeight: "360px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px" }}>
        {messages.length === 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ fontSize: "11px", color: dk.hint, marginBottom: "4px" }}>Örnek sorular:</div>
            {SUGGESTED.map(q => (
              <button key={q} onClick={() => send(q)}
                style={{ textAlign: "left", fontSize: "12px", color: dk.blue, background: dk.blueBg, border: `0.5px solid rgba(91,141,238,0.2)`, borderRadius: "8px", padding: "8px 12px", cursor: "pointer" }}>
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            {msg.role === "assistant" && (
              <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: dk.blueBg, border: `0.5px solid rgba(91,141,238,0.3)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", flexShrink: 0, marginRight: "8px", marginTop: "2px" }}>
                ⬡
              </div>
            )}
            <div style={{
              maxWidth: "78%", borderRadius: "10px", padding: "10px 14px", fontSize: "13px", lineHeight: 1.6,
              background: msg.role === "user" ? dk.blue : dk.card2,
              color: msg.role === "user" ? "#fff" : dk.text,
              whiteSpace: "pre-wrap",
            }}>
              {msg.role === "assistant" ? renderText(msg.text) : msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", alignItems: "center" }}>
            <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: dk.blueBg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", marginRight: "8px" }}>⬡</div>
            <div style={{ background: dk.card2, borderRadius: "10px", padding: "10px 14px", display: "flex", alignItems: "center", gap: "8px" }}>
              <Spinner size={12} /><span style={{ fontSize: "12px", color: dk.muted }}>Düşünüyor...</span>
            </div>
          </div>
        )}

        {error && <div style={{ fontSize: "12px", color: dk.red, background: "rgba(255,107,107,0.08)", borderRadius: "8px", padding: "8px 12px" }}>{error}</div>}
      </div>

      <div style={{ padding: "12px 16px", borderTop: `0.5px solid ${dk.border}`, display: "flex", gap: "8px" }}>
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !loading && send(input)}
          placeholder="Sorunuzu yazın..." disabled={loading}
          style={{ flex: 1, background: dk.card2, border: `0.5px solid ${dk.border2}`, borderRadius: "8px", padding: "9px 12px", fontSize: "13px", color: dk.text, outline: "none" }} />
        <button onClick={() => send(input)} disabled={loading || !input.trim()}
          style={{ background: dk.blueBg, border: `1px solid ${dk.blue}`, color: dk.blue, borderRadius: "8px", padding: "9px 18px", fontSize: "13px", cursor: "pointer", opacity: (loading || !input.trim()) ? 0.4 : 1 }}>
          Gönder
        </button>
      </div>
    </div>
  );
}
