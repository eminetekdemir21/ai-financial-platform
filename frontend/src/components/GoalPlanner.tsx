import { useEffect, useState } from "react";
import * as goalsApi from "../api/goals";
import type { Goal, GoalAnalysis } from "../api/goals";
import Spinner from "./Spinner";

interface Props { accountId: string; }

const dk = {
  card: "#1a1d27", card2: "#21253a", border: "rgba(255,255,255,0.08)", border2: "rgba(255,255,255,0.12)",
  text: "#f1f1f3", muted: "#8b8fa8", hint: "#5a5e78",
  green: "#00d68f", greenBg: "rgba(0,214,143,0.10)",
  blue: "#5b8dee", blueBg: "rgba(91,141,238,0.10)",
  red: "#ff6b6b", redBg: "rgba(255,107,107,0.10)",
  amber: "#ffa940", amberBg: "rgba(255,169,64,0.10)",
};

const PRIORITY_COLORS: Record<string, { bg: string; text: string }> = {
  low: { bg: "rgba(255,255,255,0.06)", text: dk.muted },
  medium: { bg: dk.amberBg, text: dk.amber },
  high: { bg: dk.redBg, text: dk.red },
};
const PRIORITY_LABELS: Record<string, string> = { low: "Dusuk", medium: "Orta", high: "Yuksek" };

