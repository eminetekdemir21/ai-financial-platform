import { useEffect, useState } from "react";

export interface ToastMessage {
  type: "success" | "error";
  text: string;
}

interface ToastProps {
  message: ToastMessage | null;
  onDismiss: () => void;
  durationMs?: number;
}

export default function Toast({ message, onDismiss, durationMs = 6000 }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!message) return;
    setIsVisible(true);
    const timer = setTimeout(() => {
      setIsVisible(false);
      // Kaybolma animasyonunun bitmesini bekleyip mesaji temizle
      setTimeout(onDismiss, 200);
    }, durationMs);
    return () => clearTimeout(timer);
  }, [message, durationMs, onDismiss]);

  if (!message) return null;

  const isError = message.type === "error";

  return (
    <div
      className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm transition-opacity duration-200 ${
        isVisible ? "opacity-100" : "opacity-0"
      } ${
        isError
          ? "bg-red-50 border-red-200 text-red-700"
          : "bg-emerald-50 border-emerald-200 text-emerald-700"
      }`}
    >
      <span className="mt-0.5">{isError ? "⚠" : "✓"}</span>
      <span className="flex-1">{message.text}</span>
      <button
        onClick={() => {
          setIsVisible(false);
          setTimeout(onDismiss, 200);
        }}
        className="text-xs opacity-60 hover:opacity-100 transition"
        aria-label="Kapat"
      >
        ✕
      </button>
    </div>
  );
}
