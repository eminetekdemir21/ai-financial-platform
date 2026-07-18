import { useEffect, useState } from "react";
import { getOpportunities } from "../api/opportunities";
import type { OpportunityReport, Opportunity } from "../api/opportunities";
import Spinner from "./Spinner";

interface Props { accountId: string; }

const dk = {
  card: "#1a1d27", card2: "#21253a", border: "rgba(255,255,255,0.08)", border2: "rgba(255,255,255,0.12)",
  text: "#f1f1f3", muted: "#8b8fa8", hint: "#5a5e78",
  green: "#00d68f", greenBg: "rgba(0,214,143,0.10)",
  blue: "#5b8dee", blueBg: "rgba(91,141,238,0.10)",
  red: "#ff6b6b", redBg: "rgba(255,107,107,0.10)",
  amber: "#ffa940", amberBg: "rgba(255,169,64,0.10)",
  purple: "#7c6de8", purpleBg: "rgba(124,109,232,0.10)",
};

const TYPE_ICONS: Record<string, string> = {
  abonelik: "📺",
  yuksek_harcama: "💸",
  tekrar_eden: "🔄",
  fraud_risk: "⚠️",
};

const PRIORITY_STYLE: Record<string, { bg: string; color: string; label: string }> = {
  yuksek: { bg: dk.redBg, color: dk.red, label: "Yüksek" },
  orta: { bg: dk.amberBg, color: dk.amber, label: "Orta" },
  dusuk: { bg: dk.greenBg, color: dk.green, label: "Düşük" },
};

function ScoreRing({ score }: { score: number }) {
  const color = score >= 70 ? dk.red : score >= 40 ? dk.amber : dk.green;
  const label = score >= 70 ? "Yüksek Fırsat" : score >= 40 ? "Orta Fırsat" : "Optimize";
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
      <div style={{ position: "relative", width: "80px", height: "80px" }}>
        <svg width="80" height="80" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
          <circle cx="40" cy="40" r="32" fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={`${2 * Math.PI * 32}`}
            strokeDashoffset={`${2 * Math.PI * 32 * (1 - score / 100)}`}
            strokeLinecap="round" transform="rotate(-90 40 40)"
            style={{ transition: "stroke-dashoffset 0.8s ease" }} />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: "20px", fontWeight: 500, color, lineHeight: 1 }}>{score}</span>
        </div>
      </div>
      <span style={{ fontSize: "11px", color: dk.muted }}>{label}</span>
    </div>
  );
}

export default function OpportunityEngine({ accountId }: Props) {
  const [report, setReport] = useState<OpportunityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getOpportunities(accountId)
      .then(setReport).catch(() => setError("Fırsatlar yuklenemedi.")).finally(() => setLoading(false));
  }, [accountId]);

  const s: React.CSSProperties = { background: dk.card, border: `0.5px solid ${dk.border}`, borderRadius: "12px", padding: "16px" };

  if (loading) return <div style={s}><div style={{ display: "flex", alignItems: "center", gap: "8px", color: dk.muted, fontSize: "13px" }}><Spinner size={14} /> Fırsatlar analiz ediliyor...</div></div>;
  if (error || !report) return <div style={s}><p style={{ color: dk.muted, fontSize: "13px" }}>{error}</p></div>;

  const totalMonthly = parseFloat(report.total_monthly_saving);
  const totalAnnual = parseFloat(report.total_annual_saving);

  return (
    <div style={s}>
      <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "14px" }}>
        AI Fırsat Motoru
      </div>

      {/* Özet header */}
      <div style={{ display: "flex", gap: "16px", alignItems: "center", background: dk.card2, borderRadius: "10px", padding: "14px", marginBottom: "14px" }}>
        <ScoreRing score={report.opportunity_score} />
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: "12px", color: dk.hint, lineHeight: 1.6, marginBottom: "10px" }}>{report.summary}</p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            <div>
              <div style={{ fontSize: "11px", color: dk.hint }}>Aylık Tasarruf Potansiyeli</div>
              <div style={{ fontSize: "16px", fontWeight: 500, color: dk.green }}>+{Math.round(totalMonthly).toLocaleString("tr-TR")} ₺</div>
            </div>
            <div>
              <div style={{ fontSize: "11px", color: dk.hint }}>Yıllık Tasarruf Potansiyeli</div>
              <div style={{ fontSize: "16px", fontWeight: 500, color: dk.green }}>+{Math.round(totalAnnual).toLocaleString("tr-TR")} ₺</div>
            </div>
          </div>
        </div>
      </div>

      {/* Abonelik özeti */}
      {parseFloat(report.subscriptions_total) > 0 && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: dk.purpleBg, border: `0.5px solid rgba(124,109,232,0.2)`, borderRadius: "8px", padding: "10px 14px", marginBottom: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "16px" }}>📺</span>
            <span style={{ fontSize: "13px", color: dk.text }}>Toplam abonelik harcaması</span>
          </div>
          <span style={{ fontSize: "15px", fontWeight: 500, color: dk.purple }}>
            {Math.round(parseFloat(report.subscriptions_total)).toLocaleString("tr-TR")} ₺/ay
          </span>
        </div>
      )}

      {/* Fırsatlar listesi */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {report.opportunities.map((opp, i) => {
          const pStyle = PRIORITY_STYLE[opp.priority] ?? PRIORITY_STYLE.dusuk;
          const isOpen = expanded === `${i}`;
          return (
            <div key={i} style={{ background: dk.card2, borderRadius: "10px", border: `0.5px solid ${dk.border}`, overflow: "hidden" }}>
              <button onClick={() => setExpanded(isOpen ? null : `${i}`)}
                style={{ width: "100%", display: "flex", alignItems: "center", gap: "12px", padding: "12px 14px", background: "none", border: "none", cursor: "pointer", textAlign: "left" }}>
                <span style={{ fontSize: "18px", flexShrink: 0 }}>{TYPE_ICONS[opp.type] ?? "💡"}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "13px", fontWeight: 500, color: dk.text, marginBottom: "2px" }}>{opp.title}</div>
                  <div style={{ fontSize: "11px", color: dk.green, fontWeight: 500 }}>
                    Aylık +{Math.round(parseFloat(opp.monthly_saving)).toLocaleString("tr-TR")} ₺ tasarruf
                  </div>
                </div>
                <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "20px", background: pStyle.bg, color: pStyle.color, flexShrink: 0 }}>
                  {pStyle.label}
                </span>
                <span style={{ color: dk.hint, fontSize: "12px", flexShrink: 0 }}>{isOpen ? "▲" : "▼"}</span>
              </button>

              {isOpen && (
                <div style={{ padding: "0 14px 14px" }}>
                  <p style={{ fontSize: "12px", color: dk.hint, lineHeight: 1.6, marginBottom: "10px" }}>{opp.description}</p>
                  <div style={{ background: dk.greenBg, border: `0.5px solid rgba(0,214,143,0.2)`, borderRadius: "8px", padding: "10px 12px" }}>
                    <div style={{ fontSize: "11px", color: dk.green, fontWeight: 500, marginBottom: "3px" }}>Yapılacak adım</div>
                    <p style={{ fontSize: "12px", color: dk.text }}>{opp.action}</p>
                  </div>
                  <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
                    <span style={{ fontSize: "12px", color: dk.green }}>Aylık: +{Math.round(parseFloat(opp.monthly_saving)).toLocaleString("tr-TR")} ₺</span>
                    <span style={{ fontSize: "12px", color: dk.hint }}>Yıllık: +{Math.round(parseFloat(opp.annual_saving)).toLocaleString("tr-TR")} ₺</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
