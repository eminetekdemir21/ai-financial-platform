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
    <div style={{ minHeight: "100vh", background: "#0f1117" }}>
      <div className="container-fluid" style={{ minHeight: "100vh" }}>
        <div className="row" style={{ minHeight: "100vh" }}>

          {/* Sol panel - özellikler (sadece md ve üstünde görünür) */}
          <div className="col-lg-6 d-none d-lg-flex flex-column justify-content-center px-5" style={{ background: "rgba(91,141,238,0.04)", borderRight: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="mb-5">
              <span style={{ fontSize: "22px", color: "#5b8dee" }}>⬡</span>
              <span style={{ color: "#f1f1f3", fontSize: "17px", fontWeight: 500, marginLeft: 10 }}>AI Financial Platform</span>
            </div>
            <h2 style={{ color: "#f1f1f3", fontSize: "2rem", fontWeight: 700, marginBottom: 12, lineHeight: 1.2 }}>
              Finansal zekânızı<br />
              <span style={{ color: "#5b8dee" }}>yapay zeka ile</span><br />
              güçlendirin.
            </h2>
            <p style={{ color: "#8b8fa8", fontSize: "15px", marginBottom: 40, lineHeight: 1.7 }}>
              Banka işlemlerinizi analiz eden, fraud tespit eden, tasarruf fırsatları bulan ve finansal hedeflerinize ulaşmanızı sağlayan AI destekli platform.
            </p>
            <div>
              {features.map((f, i) => (
                <div key={i} className="d-flex align-items-start mb-3">
                  <div style={{ width: 40, height: 40, background: "rgba(91,141,238,0.10)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0, marginRight: 14 }}>
                    {f.icon}
                  </div>
                  <div>
                    <div style={{ color: "#f1f1f3", fontWeight: 600, fontSize: 14 }}>{f.title}</div>
                    <div style={{ color: "#8b8fa8", fontSize: 13 }}>{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sağ panel - giriş formu */}
          <div className="col-12 col-lg-6 d-flex flex-column justify-content-center align-items-center px-3 px-md-5 py-5">
            {/* Mobilde logo */}
            <div className="d-lg-none mb-4 text-center">
              <span style={{ fontSize: "22px", color: "#5b8dee" }}>⬡</span>
              <span style={{ color: "#f1f1f3", fontSize: "17px", fontWeight: 500, marginLeft: 10 }}>AI Financial Platform</span>
            </div>

            <div style={{ width: "100%", maxWidth: 400 }}>
              <h3 style={{ color: "#f1f1f3", fontWeight: 700, marginBottom: 8, fontSize: "1.5rem" }}>Hesabınıza giriş yapın</h3>
              <p style={{ color: "#8b8fa8", marginBottom: 32, fontSize: 14 }}>Demo: test@example.com / Sifre123</p>

              {error && (
                <div className="alert" style={{ background: "rgba(255,107,107,0.10)", border: "1px solid rgba(255,107,107,0.3)", color: "#ff6b6b", borderRadius: 10, padding: "12px 16px", marginBottom: 20, fontSize: 14 }}>
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label style={{ color: "#8b8fa8", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6, display: "block" }}>E-posta</label>
                  <input
                    type="email"
                    className="form-control"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    placeholder="ornek@eposta.com"
                    style={{ background: "#21253a", border: "1px solid rgba(255,255,255,0.12)", color: "#f1f1f3", borderRadius: 10, padding: "12px 16px", fontSize: 15 }}
                  />
                </div>
                <div className="mb-4">
                  <label style={{ color: "#8b8fa8", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6, display: "block" }}>Şifre</label>
                  <input
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    style={{ background: "#21253a", border: "1px solid rgba(255,255,255,0.12)", color: "#f1f1f3", borderRadius: 10, padding: "12px 16px", fontSize: 15 }}
                  />
                </div>
                <button
                  type="submit"
                  className="btn w-100"
                  disabled={isSubmitting}
                  style={{ background: "#5b8dee", color: "#fff", border: "none", borderRadius: 10, padding: "13px", fontSize: 15, fontWeight: 600 }}
                >
                  {isSubmitting ? <Spinner /> : "Giriş Yap"}
                </button>
              </form>

              <p style={{ color: "#8b8fa8", textAlign: "center", marginTop: 24, fontSize: 14 }}>
                Hesabınız yok mu?{" "}
                <Link to="/register" style={{ color: "#5b8dee", textDecoration: "none", fontWeight: 500 }}>Kayıt olun</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

