import { useState, type KeyboardEvent } from "react";
import * as assistantApi from "../api/assistant";
import Spinner from "./Spinner";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

interface AssistantChatProps {
  accountId: string;
}

export default function AssistantChat({ accountId }: AssistantChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const result = await assistantApi.sendChatMessage(accountId, trimmed);
      setMessages((prev) => [...prev, { role: "assistant", text: result.reply }]);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ??
          "AI asistanina ulasilamadi. Lutfen daha sonra tekrar deneyin."
      );
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      handleSend();
    }
  }

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-4 flex flex-col">
      <h2 className="text-sm font-medium text-slate-700 mb-3">
        AI Finansal Asistan
      </h2>

      <div className="flex-1 space-y-3 mb-3 max-h-72 overflow-y-auto">
        {messages.length === 0 && (
          <p className="text-sm text-slate-400">
            Islemleriniz hakkinda soru sorun - orn. "Bu ay en cok nereye
            harcadim?" veya "Tasarruf onerisi ver".
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-sm rounded-lg px-3 py-2 max-w-[85%] whitespace-pre-wrap ${
              m.role === "user"
                ? "bg-indigo-600 text-white ml-auto"
                : "bg-slate-100 text-slate-800"
            }`}
          >
            {m.text}
          </div>
        ))}
        {isSending && (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Spinner size={14} />
            Yaziyor...
          </div>
        )}
      </div>

      {error && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-2">
          {error}
        </p>
      )}

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending}
          placeholder="Bir soru sorun..."
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={isSending || !input.trim()}
          className="bg-indigo-600 text-white text-sm rounded-lg px-4 py-2 hover:bg-indigo-700 transition disabled:opacity-50"
        >
          Gonder
        </button>
      </div>
    </section>
  );
}
