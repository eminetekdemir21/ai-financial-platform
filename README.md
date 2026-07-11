# AI Financial Platform

Bankacılık sektörüne yönelik, yapay zekâ destekli kişisel finans analiz platformu. Kullanıcılar banka ekstrelerini (CSV/Excel) yükleyerek işlemlerini otomatik kategorilendirebilir, şüpheli işlemleri tespit ettirebilir, finansal sağlık skorlarını görebilir, gelecek ay tahminleri alabilir, finansal hedefler belirleyip yapay zekâdan kişiselleştirilmiş planlar isteyebilir ve kendi verileriyle sohbet edebilir.

Bu proje bir yazılım/AI mühendisliği stajı kapsamında, sıfırdan uçtan uca geliştirilmiştir.

## Özellikler

- **Kimlik Doğrulama** — JWT (Bearer token) tabanlı kayıt/giriş sistemi
- **Hesap ve İşlem Yönetimi** — Çoklu banka hesabı desteği, CSV/Excel ekstre yükleme
- **Mükerrer Kayıt Koruması** — Aynı ekstrenin yanlışlıkla iki kez yüklenmesi durumunda otomatik tekilleştirme
- **AI Kategorilendirme** — Kural tabanlı + TF-IDF embedding hibrit sınıflandırma (market, fatura, abonelik, ulaşım vb.)
- **Fraud Detection** — Büyük tutar sapması, alışılmadık saat, mükerrer işlem ve yüksek frekans sinyalleriyle şüpheli işlem tespiti
- **Financial Health Score** — Tasarruf oranı, gider çeşitliliği, fraud riski, gelir istikrarı ve harcama trendinden hesaplanan 0-100 arası puan
- **Time Series Forecasting** — Geçmiş verilere dayanarak gelecek ayın net nakit akışı tahmini
- **AI Finansal Asistan** — Kullanıcının gerçek işlem verisine dayanarak doğal dilde soru cevaplayan LLM destekli sohbet (Google Gemini)
- **AI Destekli Hedef Planlayıcı** — Finansal hedef tanımlama, ilerleme takibi ve LLM tarafından üretilen kişiselleştirilmiş tasarruf planı
- **Otomatik Testler** — 60+ pytest testi, GitHub Actions ile her push'ta otomatik çalışır

## Teknoloji Yığını

**Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL (pgvector), Alembic, Pydantic, JWT, pandas, scikit-learn, Google Generative AI (Gemini)

**Frontend:** React, TypeScript, Vite, Tailwind CSS

**Altyapı:** Docker, Docker Compose, Redis, Celery, GitHub Actions

## Proje Yapısı

```
ai-financial-platform/
├── backend/
│   ├── app/
│   │   ├── core/              # Config, database, security
│   │   ├── domains/
│   │   │   ├── auth/           # Kimlik doğrulama
│   │   │   ├── transactions/   # Hesaplar, işlemler, CSV/Excel parser
│   │   │   ├── categorization/ # AI kategorilendirme
│   │   │   ├── fraud/          # Fraud detection
│   │   │   ├── financial_health/ # Health score
│   │   │   ├── forecasting/    # Gelecek ay tahmini
│   │   │   ├── assistant/      # LLM finansal asistan
│   │   │   └── goal_planner/   # AI hedef planlayıcı
│   │   └── main.py
│   ├── alembic/                # Veritabanı migration'ları
│   ├── tests/                  # pytest test paketi
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                # Backend API istemcileri
│       ├── components/         # Yeniden kullanılabilir bileşenler
│       ├── context/             # Auth context
│       └── pages/               # Login, Register, Dashboard
├── .github/workflows/          # CI/CD (GitHub Actions)
└── docker-compose.yml
```

## Kurulum

### Gereksinimler

- Docker ve Docker Compose
- Node.js (v18+)

### Backend

1. `backend/.env.example` dosyasını `backend/.env` olarak kopyalayın, gerekli değerleri doldurun (özellikle `SECRET_KEY` ve isterseniz `LLM_API_KEY`).
2. Proje kök dizininde:

```bash
docker compose up --build -d
```

3. API dokümantasyonu: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Uygulama: http://localhost:5173

## Testler

```bash
docker exec afp_backend python -m pytest -v
```

## LLM Özellikleri Hakkında

AI Finansal Asistan ve Hedef Planlayıcı'nın AI analiz özelliği, Google Gemini API kullanır. Bu özellikleri denemek için `backend/.env` dosyasındaki `LLM_API_KEY` alanına [Google AI Studio](https://aistudio.google.com/apikey) üzerinden alınan bir API anahtarı girilmelidir. Anahtar girilmezse bu uç noktalar `503 Service Unavailable` ile anlamlı bir hata mesajı döner; sistemin geri kalanı bundan etkilenmez.

## Lisans

Bu proje eğitim/staj amaçlı geliştirilmiştir.
