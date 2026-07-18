import { useEffect, useState } from "react";
import { deleteScenario, getScenario, listScenarios, runSimulation, saveScenario } from "../api/simulation";
import type { SavedScenarioSummary, SimulationResult } from "../api/simulation";
import Spinner from "./Spinner";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const dk = {
  card: "#1a1d27", card2: "#21253a", border: "rgba(255,255,255,0.08)", border2: "rgba(255,255,255,0.12)",
  text: "#f1f1f3", muted: "#8b8fa8", hint: "#5a5e78",
  green: "#00d68f", greenBg: "rgba(0,214,143,0.10)",
  blue: "#5b8dee", blueBg: "rgba(91,141,238,0.10)",
  red: "#ff6b6b", redBg: "rgba(255,107,107,0.10)",
  amber: "#ffa940",
};

const PRESETS = [
  { label: "Maasim %20 artarsa", payload: { income_change: 0.2, description: "Maas artisi %20" } },
  { label: "Kira zammi geldi", payload: { category_changes: { kira: 0.3 }, description: "Kira zammi" } },
  { label: "Yemek harcamami yariya indirsem", payload: { category_changes: { yemek: -0.5 }, description: "Yemek yariya" } },
];

const TABS = ["Gelir degisikligi", "Tek seferlik harcama", "Harcama kategorisi"];
const HORIZONS = [{ months: 6, label: "6 ay" }, { months: 12, label: "1 yil" }, { months: 60, label: "5 yil" }];

function formatTL(v: string | number) {
  const n = typeof v === "string" ? parseFloat(v) : v;
  return `${n >= 0 ? "+" : ""}${Math.round(Math.abs(n)).toLocaleString("tr-TR")} ₺`;
}

