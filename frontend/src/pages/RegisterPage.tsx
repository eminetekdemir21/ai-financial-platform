import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Spinner from "../components/Spinner";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(email, password, fullName);
      navigate("/dashboard");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Kayıt başarısız. Bilgilerinizi kontrol edin.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const features = [
    { icon: "⚡", title: "Saniyeler içinde kurulum", desc: "CSV yükle, AI analiz etsin" },
    { icon: "🔒", title: "Güvenli ve özel", desc: "Verileriniz şifreli ve güvende" },
    { icon: "🤖", title: "Kişisel AI asistan", desc: "Verilerinize dayalı öneriler" },
    { icon: "📈", title: "Gerçek zamanlı içgörüler", desc: "Finansal sağlık skoru ve tahminler" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#0f1117" }}>
      <div className="container-fluid" style={{ minHeight: "100vh" }}>
        <div className="row" style={{ minHeight: "100vh" }}>

          {/* Sol panel - sadece geniş ekranda */}
          <div className="col-lg-6 d-none d-lg-flex flex-column justify-content-center px-5" style={{ background: "rgba(124,109,232,0.04)", borderRight: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="mb-5">
              <span style={{ fontSize: "22px", color: "#7c6de8" }}>⬡</span>
              <span style={{ color: "#f1f1f3", fontSize: "17px", fontWeight: 500, marginLeft: 10 }}>AI Financial Platform</span>
            </div>
            <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "#f1f1f3", lineHeight: 1.2, marginBottom: 16 }}>
              Finansal geleceğinizi<br />
              <span style={{ color: "#7c6de8" }}>bugün şekillendirin.</span>
            </h1>
            <p style={{ fontSize: "14px", color: "#8b8fa8", lineHeight: 1.7, maxWidth: 400, marginBottom: 40 }}>
              Ücretsiz hesap oluşturun, banka ekstrelerinizi yükleyin ve yapay zekânın finansal analizinizi saniyeler içinde tamamlamasını izleyin.
            </p>
            {features.map(f => (
              <div key={f.title} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14 }}>
                <div style={{ width: 38, height: 38, borderRadius: 10, background: "rgba(124,109,232,0.10)", border: "0.5px solid rgba(124,109,232,0.18)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 17, flexShrink: 0 }}>
                  {f.icon}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "#f1f1f3" }}>{f.title}</div>
                  <div style={{ fontSize: 12, color: "#8b8fa8" }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Sağ panel - form */}
          <div className="col-12 col-lg-6 d-flex flex-column justify-content-center align-items-center px-3 px-md-5 py-5">
            {/* Mobilde logo */}
            <div className="d-lg-none mb-4 text-center">
              <span style={{ fontSize: "22px", color: "#7c6de8" }}>⬡</span>
              <span style={{ color: "#f1f1f3", fontSize: "17px", fontWeight: 500, marginLeft: 10 }}>AI Financial Platform</span>
            </div>

            <div style={{ width: "100%", maxWidth: 420, background: "#1a1d27", border: "0.5px solid rgba(255,255,255,0.08)", borderRadius: 16, padding: 36 }}>
              <h2 style={{ fontSize: 22, fontWeight: 500, color: "#f1f1f3", marginBottom: 6 }}>Hesap Oluştur</h2>
              <p style={{ fontSize: 13, color: "#8b8fa8", marginBottom: 24 }}>Birkaç saniyede ücretsiz hesabınızı açın.</p>

              {error && (
                <div style={{ display: "flex", alignItems: "flex-start", gap: 8, background: "rgba(255,107,107,0.08)", border: "0.5px solid rgba(255,107,107,0.2)", borderRadius: 8, padding: "10px 12px", marginBottom: 16 }}>
                  <span style={{ color: "#ff6b6b" }}>⚠</span>
                  <span style={{ color: "#ff6b6b", fontSize: 13 }}>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit}>
                {[
                  { label: "Ad Soyad", type: "text", value: fullName, onChange: setFullName, placeholder: "Ad Soyad" },
                  { label: "E-posta", type: "email", value: email, onChange: setEmail, placeholder: "ornek@eposta.com" },
                  { label: "Şifre", type: "password", value: password, onChange: setPassword, placeholder: "En az 8 karakter", minLength: 8 },
                ].map(field => (
                  <div key={field.label} className="mb-3">
                    <label style={{ display: "block", fontSize: 11, color: "#8b8fa8", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.5px" }}>{field.label}</label>
                    <input
                      type={field.type}
                      required
                      value={field.value}
                      onChange={e => field.onChange(e.target.value)}
                      placeholder={field.placeholder}
                      minLength={field.minLength}
                      className="form-control"
                      style={{ background: "#21253a", border: "0.5px solid rgba(255,255,255,0.12)", borderRadius: 8, padding: "10px 14px", fontSize: 14, color: "#f1f1f3" }}
                    />
                  </div>
                ))}

                <button type="submit" disabled={isSubmitting} className="btn w-100"
                  style={{ background: "#7c6de8", color: "#fff", borderRadius: 8, padding: 11, fontSize: 14, fontWeight: 500, border: "none", opacity: isSubmitting ? 0.7 : 1, marginTop: 8 }}>
                  {isSubmitting && <Spinner size={14} />}
                  {isSubmitting ? "Hesap oluşturuluyor..." : "Hesap Oluştur"}
                </button>
              </form>

              <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "#8b8fa8" }}>
                Zaten hesabınız var mı?{" "}
                <Link to="/login" style={{ color: "#7c6de8", textDecoration: "none", fontWeight: 500 }}>Giriş yapın</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
