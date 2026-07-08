import { useEffect, useState } from "react";
import * as goalsApi from "../api/goals";
import type { Goal, GoalAnalysis } from "../api/goals";
import Spinner from "./Spinner";

interface Props {
  accountId: string;
}

const PRIORITY_LABELS: Record<string, string> = {
  low: "Dusuk",
  medium: "Orta",
  high: "Yuksek",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-slate-100 text-slate-600",
  medium: "bg-yellow-50 text-yellow-700 border border-yellow-200",
  high: "bg-red-50 text-red-700 border border-red-200",
};

export default function GoalPlanner({ accountId }: Props) {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<GoalAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [priority, setPriority] = useState("medium");
  const [savings, setSavings] = useState("0");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadGoals();
  }, [accountId]);

  async function loadGoals() {
    setLoading(true);
    try {
      const data = await goalsApi.listGoals(accountId);
      setGoals(data);
    } catch {
      setError("Hedefler yuklenemedi.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!name || !amount || !date) {
      setError("Hedef adi, tutar ve tarih zorunludur.");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      await goalsApi.createGoal(accountId, {
        name,
        target_amount: parseFloat(amount),
        target_date: date,
        priority,
        current_savings: parseFloat(savings) || 0,
      });
      setShowForm(false);
      setName(""); setAmount(""); setDate(""); setPriority("medium"); setSavings("0");
      await loadGoals();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Hedef olusturulamadi.");
    } finally {
      setCreating(false);
    }
  }

  async function handleAnalyze(goal: Goal) {
    setAnalysisLoading(true);
    setSelectedAnalysis(null);
    try {
      const analysis = await goalsApi.analyzeGoal(goal.id, accountId);
      setSelectedAnalysis(analysis);
    } catch {
      setError("Analiz yapilamadi.");
    } finally {
      setAnalysisLoading(false);
    }
  }

  async function handleDelete(goalId: string) {
    if (!window.confirm("Bu hedefi iptal etmek istiyor musunuz?")) return;
    try {
      await goalsApi.deleteGoal(goalId);
      setGoals((prev) => prev.filter((g) => g.id !== goalId));
      if (selectedAnalysis?.goal.id === goalId) setSelectedAnalysis(null);
    } catch {
      setError("Hedef silinemedi.");
    }
  }

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-slate-700">Finansal Hedefler</h2>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="text-sm text-indigo-600 hover:underline"
        >
          + Yeni Hedef
        </button>
      </div>

      {error && (
        <div className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2 mb-3">
          {error}
        </div>
      )}

      {/* Hedef oluşturma formu */}
      {showForm && (
        <div className="border border-slate-200 rounded-xl p-4 mb-4 bg-slate-50 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Hedef Adi</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="orn. Bilgisayar, Tatil"
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-400"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Hedef Tutar (TL)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="80000"
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-400"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Hedef Tarihi</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-400"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Mevcut Birikim (TL)</label>
              <input
                type="number"
                value={savings}
                onChange={(e) => setSavings(e.target.value)}
                placeholder="0"
                className="w-full text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-400"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Oncelik</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-400"
            >
              <option value="low">Dusuk</option>
              <option value="medium">Orta</option>
              <option value="high">Yuksek</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={creating}
              className="inline-flex items-center gap-2 bg-indigo-600 text-white text-sm rounded-lg px-4 py-1.5 hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {creating && <Spinner size={14} />}
              {creating ? "Olusturuluyor..." : "Hedef Olustur"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="text-sm text-slate-500 hover:text-slate-700 px-3 py-1.5"
            >
              Iptal
            </button>
          </div>
        </div>
      )}

      {/* Hedef listesi */}
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner size={14} /> Hedefler yukleniyor...
        </div>
      ) : goals.length === 0 ? (
        <p className="text-sm text-slate-400">
          Henuz hedef yok. "+ Yeni Hedef" ile baslayin.
        </p>
      ) : (
        <div className="space-y-2">
          {goals.map((goal) => (
            <div
              key={goal.id}
              className="flex items-center justify-between border border-slate-100 rounded-lg px-3 py-2.5 hover:bg-slate-50"
            >
              <div className="flex items-center gap-3">
                <div>
                  <p className="text-sm font-medium text-slate-800">{goal.name}</p>
                  <p className="text-xs text-slate-400">
                    {parseFloat(goal.target_amount).toLocaleString("tr-TR")} TL
                    {" · "}
                    {new Date(goal.target_date).toLocaleDateString("tr-TR")}
                  </p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_COLORS[goal.priority]}`}>
                  {PRIORITY_LABELS[goal.priority]}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleAnalyze(goal)}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  AI Analizi
                </button>
                <button
                  onClick={() => handleDelete(goal.id)}
                  className="text-xs text-slate-400 hover:text-red-500"
                >
                  Sil
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI Analiz sonucu */}
      {analysisLoading && (
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
          <Spinner size={14} /> AI analiz yapiliyor...
        </div>
      )}

      {selectedAnalysis && (
        <div className={`mt-4 rounded-xl p-4 border ${selectedAnalysis.is_achievable ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"}`}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-800">
              {selectedAnalysis.goal.name} — AI Analizi
            </h3>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${selectedAnalysis.is_achievable ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
              {selectedAnalysis.is_achievable ? "Ulasılabilir" : "Zor Gorunuyor"}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white rounded-lg p-3 border border-slate-100">
              <p className="text-xs text-slate-400">Gereken Aylik Tasarruf</p>
              <p className="text-sm font-bold text-slate-800">
                {parseFloat(selectedAnalysis.monthly_savings_needed).toLocaleString("tr-TR", { maximumFractionDigits: 0 })} TL
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-100">
              <p className="text-xs text-slate-400">Mevcut Aylik Tasarruf</p>
              <p className="text-sm font-bold text-emerald-600">
                {parseFloat(selectedAnalysis.current_monthly_savings).toLocaleString("tr-TR", { maximumFractionDigits: 0 })} TL
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-100">
              <p className="text-xs text-slate-400">Kalan Sure</p>
              <p className="text-sm font-bold text-slate-800">
                {selectedAnalysis.months_remaining} ay
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-slate-100">
              <p className="text-xs text-slate-400">Tahmini Tamamlanma</p>
              <p className="text-sm font-bold text-slate-800">
                {new Date(selectedAnalysis.estimated_completion_date).toLocaleDateString("tr-TR", { year: "numeric", month: "long" })}
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg p-3 border border-slate-100 mb-3">
            <p className="text-xs text-slate-500 mb-1">AI Onerisi</p>
            <p className="text-sm text-slate-700">{selectedAnalysis.ai_recommendation}</p>
          </div>

          {selectedAnalysis.top_saving_opportunities.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Tasarruf Firsatlari</p>
              <div className="space-y-1.5">
                {selectedAnalysis.top_saving_opportunities.map((opp) => (
                  <div key={opp.category} className="bg-white rounded-lg px-3 py-2 border border-slate-100 flex items-center justify-between">
                    <span className="text-xs text-slate-700 capitalize">{opp.category}</span>
                    <span className="text-xs text-slate-500">
                      %20 azaltirsan →{" "}
                      <span className="text-emerald-600 font-medium">
                        +{opp.saving_20_percent.toLocaleString("tr-TR", { maximumFractionDigits: 0 })} TL/ay
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => setSelectedAnalysis(null)}
            className="mt-3 text-xs text-slate-400 hover:text-slate-600"
          >
            Kapat
          </button>
        </div>
      )}
    </section>
  );
}