export default function GoalPlanner({ accountId }: Props) {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<GoalAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [priority, setPriority] = useState("medium");
  const [savings, setSavings] = useState("0");
  const [creating, setCreating] = useState(false);

  useEffect(() => { loadGoals(); }, [accountId]);

  async function loadGoals() {
    setLoading(true);
    try { const data = await goalsApi.listGoals(accountId); setGoals(data); }
    catch { setError("Hedefler yuklenemedi."); }
    finally { setLoading(false); }
  }

  async function handleCreate() {
    if (!name || !amount || !date) { setError("Hedef adi, tutar ve tarih zorunludur."); return; }
    setCreating(true); setError(null);
    try {
      await goalsApi.createGoal(accountId, { name, target_amount: parseFloat(amount), target_date: date, priority, current_savings: parseFloat(savings) || 0 });
      setShowForm(false); setName(""); setAmount(""); setDate(""); setPriority("medium"); setSavings("0");
      await loadGoals();
    } catch (err: any) { setError(err?.response?.data?.detail ?? "Hedef olusturulamadi."); }
    finally { setCreating(false); }
  }

  async function handleAnalyze(goal: Goal) {
    setAnalysisLoading(true); setSelectedAnalysis(null);
    try { const a = await goalsApi.analyzeGoal(goal.id, accountId); setSelectedAnalysis(a); }
    catch { setError("Analiz yapilamadi."); }
    finally { setAnalysisLoading(false); }
  }

  async function handleDelete(goalId: string) {
    if (!window.confirm("Bu hedefi iptal etmek istiyor musunuz?")) return;
    try { await goalsApi.deleteGoal(goalId); setGoals(p => p.filter(g => g.id !== goalId)); if (selectedAnalysis?.goal.id === goalId) setSelectedAnalysis(null); }
    catch { setError("Hedef silinemedi."); }
  }

  const s: React.CSSProperties = { background: dk.card, border: `0.5px solid ${dk.border}`, borderRadius: "12px", padding: "16px" };
  const input: React.CSSProperties = { background: dk.card2, border: `0.5px solid ${dk.border2}`, borderRadius: "8px", padding: "7px 12px", fontSize: "13px", color: dk.text, outline: "none", width: "100%", boxSizing: "border-box" };

  return (
    <div style={s}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
        <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px" }}>Finansal Hedefler</div>
        <button onClick={() => setShowForm(v => !v)} style={{ fontSize: "12px", color: dk.blue, background: "none", border: "none", cursor: "pointer" }}>+ Yeni Hedef</button>
      </div>

      {error && <div style={{ fontSize: "12px", color: dk.red, background: dk.redBg, borderRadius: "8px", padding: "8px 12px", marginBottom: "10px" }}>{error}</div>}

      {showForm && (
        <div style={{ background: dk.card2, borderRadius: "10px", padding: "14px", marginBottom: "14px", border: `0.5px solid ${dk.border2}` }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "10px" }}>
            <div>
              <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Hedef Adi</div>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="orn. Bilgisayar" style={input} />
            </div>
            <div>
              <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Tutar (TL)</div>
              <input type="number" value={amount} onChange={e => setAmount(e.target.value)} placeholder="80000" style={input} />
            </div>
            <div>
              <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Hedef Tarihi</div>
              <input type="date" value={date} onChange={e => setDate(e.target.value)} style={input} />
            </div>
            <div>
              <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Mevcut Birikim (TL)</div>
              <input type="number" value={savings} onChange={e => setSavings(e.target.value)} placeholder="0" style={input} />
            </div>
          </div>
          <div style={{ marginBottom: "10px" }}>
            <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "4px" }}>Oncelik</div>
            <select value={priority} onChange={e => setPriority(e.target.value)} style={{ ...input, width: "auto" }}>
              <option value="low">Dusuk</option>
              <option value="medium">Orta</option>
              <option value="high">Yuksek</option>
            </select>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={handleCreate} disabled={creating}
              style={{ display: "flex", alignItems: "center", gap: "6px", background: dk.blueBg, border: `1px solid ${dk.blue}`, color: dk.blue, borderRadius: "8px", padding: "7px 16px", fontSize: "13px", cursor: "pointer", opacity: creating ? 0.6 : 1 }}>
              {creating && <Spinner size={13} />}{creating ? "Olusturuluyor..." : "Hedef Olustur"}
            </button>
            <button onClick={() => setShowForm(false)} style={{ background: "none", border: "none", color: dk.muted, fontSize: "13px", cursor: "pointer" }}>Iptal</button>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: dk.muted, fontSize: "13px" }}><Spinner size={14} /> Yukleniyor...</div>
      ) : goals.length === 0 ? (
        <p style={{ color: dk.hint, fontSize: "13px" }}>Henuz hedef yok. "+ Yeni Hedef" ile baslayin.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {goals.map(goal => (
            <div key={goal.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: dk.card2, borderRadius: "8px", padding: "10px 12px", border: `0.5px solid ${dk.border}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 500, color: dk.text }}>{goal.name}</div>
                  <div style={{ fontSize: "11px", color: dk.hint }}>
                    {parseFloat(goal.target_amount).toLocaleString("tr-TR")} TL · {new Date(goal.target_date).toLocaleDateString("tr-TR")}
                  </div>
                </div>
                <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "20px", background: PRIORITY_COLORS[goal.priority]?.bg, color: PRIORITY_COLORS[goal.priority]?.text }}>
                  {PRIORITY_LABELS[goal.priority]}
                </span>
              </div>
              <div style={{ display: "flex", gap: "10px" }}>
                <button onClick={() => handleAnalyze(goal)} style={{ fontSize: "12px", color: dk.blue, background: "none", border: "none", cursor: "pointer" }}>AI Analizi</button>
                <button onClick={() => handleDelete(goal.id)} style={{ fontSize: "12px", color: dk.hint, background: "none", border: "none", cursor: "pointer" }}>Sil</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {analysisLoading && (
        <div style={{ marginTop: "12px", display: "flex", alignItems: "center", gap: "8px", color: dk.muted, fontSize: "13px" }}><Spinner size={14} /> Analiz yapiliyor...</div>
      )}

      {selectedAnalysis && (
        <div style={{ marginTop: "14px", borderRadius: "10px", padding: "14px", border: `0.5px solid ${selectedAnalysis.is_achievable ? "rgba(0,214,143,0.2)" : "rgba(255,169,64,0.2)"}`, background: selectedAnalysis.is_achievable ? "rgba(0,214,143,0.05)" : "rgba(255,169,64,0.05)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontSize: "13px", fontWeight: 500, color: dk.text }}>{selectedAnalysis.goal.name} — AI Analizi</span>
            <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "20px", background: selectedAnalysis.is_achievable ? dk.greenBg : dk.amberBg, color: selectedAnalysis.is_achievable ? dk.green : dk.amber }}>
              {selectedAnalysis.is_achievable ? "Ulasılabilir" : "Zor Gorunuyor"}
            </span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "10px" }}>
            {[
              { label: "Gereken Aylik Tasarruf", value: `${parseFloat(selectedAnalysis.monthly_savings_needed).toLocaleString("tr-TR", { maximumFractionDigits: 0 })} TL`, color: dk.text },
              { label: "Mevcut Aylik Tasarruf", value: `${parseFloat(selectedAnalysis.current_monthly_savings).toLocaleString("tr-TR", { maximumFractionDigits: 0 })} TL`, color: dk.green },
              { label: "Kalan Sure", value: `${selectedAnalysis.months_remaining} ay`, color: dk.text },
              { label: "Tahmini Tamamlanma", value: new Date(selectedAnalysis.estimated_completion_date).toLocaleDateString("tr-TR", { year: "numeric", month: "long" }), color: dk.text },
            ].map(item => (
              <div key={item.label} style={{ background: dk.card2, borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "11px", color: dk.hint, marginBottom: "3px" }}>{item.label}</div>
                <div style={{ fontSize: "14px", fontWeight: 500, color: item.color }}>{item.value}</div>
              </div>
            ))}
          </div>
          <div style={{ background: dk.card2, borderRadius: "8px", padding: "10px 12px", marginBottom: "8px" }}>
            <div style={{ fontSize: "11px", color: dk.hint, marginBottom: "4px" }}>AI Onerisi</div>
            <p style={{ fontSize: "13px", color: dk.text, lineHeight: 1.5 }}>{selectedAnalysis.ai_recommendation}</p>
          </div>
          {selectedAnalysis.top_saving_opportunities.length > 0 && (
            <div>
              <div style={{ fontSize: "11px", color: dk.hint, marginBottom: "6px" }}>Tasarruf Firsatlari</div>
              {selectedAnalysis.top_saving_opportunities.map(opp => (
                <div key={opp.category} style={{ display: "flex", justifyContent: "space-between", background: dk.card2, borderRadius: "6px", padding: "7px 12px", marginBottom: "4px" }}>
                  <span style={{ fontSize: "12px", color: dk.muted, textTransform: "capitalize" }}>{opp.category}</span>
                  <span style={{ fontSize: "12px", color: dk.green }}>+{opp.saving_20_percent.toLocaleString("tr-TR", { maximumFractionDigits: 0 })} TL/ay</span>
                </div>
              ))}
            </div>
          )}
          <button onClick={() => setSelectedAnalysis(null)} style={{ marginTop: "8px", fontSize: "12px", color: dk.hint, background: "none", border: "none", cursor: "pointer" }}>Kapat</button>
        </div>
      )}
    </div>
  );
}
