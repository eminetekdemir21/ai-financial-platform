import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Spinner from "../components/Spinner";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Giris basarisiz. Bilgilerinizi kontrol edin.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const features = [
    { icon: "🛡️", title: "Fraud Detection", desc: "Şüpheli işlemleri AI ile otomatik tespit eder" },
    { icon: "📊", title: "Financial Health Score", desc: "0-100 arası finansal sağlık puanı" },
    { icon: "🎯", title: "AI Goal Planner", desc: "Hedeflerinize akıllı tasarruf planı" },
    { icon: "🔮", title: "What-If Simülasyon", desc: "Finansal senaryoları önceden modelleyin" },
    { icon: "💬", title: "AI Finansal Asistan", desc: "Verilerinize dayalı kişisel danışmanınız" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#0f1117", display: "flex", position: "relative", overflow: "hidden" }}>
      {/* Arka plan ışık efektleri */}
      <div style={{ position: "absolute", top: "-100px", left: "-100px", width: "500px", height: "500px", borderRadius: "50%", background: "radial-gradient(circle, rgba(91,141,238,0.10) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", bottom: "-100px", right: "400px", width: "400px", height: "400px", borderRadius: "50%", background: "radial-gradient(circle, rgba(124,109,232,0.08) 0%, transparent 70%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: "50%", left: "40%", width: "300px", height: "300px", borderRadius: "50%", background: "radial-gradient(circle, rgba(0,214,143,0.05) 0%, transparent 70%)", pointerEvents: "none" }} />

      {/* Sol panel */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px 64px" }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "56px" }}>
          <span style={{ fontSize: "22px", color: "#5b8dee" }}>⬡</span>
          <span style={{ color: "#f1f1f3", fontSize: "17px", fontWeight: 500 }}>AI Financial Platform</span>
        </div>

        {/* Başlık */}
        <h1 style={{ fontSize: "38px", fontWeight: 500, color: "#f1f1f3", lineHeight: 1.25, marginBottom: "16px" }}>
          Finansal zekânızı<br />
          <span style={{ color: "#5b8dee" }}>yapay zeka ile</span><br />
          güçlendirin.
        </h1>
        <p style={{ fontSize: "14px", color: "#8b8fa8", lineHeight: 1.7, maxWidth: "400px", marginBottom: "40px" }}>
          Banka işlemlerinizi analiz eden, fraud tespit eden, tasarruf fırsatları bulan ve finansal hedeflerinize ulaşmanızı sağlayan AI destekli platform.
        </p>

        {/* Özellikler */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {features.map((f) => (
            <div key={f.title} style={{ display: "flex", alignItems: "center", gap: "14px" }}>
              <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "rgba(91,141,238,0.10)", border: "0.5px solid rgba(91,141,238,0.18)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "17px", flexShrink: 0 }}>
                {f.icon}
              </div>
              <div>
                <div style={{ fontSize: "13px", fontWeight: 500, color: "#f1f1f3" }}>{f.title}</div>
                <div style={{ fontSize: "12px", color: "#8b8fa8" }}>{f.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dikey ayraç */}
      <div style={{ width: "0.5px", background: "rgba(255,255,255,0.06)", margin: "40px 0", flexShrink: 0 }} />

      {/* Sağ panel — form */}
      <div style={{ width: "480px", display: "flex", alignItems: "center", justifyContent: "center", padding: "40px" }}>
        <div style={{ width: "100%", background: "#1a1d27", border: "0.5px solid rgba(255,255,255,0.08)", borderRadius: "16px", padding: "36px" }}>
          <div style={{ marginBottom: "28px" }}>
            <h2 style={{ fontSize: "22px", fontWeight: 500, color: "#f1f1f3", marginBottom: "6px" }}>Giriş Yap</h2>
            <p style={{ fontSize: "13px", color: "#8b8fa8" }}>Hesabınıza erişmek için bilgilerinizi girin.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "11px", color: "#8b8fa8", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>E-posta</label>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="ornek@eposta.com"
                style={{ width: "100%", background: "#21253a", border: "0.5px solid rgba(255,255,255,0.12)", borderRadius: "8px", padding: "10px 14px", fontSize: "14px", color: "#f1f1f3", outline: "none", boxSizing: "border-box" }}
                onFocus={(e) => e.target.style.borderColor = "#5b8dee"}
                onBlur={(e) => e.target.style.borderColor = "rgba(255,255,255,0.12)"} />
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "11px", color: "#8b8fa8", marginBottom: "6px", textTransform: "uppercase", letterSpacing: "0.5px" }}>Şifre</label>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{ width: "100%", background: "#21253a", border: "0.5px solid rgba(255,255,255,0.12)", borderRadius: "8px", padding: "10px 14px", fontSize: "14px", color: "#f1f1f3", outline: "none", boxSizing: "border-box" }}
                onFocus={(e) => e.target.style.borderColor = "#5b8dee"}
                onBlur={(e) => e.target.style.borderColor = "rgba(255,255,255,0.12)"} />
            </div>

            {error && (
              <div style={{ display: "flex", alignItems: "flex-start", gap: "8px", background: "rgba(255,107,107,0.08)", border: "0.5px solid rgba(255,107,107,0.2)", borderRadius: "8px", padding: "10px 12px", marginBottom: "16px" }}>
                <span style={{ color: "#ff6b6b" }}>⚠</span>
                <span style={{ color: "#ff6b6b", fontSize: "13px" }}>{error}</span>
              </div>
            )}

            <button type="submit" disabled={isSubmitting}
              style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", background: "#5b8dee", color: "#fff", borderRadius: "8px", padding: "11px", fontSize: "14px", fontWeight: 500, border: "none", cursor: isSubmitting ? "not-allowed" : "pointer", opacity: isSubmitting ? 0.7 : 1 }}
              onMouseOver={(e) => { if (!isSubmitting) e.currentTarget.style.background = "#4a7de0"; }}
              onMouseOut={(e) => { e.currentTarget.style.background = "#5b8dee"; }}>
              {isSubmitting && <Spinner size={14} />}
              {isSubmitting ? "Giris yapiliyor..." : "Giriş Yap"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: "20px", fontSize: "13px", color: "#8b8fa8" }}>
            Hesabınız yok mu?{" "}
            <Link to="/register" style={{ color: "#5b8dee", textDecoration: "none", fontWeight: 500 }}>Kayıt olun</Link>
          </p>

          {/* Demo hesap */}
          <div style={{ marginTop: "20px", padding: "10px 14px", background: "rgba(0,214,143,0.06)", border: "0.5px solid rgba(0,214,143,0.15)", borderRadius: "8px" }}>
            <div style={{ fontSize: "11px", color: "#00d68f", fontWeight: 500, marginBottom: "4px" }}>Demo Hesabı</div>
            <div style={{ fontSize: "12px", color: "#8b8fa8" }}>test@example.com / Sifre123</div>
          </div>
        </div>
      </div>
    </div>
  );
}