export default function WhatIfSimulator({ accountId }: { accountId: string }) {
  const [tab, setTab] = useState(0);
  const [horizonMonths, setHorizonMonths] = useState(12);
  const [incomeChange, setIncomeChange] = useState("");
  const [oneTimeExpense, setOneTimeExpense] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [categoryPct, setCategoryPct] = useState(0);
  const [description, setDescription] = useState("");
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<SavedScenarioSummary[]>([]);
  const [showScenarios, setShowScenarios] = useState(false);
  const [scenarioName, setScenarioName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => { listScenarios(accountId).then(setScenarios).catch(() => {}); }, [accountId]);

  function buildPayload(): Record<string, unknown> {
    const payload: Record<string, unknown> = { horizon_months: horizonMonths };
    if (tab === 0 && incomeChange.trim()) payload.income_change = Number(incomeChange);
    if (tab === 1 && oneTimeExpense.trim()) payload.one_time_expense = Number(oneTimeExpense);
    if (tab === 2 && categoryName.trim()) payload.category_changes = { [categoryName.trim()]: categoryPct / 100 };
    if (description.trim()) payload.description = description.trim();
    return payload;
  }

  async function handleRun() {
    setLoading(true); setError(null); setResult(null);
    try { setResult(await runSimulation(accountId, buildPayload())); }
    catch (err: any) { setError(err?.response?.data?.detail ?? "Simulasyon calistirilamadi."); }
    finally { setLoading(false); }
  }

  async function handleSave() {
    setIsSaving(true); setSaveMessage("");
    try {
      await saveScenario(accountId, scenarioName || description, buildPayload());
      setSaveMessage("Senaryo kaydedildi.");
      setScenarios(await listScenarios(accountId));
    } catch { setSaveMessage("Kaydedilirken bir hata olustu."); }
    finally { setIsSaving(false); }
  }

  async function handleLoadScenario(id: string) {
    try {
      const s = await getScenario(accountId, id);
      if (s.payload.income_change) { setTab(0); setIncomeChange(String(s.payload.income_change)); }
      else if (s.payload.one_time_expense) { setTab(1); setOneTimeExpense(String(s.payload.one_time_expense)); }
      else if (s.payload.category_changes) {
        setTab(2);
        const [cat, pct] = Object.entries(s.payload.category_changes)[0];
        setCategoryName(cat); setCategoryPct(Math.round((pct as number) * 100));
      }
      if (s.payload.description) setDescription(s.payload.description as string);
      setShowScenarios(false);
    } catch {}
  }

  const impactColor = result?.impact_level === "positive" ? dk.green : result?.impact_level === "negative" ? dk.red : dk.muted;

  const s: React.CSSProperties = { background: dk.card, border: `0.5px solid ${dk.border}`, borderRadius: "12px", padding: "16px" };
  const inp: React.CSSProperties = { background: dk.card2, border: `0.5px solid ${dk.border2}`, borderRadius: "8px", padding: "8px 12px", fontSize: "13px", color: dk.text, outline: "none", width: "100%", boxSizing: "border-box" };

  return (
    <div style={s}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <div style={{ fontSize: "11px", color: dk.muted, textTransform: "uppercase", letterSpacing: "0.5px" }}>Senaryo Simulatoru</div>
        <button onClick={() => setShowScenarios(v => !v)} style={{ fontSize: "12px", color: dk.blue, background: "none", border: "none", cursor: "pointer" }}>
          Gecmis ({scenarios.length})
        </button>
      </div>

      {showScenarios && (
        <div style={{ background: dk.card2, borderRadius: "8px", padding: "10px", marginBottom: "12px", border: `0.5px solid ${dk.border}` }}>
          {scenarios.length === 0 ? (
            <p style={{ fontSize: "12px", color: dk.hint }}>Henuz kaydedilmis senaryo yok.</p>
          ) : scenarios.map(item => (
            <div key={item.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderBottom: `0.5px solid ${dk.border}` }}>
              <div>
                <span style={{ fontSize: "12px", color: dk.text }}>{item.name}</span>
                <span style={{ fontSize: "11px", color: dk.hint, marginLeft: "8px" }}>{item.horizon_months} ay · {formatTL(item.savings_difference)}/ay</span>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button onClick={() => handleLoadScenario(item.id)} style={{ fontSize: "11px", color: dk.blue, background: "none", border: "none", cursor: "pointer" }}>Yukle</button>
                <button onClick={async () => { await deleteScenario(accountId, item.id); setScenarios(await listScenarios(accountId)); }} style={{ fontSize: "11px", color: dk.hint, background: "none", border: "none", cursor: "pointer" }}>Sil</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preset butonlar */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "12px" }}>
        {PRESETS.map(p => (
          <button key={p.label} onClick={() => {
            if (p.payload.income_change) { setTab(0); setIncomeChange(String(p.payload.income_change)); }
            else if (p.payload.category_changes) {
              setTab(2);
              const [cat, pct] = Object.entries(p.payload.category_changes)[0];
              setCategoryName(cat); setCategoryPct(Math.round((pct as number) * 100));
            }
            setDescription(p.payload.description);
          }} style={{ fontSize: "12px", color: dk.muted, background: dk.card2, border: `0.5px solid ${dk.border}`, borderRadius: "20px", padding: "5px 12px", cursor: "pointer" }}>
            {p.label}
          </button>
        ))}
      </div>

      {/* Tab seçici */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", background: dk.card2, borderRadius: "8px", padding: "3px", marginBottom: "14px" }}>
        {TABS.map((t, i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{ fontSize: "12px", padding: "7px", borderRadius: "6px", border: "none", cursor: "pointer", fontWeight: tab === i ? 500 : 400, background: tab === i ? dk.card : "transparent", color: tab === i ? dk.text : dk.muted }}>
            {t}
          </button>
        ))}
      </div>

      {/* Tab içerik */}
      {tab === 0 && (
        <div style={{ marginBottom: "12px" }}>
          <p style={{ fontSize: "12px", color: dk.hint, marginBottom: "8px" }}>Maas artisi, ek gelir gibi aylik gelirindeki degisimi gir.</p>
          <label style={{ fontSize: "11px", color: dk.muted, display: "block", marginBottom: "4px" }}>Aylik gelir degisimi (TL)</label>
          <input type="number" value={incomeChange} onChange={e => setIncomeChange(e.target.value)} placeholder="orn. 5000 veya -2000" style={inp} />
        </div>
      )}
      {tab === 1 && (
        <div style={{ marginBottom: "12px" }}>
          <p style={{ fontSize: "12px", color: dk.hint, marginBottom: "8px" }}>Tek seferlik buyuk harcama (telefon, tatil, araba vb.)</p>
          <label style={{ fontSize: "11px", color: dk.muted, display: "block", marginBottom: "4px" }}>Harcama tutari (TL)</label>
          <input type="number" value={oneTimeExpense} onChange={e => setOneTimeExpense(e.target.value)} placeholder="orn. 15000" style={inp} />
        </div>
      )}
      {tab === 2 && (
        <div style={{ marginBottom: "12px" }}>
          <p style={{ fontSize: "12px", color: dk.hint, marginBottom: "8px" }}>Belirli bir harcama kategorisini artir ya da azalt.</p>
          <label style={{ fontSize: "11px", color: dk.muted, display: "block", marginBottom: "4px" }}>Kategori adi</label>
          <input value={categoryName} onChange={e => setCategoryName(e.target.value)} placeholder="orn. yemek, ulasim" style={{ ...inp, marginBottom: "10px" }} />
          <label style={{ fontSize: "11px", color: dk.muted, display: "block", marginBottom: "4px" }}>Degisim orani</label>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <input type="range" min={-100} max={100} value={categoryPct} onChange={e => setCategoryPct(Number(e.target.value))} style={{ flex: 1, accentColor: dk.blue }} />
            <span style={{ fontSize: "13px", fontWeight: 500, color: categoryPct < 0 ? dk.green : dk.red, minWidth: "45px", textAlign: "right" }}>
              {categoryPct > 0 ? "+" : ""}{categoryPct}%
            </span>
          </div>
          <p style={{ fontSize: "11px", color: dk.hint, marginTop: "4px" }}>Negatif = harcamayi azalt, pozitif = harcamayi artir.</p>
        </div>
      )}

      {/* Projeksiyon süresi */}
      <div style={{ marginBottom: "12px" }}>
        <label style={{ fontSize: "11px", color: dk.muted, display: "block", marginBottom: "6px" }}>Projeksiyon suresi</label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "6px" }}>
          {HORIZONS.map(h => (
            <button key={h.months} onClick={() => setHorizonMonths(h.months)}
              style={{ fontSize: "13px", padding: "8px", borderRadius: "8px", border: `1px solid ${horizonMonths === h.months ? dk.blue : dk.border}`, background: horizonMonths === h.months ? dk.blueBg : "transparent", color: horizonMonths === h.months ? dk.blue : dk.muted, cursor: "pointer" }}>
              {h.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: "14px" }}>
        <label style={{ fontSize: "11px", color: dk.muted, display: "block", marginBottom: "4px" }}>Senaryo aciklamasi (opsiyonel)</label>
        <input value={description} onChange={e => setDescription(e.target.value)} placeholder="orn. Maas artisi + yemek harcamasini azaltma" style={inp} />
      </div>

      <button onClick={handleRun} disabled={loading}
        style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", background: "#5b8dee", color: "#fff", borderRadius: "8px", padding: "10px", fontSize: "14px", fontWeight: 500, border: "none", cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1, marginBottom: "12px" }}>
        {loading && <Spinner size={14} />}
        {loading ? "Simulasyon calistiriliyor..." : "Simulasyonu Calistir"}
      </button>

      {error && <div style={{ fontSize: "12px", color: dk.red, background: dk.redBg, borderRadius: "8px", padding: "8px 12px", marginBottom: "10px" }}>{error}</div>}

      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ borderRadius: "10px", padding: "12px 14px", border: `0.5px solid ${impactColor}22`, background: `${impactColor}08` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
              <span style={{ fontSize: "13px", fontWeight: 500, color: dk.text }}>{result.description}</span>
              <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "20px", background: `${impactColor}18`, color: impactColor }}>
                {result.impact_level === "positive" ? "Olumlu" : result.impact_level === "negative" ? "Olumsuz" : "Notr"}
              </span>
            </div>
            <p style={{ fontSize: "12px", color: dk.hint, lineHeight: 1.5 }}>{result.ai_summary}</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
            {[
              { label: "Mevcut aylik tasarruf", value: `${Math.round(parseFloat(result.current_monthly_savings)).toLocaleString("tr-TR")} ₺`, color: dk.muted },
              { label: "Simule edilen aylik tasarruf", value: `${Math.round(parseFloat(result.simulated_monthly_savings)).toLocaleString("tr-TR")} ₺`, color: parseFloat(result.savings_difference) >= 0 ? dk.green : dk.red },
              { label: "Aylik fark", value: `${parseFloat(result.savings_difference) >= 0 ? "+" : ""}${Math.round(parseFloat(result.savings_difference)).toLocaleString("tr-TR")} ₺`, color: parseFloat(result.savings_difference) >= 0 ? dk.green : dk.red },
              { label: "Yillik fark", value: `${parseFloat(result.annual_savings_difference) >= 0 ? "+" : ""}${Math.round(parseFloat(result.annual_savings_difference)).toLocaleString("tr-TR")} ₺`, color: parseFloat(result.annual_savings_difference) >= 0 ? dk.green : dk.red },
            ].map(item => (
              <div key={item.label} style={{ background: dk.card2, borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "11px", color: dk.hint, marginBottom: "3px" }}>{item.label}</div>
                <div style={{ fontSize: "15px", fontWeight: 500, color: item.color }}>{item.value}</div>
              </div>
            ))}
          </div>

          {result.monthly_projections && (
            <div>
              <div style={{ fontSize: "11px", color: dk.muted, marginBottom: "8px" }}>{result.horizon_months} aylik projeksiyon (kumulatif tasarruf)</div>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart data={result.monthly_projections.map(p => ({ ay: `Ay ${p.month}`, Birikim: Math.round(parseFloat(p.cumulative_savings)) }))} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="ay" tick={{ fontSize: 10, fill: dk.hint }} />
                  <YAxis tick={{ fontSize: 10, fill: dk.hint }} tickFormatter={v => `${(v/1000).toFixed(0)}K`} />
                  <Tooltip formatter={(v: number) => [`${v.toLocaleString("tr-TR")} ₺`, "Birikim"]} contentStyle={{ background: dk.card2, border: `0.5px solid ${dk.border}`, borderRadius: "8px", color: dk.text, fontSize: "12px" }} />
                  <Bar dataKey="Birikim" fill={dk.blue} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div style={{ display: "flex", gap: "8px" }}>
            <input value={scenarioName} onChange={e => setScenarioName(e.target.value)} placeholder="Senaryo adı (opsiyonel)" style={{ ...inp, flex: 1 }} />
            <button onClick={handleSave} disabled={isSaving}
              style={{ background: dk.card2, border: `0.5px solid ${dk.border2}`, color: dk.text, borderRadius: "8px", padding: "8px 14px", fontSize: "13px", cursor: "pointer", whiteSpace: "nowrap" }}>
              {isSaving ? "..." : "Kaydet"}
            </button>
          </div>
          {saveMessage && <p style={{ fontSize: "12px", color: saveMessage.includes("hata") ? dk.red : dk.green }}>{saveMessage}</p>}
        </div>
      )}
    </div>
  );
}
