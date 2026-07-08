import type { HealthScoreResult } from "../api/health";
import Spinner from "./Spinner";

function gradeColor(grade: string): { bg: string; text: string; border: string } {
  if (grade === "A" || grade === "B") {
    return { bg: "bg-emerald-50", text: "text-emerald-700", border: "border-emerald-200" };
  }
  if (grade === "C") {
    return { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" };
  }
  return { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" };
}

function barColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

interface HealthScoreCardProps {
  data: HealthScoreResult | null;
  isLoading: boolean;
}

export default function HealthScoreCard({ data, isLoading }: HealthScoreCardProps) {
  if (isLoading) {
    return (
      <section className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner size={14} />
          Finansal saglik skoru hesaplaniyor...
        </div>
      </section>
    );
  }

  if (!data) return null;

  const colors = gradeColor(data.grade);
  const factors = Object.values(data.breakdown);

  return (
    <section className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="text-sm font-medium text-slate-700 mb-1">
            Finansal Saglik Skoru
          </h2>
          <p className="text-sm text-slate-500 max-w-md">{data.summary}</p>
        </div>
        <div
          className={`flex items-center gap-3 shrink-0 rounded-xl border px-4 py-2 ${colors.bg} ${colors.border}`}
        >
          <span className={`text-3xl font-semibold ${colors.text}`}>{data.score}</span>
          <span
            className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold ${colors.text} ${colors.bg} border ${colors.border}`}
          >
            {data.grade}
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {factors.map((factor) => (
          <div key={factor.label}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-600 font-medium">{factor.label}</span>
              <span className="text-slate-400">{factor.score}/100</span>
            </div>
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${barColor(factor.score)}`}
                style={{ width: `${factor.score}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-1">{factor.comment}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
