import { useEffect, useState } from "react";
import {
  deleteScenario,
  getScenario,
  listScenarios,
  runSimulation,
  saveScenario,
} from "../api/simulation";
import type { SavedScenarioSummary, SimulationResult } from "../api/simulation";
import Spinner from "./Spinner";

function formatTL(value: string | number) {
  const num = typeof value === "string" ? parseFloat(value) : value;
  const sign = num >= 0 ? "+" : "";
  return `${sign}${num.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺`;
}

function impactBadge(level: string) {
  const map: Record<string, { text: string; classes: string }> = {
    positive: { text: "olumlu", classes: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    negative: { text: "olumsuz", classes: "bg-red-50 text-red-700 border-red-200" },
    neutral: { text: "Notr", classes: "bg-slate-100 text-slate-500 border-slate-200" },
  };
  const info = map[level?.toLowerCase()] ?? map.neutral;
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${info.classes}`}>
      {info.text}
    </span>
  );
}

interface WhatIfSimulatorProps {
  accountId: string | null;
}

type ScenarioTab = "gelir" | "harcama" | "kategori";

const HORIZON_OPTIONS = [
  { months: 6, label: "6 ay" },
  { months: 12, label: "1 yil" },
  { months: 60, label: "5 yil" },
];

export default function WhatIfSimulator({ accountId }: WhatIfSimulatorProps) {
  const [activeTab, setActiveTab] = useState<ScenarioTab>("gelir");
  const [incomeChange, setIncomeChange] = useState("");
  const [oneTimeExpense, setOneTimeExpense] = useState("");
  const [categoryName, setCategoryName] = useState("");
  const [categoryPct, setCategoryPct] = useState(""); // decimal, orn. -0.30
  const [description, setDescription] = useState("");
  const [horizonMonths, setHorizonMonths] = useState(12);

  const [result, setResult] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [scenarioName, setScenarioName] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const [history, setHistory] = useState<SavedScenarioSummary[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  useEffect(() => {
    if (accountId) {
      void fetchHistory();
    } else {
      setHistory([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId]);

  async function fetchHistory() {
    if (!accountId) return;
    setIsHistoryLoading(true);
    try {
      const data = await listScenarios(accountId);
      setHistory(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsHistoryLoading(false);
    }
  }

  const categoryPctDisplay =
    categoryPct.trim() === "" ? 0 : Math.round(Number(categoryPct) * 100);

  function handleCategorySlider(val: number) {
    setCategoryPct((val / 100).toString());
  }

  function applyPreset(preset: "maas" | "kira" | "yemek") {
    if (preset === "maas") {
      setActiveTab("gelir");
      setIncomeChange("5000");
      setDescription("Maas artisi");
    } else if (preset === "kira") {
      setActiveTab("kategori");
      setCategoryName("kira");
      setCategoryPct("0.30");
      setDescription("Kira zammi");
    } else {
      setActiveTab("kategori");
      setCategoryName("yemek");
      setCategoryPct("-0.50");
      setDescription("Yemek harcamasini yariya indirme");
    }
  }

  function buildPayload(): Record<string, unknown> {
    const payload: Record<string, unknown> = { horizon_months: horizonMonths };
    if (incomeChange.trim() !== "") payload.income_change = Number(incomeChange);
    if (oneTimeExpense.trim() !== "") payload.one_time_expense = Number(oneTimeExpense);
    if (categoryName.trim() !== "" && categoryPct.trim() !== "") {
      payload.category_changes = { [categoryName.trim()]: Number(categoryPct) };
    }
    if (description.trim() !== "") payload.description = description.trim();
    return payload;
  }

  async function handleRun() {
    if (!accountId) {
      setError("Once bir hesap secmelisiniz.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setSaveMessage(null);
    try {
      const data = await runSimulation(accountId, buildPayload());
      setResult(data);
    } catch (err) {
      setError("Simulasyon calistirilirken bir hata olustu.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSave() {
    if (!accountId) return;
    setIsSaving(true);
    setSaveMessage(null);
    try {
      await saveScenario(accountId, scenarioName || description, buildPayload());
      setSaveMessage("Senaryo kaydedildi.");
      setScenarioName("");
      await fetchHistory();
    } catch (err) {
      setSaveMessage("Kaydedilirken bir hata olustu.");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLoadScenario(scenarioId: string) {
    if (!accountId) return;
    try {
      const detail = await getScenario(accountId, scenarioId);
      const req = detail.request;
      setIncomeChange(req.income_change ? String(req.income_change) : "");
      setOneTimeExpense(req.one_time_expense ? String(req.one_time_expense) : "");
      const catEntries = Object.entries(req.category_changes ?? {});
      if (catEntries.length > 0) {
        setCategoryName(catEntries[0][0]);
        setCategoryPct(String(catEntries[0][1]));
        setActiveTab("kategori");
      } else if (req.income_change) {
        setActiveTab("gelir");
      } else if (req.one_time_expense) {
        setActiveTab("harcama");
      }
      setDescription(req.description ?? "");
      setHorizonMonths(req.horizon_months ?? 12);
      setResult(detail.result);
      setIsHistoryOpen(false);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleDeleteScenario(scenarioId: string) {
    if (!accountId) return;
    try {
      await deleteScenario(accountId, scenarioId);
      await fetchHistory();
    } catch (err) {
      console.error(err);
    }
  }

  const tabs: { key: ScenarioTab; label: string }[] = [
    { key: "gelir", label: "Gelir degisikligi" },
    { key: "harcama", label: "Tek seferlik harcama" },
    { key: "kategori", label: "Harcama kategorisi" },
  ];

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-medium text-slate-700">Senaryo Simulatoru</h2>
        <button
          type="button"
          onClick={() => setIsHistoryOpen((v) => !v)}
          className="text-xs text-indigo-600 hover:text-indigo-700"
        >
          Gecmis ({history.length})
        </button>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Bir degisiklik yapsan butcen nasil etkilenir, onceden gor.
      </p>

      {isHistoryOpen && (
        <div className="mb-4 border border-slate-200 rounded-lg p-3">
          {isHistoryLoading && <p className="text-xs text-slate-400">Yukleniyor...</p>}
          {!isHistoryLoading && history.length === 0 && (
            <p className="text-xs text-slate-400">Henuz kaydedilmis senaryo yok.</p>
          )}
          <ul className="space-y-2">
            {history.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between text-xs bg-slate-50 rounded-lg px-3 py-2"
              >
                <button
                  type="button"
                  onClick={() => handleLoadScenario(item.id)}
                  className="text-left flex-1 mr-2"
                >
                  <span className="font-medium text-slate-700">{item.name}</span>
                  <span className="text-slate-400 ml-2">
                    {item.horizon_months} ay ·{" "}
                    {formatTL(item.savings_difference)}/ay
                  </span>
                </button>
                {impactBadge(item.impact_level)}
                <button
                  type="button"
                  onClick={() => handleDeleteScenario(item.id)}
                  className="ml-2 text-slate-400 hover:text-red-500"
                  aria-label="Senaryoyu sil"
                >
                  âœ•
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Hazir senaryo cipleri */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          onClick={() => applyPreset("maas")}
          className="text-xs px-3 py-1.5 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50"
        >
          Maasim %20 artarsa
        </button>
        <button
          type="button"
          onClick={() => applyPreset("kira")}
          className="text-xs px-3 py-1.5 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50"
        >
          Kira zammi geldi
        </button>
        <button
          type="button"
          onClick={() => applyPreset("yemek")}
          className="text-xs px-3 py-1.5 rounded-full border border-slate-200 text-slate-600 hover:bg-slate-50"
        >
          Yemek harcamami yariya indirsem
        </button>
      </div>

      {/* Sekmeler */}
      <div className="flex gap-1 bg-slate-50 rounded-lg p-1 mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 text-xs px-2 py-2 rounded-md transition-colors ${
              activeTab === tab.key
                ? "bg-white text-slate-800 font-medium shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Gelir degisikligi */}
      {activeTab === "gelir" && (
        <div className="mb-4">
          <p className="text-xs text-slate-400 mb-2">
            Maas artisi, ek gelir gibi aylik gelirindeki degisimi gir.
          </p>
          <label className="text-xs text-slate-500 block mb-1">Aylik gelir degisimi (TL)</label>
          <input
            type="number"
            value={incomeChange}
            onChange={(e) => setIncomeChange(e.target.value)}
            placeholder="orn. 5000"
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />
        </div>
      )}

      {/* Tek seferlik harcama */}
      {activeTab === "harcama" && (
        <div className="mb-4">
          <p className="text-xs text-slate-400 mb-2">
            Bir alet alma, tatil ya da tek seferlik bir odeme gibi harcamalar icin.
          </p>
          <label className="text-xs text-slate-500 block mb-1">Tutar (TL)</label>
          <input
            type="number"
            value={oneTimeExpense}
            onChange={(e) => setOneTimeExpense(e.target.value)}
            placeholder="orn. 15000"
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />
        </div>
      )}

      {/* Harcama kategorisi */}
      {activeTab === "kategori" && (
        <div className="mb-4">
          <p className="text-xs text-slate-400 mb-2">
            Belirli bir harcama kategorisini artir ya da azalt.
          </p>
          <label className="text-xs text-slate-500 block mb-1">Kategori adi</label>
          <input
            type="text"
            value={categoryName}
            onChange={(e) => setCategoryName(e.target.value)}
            placeholder="orn. yemek"
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />
          <label className="text-xs text-slate-500 block mb-1">Degisim orani</label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={-80}
              max={80}
              step={5}
              value={categoryPctDisplay}
              onChange={(e) => handleCategorySlider(Number(e.target.value))}
              className="flex-1"
            />
            <span
              className={`text-sm font-medium min-w-[48px] text-right ${
                categoryPctDisplay < 0 ? "text-emerald-600" : "text-red-600"
              }`}
            >
              {categoryPctDisplay > 0 ? "+" : ""}
              {categoryPctDisplay}%
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Negatif = harcamayi azalt, pozitif = harcamayi artir.
          </p>
        </div>
      )}

      {/* Zaman ufku */}
      <div className="mb-4">
        <label className="text-xs text-slate-500 block mb-1">Projeksiyon suresi</label>
        <div className="flex gap-2">
          {HORIZON_OPTIONS.map((opt) => (
            <button
              key={opt.months}
              type="button"
              onClick={() => setHorizonMonths(opt.months)}
              className={`flex-1 text-xs px-3 py-2 rounded-lg border transition-colors ${
                horizonMonths === opt.months
                  ? "border-indigo-400 bg-indigo-50 text-indigo-700 font-medium"
                  : "border-slate-200 text-slate-500 hover:bg-slate-50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3">
        <label className="text-xs text-slate-500 block mb-1">Senaryo aciklamasi (opsiyonel)</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="orn. Maas artisi + yemek harcamasini azaltma"
          className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200"
        />
      </div>

      <button
        onClick={handleRun}
        disabled={isLoading}
        className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <Spinner size={14} /> Calistiriliyor...
          </span>
        ) : (
          "Simulasyonu Calistir"
        )}
      </button>

      {error && <p className="text-xs text-red-500 mt-2">{error}</p>}

      {result && (
        <div className="mt-5 pt-4 border-t border-slate-100">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-medium text-slate-700">{result.description}</h3>
            {impactBadge(result.impact_level)}
          </div>
          <p className="text-xs text-slate-400 mb-4">{result.ai_summary}</p>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-xs text-slate-400 mb-1">Mevcut aylik tasarruf</p>
              <p className="text-lg font-semibold text-slate-900">
                {formatTL(result.current_monthly_savings)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Simule edilen aylik tasarruf</p>
              <p
                className={`text-lg font-semibold ${
                  parseFloat(result.simulated_monthly_savings) >= 0
                    ? "text-emerald-600"
                    : "text-red-600"
                }`}
              >
                {formatTL(result.simulated_monthly_savings)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Aylik fark</p>
              <p
                className={`text-lg font-semibold ${
                  parseFloat(result.savings_difference) >= 0
                    ? "text-emerald-600"
                    : "text-red-600"
                }`}
              >
                {formatTL(result.savings_difference)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Yillik fark</p>
              <p
                className={`text-lg font-semibold ${
                  parseFloat(result.annual_savings_difference) >= 0
                    ? "text-emerald-600"
                    : "text-red-600"
                }`}
              >
                {formatTL(result.annual_savings_difference)}
              </p>
            </div>
          </div>

          {result.monthly_projections.length > 0 && (
            <div className="mb-4">
              <p className="text-xs text-slate-400 mb-2">
                {result.horizon_months} aylik projeksiyon (kumulatif tasarruf)
              </p>
              <div className="flex items-end gap-1" style={{ height: "80px" }}>
                {result.monthly_projections.map((proj) => {
                  const values = result.monthly_projections.map((p) =>
                    Math.abs(parseFloat(p.cumulative_savings))
                  );
                  const maxAbs = Math.max(...values, 1);
                  const val = parseFloat(proj.cumulative_savings);
                  const heightPx = Math.max((Math.abs(val) / maxAbs) * 64, 8);
                  return (
                    <div
                      key={proj.month}
                      className="flex-1 flex flex-col items-center justify-end gap-1"
                      style={{ height: "80px" }}
                    >
                      <div
                        className={`w-full rounded-t ${
                          val >= 0 ? "bg-emerald-400" : "bg-red-300"
                        }`}
                        style={{ height: `${heightPx}px` }}
                        title={formatTL(proj.cumulative_savings)}
                      />
                      {result.horizon_months <= 12 && (
                        <span className="text-[10px] text-slate-400">Ay {proj.month}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Senaryoyu kaydet */}
          <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
            <input
              type="text"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              placeholder="Senaryoya bir isim ver (opsiyonel)"
              className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="text-sm font-medium px-4 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-50"
            >
              {isSaving ? "Kaydediliyor..." : "Kaydet"}
            </button>
          </div>
          {saveMessage && <p className="text-xs text-slate-400 mt-2">{saveMessage}</p>}
        </div>
      )}
    </section>
  );
}


