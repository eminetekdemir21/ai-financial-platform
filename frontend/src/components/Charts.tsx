import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { Transaction } from "../api/transactions";

// Kategori renkleri
const CATEGORY_COLORS: Record<string, string> = {
  market: "#6366f1",
  yemek: "#f59e0b",
  ulasim: "#10b981",
  alisveris: "#3b82f6",
  fatura: "#ef4444",
  abonelik: "#8b5cf6",
  yatirim: "#14b8a6",
  saglik: "#ec4899",
  egitim: "#f97316",
  gelir: "#22c55e",
  diger: "#94a3b8",
  kategorisiz: "#cbd5e1",
};

function getColor(category: string): string {
  return CATEGORY_COLORS[category] ?? "#94a3b8";
}

// --- Kategori Pasta Grafiği ---
interface CategoryChartProps {
  transactions: Transaction[];
}

export function CategoryPieChart({ transactions }: CategoryChartProps) {
  const expenses = transactions.filter((t) => parseFloat(t.amount) < 0);

  const categoryTotals: Record<string, number> = {};
  for (const tx of expenses) {
    const cat = tx.category ?? "kategorisiz";
    categoryTotals[cat] = (categoryTotals[cat] ?? 0) + Math.abs(parseFloat(tx.amount));
  }

  const data = Object.entries(categoryTotals)
    .map(([name, value]) => ({ name, value: Math.round(value * 100) / 100 }))
    .sort((a, b) => b.value - a.value);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-slate-400">
        Grafik için kategorilendirilmiş harcama gerekiyor.
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload?.length) {
      return (
        <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs shadow">
          <p className="font-medium text-slate-700">{payload[0].name}</p>
          <p className="text-slate-500">
            {payload[0].value.toLocaleString("tr-TR", { minimumFractionDigits: 2 })} ₺
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={getColor(entry.name)} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => (
            <span className="text-xs text-slate-600">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

// --- Aylık Gelir/Gider Bar Chart ---
export function MonthlyBarChart({ transactions }: CategoryChartProps) {
  // İşlemleri aya göre grupla
  const monthly: Record<string, { gelir: number; gider: number }> = {};

  for (const tx of transactions) {
    const date = new Date(tx.transaction_date);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    if (!monthly[key]) monthly[key] = { gelir: 0, gider: 0 };

    const amount = parseFloat(tx.amount);
    if (amount > 0) {
      monthly[key].gelir += amount;
    } else {
      monthly[key].gider += Math.abs(amount);
    }
  }

  const data = Object.entries(monthly)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, values]) => ({
      month,
      Gelir: Math.round(values.gelir),
      Gider: Math.round(values.gider),
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-slate-400">
        Grafik için işlem verisi gerekiyor.
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload?.length) {
      return (
        <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs shadow">
          <p className="font-medium text-slate-700 mb-1">{label}</p>
          {payload.map((p: any) => (
            <p key={p.name} style={{ color: p.color }}>
              {p.name}: {p.value.toLocaleString("tr-TR")} ₺
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#94a3b8" }} />
        <YAxis
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="square"
          iconSize={8}
          formatter={(value) => (
            <span className="text-xs text-slate-600">{value}</span>
          )}
        />
        <Bar dataKey="Gelir" fill="#22c55e" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Gider" fill="#f87171" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// --- Health Score Gauge (SVG tabanlı) ---
interface GaugeProps {
  score: number;
  grade: string;
}

export function HealthScoreGauge({ score, grade }: GaugeProps) {
  const radius = 70;
  const stroke = 12;
  const normalizedRadius = radius - stroke / 2;
  const circumference = normalizedRadius * Math.PI; // yarım daire

  // 0-100 skoru yarım daire üzerinde göster
  const progress = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const gradeColors: Record<string, string> = {
    A: "#22c55e",
    B: "#3b82f6",
    C: "#f59e0b",
    D: "#f97316",
    F: "#ef4444",
  };
  const color = gradeColors[grade] ?? "#94a3b8";

  return (
    <div className="flex flex-col items-center">
      <svg width={radius * 2} height={radius + stroke} viewBox={`0 0 ${radius * 2} ${radius + stroke}`}>
        {/* Arka plan yayı */}
        <path
          d={`M ${stroke / 2} ${radius} A ${normalizedRadius} ${normalizedRadius} 0 0 1 ${radius * 2 - stroke / 2} ${radius}`}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Skor yayı */}
        <path
          d={`M ${stroke / 2} ${radius} A ${normalizedRadius} ${normalizedRadius} 0 0 1 ${radius * 2 - stroke / 2} ${radius}`}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        {/* Skor metni */}
        <text
          x={radius}
          y={radius - 8}
          textAnchor="middle"
          fontSize="24"
          fontWeight="700"
          fill={color}
        >
          {score}
        </text>
        <text
          x={radius}
          y={radius + 10}
          textAnchor="middle"
          fontSize="13"
          fill="#94a3b8"
        >
          / 100
        </text>
      </svg>
      <span
        className="text-2xl font-bold mt-1"
        style={{ color }}
      >
        {grade}
      </span>
    </div>
  );
}
