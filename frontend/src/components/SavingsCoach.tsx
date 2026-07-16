import { useEffect, useState } from "react";
import { getSavingsReport } from "../api/savingsCoach";
import type { SavingsCoachReport, SavingTip, SpendingTrend } from "../api/savingsCoach";
import Spinner from "./Spinner";

interface Props {
  accountId: string;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  kolay: "bg-emerald-50 text-emerald-700 border-emerald-200",
  orta: "bg-yellow-50 text-yellow-700 border-yellow-200",
  zor: "bg-red-50 text-red-700 border-red-200",
};

const PRIORITY_COLORS: Record<string, string> = {
  yuksek: "bg-red-50 text-red-600 border-red-200",
  orta: "bg-yellow-50 text-yellow-600 border-yellow-200",
  dusuk: "bg-slate-50 text-slate-500 border-slate-200",
};

const TREND_ICONS: Record<string, string> = {
  artiyor: "↑",
  azaliyor: "↓",
  stabil: "→",
};

const TREND_COLORS: Record<string, string> = {
  artiyor: "text-red-500",
  azaliyor: "text-emerald-500",
  stabil: "text-slate-400",
};

function formatTL(value: string | number) {
  const num = typeof value === "string" ? parseFloat(value) : value;
  return num.toLocaleString("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: 0 }) + " ₺";
}

function SavingsRateBar({ current, target }: { current: number; target: number }) {
  const pct = Math.min(current, 100);
  const color = current >= target ? "bg-emerald-500" : current >= target / 2 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="w-full bg-slate-100 rounded-full h-3 relative">
      <div className={`h-3 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      <div
        className="absolute top-0 h-3 w-0.5 bg-slate-400"
        style={{ left: `${target}%` }}
        title={`Hedef: %${target}`}
      />
    </div>
  );
}

export default function SavingsCoach({ accountId }: Props) {
  const [report, setReport] = useState<SavingsCoachReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTrends, setShowTrends] = useState(false);

  useEffect(() => {
    setLoading(true);
    getSavingsReport(accountId)
      .then(setReport)
      .catch(() => setError("Tasarruf raporu yuklenemedi."))
      .finally(() => setLoading(false));
  }, [accountId]);

  if (loading) {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner size={14} /> AI Savings Coach analiz yapıyor...
        </div>
      </section>
    );
  }

  if (error || !report) {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <p className="text-sm text-slate-400">{error ?? "Rapor yuklenemedi."}</p>
      </section>
    );
  }

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-5 space-y-5">
      {/* Başlık */}
      <div>
        <h2 className="text-sm font-medium text-slate-700 mb-1">AI Savings Coach</h2>
        <p className="text-xs text-slate-500">{report.coach_message}</p>
      </div>

      {/* Tasarruf oranı */}
      <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-700">Tasarruf Oranı</span>
          <div className="flex items-center gap-2">
            <span className={`text-sm font-bold ${report.current_savings_rate >= report.target_savings_rate ? "text-emerald-600" : "text-yellow-600"}`}>
              %{report.current_savings_rate.toFixed(1)}
            </span>
            <span className="text-xs text-slate-400">/ Hedef %{report.target_savings_rate}</span>
          </div>
        </div>
        <SavingsRateBar current={report.current_savings_rate} target={report.target_savings_rate} />
        <div className="flex justify-between mt-2 text-xs text-slate-400">
          <span>Aylık gelir: {formatTL(report.total_monthly_income)}</span>
          <span>Aylık gider: {formatTL(report.total_monthly_expense)}</span>
        </div>
        {parseFloat(report.potential_annual_savings) > 0 && (
          <div className="mt-2 text-xs text-emerald-600 font-medium">
            Önerileri uygularsan yıllık +{formatTL(report.potential_annual_savings)} tasarruf potansiyeli
          </div>
        )}
      </div>

      {/* Tasarruf önerileri */}
      {report.tips.length > 0 && (
        <div>
          <h3 className="text-xs font-medium text-slate-700 mb-2">Kişisel Öneriler</h3>
          <div className="space-y-2">
            {report.tips.map((tip, i) => (
              <div key={i} className="border border-slate-100 rounded-lg p-3">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-sm font-medium text-slate-800">{tip.title}</p>
                  <div className="flex gap-1 shrink-0">
                    <span className={`text-xs px-1.5 py-0.5 rounded-full border ${PRIORITY_COLORS[tip.priority] ?? PRIORITY_COLORS.orta}`}>
                      {tip.priority}
                    </span>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full border ${DIFFICULTY_COLORS[tip.difficulty] ?? DIFFICULTY_COLORS.orta}`}>
                      {tip.difficulty}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mb-2">{tip.description}</p>
                <div className="flex gap-4 text-xs">
                  <span className="text-emerald-600 font-medium">
                    Aylık +{formatTL(tip.monthly_saving_potential)}
                  </span>
                  <span className="text-slate-400">
                    Yıllık +{formatTL(tip.annual_saving_potential)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Harcama trendleri */}
      <div>
        <button
          onClick={() => setShowTrends((v) => !v)}
          className="text-xs text-indigo-600 hover:underline"
        >
          {showTrends ? "Trendleri Gizle" : "Harcama Trendlerini Gör"}
        </button>

        {showTrends && (
          <div className="mt-2 space-y-1.5">
            {report.spending_trends.map((trend) => (
              <div key={trend.category} className="flex items-center justify-between px-3 py-2 bg-slate-50 rounded-lg border border-slate-100">
                <span className="text-xs font-medium text-slate-700 capitalize">{trend.category}</span>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400">{formatTL(trend.current_monthly)}/ay</span>
                  <span className={`font-medium ${TREND_COLORS[trend.trend]}`}>
                    {TREND_ICONS[trend.trend]} {Math.abs(trend.change_pct).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
