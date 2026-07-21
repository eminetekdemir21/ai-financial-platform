import { useState } from "react";
import { explainFraud } from "../api/explainability";
import type { FraudExplanation } from "../api/explainability";
import Spinner from "./Spinner";

const dk = {
  card: "#1a1d27", card2: "#21253a", border: "rgba(255,255,255,0.08)",
  text: "#f1f1f3", muted: "#8b8fa8", hint: "#5a5e78",
  green: "#00d68f", blue: "#5b8dee",
  red: "#ff6b6b", redBg: "rgba(255,107,107,0.10)",
  amber: "#ffa940", amberBg: "rgba(255,169,64,0.10)",
};

const RISK_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  kritik: { bg: "rgba(255,107,107,0.15)", color: dk.red, label: "Kritik" },
  yuksek: { bg: "rgba(255,107,107,0.10)", color: dk.red, label: "Yuksek" },
  orta:   { bg: dk.amberBg, color: dk.amber, label: "Orta" },
  dusuk:  { bg: "rgba(0,214,143,0.10)", color: dk.green, label: "Dusuk" },
};

interface Props {
  accountId: string;
  transactionId: string;
  onClose: () => void;
}

export default function FraudExplanationModal({ accountId, transactionId, onClose }: Props) {
  const [data, setData] = useState<FraudExplanation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useState(() => {
    explainFraud(accountId, transactionId)
      .then(setData)
      .catch(() => setError("Aciklama yuklenemedi."))
      .finally(() => setLoading(false));
  });

  const risk = data ? (RISK_STYLE[data.risk_level] ?? RISK_STYLE.dusuk) : null;

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}
      onClick={onClose}>
      <div style={{ background: dk.card, border: `0.5px solid ${dk.border}`, borderRadius: "14px", padding: "24px", width: "480px", maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" }}
        onClick={e => e.stopPropagation()}>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Fraud Aciklamasi
          </div>
          <button onClick={onClose} style={{ color: dk.hint, background: "none", border: "none", cursor: "pointer", fontSize: "18px" }}>×</button>
        </div>

        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: dk.muted, fontSize: "13px" }}>
            <Spinner size={14} /> Aciklama yukleniyor...
          </div>
        )}

        {error && <p style={{ color: dk.red, fontSize: "13px" }}>{error}</p>}

        {data && risk && (
          <>
            {/* İşlem bilgisi */}
            <div style={{ background: dk.card2, borderRadius: "10px", padding: "14px", marginBottom: "14px" }}>
              <div style={{ fontSize: "14px", fontWeight: 500, color: dk.text, marginBottom: "4px" }}>{data.description}</div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "13px", color: parseFloat(data.amount) >= 0 ? dk.green : dk.red, fontWeight: 500 }}>
                  {parseFloat(data.amount) >= 0 ? "+" : ""}{parseFloat(data.amount).toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺
                </span>
                <span style={{ fontSize: "11px", padding: "2px 10px", borderRadius: "20px", background: risk.bg, color: risk.color, fontWeight: 500 }}>
                  {risk.label} Risk · {(data.fraud_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Fraud nedenleri */}
            <div style={{ marginBottom: "14px" }}>
              <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "8px" }}>
                Tespit Edilen Sinyaller
              </div>
              {data.reasons.map((reason, i) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "10px", padding: "8px 12px", background: dk.card2, borderRadius: "8px", marginBottom: "6px", border: `0.5px solid ${dk.border}` }}>
                  <span style={{ color: dk.red, fontSize: "14px", flexShrink: 0 }}>⚠</span>
                  <span style={{ fontSize: "12px", color: dk.text, lineHeight: 1.5 }}>{reason}</span>
                </div>
              ))}
            </div>

            {/* Öneri */}
            <div style={{ background: `${risk.color}10`, border: `0.5px solid ${risk.color}30`, borderRadius: "10px", padding: "12px 14px" }}>
              <div style={{ fontSize: "11px", color: risk.color, fontWeight: 500, marginBottom: "4px" }}>Tavsiye</div>
              <p style={{ fontSize: "12px", color: dk.text, lineHeight: 1.6 }}>{data.recommendation}</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
