import type { ForecastResult } from "../api/forecast";
import Spinner from "./Spinner";

function formatTL(amount: number) {
  const sign = amount >= 0 ? "+" : "";
  return `${sign}${amount.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺`;
}

function confidenceBadge(confidence: string) {
  const map: Record<string, { text: string; classes: string }> = {
    high: { text: "yuksek guven", classes: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    medium: { text: "orta guven", classes: "bg-amber-50 text-amber-700 border-amber-200" },
    low: { text: "dusuk guven", classes: "bg-slate-100 text-slate-500 border-slate-200" },
    none: { text: "veri yok", classes: "bg-slate-100 text-slate-400 border-slate-200" },
  };
  const info = map[confidence] ?? map.low;
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${info.classes}`}>
      {info.text}
    </span>
  );
}

interface ForecastCardProps {
  data: ForecastResult | null;
  isLoading: boolean;
}

export default function ForecastCard({ data, isLoading }: ForecastCardProps) {
  if (isLoading) {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner size={14} />
          Gelecek ay tahmini hesaplaniyor...
        </div>
      </section>
    );
  }

  if (!data) return null;

  if (data.method === "insufficient_data") {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <h2 className="text-sm font-medium text-slate-700 mb-1">
          Gelecek Ay Tahmini
        </h2>
        <p className="text-sm text-slate-400">{data.message}</p>
      </section>
    );
  }

  const months = Object.entries(data.monthly_history);

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-medium text-slate-700">Gelecek Ay Tahmini</h2>
        {confidenceBadge(data.confidence)}
      </div>
      <p className="text-xs text-slate-400 mb-4">{data.message}</p>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-slate-400 mb-1">Tahmini net nakit akisi</p>
          <p
            className={`text-xl font-semibold ${
              data.predicted_next_month_net >= 0 ? "text-emerald-600" : "text-red-600"
            }`}
          >
            {formatTL(data.predicted_next_month_net)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400 mb-1">Projekte edilen bakiye</p>
          <p className="text-xl font-semibold text-slate-900">
            {formatTL(data.projected_balance)}
          </p>
        </div>
      </div>

      {months.length > 0 && (
        <div>
          <p className="text-xs text-slate-400 mb-2">Aylik gecmis</p>
          <div className="flex items-end gap-2 h-16">
            {months.map(([month, value]) => {
              const maxAbs = Math.max(...months.map(([, v]) => Math.abs(v)), 1);
              const heightPct = Math.max((Math.abs(value) / maxAbs) * 100, 8);
              return (
                <div key={month} className="flex-1 flex flex-col items-center gap-1">
                  <div
                    className={`w-full rounded-t ${
                      value >= 0 ? "bg-emerald-400" : "bg-red-300"
                    }`}
                    style={{ height: `${heightPct}%` }}
                    title={formatTL(value)}
                  />
                  <span className="text-[10px] text-slate-400">{month.slice(5)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
