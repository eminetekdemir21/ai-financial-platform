import { useEffect, useState } from "react";
import { getSavingsReport } from "../api/savingsCoach";
import type { SavingsCoachReport } from "../api/savingsCoach";
import Spinner from "./Spinner";

interface Props { accountId: string; }

const dk = {
  card: "#1a1d27", card2: "#21253a", border: "rgba(255,255,255,0.08)",
  text: "#f1f1f3", muted: "#8b8fa8", hint: "#5a5e78",
  green: "#00d68f", blue: "#5b8dee", red: "#ff6b6b", amber: "#ffa940",
  redBg: "rgba(255,107,107,0.10)", amberBg: "rgba(255,169,64,0.10)",
};

function fmt(v: string | number) {
  const n = typeof v === "string" ? parseFloat(v) : v;
  return `${n >= 0 ? "+" : ""}${Math.round(n).toLocaleString("tr-TR")} ₺`;
}

export default function SavingsCoach({ accountId }: Props) {
  const [report, setReport] = useState<SavingsCoachReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTrends, setShowTrends] = useState(false);

  useEffect(() => {
    setLoading(true);
    getSavingsReport(accountId).then(setReport).catch(() => {}).finally(() => setLoading(false));
  }, [accountId]);

  const s: React.CSSProperties = { background: dk.card, border: `0.5px solid ${dk.border}`, borderRadius: "12px", padding: "16px" };
  const label: React.CSSProperties = { fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "12px" };

  if (loading) return <div style={s}><div style={{ display:"flex", alignItems:"center", gap:"8px", color:dk.muted, fontSize:"13px" }}><Spinner size={14} /> Analiz yapiyor...</div></div>;
  if (!report) return <div style={s}><p style={{ color:dk.muted, fontSize:"13px" }}>Rapor yuklenemedi.</p></div>;

  const rate = report.current_savings_rate;
  const rateColor = rate >= report.target_savings_rate ? dk.green : rate >= 10 ? dk.amber : dk.red;

  return (
    <div style={s}>
      <div style={label}>AI Tasarruf Kocu</div>
      <p style={{ fontSize:"12px", color:dk.hint, marginBottom:"14px", lineHeight:1.6 }}>{report.coach_message}</p>

      <div style={{ background:dk.card2, borderRadius:"8px", padding:"12px", marginBottom:"12px" }}>
        <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"8px" }}>
          <span style={{ fontSize:"12px", color:dk.muted }}>Tasarruf Orani</span>
          <span style={{ fontSize:"15px", fontWeight:500, color:rateColor }}>%{rate.toFixed(1)} <span style={{ fontSize:"11px", color:dk.hint }}>/ Hedef %{report.target_savings_rate}</span></span>
        </div>
        <div style={{ background:"rgba(255,255,255,0.06)", borderRadius:"4px", height:"6px" }}>
          <div style={{ height:"6px", borderRadius:"4px", background:rateColor, width:`${Math.min(rate,100)}%` }} />
        </div>
        <div style={{ display:"flex", justifyContent:"space-between", marginTop:"8px" }}>
          <span style={{ fontSize:"11px", color:dk.hint }}>Gelir: {fmt(report.total_monthly_income)}</span>
          <span style={{ fontSize:"11px", color:dk.hint }}>Gider: {fmt(report.total_monthly_expense)}</span>
        </div>
        {parseFloat(report.potential_annual_savings) > 0 && (
          <div style={{ marginTop:"6px", fontSize:"12px", color:dk.green, fontWeight:500 }}>
            Yillik +{fmt(report.potential_annual_savings)} potansiyel
          </div>
        )}
      </div>

      {report.tips.length > 0 && (
        <div style={{ marginBottom:"12px" }}>
          <div style={{ fontSize:"11px", color:dk.muted, textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"8px" }}>Oneriler</div>
          {report.tips.map((tip, i) => (
            <div key={i} style={{ background:dk.card2, borderRadius:"8px", padding:"10px 12px", marginBottom:"6px", border:`0.5px solid ${dk.border}` }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"3px" }}>
                <span style={{ fontSize:"13px", fontWeight:500, color:dk.text }}>{tip.title}</span>
                <span style={{ fontSize:"10px", padding:"2px 6px", borderRadius:"20px", background:tip.priority==="yuksek"?dk.redBg:dk.amberBg, color:tip.priority==="yuksek"?dk.red:dk.amber }}>{tip.priority}</span>
              </div>
              <p style={{ fontSize:"11px", color:dk.hint, marginBottom:"4px", lineHeight:1.5 }}>{tip.description}</p>
              <span style={{ fontSize:"12px", color:dk.green, fontWeight:500 }}>Aylik {fmt(tip.monthly_saving_potential)}</span>
            </div>
          ))}
        </div>
      )}

      <button onClick={() => setShowTrends(v => !v)} style={{ fontSize:"12px", color:dk.blue, background:"none", border:"none", cursor:"pointer", padding:0 }}>
        {showTrends ? "Trendleri Gizle" : "Harcama Trendleri"}
      </button>
      {showTrends && (
        <div style={{ marginTop:"8px", display:"flex", flexDirection:"column", gap:"4px" }}>
          {report.spending_trends.map(t => (
            <div key={t.category} style={{ display:"flex", justifyContent:"space-between", padding:"6px 10px", background:dk.card2, borderRadius:"6px" }}>
              <span style={{ fontSize:"12px", color:dk.muted, textTransform:"capitalize" }}>{t.category}</span>
              <span style={{ fontSize:"12px", fontWeight:500, color:t.trend==="artiyor"?dk.red:t.trend==="azaliyor"?dk.green:dk.hint }}>
                {t.trend==="artiyor"?"↑":t.trend==="azaliyor"?"↓":"→"} {Math.abs(t.change_pct).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
